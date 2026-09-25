"""Chave local persistente, separada do código versionado."""
import os
import secrets
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured


def local_secret(base_dir):
    directory = Path(base_dir) / '.local'
    # No Windows, herdar as ACLs do projeto preserva o acesso do propriet?rio.
    directory.mkdir(mode=0o777 if os.name == 'nt' else 0o700, exist_ok=True)
    path = directory / 'django-secret.key'
    try:
        with path.open('x', encoding='utf-8') as stream:
            stream.write(secrets.token_urlsafe(64))
        path.chmod(0o600)
    except FileExistsError:
        pass
    value = path.read_text(encoding='utf-8').strip()
    if len(value) < 50:
        raise ImproperlyConfigured('A chave em .local/django-secret.key está inválida.')
    return value
