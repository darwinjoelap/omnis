from django.urls import path

from . import views

app_name = 'cobros'

urlpatterns = [
    path('servicios/', views.servicios, name='servicios'),
    path('servicios/<int:pk>/', views.servicio_editar, name='servicio_editar'),
    path('pacientes/<int:paciente_pk>/', views.cuenta, name='cuenta'),
    path('cargos/<int:pk>/anular/', views.cargo_anular, name='cargo_anular'),
    path('pagos/<int:pk>/anular/', views.pago_anular, name='pago_anular'),
    path('por-cobrar/', views.por_cobrar, name='por_cobrar'),
    path('caja/', views.caja, name='caja'),
]
