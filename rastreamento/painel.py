from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import DispositivoForm, PessoaForm
from .models import Dispositivo, Localizacao, Pessoa


def pessoa_do_usuario(user, identificador):
    try:
        identificador = UUID(str(identificador))
    except (ValueError, TypeError, AttributeError):
        raise Http404('Pessoa não encontrada.')
    return get_object_or_404(Pessoa, pk=identificador, responsavel=user)


@never_cache
@login_required
def painel(request):
    pessoas = Pessoa.objects.filter(responsavel=request.user)
    selecionada = pessoa_do_usuario(request.user, request.GET['pessoa']) if request.GET.get('pessoa') else pessoas.first()
    dispositivos = Dispositivo.objects.filter(pessoa=selecionada) if selecionada else Dispositivo.objects.none()
    historico = Localizacao.objects.filter(dispositivo__pessoa=selecionada).select_related('dispositivo') if selecionada else Localizacao.objects.none()
    ultima = historico.first()
    pagina = Paginator(historico, 20).get_page(request.GET.get('pagina'))
    pontos = [{
        'latitude': float(p.latitude), 'longitude': float(p.longitude),
        'precisao': p.precisao_metros, 'capturado_em': p.capturado_em.isoformat(),
        'dispositivo': p.dispositivo.nome,
    } for p in pagina]
    return render(request, 'rastreamento/painel.html', {
        'pessoas': pessoas, 'selecionada': selecionada, 'dispositivos': dispositivos,
        'dispositivos_ativos': dispositivos.filter(ativo=True),
        'ultima': ultima, 'posicao_antiga': bool(ultima and ultima.capturado_em < timezone.now() - timedelta(minutes=15)),
        'pagina': pagina, 'pontos': pontos, 'map_config': {'tile_url': settings.MAP_TILE_URL, 'attribution': settings.MAP_ATTRIBUTION},
        'total_pessoas': pessoas.count(),
        'total_dispositivos': Dispositivo.objects.filter(pessoa__responsavel=request.user).count(),
        'pessoa_form': PessoaForm(auto_id='pessoa_%s'),
        'dispositivo_form': DispositivoForm(user=request.user, initial={'pessoa': selecionada}, auto_id='dispositivo_%s'),
    })


@login_required
@require_POST
def cadastrar_pessoa(request):
    form = PessoaForm(request.POST)
    if form.is_valid():
        pessoa = form.save(commit=False)
        pessoa.responsavel = request.user
        pessoa.save()
        messages.success(request, 'Pessoa cadastrada. O compartilhamento começa desativado.')
        return redirect(f"{reverse('painel')}?pessoa={pessoa.pk}")
    messages.error(request, 'Não foi possível cadastrar: ' + '; '.join(error for errors in form.errors.values() for error in errors))
    return redirect('painel')


@login_required
@require_POST
def cadastrar_dispositivo(request):
    form = DispositivoForm(request.POST, user=request.user)
    if form.is_valid():
        dispositivo = form.save()
        messages.success(request, 'Dispositivo cadastrado.')
        return redirect(f"{reverse('painel')}?pessoa={dispositivo.pessoa_id}")
    messages.error(request, 'Verifique o nome e selecione uma pessoa do seu cadastro.')
    return redirect('painel')


@login_required
@require_POST
def compartilhar(request, pessoa_id):
    pessoa = pessoa_do_usuario(request.user, pessoa_id)
    ativar = request.POST.get('ativo') == 'true'
    if ativar and request.POST.get('autorizado') != 'on':
        messages.error(request, 'Confirme que o compartilhamento está autorizado antes de ativá-lo.')
    else:
        pessoa.compartilhamento_ativo = ativar
        pessoa.save(update_fields=['compartilhamento_ativo'])
        messages.success(request, 'Compartilhamento ativado.' if ativar else 'Compartilhamento desativado. Novos envios estão bloqueados.')
    return redirect(f"{reverse('painel')}?pessoa={pessoa.pk}")
