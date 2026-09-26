"""Invalida links e token de API quando uma conta é desativada."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from rest_framework.authtoken.models import Token

from .models import EstadoSessao, LinkDispositivo


@receiver(user_logged_in, dispatch_uid='rastreio_marcar_versao_sessao')
def marcar_versao_sessao(sender, request, user, **kwargs):
    with transaction.atomic():
        current = get_user_model().objects.select_for_update().filter(pk=user.pk, is_active=True).first()
        if current is None:
            request.session.flush()
            raise PermissionDenied('Conta indisponível. Entre novamente.')
        state, _ = EstadoSessao.objects.get_or_create(usuario=current)
        request.session['rastreio_auth_version'] = state.versao


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='rastreio_revogar_conta_inativa')
def revogar_conta_inativa(sender, instance, created, raw, using, update_fields, **kwargs):
    if raw or created or instance.is_active or (update_fields is not None and 'is_active' not in update_fields):
        return
    with transaction.atomic(using=using):
        state, _ = EstadoSessao.objects.using(using).get_or_create(usuario_id=instance.pk)
        EstadoSessao.objects.using(using).filter(pk=state.pk).update(versao=F('versao') + 1)
        LinkDispositivo.objects.using(using).filter(
            dispositivo__pessoa__responsavel_id=instance.pk, utilizado_em__isnull=True, revogado_em__isnull=True,
        ).update(revogado_em=timezone.now())
        Token.objects.using(using).filter(user_id=instance.pk).delete()
