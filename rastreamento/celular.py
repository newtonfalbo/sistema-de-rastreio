import base64
import hashlib
import json
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
from django.db import transaction
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import Dispositivo, LinkDispositivo
from .serializers import LocalizacaoSerializer


def public_origin():
    value = os.environ.get('RASTREIO_PUBLIC_ORIGIN', '')
    if not value:
        try:
            value = (settings.BASE_DIR / '.local' / 'mobile-origin.txt').read_text(encoding='utf-8-sig').strip()
        except FileNotFoundError:
            return ''
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
        return ''
    return value.rstrip('/')


def links_validos():
    return LinkDispositivo.objects.filter(
        expira_em__gt=timezone.now(), utilizado_em__isnull=True, revogado_em__isnull=True,
        dispositivo__ativo=True, dispositivo__pessoa__compartilhamento_ativo=True,
        dispositivo__pessoa__responsavel__is_active=True,
    )


def emitir_link(dispositivo):
    token = secrets.token_urlsafe(32)
    with transaction.atomic():
        Dispositivo.objects.select_for_update().get(pk=dispositivo.pk)
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
    link, token = emitir_link(dispositivo)
    url = f'{origin}/celular/#{token}'
    output = BytesIO()
    qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage).save(output)
    qr = base64.b64encode(output.getvalue()).decode('ascii')
    return render(request, 'rastreamento/link_dispositivo.html', {'dispositivo': dispositivo, 'link_url': url, 'expira_em': link.expira_em, 'qr_svg': qr})


@login_required
@require_POST
def revogar_links(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, pk=dispositivo_id, pessoa__responsavel=request.user)
    LinkDispositivo.objects.filter(dispositivo=dispositivo, utilizado_em__isnull=True, revogado_em__isnull=True).update(revogado_em=timezone.now())
    messages.success(request, 'Links pendentes deste dispositivo foram revogados.')
    return redirect(f"{reverse('painel')}?pessoa={dispositivo.pessoa_id}")


@never_cache
@ensure_csrf_cookie
@require_GET
def pagina_celular(request):
    response = render(request, 'rastreamento/celular.html')
    response['Content-Security-Policy'] = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    return response


def carregar_link(request):
    try:
        payload = json.loads(request.body)
        token = payload.get('token', '')
        if not isinstance(token, str) or not 32 <= len(token) <= 128:
            raise ValueError
    except (ValueError, AttributeError, UnicodeError):
        return None, None
    link = links_validos().select_related('dispositivo__pessoa__responsavel').filter(token_hash=hashlib.sha256(token.encode()).hexdigest()).first()
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
    data = {name: payload.get(name) for name in ['latitude', 'longitude', 'precisao_metros', 'capturado_em']}
    data['dispositivo'] = str(link.dispositivo_id)
    serializer = LocalizacaoSerializer(data=data, context={'request': SimpleNamespace(user=link.dispositivo.pessoa.responsavel)})
    if not serializer.is_valid():
        return JsonResponse({'detail': 'Coordenadas ou data inválidas.', 'errors': serializer.errors}, status=400)
    with transaction.atomic():
        # Uma atualização condicional consome o link: envios concorrentes não duplicam a posição.
        if links_validos().filter(pk=link.pk).update(utilizado_em=timezone.now()) != 1:
            return indisponivel()
        serializer.save()
    return JsonResponse({'detail': 'Posição registrada. Este link já foi utilizado.'}, status=201)


@require_GET
def asset_celular(request, arquivo):
    if arquivo not in {'celular.css', 'celular.js'}:
        raise Http404
    path = settings.BASE_DIR / 'rastreamento' / 'static' / 'rastreamento' / arquivo
    return FileResponse(path.open('rb'), content_type='text/css' if arquivo.endswith('.css') else 'application/javascript')
