from django.urls import path
from . import views

urlpatterns = [
    path("cadastro_colaborador/", views.Cadastro, name='cadastro_colaborador'),
    path("visualizar_colaboradores/", views.Visualizar, name='visualizar_colaboradores'),
    path("inativar_colaborador/<int:colaborador_id>/", views.Inativar, name="inativar_colaborador"),
    path("ativar_colaborador/<int:colaborador_id>/", views.Ativar, name="ativar_colaborador"),
    path("acessar_colaborador/<int:colaborador_id>/", views.Acessar, name="acessar_colaborador"),
    path("alterar_colaborador/<int:colaborador_id>/", views.Alterar, name="alterar_colaborador"),
]
