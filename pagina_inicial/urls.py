from django.urls import path
from . import views

urlpatterns = [
    path("", views.Pagina_inicial, name='pagina_inicial'),
]
