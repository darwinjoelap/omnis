from django.urls import path

from . import views

app_name = 'equipo'

urlpatterns = [
    path('elegir/', views.seleccionar, name='seleccionar'),
    path('sin-consultorio/', views.sin_tenant, name='sin_tenant'),
    path('', views.lista, name='lista'),
    path('agregar/', views.agregar, name='agregar'),
    path('<int:pk>/', views.actualizar, name='actualizar'),
    path('<int:pk>/clave/', views.restablecer_clave, name='clave'),
    path('<int:pk>/profesional/', views.perfil_profesional, name='perfil_profesional'),
    path('<int:pk>/profesional/quitar/', views.quitar_perfil, name='quitar_perfil'),
    path('mi-perfil-profesional/', views.mi_perfil_profesional, name='mi_perfil_profesional'),
]
