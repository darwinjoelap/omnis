from django.urls import path

from . import views

app_name = 'pacientes'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('nuevo/', views.nuevo, name='nuevo'),
    path('opciones/', views.buscar_opciones, name='opciones'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/editar/', views.editar, name='editar'),
    path('<int:pk>/antecedentes/', views.antecedentes, name='antecedentes'),
    path('<int:pk>/representantes/nuevo/', views.representante, name='representante_nuevo'),
    path('<int:pk>/representantes/<int:rep_pk>/', views.representante, name='representante'),
    path('<int:pk>/representantes/<int:rep_pk>/eliminar/', views.representante_eliminar,
         name='representante_eliminar'),
]
