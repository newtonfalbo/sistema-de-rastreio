import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, router, transaction
from django.utils import timezone


class EstadoSessao(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='estado_sessao')
    versao = models.PositiveBigIntegerField(default=0)


class Pessoa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pessoas")
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, max_length=2000)
    compartilhamento_ativo = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome", "id"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        using = kwargs.get('using') or router.db_for_write(type(self), instance=self)
        fields = kwargs.get('update_fields')
        with transaction.atomic(using=using):
            previous_owner = None
            if not self._state.adding:
                previous_owner = type(self).objects.using(using).select_for_update().filter(pk=self.pk).values_list('responsavel_id', flat=True).first()
            super().save(*args, **kwargs)
            disabled = not self.compartilhamento_ativo and (fields is None or 'compartilhamento_ativo' in fields)
            transferred = previous_owner is not None and previous_owner != self.responsavel_id and (fields is None or {'responsavel', 'responsavel_id'}.intersection(fields))
            if disabled or transferred:
                LinkDispositivo.objects.using(using).filter(
                    dispositivo__pessoa_id=self.pk, utilizado_em__isnull=True, revogado_em__isnull=True,
                ).update(revogado_em=timezone.now())


class Dispositivo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE, related_name="dispositivos")
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome", "id"]

    def __str__(self):
        return f"{self.nome} — {self.pessoa.nome}"

    def save(self, *args, **kwargs):
        using = kwargs.get('using') or router.db_for_write(type(self), instance=self)
        fields = kwargs.get('update_fields')
        with transaction.atomic(using=using):
            previous_person = None
            if not self._state.adding:
                previous_person = type(self).objects.using(using).select_for_update().filter(pk=self.pk).values_list('pessoa_id', flat=True).first()
            super().save(*args, **kwargs)
            disabled = not self.ativo and (fields is None or 'ativo' in fields)
            transferred = previous_person is not None and previous_person != self.pessoa_id and (fields is None or {'pessoa', 'pessoa_id'}.intersection(fields))
            if disabled or transferred:
                LinkDispositivo.objects.using(using).filter(
                    dispositivo_id=self.pk, utilizado_em__isnull=True, revogado_em__isnull=True,
                ).update(revogado_em=timezone.now())


class Localizacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE, related_name="localizacoes")
    latitude = models.DecimalField(max_digits=10, decimal_places=7, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=10, decimal_places=7, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    precisao_metros = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    capturado_em = models.DateTimeField()
    recebido_em = models.DateTimeField(auto_now_add=True)
    autorizacao_versao = models.CharField(max_length=32, blank=True, default='')
    autorizacao_texto = models.TextField(blank=True, default='')
    autorizacao_recebida_em = models.DateTimeField(null=True, blank=True)
    canal_envio = models.CharField(max_length=16, default='legado', choices=[
        ('legado', 'Sem registro de autorização'), ('api', 'API autenticada'),
        ('sessao', 'Sessão autenticada'), ('link', 'Link temporário'),
    ])

    class Meta:
        ordering = ["-capturado_em", "-recebido_em", "-id"]
        indexes = [models.Index(fields=["dispositivo", "-capturado_em"], name="local_dispositivo_data_idx")]
        constraints = [
            models.CheckConstraint(condition=models.Q(latitude__gte=-90, latitude__lte=90), name="latitude_valida"),
            models.CheckConstraint(condition=models.Q(longitude__gte=-180, longitude__lte=180), name="longitude_valida"),
            models.CheckConstraint(condition=models.Q(precisao_metros__isnull=True) | models.Q(precisao_metros__gte=0), name="precisao_valida"),
        ]

    def __str__(self):
        return f"{self.dispositivo.nome} @ {self.capturado_em}"


class LinkDispositivo(models.Model):
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE, related_name='links_envio')
    token_hash = models.CharField(max_length=64, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    utilizado_em = models.DateTimeField(null=True, blank=True)
    revogado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criado_em']
