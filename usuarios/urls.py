from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.Login, name='login'),
    path("logout/", views.Logout, name='logout'),
    path("cadastrar_usuario/", views.Cadastro, name='cadastrar_usuario'),
    path("visualizar_usuarios/", views.Visualizar, name='visualizar_usuarios'),
    path("inativar_usuario/<int:usuario_id>/", views.Inativar, name="inativar_usuario"),
    path("ativar_usuario/<int:usuario_id>/", views.Ativar, name="ativar_usuario"),
    path("acessar_usuario/<int:usuario_id>/", views.Acessar, name="acessar_usuario"),
    path("alterar_usuario/<int:usuario_id>/", views.Alterar, name="alterar_usuario"),
]
