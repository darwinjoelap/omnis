from django.urls import path

from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.tablero, name='tablero'),
    path('pdf/', views.pdf, name='pdf'),
    path('excel/', views.excel, name='excel'),
]
