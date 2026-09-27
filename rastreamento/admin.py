from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.db import router, transaction
from django.utils import timezone
from rest_framework.authtoken.models import Token

from .models import Dispositivo, LinkDispositivo, Localizacao, Pessoa


class RevogarAcessosPasswordForm(AdminPasswordChangeForm):
    def save(self, commit=True):
        if not commit:
            return super().save(commit=False)
        using = router.db_for_write(type(self.user), instance=self.user)
        with transaction.atomic(using=using):
            self.user = type(self.user).objects.using(using).select_for_update().get(pk=self.user.pk)
            user = super().save(commit=True)
            Token.objects.using(using).filter(user_id=user.pk).delete()
            LinkDispositivo.objects.using(using).filter(
                dispositivo__pessoa__responsavel_id=user.pk,
                utilizado_em__isnull=True, revogado_em__isnull=True,
            ).update(revogado_em=timezone.now())
        return user


class RastreioUserAdmin(UserAdmin):
    change_password_form = RevogarAcessosPasswordForm


admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), RastreioUserAdmin)


class SomenteSuperusuarioAdmin(admin.ModelAdmin):
    """A API é por responsável; o painel global é exclusivo do superusuário."""
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Pessoa)
class PessoaAdmin(SomenteSuperusuarioAdmin):
    list_display = ["nome", "responsavel", "compartilhamento_ativo", "criado_em"]
    list_filter = ["compartilhamento_ativo"]
    search_fields = ["nome", "responsavel__username"]
    readonly_fields = ["id", "criado_em"]


@admin.register(Dispositivo)
class DispositivoAdmin(SomenteSuperusuarioAdmin):
    list_display = ["nome", "pessoa", "ativo"]
    list_filter = ["ativo"]
    readonly_fields = ["id", "criado_em"]

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + (["pessoa"] if obj else [])


@admin.register(Localizacao)
class LocalizacaoAdmin(SomenteSuperusuarioAdmin):
    list_display = ["dispositivo", "latitude", "longitude", "capturado_em", "recebido_em"]
    list_select_related = ["dispositivo"]
    readonly_fields = [field.name for field in Localizacao._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
