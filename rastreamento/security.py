from django.conf import settings
from django.utils.cache import add_never_cache_headers


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
