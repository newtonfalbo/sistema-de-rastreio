from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class RevogacaoSessaoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='sessao_ficticia', password='Senha-teste-932!')
        self.first, self.second = Client(), Client()
        self.first.force_login(self.user)
        self.second.force_login(self.user)

    def test_reativar_conta_nao_recupera_sessoes_anteriores(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
        for client in [self.first, self.second]:
            self.assertEqual(client.get('/').status_code, 302)
            self.assertNotIn('_auth_user_id', client.session)
        self.assertEqual(self.first.post('/entrar/', {'username': self.user.username, 'password': 'Senha-teste-932!'}).status_code, 302)
        self.assertEqual(self.first.get('/').status_code, 200)

    def test_edicao_parcial_nao_revoga_sessao_nem_afeta_outra_conta(self):
        other = get_user_model().objects.create_user(username='outra_sessao')
        client = Client()
        client.force_login(other)
        self.user.is_active = False
        self.user.first_name = 'Nome ficticio'
        self.user.save(update_fields=['first_name'])
        self.assertEqual(self.first.get('/').status_code, 200)
        self.user.save(update_fields=['is_active'])
        self.assertEqual(client.get('/').status_code, 200)

    def test_sessao_sem_versao_precisa_entrar_novamente(self):
        session = self.first.session
        session.pop('rastreio_auth_version', None)
        session.save()
        self.assertEqual(self.first.get('/api/pessoas/').status_code, 401)
