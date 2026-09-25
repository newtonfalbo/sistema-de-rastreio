import hashlib
import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from rastreamento.celular import emitir_link
from rastreamento.models import Dispositivo, LinkDispositivo, Localizacao, Pessoa


class LinkCelularTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='dono_link')
        cls.outro = get_user_model().objects.create_user(username='outro_link')
        cls.pessoa = Pessoa.objects.create(nome='Pessoa teste', responsavel=cls.user, compartilhamento_ativo=True)
        cls.dispositivo = Dispositivo.objects.create(nome='Dispositivo teste', pessoa=cls.pessoa)

    def setUp(self):
        self.link, self.token = emitir_link(self.dispositivo)

    def post(self, action='verificar', **extra):
        return self.client.post(f'/celular/{action}/', {'token': self.token, **extra}, content_type='application/json')

    def posicao(self, **extra):
        data = dict(autorizado=True, latitude='-3.73', longitude='-38.52', capturado_em=timezone.now().isoformat())
        data.update(extra)
        return self.post('enviar', **data)

    def test_pagina_generica_nao_revela_cadastro_e_nao_coleta(self):
        response = self.client.get('/celular/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.pessoa.nome)
        self.assertNotContains(response, self.token)
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn("script-src 'self'", response['Content-Security-Policy'])

    def test_apenas_hash_e_armazenado(self):
        self.assertEqual(self.link.token_hash, hashlib.sha256(self.token.encode()).hexdigest())
        self.assertNotIn(self.token, str(self.link.__dict__))

    def test_validacao_nao_consume_link(self):
        self.assertEqual(self.post().status_code, 200)
        self.link.refresh_from_db()
        self.assertIsNone(self.link.utilizado_em)

    def test_envio_unico_e_sem_leitura_do_historico(self):
        response = self.posicao()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Localizacao.objects.get().dispositivo_id, self.dispositivo.pk)
        self.assertEqual(self.posicao().status_code, 410)
        self.assertEqual(self.post().status_code, 410)
        self.assertEqual(Localizacao.objects.count(), 1)
        self.assertNotIn('latitude', response.json())

    def test_consentimento_e_obrigatorio(self):
        self.assertEqual(self.posicao(autorizado=False).status_code, 400)
        self.assertFalse(Localizacao.objects.exists())

    def test_link_nao_permite_escolher_outro_dispositivo(self):
        self.assertEqual(self.posicao(dispositivo=str(self.dispositivo.pk)).status_code, 400)
        self.assertFalse(Localizacao.objects.exists())

    def test_posicao_invalida_nao_consume_link(self):
        self.assertEqual(self.posicao(latitude='100').status_code, 400)
        self.assertEqual(self.posicao().status_code, 201)

    def test_expirado_revogado_e_invalido(self):
        LinkDispositivo.objects.filter(pk=self.link.pk).update(expira_em=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.posicao().status_code, 410)
        self.link, self.token = emitir_link(self.dispositivo)
        LinkDispositivo.objects.filter(pk=self.link.pk).update(revogado_em=timezone.now())
        self.assertEqual(self.posicao().status_code, 410)
        self.assertEqual(self.post(token='x'*43).status_code, 410)

    def test_gerar_novo_link_revoga_anterior(self):
        emitir_link(self.dispositivo)
        self.assertEqual(self.posicao().status_code, 410)

    def test_compartilhamento_desativado_bloqueia_envio(self):
        self.pessoa.compartilhamento_ativo = False
        self.pessoa.save()
        self.assertEqual(self.posicao().status_code, 410)

    def test_dispositivo_inativo_bloqueia_envio(self):
        self.dispositivo.ativo = False
        self.dispositivo.save()
        self.assertEqual(self.posicao().status_code, 410)

    def test_responsavel_inativo_bloqueia_envio(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.posicao().status_code, 410)

    @patch('rastreamento.celular.public_origin', return_value='https://mobile.example.com')
    def test_geracao_exige_dono_e_mostra_qr_local(self, _origin):
        url = f'/painel/dispositivos/{self.dispositivo.pk}/link/'
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.outro)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(self.user)
        response = self.client.post(url)
        self.assertContains(response, 'data:image/svg+xml;base64,')
        self.assertContains(response, 'https://mobile.example.com/celular/#')
        self.assertIn('no-store', response['Cache-Control'])

    def test_revogacao_exige_dono(self):
        url = f'/painel/dispositivos/{self.dispositivo.pk}/revogar/'
        self.client.force_login(self.outro)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(self.posicao().status_code, 410)

    def test_csrf_obrigatorio_e_aceito_com_cookie(self):
        client = Client(enforce_csrf_checks=True)
        data = {'token': self.token}
        self.assertEqual(client.post('/celular/verificar/', data, content_type='application/json').status_code, 403)
        client.get('/celular/')
        from django.conf import settings
        cookie = client.cookies[settings.CSRF_COOKIE_NAME].value
        self.assertEqual(client.post('/celular/verificar/', data, content_type='application/json', HTTP_X_CSRFTOKEN=cookie).status_code, 200)
        self.assertEqual(client.post('/celular/verificar/', data, content_type='application/json', HTTP_X_CSRFTOKEN=cookie, HTTP_ORIGIN='https://atacante.example').status_code, 403)

    @override_settings(ROOT_URLCONF='config.mobile_root_urls')
    def test_receptor_publico_nao_expoe_painel_api_ou_admin(self):
        for path in ['/', '/admin/', '/api/pessoas/', '/entrar/', '/painel/pessoas/', '/static/rastreamento/painel.js', '/celular/assets/models.py']:
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.get('/celular/').status_code, 200)
        self.assertEqual(self.client.get('/celular/assets/celular.js').status_code, 200)

    def test_dados_malformados_nao_causam_erro_500(self):
        for value in ['[1]', 'null', '{}', '{"token":true}', '{']:
            self.assertEqual(self.client.post('/celular/verificar/', value, content_type='application/json').status_code, 410)
