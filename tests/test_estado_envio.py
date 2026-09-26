from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from rastreamento.autorizacao import AVISO_VERSAO
from rastreamento.models import Dispositivo, Localizacao, Pessoa
from rastreamento.serializers import DispositivoSerializer, LocalizacaoSerializer, PessoaSerializer
from rastreamento.views import DispositivoViewSet, PessoaViewSet
from rastreamento.celular import emitir_link


class EstadoEnvioTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='dono_estado_teste')
        self.other = get_user_model().objects.create_user(username='outro_estado_teste')
        self.person = Pessoa.objects.create(nome='Pessoa fictícia', responsavel=self.owner, compartilhamento_ativo=True)
        self.device = Dispositivo.objects.create(nome='Dispositivo fictício', pessoa=self.person)
        self.context = {'request': SimpleNamespace(user=self.owner)}

    def validated_position(self):
        serializer = LocalizacaoSerializer(data={
            'dispositivo': str(self.device.pk), 'latitude': '0', 'longitude': '0',
            'capturado_em': timezone.now().isoformat(), 'autorizado': True, 'aviso_versao': AVISO_VERSAO,
        }, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        return serializer

    def test_person_disabled_between_validation_and_save_blocks_position(self):
        serializer = self.validated_position()
        self.person.compartilhamento_ativo = False
        self.person.save(update_fields=['compartilhamento_ativo'])
        with self.assertRaises(ValidationError):
            serializer.save()
        self.assertFalse(Localizacao.objects.exists())

    def test_device_disabled_between_validation_and_save_blocks_position(self):
        serializer = self.validated_position()
        self.device.ativo = False
        self.device.save(update_fields=['ativo'])
        with self.assertRaises(ValidationError):
            serializer.save()
        self.assertFalse(Localizacao.objects.exists())

    def test_account_disabled_between_validation_and_save_blocks_position(self):
        serializer = self.validated_position()
        get_user_model().objects.filter(pk=self.owner.pk).update(is_active=False)
        with self.assertRaises(ValidationError):
            serializer.save()
        self.assertFalse(Localizacao.objects.exists())

    def test_owner_changed_between_validation_and_save_blocks_position(self):
        serializer = self.validated_position()
        self.person.responsavel = self.other
        self.person.save(update_fields=['responsavel'])
        with self.assertRaises(ValidationError):
            serializer.save()
        self.assertFalse(Localizacao.objects.exists())

    def test_person_rename_does_not_restore_stale_sharing_state(self):
        serializer = PessoaSerializer(self.person, data={'nome': 'Nome corrigido'}, partial=True, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        current = Pessoa.objects.get(pk=self.person.pk)
        current.compartilhamento_ativo = False
        current.save(update_fields=['compartilhamento_ativo'])
        serializer.save()
        current.refresh_from_db()
        self.assertFalse(current.compartilhamento_ativo)
        self.assertEqual(current.nome, 'Nome corrigido')

    def test_device_rename_does_not_restore_stale_active_state(self):
        serializer = DispositivoSerializer(self.device, data={'nome': 'Nome corrigido'}, partial=True, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        current = Dispositivo.objects.get(pk=self.device.pk)
        current.ativo = False
        current.save(update_fields=['ativo'])
        serializer.save()
        current.refresh_from_db()
        self.assertFalse(current.ativo)

    def test_ownership_change_blocks_previously_validated_edit(self):
        serializer = PessoaSerializer(self.person, data={'nome': 'Alteração antiga'}, partial=True, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        current = Pessoa.objects.get(pk=self.person.pk)
        current.responsavel = self.other
        current.save(update_fields=['responsavel'])
        with self.assertRaises(ValidationError):
            serializer.save()
        current.refresh_from_db()
        self.assertEqual(current.responsavel, self.other)
        self.assertEqual(current.nome, 'Pessoa fictícia')

    def test_ownership_change_blocks_device_creation(self):
        serializer = DispositivoSerializer(data={'pessoa': str(self.person.pk), 'nome': 'Novo fictício'}, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.person.responsavel = self.other
        self.person.save(update_fields=['responsavel'])
        with self.assertRaises(ValidationError):
            serializer.save()
        self.assertEqual(Dispositivo.objects.count(), 1)

    def test_disabled_account_cannot_finish_person_creation(self):
        serializer = PessoaSerializer(data={'nome': 'Novo fictício'}, context=self.context)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        get_user_model().objects.filter(pk=self.owner.pk).update(is_active=False)
        with self.assertRaises(ValidationError):
            serializer.save()
        self.assertEqual(Pessoa.objects.count(), 1)

    def test_ownership_change_blocks_previously_authorized_deletion(self):
        self.person.responsavel = self.other
        self.person.save(update_fields=['responsavel'])
        for view_type, instance in [(PessoaViewSet, self.person), (DispositivoViewSet, self.device)]:
            with self.subTest(view=view_type.__name__):
                view = view_type()
                view.request = self.context['request']
                with self.assertRaises(NotFound):
                    view.perform_destroy(instance)
        self.assertTrue(Pessoa.objects.filter(pk=self.person.pk).exists())
        self.assertTrue(Dispositivo.objects.filter(pk=self.device.pk).exists())

    def test_mobile_deactivation_after_validation_returns_unavailable(self):
        link, token = emitir_link(self.device)
        payload = dict(self.validated_position().initial_data)
        payload.pop('dispositivo')
        payload['token'] = token
        original = LocalizacaoSerializer.is_valid

        def deactivate(serializer, *args, **kwargs):
            valid = original(serializer, *args, **kwargs)
            self.device.ativo = False
            self.device.save(update_fields=['ativo'])
            return valid

        with patch.object(LocalizacaoSerializer, 'is_valid', deactivate):
            response = self.client.post('/celular/enviar/', payload, content_type='application/json')
        self.assertEqual(response.status_code, 410)
        link.refresh_from_db()
        self.assertIsNone(link.utilizado_em)
        self.assertFalse(Localizacao.objects.exists())

    def test_failed_mobile_save_rolls_back_link_consumption(self):
        link, token = emitir_link(self.device)
        payload = dict(self.validated_position().initial_data)
        payload.pop('dispositivo')
        payload['token'] = token
        with patch.object(LocalizacaoSerializer, 'save', side_effect=ValidationError('simulated state change')):
            response = self.client.post('/celular/enviar/', payload, content_type='application/json')
        self.assertEqual(response.status_code, 410)
        link.refresh_from_db()
        self.assertIsNone(link.utilizado_em)
        self.assertFalse(Localizacao.objects.exists())
        self.assertEqual(self.client.post('/celular/enviar/', payload, content_type='application/json').status_code, 201)
