"""Receptor isolado do celular. Não publica o painel administrativo."""
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from config.storage import data_directory
from config.mobile_origin import load_mobile_origin

private_root = data_directory(root)
try:
    origin = load_mobile_origin(root)
except (OSError, UnicodeError, ValueError):
    raise SystemExit('Configure uma origem HTTPS válida e acessível para o receptor.') from None
parsed = urlsplit(origin)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.mobile_settings'
os.environ['DJANGO_DEBUG'] = 'false'
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = (private_root / '.local' / 'django-secret.key').read_text(encoding='utf-8').strip()
os.environ['DJANGO_ALLOWED_HOSTS'] = parsed.hostname
from django.core.wsgi import get_wsgi_application
from waitress import serve

# Exclusivamente loopback. O único consumidor externo é o túnel HTTPS.
serve(get_wsgi_application(), listen='127.0.0.1:8001', url_scheme='https', threads=4, max_request_body_size=8192)
