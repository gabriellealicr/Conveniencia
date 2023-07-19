from django.urls import path
from . import views

urlpatterns = [
    path("estoque/", views.Visualizar, name='estoque'),
    path("att_qtd_entrada/<int:estoque_id>/", views.Att_qtd_entrada, name='att_qtd_entrada'),
    path("att_qtd_saida/<int:estoque_id>/", views.Att_qtd_saida, name='att_qtd_saida'),
    path("entrada_estoque/<int:estoque_id>/", views.Entrada_estoque, name='entrada_estoque'),
    path("saida_estoque/<int:estoque_id>/", views.Saida_estoque, name='saida_estoque'),
    path("movimentacao/", views.Movimentacao, name='movimentacao'),
]
