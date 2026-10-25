from django.urls import path
from . import views, marca_views
from . import password_reset
from .privacidad import aviso_privacidad

urlpatterns = [
    path('aviso-de-privacidad/', aviso_privacidad, name='aviso_privacidad'),
    path('recuperar-contrasena/', password_reset.RecuperarPasswordView.as_view(), name='password_reset'),
    path('recuperar-contrasena/enviado/', password_reset.RecuperarPasswordDoneView.as_view(), name='password_reset_done'),
    path('restablecer/<uidb64>/<token>/', password_reset.RecuperarPasswordConfirmView.as_view(), name='password_reset_confirm'),
    path('recuperar-contrasena/completado/', password_reset.RecuperarPasswordCompleteView.as_view(), name='password_reset_complete'),
    path('mi-despacho/', marca_views.mi_despacho, name='mi_despacho'),
    path('organizaciones/<int:pk>/presentacion/', marca_views.presentacion_empresa, name='presentacion_empresa'),
    path('marca/logos/<uuid:pk>/', marca_views.logo_documento, name='logo_documento'),
    path('', views.landing, name='landing'),
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('organizaciones/', views.lista_tenants, name='lista_tenants'),
    path('organizaciones/crear/', views.crear_tenant, name='crear_tenant'),
    path('organizaciones/<int:pk>/editar/', views.editar_tenant, name='editar_tenant'),
    path('organizaciones/<int:pk>/equipo/', views.equipo_tenant, name='equipo_tenant'),
    path('organizaciones/<int:pk>/seleccionar/', views.seleccionar_tenant, name='seleccionar_tenant'),
    path('organizaciones/<int:tenant_pk>/registrar/', views.registrar_usuario, name='registrar_usuario'),
    path('organizaciones/<int:tenant_pk>/miembro/<int:membresia_pk>/eliminar/', views.eliminar_miembro, name='eliminar_miembro'),
    path('invitacion/<str:token>/', views.establecer_password_invitacion, name='establecer_password_invitacion'),
]
