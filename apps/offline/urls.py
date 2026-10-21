from django.urls import path

from . import views

app_name = 'offline'

urlpatterns = [
    path('ping/', views.ping, name='ping'),
    path('precache/', views.precache, name='precache'),
]
