from django.urls import path
from . import views

urlpatterns = [
    path("cadastro_produto/", views.Cadastro, name='cadastro_produto'),
    path("visualizar_produtos/", views.Visualizar, name='visualizar_produtos'),
    path("acessar_produto/<int:produto_id>/", views.Acessar, name="acessar_produto"),
    path("inativar_produto/<int:produto_id>/", views.Inativar, name="inativar_produto"),
    path("ativar_produto/<int:produto_id>/", views.Ativar, name="ativar_produto"),
    path("alterar_produto/<int:produto_id>/", views.Alterar, name="alterar_produto"),
]
