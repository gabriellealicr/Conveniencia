from django.contrib import admin
from .models import Estoque, MovimentacaoEstoque

# Register your models here.
admin.site.register(Estoque)
admin.site.register(MovimentacaoEstoque)
