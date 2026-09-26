from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from rastreamento.celular import emitir_link
from rastreamento.models import Dispositivo, LinkDispositivo, Pessoa


class RevogacaoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='dono_revogacao')
        self.person = Pessoa.objects.create(nome='Pessoa fictícia', responsavel=self.user, compartilhamento_ativo=True)
        self.device = Dispositivo.objects.create(nome='Celular fictício', pessoa=self.person)
        self.link, self.token = emitir_link(self.device)

    def verify_old(self):
        return self.client.post('/celular/verificar/', {'token': self.token}, content_type='application/json')

    def test_person_reactivation_does_not_restore_old_link(self):
        self.person.compartilhamento_ativo = False
        self.person.save(update_fields=['compartilhamento_ativo'])
        self.person.compartilhamento_ativo = True
        self.person.save(update_fields=['compartilhamento_ativo'])
        self.assertEqual(self.verify_old().status_code, 410)
        self.link.refresh_from_db()
        self.assertIsNotNone(self.link.revogado_em)

    def test_device_reactivation_does_not_restore_old_link(self):
        self.device.ativo = False
        self.device.save(update_fields=['ativo'])
        self.device.ativo = True
        self.device.save(update_fields=['ativo'])
        self.assertEqual(self.verify_old().status_code, 410)

    def test_account_reactivation_does_not_restore_old_link(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
        self.assertEqual(self.verify_old().status_code, 410)

    def test_api_disabling_person_revokes_pending_link(self):
        api = APIClient()
        api.force_authenticate(self.user)
        self.assertEqual(api.patch(f'/api/pessoas/{self.person.pk}/', {'compartilhamento_ativo': False}, format='json').status_code, 200)
        self.link.refresh_from_db()
        self.assertIsNotNone(self.link.revogado_em)

    def test_panel_disabling_person_revokes_pending_link(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(f'/painel/pessoas/{self.person.pk}/compartilhamento/', {'ativo': 'false'}).status_code, 302)
        self.link.refresh_from_db()
        self.assertIsNotNone(self.link.revogado_em)

    def test_stale_device_instance_cannot_issue_after_disabling(self):
        Dispositivo.objects.filter(pk=self.device.pk).update(ativo=False)
        with self.assertRaises(ValueError):
            emitir_link(self.device)
        self.assertEqual(LinkDispositivo.objects.count(), 1)

    def test_changing_owner_revokes_old_link(self):
        other = get_user_model().objects.create_user(username='novo_dono_teste')
        self.person.responsavel = other
        self.person.save(update_fields=['responsavel'])
        self.assertEqual(self.verify_old().status_code, 410)

    def test_failure_to_revoke_rolls_back_person_or_device_deactivation(self):
        for instance, field in [(self.person, 'compartilhamento_ativo'), (self.device, 'ativo')]:
            with self.subTest(field=field):
                setattr(instance, field, False)
                with patch('django.db.models.query.QuerySet.update', side_effect=IntegrityError('simulated failure')):
                    with self.assertRaises(IntegrityError):
                        instance.save(update_fields=[field])
                instance.refresh_from_db()
                self.assertTrue(getattr(instance, field))
                self.assertEqual(self.verify_old().status_code, 200)

    def test_new_link_after_reactivation_is_valid_but_old_remains_revoked(self):
        self.person.compartilhamento_ativo = False
        self.person.save()
        self.person.compartilhamento_ativo = True
        self.person.save()
        _, token = emitir_link(self.device)
        self.assertEqual(self.verify_old().status_code, 410)
        self.assertEqual(self.client.post('/celular/verificar/', {'token': token}, content_type='application/json').status_code, 200)

    def test_unrelated_partial_save_does_not_revoke_link(self):
        self.person.compartilhamento_ativo = False
        self.person.nome = 'Nome fictício corrigido'
        self.person.save(update_fields=['nome'])
        self.assertEqual(self.verify_old().status_code, 200)

    def test_used_link_history_is_not_rewritten_on_deactivation(self):
        from django.utils import timezone
        used = timezone.now()
        LinkDispositivo.objects.filter(pk=self.link.pk).update(utilizado_em=used)
        self.person.compartilhamento_ativo = False
        self.person.save()
        self.link.refresh_from_db()
        self.assertEqual(self.link.utilizado_em, used)
        self.assertIsNone(self.link.revogado_em)

    def test_upgrade_revokes_only_pending_links_and_keeps_existing_timestamps(self):
        from importlib import import_module
        from types import SimpleNamespace
        from django.apps import apps
        from django.utils import timezone
        used = LinkDispositivo.objects.create(dispositivo=self.device, token_hash='a' * 64,
                                             expira_em=self.link.expira_em, utilizado_em=timezone.now())
        revoked = LinkDispositivo.objects.create(dispositivo=self.device, token_hash='b' * 64,
                                                expira_em=self.link.expira_em, revogado_em=timezone.now())
        used_at, revoked_at = used.utilizado_em, revoked.revogado_em
        migration = import_module('rastreamento.migrations.0004_revogar_links_anteriores')
        migration.revogar_pendentes(apps, SimpleNamespace(connection=SimpleNamespace(alias='default')))
        self.link.refresh_from_db()
        used.refresh_from_db()
        revoked.refresh_from_db()
        self.assertIsNotNone(self.link.revogado_em)
        self.assertEqual(used.utilizado_em, used_at)
        self.assertIsNone(used.revogado_em)
        self.assertEqual(revoked.revogado_em, revoked_at)
