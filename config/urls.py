from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rastreamento import painel, celular
from rastreamento.views import DispositivoViewSet, LocalizacaoViewSet, PessoaViewSet

router = DefaultRouter()
router.register('pessoas', PessoaViewSet, basename='pessoa')
router.register('dispositivos', DispositivoViewSet, basename='dispositivo')
router.register('localizacoes', LocalizacaoViewSet, basename='localizacao')
urlpatterns = [
    path('celular/', include('config.mobile_urls')),
    path('painel/dispositivos/<uuid:dispositivo_id>/link/', celular.gerar_link, name='gerar-link'),
    path('painel/dispositivos/<uuid:dispositivo_id>/revogar/', celular.revogar_links, name='revogar-links'),
    path('', painel.painel, name='painel'),
    path('entrar/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('painel/pessoas/', painel.cadastrar_pessoa, name='cadastrar-pessoa'),
    path('painel/dispositivos/', painel.cadastrar_dispositivo, name='cadastrar-dispositivo'),
    path('painel/pessoas/<uuid:pessoa_id>/compartilhamento/', painel.compartilhar, name='compartilhar'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]
admin.site.site_header = 'Sistema de Rastreio'
admin.site.site_title = 'Sistema de Rastreio'
admin.site.index_title = 'Administração'
