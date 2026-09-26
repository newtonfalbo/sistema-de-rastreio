import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from rastreamento.celular import public_origin


class PublicOriginTests(SimpleTestCase):
    def test_unreadable_file_disables_links_without_breaking_dashboard(self):
        with patch.dict(os.environ, {'RASTREIO_PUBLIC_ORIGIN': ''}):
            for error in [PermissionError(), UnicodeError()]:
                with self.subTest(error=type(error)), patch('pathlib.Path.read_text', side_effect=error):
                    with self.assertLogs('rastreamento.celular', level='WARNING') as captured:
                        self.assertEqual(public_origin(), '')
                    self.assertNotIn('https://', str(captured.output))

    def test_invalid_origins_are_rejected_without_exception(self):
        for value in ['https://[', 'https://example.com:invalid', 'http://example.com',
                      'https://user:password@example.com', 'https://example.com/?token=value',
                      'https://@example.com', 'https://example.com:0',
                      'https://exam\nple.com', 'https://example.com\\other']:
            with self.subTest(value=value), patch.dict(os.environ, {'RASTREIO_PUBLIC_ORIGIN': value}):
                self.assertEqual(public_origin(), '')

    def test_valid_environment_origin_takes_precedence_without_reading_file(self):
        with patch.dict(os.environ, {'RASTREIO_PUBLIC_ORIGIN': 'https://mobile.example.com/'}):
            with patch('pathlib.Path.read_text', side_effect=AssertionError('must not read file')):
                self.assertEqual(public_origin(), 'https://mobile.example.com')

    def test_receiver_uses_same_environment_origin_without_reading_file(self):
        script = Path(__file__).resolve().parents[1] / 'scripts' / 'servidor-celular.py'
        with patch.dict(os.environ, {'RASTREIO_PUBLIC_ORIGIN': 'https://mobile.example.com:8443/', 'DJANGO_SECRET_KEY': 'ficticio-' * 9}):
            with patch('pathlib.Path.read_text', side_effect=AssertionError('must not read private file')), patch('django.core.wsgi.get_wsgi_application'), patch('waitress.serve') as serve:
                runpy.run_path(str(script))
                self.assertEqual(os.environ['DJANGO_ALLOWED_HOSTS'], 'mobile.example.com')
                self.assertEqual(serve.call_args.kwargs['listen'], '127.0.0.1:8001')
                self.assertEqual(serve.call_args.kwargs['url_scheme'], 'https')
