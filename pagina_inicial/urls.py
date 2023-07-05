from django.urls import path
from . import views

urlpatterns = [
    path("pagina_inicial/", views.Pagina_inicial, name='pagina_inicial'),
]
