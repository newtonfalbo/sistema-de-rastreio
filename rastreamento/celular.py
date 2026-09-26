import base64
import hashlib
import json
import logging
import os
import secrets
from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace
from urllib.parse import urlsplit

import qrcode
import qrcode.image.svg
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import Dispositivo, LinkDispositivo
from .serializers import LocalizacaoSerializer
from .autorizacao import aviso_envio
from .servicos import AutorizacaoAlterada, dispositivo_para_escrita
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


def public_origin():
    value = os.environ.get('RASTREIO_PUBLIC_ORIGIN', '')
    if not value:
        try:
            value = (settings.BASE_DIR / '.local' / 'mobile-origin.txt').read_text(encoding='utf-8-sig').strip()
        except FileNotFoundError:
            return ''
        except (OSError, UnicodeError):
            logger.warning('Endereço móvel indisponível: confira acesso e codificação do arquivo local.')
            return ''
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return ''
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
        return ''
    return value.rstrip('/')


def links_validos():
    return LinkDispositivo.objects.filter(
        expira_em__gt=timezone.now(), utilizado_em__isnull=True, revogado_em__isnull=True,
        dispositivo__ativo=True, dispositivo__pessoa__compartilhamento_ativo=True,
        dispositivo__pessoa__responsavel__is_active=True,
    )


def emitir_link(dispositivo, responsavel_id=None):
    token = secrets.token_urlsafe(32)
    if responsavel_id is None:
        responsavel_id = dispositivo.pessoa.responsavel_id
    with dispositivo_para_escrita(dispositivo.pk, responsavel_id) as dispositivo:
        LinkDispositivo.objects.filter(dispositivo=dispositivo, utilizado_em__isnull=True, revogado_em__isnull=True).update(revogado_em=timezone.now())
        link = LinkDispositivo.objects.create(dispositivo=dispositivo, token_hash=hashlib.sha256(token.encode()).hexdigest(), expira_em=timezone.now()+timedelta(minutes=30))
    return link, token


@never_cache
@login_required
@require_POST
def gerar_link(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo.objects.select_related('pessoa'), pk=dispositivo_id, pessoa__responsavel=request.user)
    origin = public_origin()
    if not origin or not dispositivo.ativo or not dispositivo.pessoa.compartilhamento_ativo:
        messages.error(request, 'Ative o dispositivo e o compartilhamento e confirme que o endereço HTTPS de teste está configurado.')
        return redirect(f"{reverse('painel')}?pessoa={dispositivo.pessoa_id}")
    try:
        link, token = emitir_link(dispositivo, responsavel_id=request.user.pk)
    except AutorizacaoAlterada:
        messages.error(request, 'O cadastro mudou. Confira dispositivo e compartilhamento antes de gerar outro link.')
        return redirect('painel')
    url = f'{origin}/celular/#{token}'
    output = BytesIO()
    qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage).save(output)
    qr = base64.b64encode(output.getvalue()).decode('ascii')
    return render(request, 'rastreamento/link_dispositivo.html', {'dispositivo': dispositivo, 'link_url': url, 'expira_em': link.expira_em, 'qr_svg': qr})


@login_required
@require_POST
def revogar_links(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, pk=dispositivo_id, pessoa__responsavel=request.user)
    try:
        with dispositivo_para_escrita(dispositivo.pk, request.user.pk, exigir_envio=False):
            LinkDispositivo.objects.filter(dispositivo=dispositivo, utilizado_em__isnull=True, revogado_em__isnull=True).update(revogado_em=timezone.now())
    except AutorizacaoAlterada:
        raise Http404('Dispositivo não encontrado.') from None
    messages.success(request, 'Links pendentes deste dispositivo foram revogados.')
    return redirect(f"{reverse('painel')}?pessoa={dispositivo.pessoa_id}")


@never_cache
@ensure_csrf_cookie
@require_GET
def pagina_celular(request):
    response = render(request, 'rastreamento/celular.html', {'aviso_envio': aviso_envio()})
    response['Content-Security-Policy'] = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    return response


def carregar_link(request):
    try:
        payload = json.loads(request.body)
        token = payload.get('token', '')
        if not isinstance(token, str) or not 32 <= len(token) <= 128:
            raise ValueError
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    except (ValueError, AttributeError, UnicodeError, RecursionError):
        return None, None
    link = links_validos().select_related('dispositivo__pessoa__responsavel').filter(token_hash=token_hash).first()
    return link, payload


def indisponivel():
    return JsonResponse({'detail': 'Link inválido, expirado, revogado ou já utilizado. Solicite um novo link ao responsável.'}, status=410)


@require_POST
def verificar_link(request):
    link, _ = carregar_link(request)
    if link is None:
        return indisponivel()
    return JsonResponse({'pessoa': link.dispositivo.pessoa.nome, 'dispositivo': link.dispositivo.nome, 'expira_em': link.expira_em.isoformat()})


@require_POST
def enviar_posicao(request):
    link, payload = carregar_link(request)
    if link is None:
        return indisponivel()
    if payload.get('autorizado') is not True:
        return JsonResponse({'detail': 'Autorize o envio pontual antes de continuar.'}, status=400)
    if 'dispositivo' in payload or 'pessoa' in payload:
        return JsonResponse({'detail': 'O vínculo do dispositivo é definido exclusivamente pelo link.'}, status=400)
    data = {name: payload.get(name) for name in ['latitude', 'longitude', 'precisao_metros', 'capturado_em', 'autorizado', 'aviso_versao']}
    data['dispositivo'] = str(link.dispositivo_id)
    serializer = LocalizacaoSerializer(data=data, context={'request': SimpleNamespace(user=link.dispositivo.pessoa.responsavel), 'canal_envio': 'link'})
    if not serializer.is_valid():
        return JsonResponse({'detail': 'Envio inválido. Confira os dados; se a página estiver antiga, reabra o link para ler o aviso atual.', 'errors': serializer.errors}, status=400)
    try:
        with dispositivo_para_escrita(link.dispositivo_id, link.dispositivo.pessoa.responsavel_id):
            # O link só é consumido após bloquear/revalidar o vínculo; a gravação é atômica.
            if links_validos().filter(pk=link.pk).update(utilizado_em=timezone.now()) != 1:
                return indisponivel()
            serializer.save()
    except (AutorizacaoAlterada, ValidationError):
        return indisponivel()
    return JsonResponse({'detail': 'Posição registrada. Este link já foi utilizado.'}, status=201)


@require_GET
def asset_celular(request, arquivo):
    if arquivo not in {'celular.css', 'celular.js'}:
        raise Http404
    path = settings.BASE_DIR / 'rastreamento' / 'static' / 'rastreamento' / arquivo
    return FileResponse(path.open('rb'), content_type='text/css' if arquivo.endswith('.css') else 'application/javascript')
