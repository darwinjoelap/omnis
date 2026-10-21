from django.urls import path

from . import views

app_name = 'plataforma'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nuevo/', views.nuevo, name='nuevo'),
    path('<int:pk>/', views.editar, name='editar'),
    path('<int:pk>/renovar/', views.renovar, name='renovar'),
    path('<int:pk>/entrar/', views.entrar, name='entrar'),
    path('salir/', views.salir, name='salir'),
    path('tasas/', views.tasas, name='tasas'),
]
