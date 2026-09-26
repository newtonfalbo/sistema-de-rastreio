from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from rastreamento.autorizacao import AVISO_TEXTO, AVISO_VERSAO
from rastreamento.celular import emitir_link
from rastreamento.models import Dispositivo, Localizacao, Pessoa


class AutorizacaoEnvioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='participante_teste')
        cls.pessoa = Pessoa.objects.create(nome='Participante fictício', responsavel=cls.user, compartilhamento_ativo=True)
        cls.dispositivo = Dispositivo.objects.create(nome='Aparelho fictício', pessoa=cls.pessoa)

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(self.user)
        self.payload = {
            'dispositivo': str(self.dispositivo.pk), 'latitude': '0', 'longitude': '0',
            'capturado_em': timezone.now().isoformat(), 'autorizado': True, 'aviso_versao': AVISO_VERSAO,
        }

    def test_missing_false_or_stale_confirmation_does_not_create_position(self):
        for field, value in [('autorizado', False), ('autorizado', None), ('aviso_versao', 'old'), ('aviso_versao', None)]:
            data = {**self.payload, field: value}
            if value is None:
                data.pop(field)
            with self.subTest(field=field, value=value):
                self.assertEqual(self.api.post('/api/localizacoes/', data, format='json').status_code, 400)
        self.assertFalse(Localizacao.objects.exists())

    def test_server_records_snapshot_time_and_channel_not_client_values(self):
        before = timezone.now()
        response = self.api.post('/api/localizacoes/', {
            **self.payload, 'autorizacao_texto': 'texto adulterado', 'autorizacao_versao': 'forjada',
            'autorizacao_recebida_em': '2000-01-01T00:00:00Z', 'canal_envio': 'link',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        point = Localizacao.objects.get()
        self.assertEqual(point.autorizacao_texto, AVISO_TEXTO)
        self.assertEqual(point.autorizacao_versao, AVISO_VERSAO)
        self.assertGreaterEqual(point.autorizacao_recebida_em, before)
        self.assertEqual(point.canal_envio, 'api')
        self.assertNotIn('autorizado', response.data)

    def test_authenticated_session_is_distinguished_from_api_token(self):
        api = APIClient()
        api.force_login(self.user)
        response = api.post('/api/localizacoes/', self.payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Localizacao.objects.get().canal_envio, 'sessao')

    def test_mobile_stale_notice_does_not_consume_link(self):
        link, token = emitir_link(self.dispositivo)
        data = {k: v for k, v in self.payload.items() if k != 'dispositivo'}
        data.update(token=token, aviso_versao='old')
        self.assertEqual(self.client.post('/celular/enviar/', data, content_type='application/json').status_code, 400)
        link.refresh_from_db()
        self.assertIsNone(link.utilizado_em)
        self.assertFalse(Localizacao.objects.exists())
        data['aviso_versao'] = AVISO_VERSAO
        self.assertEqual(self.client.post('/celular/enviar/', data, content_type='application/json').status_code, 201)
        self.assertEqual(Localizacao.objects.get().canal_envio, 'link')
        self.assertEqual(Localizacao.objects.get().autorizacao_texto, AVISO_TEXTO)

    def test_legacy_rows_do_not_gain_fabricated_authorization(self):
        point = Localizacao.objects.create(dispositivo=self.dispositivo, latitude=0, longitude=0, capturado_em=timezone.now())
        self.assertEqual(point.canal_envio, 'legado')
        self.assertEqual(point.autorizacao_texto, '')
        self.assertIsNone(point.autorizacao_recebida_em)

    def test_notice_endpoint_requires_authentication_and_is_not_cached(self):
        self.assertEqual(self.client.get('/api/aviso-envio/').status_code, 401)
        response = self.api.get('/api/aviso-envio/')
        self.assertEqual(response.data, {'versao': AVISO_VERSAO, 'texto': AVISO_TEXTO})
        self.assertIn('no-store', response['Cache-Control'])

    def test_mobile_page_displays_the_recorded_notice_and_version(self):
        response = self.client.get('/celular/')
        self.assertContains(response, AVISO_TEXTO)
        self.assertContains(response, AVISO_VERSAO)
