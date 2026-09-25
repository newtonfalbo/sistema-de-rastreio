from django.contrib import admin

from .models import Dispositivo, Localizacao, Pessoa


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
