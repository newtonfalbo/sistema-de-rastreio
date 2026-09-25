import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


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


class Localizacao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE, related_name="localizacoes")
    latitude = models.DecimalField(max_digits=10, decimal_places=7, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=10, decimal_places=7, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    precisao_metros = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    capturado_em = models.DateTimeField()
    recebido_em = models.DateTimeField(auto_now_add=True)

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
