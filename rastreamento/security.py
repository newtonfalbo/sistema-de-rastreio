from django.conf import settings
from django.contrib.auth import logout
from django.utils.cache import add_never_cache_headers

from .models import EstadoSessao


class SessionVersionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            version = EstadoSessao.objects.filter(usuario_id=request.user.pk).values_list('versao', flat=True).first()
            stored = request.session.get('rastreio_auth_version')
            if version is None or stored != version:
                logout(request)
        return self.get_response(request)


def direct_client_ip(request):
    # Não confiar em X-Forwarded-For enviado pelo cliente. Proxy exige configuração própria.
    return request.META.get('REMOTE_ADDR')


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Permissions-Policy'] = 'geolocation=(self), camera=(), microphone=()'
        response['Referrer-Policy'] = settings.SECURE_REFERRER_POLICY
        # Toda resposta da aplicação pode conter informações privadas, inclusive erros.
        if not request.path.startswith('/static/'):
            add_never_cache_headers(response)
        return response
