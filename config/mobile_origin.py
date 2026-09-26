"""Origem HTTPS compartilhada pelo painel, receptor e diagnóstico."""
import os
from urllib.parse import urlsplit


def load_mobile_origin(root):
    value = os.environ.get('RASTREIO_PUBLIC_ORIGIN') or (
        root / '.local' / 'mobile-origin.txt'
    ).read_text(encoding='utf-8-sig').strip()
    if any(char.isspace() or ord(char) < 32 for char in value):
        raise ValueError('Origem móvel inválida.')
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment
            or parsed.port == 0 or '\\' in value):
        raise ValueError('Origem móvel inválida.')
    return value.rstrip('/')
