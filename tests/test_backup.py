import importlib.util
import io
import sqlite3
import tempfile
from contextlib import closing, redirect_stdout
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

spec = importlib.util.spec_from_file_location('verificar_backup', settings.BASE_DIR / 'scripts/verificar-backup.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class BackupTests(SimpleTestCase):
    def criar(self, path):
        with closing(sqlite3.connect(path)) as db, db:
            for table in ['django_migrations', 'auth_user', 'rastreamento_pessoa',
                          'rastreamento_dispositivo', 'rastreamento_localizacao',
                          'rastreamento_linkdispositivo']:
                db.execute(f'CREATE TABLE {table} (id INTEGER PRIMARY KEY)')

    def test_aprova_copia_consistente_sem_modificar_arquivo(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'origem.sqlite3'
            target = Path(directory) / 'copia.sqlite3'
            self.criar(source)
            with closing(sqlite3.connect(source)) as original, closing(sqlite3.connect(target)) as copied:
                original.backup(copied)
            before = target.read_bytes()
            backup.verificar(target)
            self.assertEqual(target.read_bytes(), before)

    def test_rejeita_ausente_vazio_corrompido_e_banco_alheio(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'privado.sqlite3'
            with self.assertRaises(OSError):
                backup.verificar(path)
            self.assertFalse(path.exists())
            for content in [b'', b'SQLite format 3\x00' + b'invalido' * 100]:
                path.write_bytes(content)
                with self.assertRaises((ValueError, sqlite3.Error)):
                    backup.verificar(path)
            path.unlink()
            with closing(sqlite3.connect(path)) as db, db:
                db.execute('CREATE TABLE outro (id INTEGER)')
            with self.assertRaises(ValueError):
                backup.verificar(path)

    def test_rejeita_referencia_quebrada_sem_imprimir_conteudo(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'privado.sqlite3'
            self.criar(path)
            with closing(sqlite3.connect(path)) as db, db:
                db.execute('CREATE TABLE filho (id INTEGER REFERENCES auth_user(id), segredo TEXT)')
                db.execute("INSERT INTO filho VALUES (99, 'dado-privado-ficticio')")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(backup.main([str(path)]), 1)
            self.assertNotIn('dado-privado-ficticio', output.getvalue())
            self.assertNotIn(str(path), output.getvalue())
