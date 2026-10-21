from django.urls import path

from . import views

app_name = 'documentos'

urlpatterns = [
    path('emitir/<str:codigo>/', views.emitir, name='emitir'),
    path('<int:pk>/', views.ver, name='documento'),
    path('<int:pk>/pdf/', views.pdf, name='pdf'),
    path('<int:pk>/anular/', views.anular, name='anular'),
    path('recibos/<int:pago_pk>/', views.recibo, name='recibo'),
    path('muestra/', views.prueba, name='muestra'),
    path('muestra/<int:perfil_pk>/', views.prueba, name='muestra_perfil'),
]
