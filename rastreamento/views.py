from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Dispositivo, Localizacao, Pessoa
from .serializers import DispositivoSerializer, FiltrosLocalizacaoSerializer, LocalizacaoSerializer, PessoaSerializer


class PessoaViewSet(viewsets.ModelViewSet):
    serializer_class = PessoaSerializer

    def get_queryset(self):
        return Pessoa.objects.filter(responsavel=self.request.user)

    def perform_create(self, serializer):
        serializer.save(responsavel=self.request.user)

    @action(detail=True, methods=["get"], url_path="ultima-localizacao")
    def ultima_localizacao(self, request, pk=None):
        pessoa = self.get_object()
        localizacao = Localizacao.objects.filter(dispositivo__pessoa=pessoa).first()
        if localizacao is None:
            return Response({"detail": "Esta pessoa ainda não possui localizações."}, status=status.HTTP_404_NOT_FOUND)
        return Response(LocalizacaoSerializer(localizacao, context=self.get_serializer_context()).data)


class DispositivoViewSet(viewsets.ModelViewSet):
    serializer_class = DispositivoSerializer

    def get_queryset(self):
        return Dispositivo.objects.select_related("pessoa").filter(pessoa__responsavel=self.request.user)


class LocalizacaoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = LocalizacaoSerializer

    def get_queryset(self):
        queryset = Localizacao.objects.select_related("dispositivo__pessoa").filter(dispositivo__pessoa__responsavel=self.request.user)
        filtros = FiltrosLocalizacaoSerializer(data=self.request.query_params)
        filtros.is_valid(raise_exception=True)
        campos = {"pessoa": "dispositivo__pessoa_id", "dispositivo": "dispositivo_id", "inicio": "capturado_em__gte", "fim": "capturado_em__lte"}
        return queryset.filter(**{campos[key]: value for key, value in filtros.validated_data.items()})
