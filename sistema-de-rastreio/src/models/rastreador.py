from django.db import models
from django.contrib.auth.models import User

# Modelo da pessoa que será rastreada
class Pessoa(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return self.nome


# Modelo que guarda as localizações de cada pessoa
class Localizacao(models.Model):
    pessoa = models.ForeignKey(Pessoa, on_delete=models.CASCADE, related_name="localizacoes")
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pessoa.nome} @ {self.timestamp}"