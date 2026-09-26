import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from rastreamento.autorizacao import AVISO_VERSAO
from rastreamento.celular import emitir_link
from rastreamento.models import Dispositivo, Localizacao, Pessoa
from rastreamento.security import DatabaseBusyMiddleware


def busy_error():
    cause = sqlite3.OperationalError('detalhe interno ficticio')
    cause.sqlite_errorcode = sqlite3.SQLITE_BUSY
    error = OperationalError('detalhe interno ficticio')
    error.__cause__ = cause
    return error


class BancoOcupadoTests(TestCase):
    def test_reconhece_codigo_real_do_sqlite_e_nao_oculta_outros_erros(self):
        middleware = DatabaseBusyMiddleware(lambda request: None)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'concorrencia.sqlite3'
            with closing(sqlite3.connect(path)) as first, closing(sqlite3.connect(path, timeout=0)) as second:
                first.execute('CREATE TABLE exemplo (id INTEGER)')
                first.execute('BEGIN IMMEDIATE')
                try:
                    second.execute('INSERT INTO exemplo VALUES (1)')
                except sqlite3.OperationalError as cause:
                    error = OperationalError('ocupado')
                    error.__cause__ = cause
                    self.assertEqual(middleware.process_exception(None, error).status_code, 503)
                else:
                    self.fail('O segundo escritor deveria encontrar o bloqueio.')
                finally:
                    first.rollback()
        self.assertIsNone(middleware.process_exception(None, OperationalError('database is locked')))
        self.assertIsNone(middleware.process_exception(None, ValueError('erro diferente')))

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='ocupado_ficticio')
        person = Pessoa.objects.create(responsavel=self.user, nome='Pessoa ficticia', compartilhamento_ativo=True)
        self.device = Dispositivo.objects.create(pessoa=person, nome='Dispositivo ficticio')
        self.data = {'latitude': '0', 'longitude': '0', 'capturado_em': timezone.now().isoformat(),
                     'autorizado': True, 'aviso_versao': AVISO_VERSAO}

    def conferir_resposta(self, response):
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response['Retry-After'], '2')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertNotContains(response, 'detalhe interno ficticio', status_code=503)

    def test_api_nao_confirma_posicao_quando_banco_esta_ocupado(self):
        api = APIClient()
        api.force_authenticate(self.user)
        with patch('rastreamento.serializers.LocalizacaoSerializer.save', side_effect=busy_error()):
            response = api.post('/api/localizacoes/', {**self.data, 'dispositivo': str(self.device.pk)}, format='json')
        self.conferir_resposta(response)
        self.assertFalse(Localizacao.objects.exists())

    def test_celular_desfaz_consumo_do_link_e_permite_nova_tentativa(self):
        link, token = emitir_link(self.device)
        data = {**self.data, 'token': token}
        with patch('rastreamento.serializers.LocalizacaoSerializer.save', side_effect=busy_error()):
            response = self.client.post('/celular/enviar/', data, content_type='application/json')
        self.conferir_resposta(response)
        link.refresh_from_db()
        self.assertIsNone(link.utilizado_em)
        self.assertFalse(Localizacao.objects.exists())
        response = self.client.post('/celular/enviar/', data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Localizacao.objects.count(), 1)
