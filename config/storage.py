"""Resolve o armazenamento privado sem criar ou mover dados implicitamente."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def data_directory(base_dir):
    value = os.environ.get('RASTREIO_DATA_DIR')
    if value is None:
        return Path(base_dir)
    if not value.strip():
        raise ImproperlyConfigured('RASTREIO_DATA_DIR não pode estar vazio.')
    directory = Path(value).expanduser()
    if not directory.is_absolute() or not directory.is_dir():
        raise ImproperlyConfigured('RASTREIO_DATA_DIR deve apontar para uma pasta absoluta existente.')
    return directory.resolve()
