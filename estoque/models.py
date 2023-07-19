from django.db import models
from produtos.models import Produto
from django.contrib.auth.models import User

class Estoque(models.Model):
    produtos = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField(null=True, default=0)

    def __str__(self):
        return f"Estoque {self.id}"
    
class MovimentacaoEstoque(models.Model):
    estoque = models.ForeignKey(Estoque, on_delete=models.CASCADE)
    data_hora = models.DateTimeField(null=True, default=0)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    quantidade_alteracao = models.IntegerField(null=True, default=0)

    tipos = (
        ('Entrada', 'Entrada'),
        ('Saída', 'Saída')
    )

    tipo = models.CharField(
            max_length=20, choices=tipos, null=True)

    def __str__(self):
        return f"Estoque {self.id}"
    