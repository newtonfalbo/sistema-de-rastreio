import contextlib
import importlib.util
import io
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request


spec = importlib.util.spec_from_file_location('mobile_connection', Path(__file__).resolve().parents[1] / 'scripts' / 'verificar-conexao-celular.py')
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)
HEADERS = {'Cache-Control': 'private, no-store', 'Referrer-Policy': 'no-referrer'}


class MobileConnectionTests(TestCase):
    def run_command(self, responses, external=False):
        output = io.StringIO()
        with patch.object(diagnostic, 'read_origin', return_value=('https://private.example', 'private.example')), patch.object(diagnostic, 'probe', side_effect=responses) as probe, contextlib.redirect_stdout(output):
            result = diagnostic.main(['--externo'] if external else [])
        self.assertNotIn('private.example', output.getvalue())
        return result, output.getvalue(), probe

    def test_local_success_does_not_claim_remote_access(self):
        result, output, probe = self.run_command([(200, HEADERS)])
        self.assertEqual(result, 0)
        self.assertIn('externo não verificado', output)
        self.assertEqual(probe.call_count, 1)
        self.assertEqual(probe.call_args.args[1:], ('http://127.0.0.1:8001/celular/', 'private.example'))

    def test_remote_isolation(self):
        result, _, probe = self.run_command([(200, HEADERS)] * 2 + [(404, HEADERS)] * 3, True)
        self.assertEqual(result, 0)
        self.assertEqual(probe.call_count, 5)
        result, _, _ = self.run_command([(200, HEADERS)] * 5, True)
        self.assertEqual(result, 1)

    def test_provider_page_and_network_failure_do_not_pass_or_leak(self):
        for response in [(200, {}), URLError('https://private.example/secret')]:
            result, output, _ = self.run_command([response])
            self.assertEqual(result, 1)
            self.assertNotIn('secret', output)

    def test_invalid_configuration_is_inconclusive(self):
        for value in ['http://example.com', 'https://user:password@example.com', 'https://example.com:bad', 'https://example.com/path', 'https://example.com?q=secret', 'https://example.com#secret', 'https://exam\nple.com']:
            with self.subTest(value=value), patch.dict(diagnostic.os.environ, {'RASTREIO_PUBLIC_ORIGIN': value}), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(diagnostic.main([]), 2)
                self.assertNotIn(value, output.getvalue())

    def test_redirect_is_not_followed(self):
        handler = diagnostic.NoRedirect()
        self.assertIsNone(handler.redirect_request(Request('https://example.com'), None, 302, '', {}, 'https://other.example'))

    def test_http_error_is_closed_and_classified(self):
        body = io.BytesIO(b'private body')
        error = HTTPError('https://private.example', 404, 'Not found', HEADERS, body)
        with patch.object(diagnostic, 'build_opener') as factory:
            factory.return_value.open.side_effect = error
            self.assertEqual(diagnostic.probe(factory.return_value, 'https://private.example'), (404, HEADERS))
        self.assertTrue(body.closed)
