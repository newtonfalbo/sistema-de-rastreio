"""Receptor isolado do celular. Não publica o painel administrativo."""
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
origin = (root / '.local' / 'mobile-origin.txt').read_text(encoding='utf-8-sig').strip()
parsed = urlsplit(origin)
if parsed.scheme != 'https' or not parsed.hostname or parsed.path not in ('', '/') or parsed.query or parsed.fragment or parsed.username:
    raise SystemExit('Configure um endereço HTTPS válido em .local/mobile-origin.txt.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.mobile_settings'
os.environ['DJANGO_DEBUG'] = 'false'
os.environ['DJANGO_SECRET_KEY'] = (root / '.local' / 'django-secret.key').read_text(encoding='utf-8').strip()
os.environ['DJANGO_ALLOWED_HOSTS'] = parsed.hostname
from django.core.wsgi import get_wsgi_application
from waitress import serve

# Exclusivamente loopback. O único consumidor externo é o túnel HTTPS.
serve(get_wsgi_application(), listen='127.0.0.1:8001', url_scheme='https', threads=4, max_request_body_size=8192)
