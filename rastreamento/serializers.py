import math
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Dispositivo, Localizacao, Pessoa


class PessoaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pessoa
        fields = ["id", "nome", "descricao", "compartilhamento_ativo", "criado_em"]
        read_only_fields = ["id", "criado_em"]


class DispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispositivo
        fields = ["id", "pessoa", "nome", "ativo", "criado_em"]
        read_only_fields = ["id", "criado_em"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pessoa"].queryset = Pessoa.objects.filter(responsavel=self.context["request"].user)

    def validate_pessoa(self, value):
        if self.instance and self.instance.pessoa_id != value.id:
            raise serializers.ValidationError("Não é permitido transferir um dispositivo. Cadastre outro dispositivo.")
        return value


class LocalizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localizacao
        fields = ["id", "dispositivo", "latitude", "longitude", "precisao_metros", "capturado_em", "recebido_em"]
        read_only_fields = ["id", "recebido_em"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["dispositivo"].queryset = Dispositivo.objects.filter(pessoa__responsavel=self.context["request"].user)

    def validate_dispositivo(self, value):
        if not value.ativo or not value.pessoa.compartilhamento_ativo:
            raise serializers.ValidationError("O dispositivo e o compartilhamento da pessoa devem estar ativos.")
        return value

    def validate_capturado_em(self, value):
        if value > timezone.now() + timedelta(minutes=5):
            raise serializers.ValidationError("A captura não pode estar mais de cinco minutos no futuro.")
        return value

    def validate_precisao_metros(self, value):
        if value is not None and (not math.isfinite(value) or value < 0):
            raise serializers.ValidationError("Informe uma precisão finita maior ou igual a zero.")
        return value


class FiltrosLocalizacaoSerializer(serializers.Serializer):
    pessoa = serializers.UUIDField(required=False)
    dispositivo = serializers.UUIDField(required=False)
    inicio = serializers.DateTimeField(required=False)
    fim = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if "inicio" in attrs and "fim" in attrs and attrs["inicio"] > attrs["fim"]:
            raise serializers.ValidationError("O início deve ser anterior ou igual ao fim.")
        return attrs
