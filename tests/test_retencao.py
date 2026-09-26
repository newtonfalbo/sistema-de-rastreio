from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from rastreamento.celular import emitir_link
from rastreamento.models import Dispositivo, LinkDispositivo, Localizacao, Pessoa


class RetencaoTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='retencao_teste')
        self.other = get_user_model().objects.create_user(username='outro_retencao')
        self.person = Pessoa.objects.create(nome='Pessoa fictícia', responsavel=self.owner, compartilhamento_ativo=True)
        self.device = Dispositivo.objects.create(nome='Dispositivo fictício', pessoa=self.person)
        other_person = Pessoa.objects.create(nome='Outra fictícia', responsavel=self.other)
        self.other_device = Dispositivo.objects.create(nome='Outro dispositivo', pessoa=other_person)
        self.cutoff = timezone.now() - timedelta(days=30)
        self.old = self.point(self.device, self.cutoff - timedelta(days=1))
        self.boundary = self.point(self.device, self.cutoff)
        self.foreign = self.point(self.other_device, self.cutoff - timedelta(days=1))

    def point(self, device, received):
        point = Localizacao.objects.create(dispositivo=device, latitude=0, longitude=0,
                                          capturado_em=self.cutoff - timedelta(days=60))
        Localizacao.objects.filter(pk=point.pk).update(recebido_em=received)
        return point

    def run_cleanup(self, **overrides):
        options = dict(tipo='localizacoes', antes=self.cutoff.isoformat(), responsavel=self.owner.pk)
        options.update(overrides)
        if options.get('responsavel') is None:
            options.pop('responsavel', None)
        output = StringIO()
        call_command('limpar_registros', stdout=output, **options)
        return output.getvalue()

    def test_default_is_simulation_without_personal_data_output(self):
        output = self.run_cleanup()
        self.assertIn('SIMULAÇÃO: 1 registros', output)
        self.assertEqual(Localizacao.objects.count(), 3)
        self.assertNotIn(str(self.old.pk), output)
        self.assertNotIn(self.person.nome, output)

    def test_confirmed_cleanup_preserves_boundary_recent_receipt_and_other_owner(self):
        recent = self.point(self.device, timezone.now())
        self.run_cleanup(confirmar=True, esperados=1)
        self.assertFalse(Localizacao.objects.filter(pk=self.old.pk).exists())
        self.assertEqual(set(Localizacao.objects.values_list('pk', flat=True)), {self.boundary.pk, self.foreign.pk, recent.pk})
        self.assertEqual(Pessoa.objects.count(), 2)
        self.assertEqual(Dispositivo.objects.count(), 2)

    def test_confirmation_requires_expected_count(self):
        with self.assertRaises(CommandError):
            self.run_cleanup(confirmar=True)
        self.assertEqual(Localizacao.objects.count(), 3)

    def test_stale_preview_and_limit_abort_without_partial_deletion(self):
        for overrides in [dict(esperados=0), dict(esperados=2)]:
            with self.subTest(overrides=overrides), self.assertRaisesMessage(CommandError, 'difere de --esperados'):
                self.run_cleanup(confirmar=True, **overrides)
            self.assertEqual(Localizacao.objects.count(), 3)
        with self.assertRaisesMessage(CommandError, 'acima de --maximo'):
            self.run_cleanup(confirmar=True, esperados=2, responsavel=None, todos=True, maximo=1)
        self.assertEqual(Localizacao.objects.count(), 3)

    def test_invalid_or_future_cutoff_is_rejected(self):
        for value in ['invalid', '2026-01-01T12:00:00', (timezone.now() + timedelta(days=1)).isoformat()]:
            with self.subTest(value=value), self.assertRaises(CommandError):
                self.run_cleanup(antes=value, confirmar=True, esperados=1)
        self.assertEqual(Localizacao.objects.count(), 3)

    def test_unknown_owner_does_not_fall_back_to_all(self):
        with self.assertRaises(CommandError):
            self.run_cleanup(responsavel=999999, confirmar=True, esperados=3)
        self.assertEqual(Localizacao.objects.count(), 3)

    def test_only_expired_links_before_cutoff_are_removed(self):
        old, _ = emitir_link(self.device)
        LinkDispositivo.objects.filter(pk=old.pk).update(expira_em=self.cutoff - timedelta(days=1))
        current, _ = emitir_link(self.device)
        self.run_cleanup(tipo='links', confirmar=True, esperados=1)
        self.assertFalse(LinkDispositivo.objects.filter(pk=old.pk).exists())
        self.assertTrue(LinkDispositivo.objects.filter(pk=current.pk).exists())
        self.assertEqual(Localizacao.objects.count(), 3)

    def test_all_owners_requires_explicit_scope(self):
        with self.assertRaises(CommandError):
            self.run_cleanup(responsavel=None, confirmar=True, esperados=2)
        self.run_cleanup(responsavel=None, todos=True, confirmar=True, esperados=2)
        self.assertEqual(list(Localizacao.objects.values_list('pk', flat=True)), [self.boundary.pk])
