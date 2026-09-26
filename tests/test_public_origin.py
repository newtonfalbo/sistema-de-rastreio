import os
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
                      'https://user:password@example.com', 'https://example.com/?token=value']:
            with self.subTest(value=value), patch.dict(os.environ, {'RASTREIO_PUBLIC_ORIGIN': value}):
                self.assertEqual(public_origin(), '')

    def test_valid_environment_origin_takes_precedence_without_reading_file(self):
        with patch.dict(os.environ, {'RASTREIO_PUBLIC_ORIGIN': 'https://mobile.example.com/'}):
            with patch('pathlib.Path.read_text', side_effect=AssertionError('must not read file')):
                self.assertEqual(public_origin(), 'https://mobile.example.com')
