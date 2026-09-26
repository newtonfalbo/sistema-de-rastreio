import math
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Dispositivo, Localizacao, Pessoa
from .autorizacao import AVISO_TEXTO, AVISO_VERSAO
from .servicos import AutorizacaoAlterada, dispositivo_para_escrita, pessoa_para_escrita, responsavel_para_escrita


class PessoaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pessoa
        fields = ["id", "nome", "descricao", "compartilhamento_ativo", "criado_em"]
        read_only_fields = ["id", "criado_em"]

    def create(self, validated_data):
        try:
            with responsavel_para_escrita(self.context['request'].user.pk) as owner:
                validated_data['responsavel'] = owner
                return super().create(validated_data)
        except AutorizacaoAlterada:
            raise serializers.ValidationError('Conta ou autorização alteradas. Entre novamente.') from None

    def update(self, instance, validated_data):
        try:
            with pessoa_para_escrita(instance.pk, self.context['request'].user.pk) as current:
                for name, value in validated_data.items():
                    setattr(current, name, value)
                current.save(update_fields=list(validated_data))
                return current
        except AutorizacaoAlterada:
            raise serializers.ValidationError('Cadastro ou autorização alterados. Atualize a página.') from None


class DispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispositivo
        fields = ["id", "pessoa", "nome", "ativo", "criado_em"]
        read_only_fields = ["id", "criado_em"]

    def create(self, validated_data):
        try:
            with pessoa_para_escrita(validated_data['pessoa'].pk, self.context['request'].user.pk) as current:
                validated_data['pessoa'] = current
                return super().create(validated_data)
        except AutorizacaoAlterada:
            raise serializers.ValidationError('Cadastro ou autorização alterados. Atualize a página.') from None

    def update(self, instance, validated_data):
        try:
            with dispositivo_para_escrita(instance.pk, self.context['request'].user.pk, exigir_envio=False) as current:
                if 'pessoa' in validated_data and validated_data['pessoa'].pk != current.pessoa_id:
                    raise serializers.ValidationError('O vínculo mudou. Não é permitido transferir um dispositivo.')
                for name, value in validated_data.items():
                    setattr(current, name, value)
                current.save(update_fields=list(validated_data))
                return current
        except AutorizacaoAlterada:
            raise serializers.ValidationError('Cadastro ou autorização alterados. Atualize a página.') from None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pessoa"].queryset = Pessoa.objects.filter(responsavel=self.context["request"].user)

    def validate_pessoa(self, value):
        if self.instance and self.instance.pessoa_id != value.id:
            raise serializers.ValidationError("Não é permitido transferir um dispositivo. Cadastre outro dispositivo.")
        return value


class LocalizacaoSerializer(serializers.ModelSerializer):
    autorizado = serializers.BooleanField(write_only=True, required=True)
    aviso_versao = serializers.ChoiceField(choices=[AVISO_VERSAO], write_only=True, required=True)

    class Meta:
        model = Localizacao
        fields = ["id", "dispositivo", "latitude", "longitude", "precisao_metros", "capturado_em", "recebido_em",
                  "autorizado", "aviso_versao", "autorizacao_versao", "autorizacao_texto", "autorizacao_recebida_em", "canal_envio"]
        read_only_fields = ["id", "recebido_em", "autorizacao_versao", "autorizacao_texto", "autorizacao_recebida_em", "canal_envio"]

    def validate_autorizado(self, value):
        if not value:
            raise serializers.ValidationError('Confirme a autorização do envio pontual.')
        return value

    def create(self, validated_data):
        validated_data.pop('autorizado')
        validated_data.pop('aviso_versao')
        try:
            with dispositivo_para_escrita(validated_data['dispositivo'].pk, self.context['request'].user.pk) as current:
                validated_data.update(
                    dispositivo=current, autorizacao_versao=AVISO_VERSAO, autorizacao_texto=AVISO_TEXTO,
                    autorizacao_recebida_em=timezone.now(), canal_envio=self.context.get('canal_envio', 'api'),
                )
                return super().create(validated_data)
        except AutorizacaoAlterada:
            raise serializers.ValidationError({'dispositivo': 'Cadastro ou compartilhamento alterados. Confira antes de enviar novamente.'}) from None

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
