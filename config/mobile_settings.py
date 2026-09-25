from .settings import *

if DEBUG:
    raise ImproperlyConfigured('O receptor público exige DJANGO_DEBUG=false.')
ROOT_URLCONF = 'config.mobile_root_urls'
SESSION_COOKIE_NAME = 'rastreio_mobile_session'
CSRF_COOKIE_NAME = 'rastreio_mobile_csrf'
DATA_UPLOAD_MAX_MEMORY_SIZE = 8192
SECURE_REFERRER_POLICY = 'no-referrer'
# Waitress recebe apenas loopback e define wsgi.url_scheme=https para este receptor.
# Não confiamos em headers X-Forwarded-* arbitrários.
