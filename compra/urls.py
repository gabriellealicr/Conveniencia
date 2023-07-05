from django.urls import path
from . import views

urlpatterns = [
    path("conveniencia/", views.Adicionar_produto, name='conveniencia'),
    path("finalizar_compra/", views.Finalizar_compra, name='finalizar_compra'),
    path("excluir_produto/<int:produto_id>/", views.Excluir_produto, name='excluir_produto'),
    path("limpar/", views.Limpar, name='limpar'),
    path("historico/", views.Historico, name='historico'),
    path("verificar_referencia/", views.Verificar_referencia, name='verificar_referencia'),
    path("relatorio_consumo/", views.Relatorio_consumo, name='relatorio_consumo'),
    path("relatorio_geral/", views.Relatorio_geral, name='relatorio_geral'),
]
