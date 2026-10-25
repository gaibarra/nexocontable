from django.urls import path
from . import views

urlpatterns = [
    path('', views.donar, name='donar'),
    path('exito/', views.donativo_exito, name='donativo_exito'),
    path('error/', views.donativo_error, name='donativo_error'),
    path('pendiente/', views.donativo_pendiente, name='donativo_pendiente'),
    path('webhook/', views.webhook_mercadopago, name='webhook_mercadopago'),
]
