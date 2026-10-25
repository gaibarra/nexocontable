from django.contrib import admin
from django.urls import path, include
from panel.gateway import proxy

urlpatterns = [
    path('panel/', proxy, name='panel_proxy'),
    path('panel/<path:ruta>', proxy, name='panel_proxy'),
    path('admin/', admin.site.urls),

    # App de cuentas: registro, login, dashboard, tenants, perfil
    path('', include('cuentas.urls')),

    # App de catálogo: cuentas contables y manuales (requiere tenant)
    path('catalogo/', include('catalogo.urls')),

    # App de donaciones: Mercado Pago
    path('donar/', include('donaciones.urls')),
]
