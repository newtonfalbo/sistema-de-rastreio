from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from rastreamento.admin import RevogarAcessosPasswordForm
from rastreamento.celular import emitir_link
from rastreamento.models import Dispositivo, Pessoa


class AdminPasswordTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('senha_ficticia', password='Anterior-931-x!')
        self.other = get_user_model().objects.create_user('outra_ficticia')
        person = Pessoa.objects.create(nome='Pessoa fictícia', responsavel=self.owner, compartilhamento_ativo=True)
        device = Dispositivo.objects.create(nome='Dispositivo fictício', pessoa=person)
        self.link, self.secret = emitir_link(device)
        self.token = Token.objects.create(user=self.owner)
        self.other_token = Token.objects.create(user=self.other)

    def form(self):
        form = RevogarAcessosPasswordForm(self.owner, {'password1': 'Nova-682-Troca!', 'password2': 'Nova-682-Troca!', 'usable_password': 'true'})
        self.assertTrue(form.is_valid(), form.errors)
        return form

    def test_admin_change_revokes_old_access_and_preserves_other_account(self):
        admin = get_user_model().objects.create_superuser('admin_ficticio', password='Admin-514-Ficticio!')
        self.client.force_login(admin)
        response = self.client.post(f'/admin/auth/user/{self.owner.pk}/password/', {
            'password1': 'Nova-682-Troca!', 'password2': 'Nova-682-Troca!', 'usable_password': 'true',
        })
        self.assertEqual(response.status_code, 302)
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.assertEqual(api.get('/api/pessoas/').status_code, 401)
        self.assertEqual(self.client.post('/celular/verificar/', {'token': self.secret}, content_type='application/json').status_code, 410)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password('Nova-682-Troca!'))
        self.assertTrue(Token.objects.filter(pk=self.other_token.pk).exists())

    def test_revocation_failure_rolls_back_password_and_token(self):
        before = self.owner.password
        with patch('django.db.models.query.QuerySet.update', side_effect=IntegrityError('ficticio')):
            with self.assertRaises(IntegrityError):
                self.form().save()
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.password, before)
        self.assertTrue(Token.objects.filter(pk=self.token.pk).exists())
        self.link.refresh_from_db()
        self.assertIsNone(self.link.revogado_em)

    def test_commit_false_does_not_revoke_or_save(self):
        before = self.owner.password
        self.form().save(commit=False)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.password, before)
        self.assertTrue(Token.objects.filter(pk=self.token.pk).exists())
