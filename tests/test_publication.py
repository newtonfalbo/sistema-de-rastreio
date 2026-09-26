import runpy
import os
import shutil
import subprocess
import sys
import sqlite3
import secrets
import tempfile
from contextlib import chdir, closing, redirect_stdout
from io import StringIO
from unittest.mock import patch
from pathlib import Path

from django.test import SimpleTestCase


scanner = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts' / 'verificar-publicacao.py'))


class PublicationTests(SimpleTestCase):
    def test_known_api_token_is_blocked_without_modifying_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            token = secrets.token_hex(20)
            database_path = root / 'db.sqlite3'
            with closing(sqlite3.connect(database_path)) as database, database:
                database.execute('CREATE TABLE authtoken_token (key TEXT)')
                database.execute('INSERT INTO authtoken_token VALUES (?)', [token])
            original = database_path.read_bytes()
            subprocess.run(['git', 'init', '-q', directory], check=True)
            (root / 'notes.txt').write_text(token, encoding='utf-8')
            subprocess.run(['git', 'add', 'notes.txt'], cwd=directory, check=True)
            with patch.dict(os.environ, {'RASTREIO_DATA_DIR': directory}):
                findings = scanner['check_index'](directory)
            self.assertTrue(findings)
            self.assertNotIn(token, str(findings))
            self.assertEqual(database_path.read_bytes(), original)

    def test_invalid_local_database_prevents_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'db.sqlite3').write_bytes(b'invalid database')
            output = StringIO()
            with chdir(directory), patch.dict(os.environ, {'RASTREIO_DATA_DIR': directory}), redirect_stdout(output):
                self.assertEqual(scanner['main'](), 2)
            self.assertNotIn('invalid database', output.getvalue())

    def test_secret_in_filename_is_detected_and_omitted_from_label(self):
        secret = 'gh' + 'p_' + 'X' * 36
        path = 'notes-' + secret + '.txt'
        self.assertTrue(scanner['inspect_blob'](path, b'innocent content'))
        self.assertNotIn(secret, scanner['safe_path_label'](path, []))

    def test_unreadable_private_file_fails_closed_without_exception_details(self):
        output = StringIO()
        with patch.object(Path, 'read_bytes', side_effect=PermissionError('private detail')):
            with redirect_stdout(output):
                self.assertEqual(scanner['main'](), 2)
        self.assertNotIn('private detail', output.getvalue())

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

    def test_known_private_key_is_detected_without_logging_value(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', directory], check=True)
            (root / '.local').mkdir()
            secret = 'fictitious-local-key-' + '7' * 50
            (root / '.local' / 'django-secret.key').write_text(secret, encoding='utf-8')
            (root / 'notes.txt').write_text(secret, encoding='utf-8')
            subprocess.run(['git', 'add', 'notes.txt'], cwd=directory, check=True)
            findings = scanner['check_index'](directory)
            self.assertTrue(findings)
            self.assertNotIn(secret, str(findings))

    def test_real_git_hook_blocks_staged_secret_and_allows_clean_commit(self):
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', directory], check=True)
            (root / '.githooks').mkdir()
            (root / 'scripts').mkdir()
            hook = root / '.githooks' / 'pre-commit'
            shutil.copyfile(project / '.githooks' / 'pre-commit', hook)
            shutil.copyfile(project / '.gitattributes', root / '.gitattributes')
            hook.chmod(0o755)
            shutil.copyfile(project / 'scripts' / 'verificar-publicacao.py', root / 'scripts' / 'verificar-publicacao.py')
            (root / 'notes.txt').write_text('safe example', encoding='utf-8')
            subprocess.run(['git', 'add', '.'], cwd=directory, check=True)
            env = {**os.environ, 'RASTREIO_PYTHON': Path(sys.executable).as_posix(), 'RASTREIO_DATA_DIR': directory, 'DJANGO_SECRET_KEY': ''}
            command = ['git', '-c', 'core.hooksPath=.githooks', '-c', 'commit.gpgSign=false',
                       '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'test']
            clean = subprocess.run(command, cwd=directory, env=env, capture_output=True)
            self.assertEqual(clean.returncode, 0, clean.stderr.decode(errors='replace'))
            secret = b'gh' + b'p_' + b'Q' * 36
            (root / 'notes.txt').write_bytes(secret)
            subprocess.run(['git', 'add', 'notes.txt'], cwd=directory, check=True)
            (root / 'notes.txt').write_text('clean working copy', encoding='utf-8')
            blocked = subprocess.run(command, cwd=directory, env=env, capture_output=True)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn(b'BLOQUEADO', blocked.stdout + blocked.stderr)
            self.assertNotIn(secret, blocked.stdout + blocked.stderr)
