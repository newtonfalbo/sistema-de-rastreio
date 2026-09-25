from django.urls import path
from rastreamento import celular

urlpatterns = [
    path('', celular.pagina_celular, name='pagina-celular'),
    path('verificar/', celular.verificar_link),
    path('enviar/', celular.enviar_posicao),
    path('assets/<str:arquivo>', celular.asset_celular),
]
