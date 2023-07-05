from django.db import models

class Produto(models.Model):
    nome = models.CharField(max_length=50, null=True)
    codigo_barras = models.IntegerField(unique=True)
    preco = models.FloatField(null=True)
    ativo = models.BooleanField(null=True, default=True)

    def __str__(self):
        return self.nome
