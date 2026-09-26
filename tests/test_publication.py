import runpy
import subprocess
import tempfile
from pathlib import Path

from django.test import SimpleTestCase


scanner = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts' / 'verificar-publicacao.py'))


class PublicationTests(SimpleTestCase):
    def test_private_files_and_disguised_database_are_rejected(self):
        for path in ['.local/origin.txt', '.env', '.env.production', 'dados.sqlite3', 'backup.db', 'secret.pem']:
            with self.subTest(path=path):
                self.assertTrue(scanner['inspect_blob'](path, b'example'))
        self.assertTrue(scanner['inspect_blob']('innocent.txt', b'SQLite format 3\x00other'))

    def test_credentials_are_rejected_without_returning_the_value(self):
        secret = b'gh' + b'p_' + b'A' * 36
        findings = scanner['inspect_blob']('config.txt', secret)
        self.assertTrue(findings)
        self.assertNotIn(secret.decode(), str(findings))

    def test_documented_examples_and_code_are_accepted(self):
        for path in ['.env.example', 'config/local_secret.py', 'README.md']:
            self.assertEqual(scanner['inspect_blob'](path, b'DJANGO_SECRET_KEY=<configure locally>'), [])

    def test_scans_staged_content_even_after_working_copy_is_cleaned(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(['git', 'init', '-q', directory], check=True)
            file = Path(directory) / 'config.txt'
            file.write_bytes(b'gh' + b'p_' + b'A' * 36)
            subprocess.run(['git', 'add', 'config.txt'], cwd=directory, check=True)
            file.write_text('clean working copy', encoding='utf-8')
            self.assertTrue(scanner['check_index'](directory))
            subprocess.run(['git', 'add', 'config.txt'], cwd=directory, check=True)
            self.assertEqual(scanner['check_index'](directory), [])
