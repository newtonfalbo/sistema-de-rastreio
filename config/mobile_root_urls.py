from django.urls import include, path

# O túnel não publica login, administração, cadastros ou histórico.
urlpatterns = [path('celular/', include('config.mobile_urls'))]
