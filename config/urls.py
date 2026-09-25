from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from rastreamento.views import DispositivoViewSet, LocalizacaoViewSet, PessoaViewSet

router = DefaultRouter()
router.register("pessoas", PessoaViewSet, basename="pessoa")
router.register("dispositivos", DispositivoViewSet, basename="dispositivo")
router.register("localizacoes", LocalizacaoViewSet, basename="localizacao")

urlpatterns = [
    path("", RedirectView.as_view(url="/api/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]
admin.site.site_header = "Sistema de Rastreio"
admin.site.site_title = "Sistema de Rastreio"
admin.site.index_title = "Administração"
