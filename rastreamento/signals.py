"""Invalida links quando uma conta é desativada pela administração Django."""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import LinkDispositivo


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='rastreio_revogar_conta_inativa')
def revogar_conta_inativa(sender, instance, created, raw, using, update_fields, **kwargs):
    if raw or created or instance.is_active or (update_fields is not None and 'is_active' not in update_fields):
        return
    LinkDispositivo.objects.using(using).filter(
        dispositivo__pessoa__responsavel_id=instance.pk, utilizado_em__isnull=True, revogado_em__isnull=True,
    ).update(revogado_em=timezone.now())
