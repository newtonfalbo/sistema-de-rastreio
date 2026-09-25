import tempfile
from datetime import timedelta
from pathlib import Path

from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from config.local_secret import local_secret
from rastreamento.security import direct_client_ip


class ChaveLocalTests(SimpleTestCase):
    def test_chave_aleatoria_persistente_e_diferente_por_instalacao(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            key = local_secret(first)
            self.assertGreaterEqual(len(key), 50)
            self.assertEqual(local_secret(first), key)
            self.assertNotEqual(local_secret(second), key)

    def test_chave_corrompida_nao_e_substituida_silenciosamente(self):
        with tempfile.TemporaryDirectory() as directory:
            local_secret(directory)
            (Path(directory) / '.local' / 'django-secret.key').write_text('invalida')
            with self.assertRaises(ImproperlyConfigured):
                local_secret(directory)

    def test_ip_encaminhado_pelo_cliente_nao_e_confiavel(self):
        request = RequestFactory().get('/', REMOTE_ADDR='127.0.0.1', HTTP_X_FORWARDED_FOR='203.0.113.5')
        self.assertEqual(direct_client_ip(request), '127.0.0.1')


class SegurancaLoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(username='usuario_seguro', password='Senha-correta-935!')
        cls.outro = get_user_model().objects.create_user(username='outro_seguro', password='Senha-correta-936!')

    def falhar(self, url='/entrar/', quantidade=5):
        for _ in range(quantidade):
            response = self.client.post(url, {'username': self.usuario.username, 'password': 'Senha-errada-123'})
        return response

    def test_cinco_falhas_bloqueiam_login_inclusive_com_senha_correta(self):
        self.assertEqual(self.falhar().status_code, 429)
        response = self.client.post('/entrar/', {'username': self.usuario.username, 'password': 'Senha-correta-935!'})
        self.assertContains(response, 'Aguarde para tentar novamente', status_code=429)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_bloqueio_compartilhado_entre_login_admin_e_api_navegavel(self):
        self.falhar()
        for url in ['/admin/login/', '/api-auth/login/']:
            with self.subTest(url=url):
                response = self.client.post(url, {'username': self.usuario.username, 'password': 'Senha-correta-935!'})
                self.assertEqual(response.status_code, 429)

    def test_trocar_header_de_ip_nao_contorna_bloqueio(self):
        self.falhar()
        response = self.client.post('/entrar/', {'username': self.usuario.username, 'password': 'Senha-correta-935!'}, HTTP_X_FORWARDED_FOR='203.0.113.20')
        self.assertEqual(response.status_code, 429)

    def test_bloqueio_nao_bloqueia_outro_usuario_no_mesmo_ip(self):
        self.falhar()
        response = self.client.post('/entrar/', {'username': self.outro.username, 'password': 'Senha-correta-936!'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.outro.pk)

    def test_expiracao_libera_nova_tentativa(self):
        self.falhar()
        AccessAttempt.objects.update(attempt_time=timezone.now()-timedelta(minutes=16))
        response = self.client.post('/entrar/', {'username': self.usuario.username, 'password': 'Senha-correta-935!'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    def test_sucesso_antes_do_limite_limpa_falhas(self):
        self.falhar(quantidade=3)
        self.client.post('/entrar/', {'username': self.usuario.username, 'password': 'Senha-correta-935!'})
        self.assertFalse(AccessAttempt.objects.filter(username=self.usuario.username).exists())

    def test_senha_nao_aparece_no_registro_de_falhas(self):
        self.falhar(quantidade=1)
        self.assertNotIn('Senha-errada-123', AccessAttempt.objects.get().post_data)

    def test_login_valido_nao_redireciona_para_dominio_externo(self):
        response = self.client.post('/entrar/?next=https://example.com/', {'username': self.usuario.username, 'password': 'Senha-correta-935!'})
        self.assertEqual(response['Location'], '/')

    def test_sessao_possui_cookie_http_only_e_expira_ao_fechar(self):
        response = self.client.post('/entrar/', {'username': self.usuario.username, 'password': 'Senha-correta-935!'})
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'Lax')
        self.assertEqual(cookie['max-age'], '')
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_headers_de_protecao_em_paginas_e_api(self):
        for url in ['/', '/entrar/', '/api/pessoas/', '/nao-existe/']:
            response = self.client.get(url)
            self.assertIn('no-store', response.headers['Cache-Control'])
            self.assertEqual(response.headers['Permissions-Policy'], 'geolocation=(self), camera=(), microphone=()')
            self.assertEqual(response.headers['Referrer-Policy'], 'same-origin')
            self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
            self.assertEqual(response.headers['X-Frame-Options'], 'DENY')

    def test_resposta_api_autenticada_nao_pode_ser_armazenada_em_cache(self):
        client = APIClient()
        token = Token.objects.create(user=self.usuario)
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = client.get('/api/pessoas/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response.headers['Cache-Control'])
