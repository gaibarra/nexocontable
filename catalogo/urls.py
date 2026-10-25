from django.urls import path
from . import views

urlpatterns = [
    # Catálogo de cuentas
    path('', views.catalogo_cuentas, name='catalogo_cuentas'),
    path('confirmar/<int:pk>/', views.confirmar_relacion, name='confirmar_relacion'),
    path('agregar/', views.agregar_cuenta, name='agregar_cuenta'),
    path('subir/', views.subir_catalogo, name='subir_catalogo'),
    path('plantilla/', views.descargar_plantilla, name='descargar_plantilla'),
    path('plantillas/', views.gestionar_plantillas, name='gestionar_plantillas'),
    path('plantillas/nueva/', views.crear_plantilla, name='crear_plantilla'),
    path('plantillas/<int:pk>/editar/', views.editar_plantilla, name='editar_plantilla'),
    path('plantillas/<int:pk>/eliminar/', views.eliminar_plantilla, name='eliminar_plantilla'),
    path('eliminar/<int:pk>/', views.eliminar_cuenta, name='eliminar_cuenta'),

    # Manuales
    path('generar-manual/', views.generar_manual, name='generar_manual'),
    path('manual/<int:pk>/', views.detalle_manual, name='detalle_manual'),
    path('manual/<int:pk>/exportar/', views.exportar_manual, name='exportar_manual'),
    path('manual/<int:pk>/editar/', views.editar_manual, name='editar_manual'),
    path('manual/<int:pk>/eliminar/', views.eliminar_manual, name='eliminar_manual'),
    path('manual/<int:pk>/actualizar-presentacion/', views.actualizar_presentacion_manual, name='actualizar_presentacion_manual'),
    path('manual/<int:pk>/aprobar/', views.aprobar_manual, name='aprobar_manual'),
]
