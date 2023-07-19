from django.db import models

class Colaborador(models.Model):
    nome = models.CharField(max_length=35, null=True)
    cpf = models.CharField(max_length=11, unique=True)
    email = models.CharField(unique=True, max_length=60, null=True)
    login = models.CharField(unique=True, max_length=50)
    senha = models.CharField(max_length=80, null=True)
    ativo = models.BooleanField(null=True)

    @property
    def cpf_formatado(self):
        # Aplica a máscara no CPF formatado
        cpf = self.cpf
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    def __str__(self):
        return self.nome