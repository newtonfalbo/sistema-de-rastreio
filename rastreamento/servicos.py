"""Revalidação e ordem comum de bloqueios para operações autorizadas."""
from contextlib import contextmanager

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .models import Dispositivo, Pessoa


class AutorizacaoAlterada(ValueError):
    pass


@contextmanager
def responsavel_para_escrita(responsavel_id):
    try:
        with transaction.atomic():
            owner = get_user_model().objects.select_for_update().get(pk=responsavel_id, is_active=True)
            yield owner
    except ObjectDoesNotExist:
        raise AutorizacaoAlterada('Conta ou autorização alteradas.') from None


@contextmanager
def pessoa_para_escrita(pessoa_id, responsavel_id):
    try:
        with responsavel_para_escrita(responsavel_id) as owner:
            person = Pessoa.objects.select_for_update().get(pk=pessoa_id, responsavel_id=owner.pk)
            person.responsavel = owner
            yield person
    except ObjectDoesNotExist:
        raise AutorizacaoAlterada('Cadastro ou autorização alterados.') from None


@contextmanager
def dispositivo_para_escrita(dispositivo_id, responsavel_id, *, exigir_envio=True):
    try:
        reference = Dispositivo.objects.only('pessoa_id').get(pk=dispositivo_id)
        # Todas as operações seguem conta -> pessoa -> dispositivo -> link.
        with pessoa_para_escrita(reference.pessoa_id, responsavel_id) as person:
            device = Dispositivo.objects.select_for_update().get(pk=dispositivo_id, pessoa_id=person.pk)
            if exigir_envio and (not device.ativo or not person.compartilhamento_ativo):
                raise AutorizacaoAlterada('O compartilhamento ou dispositivo foi desativado.')
            device.pessoa = person
            yield device
    except ObjectDoesNotExist:
        raise AutorizacaoAlterada('Cadastro ou autorização alterados.') from None
