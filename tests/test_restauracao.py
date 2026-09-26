"""Ensaio funcional em processos e bancos temporários, somente com dados fictícios."""
import os
import secrets
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


SETUP = '''
import os
import django
django.setup()
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rastreamento.autorizacao import AVISO_TEXTO, AVISO_VERSAO
from rastreamento.celular import emitir_link
from rastreamento.models import Pessoa, Dispositivo, Localizacao
call_command('migrate', interactive=False, verbosity=0)
owner = get_user_model().objects.create_user(username='ensaio_a', password=os.environ['TEST_PASSWORD'])
get_user_model().objects.create_user(username='ensaio_b', password=os.environ['TEST_PASSWORD'])
person = Pessoa.objects.create(responsavel=owner, nome='Pessoa ficticia de ensaio', compartilhamento_ativo=True)
device = Dispositivo.objects.create(pessoa=person, nome='Dispositivo ficticio')
Localizacao.objects.create(dispositivo=device, latitude='10.1234567', longitude='20.7654321',
    capturado_em=timezone.now(), autorizacao_versao=AVISO_VERSAO, autorizacao_texto=AVISO_TEXTO,
    autorizacao_recebida_em=timezone.now(), canal_envio='api')
Token.objects.create(user=owner)
emitir_link(device)
client = Client()
assert client.post('/entrar/', {'username': 'ensaio_a', 'password': os.environ['TEST_PASSWORD']}).status_code == 302
'''

VERIFY = '''
import os
import django
django.setup()
from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import F
from django.test import Client
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rastreamento.autorizacao import AVISO_TEXTO, AVISO_VERSAO
from rastreamento.models import EstadoSessao, LinkDispositivo, Localizacao
# Uma copia pode recuperar acessos antigos. Invalidar somente neste banco ficticio.
assert Token.objects.count() == 1 and Session.objects.count() == 1
assert LinkDispositivo.objects.filter(revogado_em__isnull=True).count() == 1
with transaction.atomic():
    Token.objects.all().delete()
    Session.objects.all().delete()
    EstadoSessao.objects.update(versao=F('versao') + 1)
    LinkDispositivo.objects.filter(utilizado_em__isnull=True, revogado_em__isnull=True).update(revogado_em=timezone.now())
assert not Token.objects.exists() and not Session.objects.exists()
assert not LinkDispositivo.objects.filter(revogado_em__isnull=True).exists()
owner, other = Client(), Client()
for client, username in [(owner, 'ensaio_a'), (other, 'ensaio_b')]:
    assert client.post('/entrar/', {'username': username, 'password': os.environ['TEST_PASSWORD']}).status_code == 302
response = owner.get('/api/localizacoes/')
assert response.status_code == 200
data = response.json()
assert data['count'] == 1
position = data['results'][0]
assert position['latitude'] == '10.1234567' and position['longitude'] == '20.7654321'
assert position['autorizacao_versao'] == AVISO_VERSAO and position['autorizacao_texto'] == AVISO_TEXTO
assert other.get('/api/localizacoes/').json()['count'] == 0
assert other.get('/api/localizacoes/' + position['id'] + '/').status_code == 404
assert Localizacao.objects.count() == 1
'''


class RestauracaoTests(SimpleTestCase):
    def test_backup_restaurado_permite_login_e_preserva_isolamento(self):
        with tempfile.TemporaryDirectory(prefix='rastreio-ensaio-') as directory:
            root = Path(directory)
            source, restored = root / 'origem', root / 'restaurado'
            source.mkdir()
            restored.mkdir()
            env = {**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.settings',
                   'DJANGO_DEBUG': 'true', 'DJANGO_ALLOWED_HOSTS': 'testserver',
                   'DJANGO_SECRET_KEY': secrets.token_urlsafe(64),
                   'TEST_PASSWORD': secrets.token_urlsafe(32)}

            def run(code, folder):
                result = subprocess.run([sys.executable, '-c', code], cwd=settings.BASE_DIR,
                                        env={**env, 'RASTREIO_DATA_DIR': str(folder)},
                                        capture_output=True, text=True, timeout=90)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            run(SETUP, source)
            copy = root / 'backup.sqlite3'
            with closing(sqlite3.connect((source / 'db.sqlite3').as_uri() + '?mode=ro', uri=True)) as original:
                with closing(sqlite3.connect(copy)) as backup:
                    original.backup(backup)
            with closing(sqlite3.connect(copy.as_uri() + '?mode=ro', uri=True)) as backup:
                with closing(sqlite3.connect(restored / 'db.sqlite3')) as destination:
                    backup.backup(destination)
                    self.assertEqual(destination.execute('PRAGMA integrity_check').fetchall(), [('ok',)])
                    self.assertEqual(destination.execute('PRAGMA foreign_key_check').fetchall(), [])
            original_bytes = (source / 'db.sqlite3').read_bytes()
            backup_bytes = copy.read_bytes()
            run(VERIFY, restored)
            self.assertEqual((source / 'db.sqlite3').read_bytes(), original_bytes)
            self.assertEqual(copy.read_bytes(), backup_bytes)
