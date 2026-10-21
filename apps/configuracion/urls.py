from django.urls import path

from . import views

app_name = 'configuracion'

urlpatterns = [
    path('', views.editar, name='editar'),
    path('pdf-prueba/', views.pdf_prueba, name='pdf_prueba'),
    path('lugares/', views.lugares, name='lugares'),
    path('lugares/<int:pk>/', views.lugar_editar, name='lugar_editar'),
]
