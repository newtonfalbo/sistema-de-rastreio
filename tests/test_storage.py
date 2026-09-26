import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.local_secret import local_secret
from config.storage import data_directory


class PrivateStorageTests(SimpleTestCase):
    def test_default_preserves_existing_installation(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(data_directory('/project'), Path('/project'))

    def test_explicit_directory_stores_key_outside_project(self):
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as private:
            with patch.dict(os.environ, {'RASTREIO_DATA_DIR': private}):
                directory = data_directory(project)
                key = local_secret(directory)
                self.assertEqual(directory, Path(private).resolve())
                self.assertEqual(local_secret(directory), key)
                self.assertFalse((Path(project) / '.local').exists())

    def test_invalid_configuration_does_not_fall_back_or_create_directory(self):
        with tempfile.TemporaryDirectory() as project:
            missing = Path(project) / 'missing'
            for value in ['', '  ', 'relative/path', str(missing)]:
                with self.subTest(value=value), patch.dict(os.environ, {'RASTREIO_DATA_DIR': value}):
                    with self.assertRaises(ImproperlyConfigured):
                        data_directory(project)
            self.assertFalse(missing.exists())

    def test_file_is_not_accepted_as_directory(self):
        with tempfile.TemporaryDirectory() as project:
            file = Path(project) / 'file'
            file.touch()
            with patch.dict(os.environ, {'RASTREIO_DATA_DIR': str(file)}):
                with self.assertRaises(ImproperlyConfigured):
                    data_directory(project)
