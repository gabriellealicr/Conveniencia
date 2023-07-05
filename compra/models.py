from django.db import models
from produtos.models import Produto
from colaboradores.models import Colaborador
from datetime import date, datetime

class Compra(models.Model):
    data = models.DateTimeField()
    valor_total = models.FloatField(default=0)
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, null=True)
    produtos = models.ManyToManyField(Produto, through='Item_Compra')

    def __str__(self):
        return f"Compra {self.id}"
    
class Item_Compra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    preco= models.FloatField(null=True)


