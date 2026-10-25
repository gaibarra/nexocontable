from django.urls import path
from . import views, crud
app_name = 'panel'
urlpatterns = [
    path('registros/<str:tipo>/nuevo/', crud.formulario, name='registro_nuevo'),
    path('registros/<str:tipo>/<int:pk>/', crud.ver, name='registro_ver'),
    path('registros/<str:tipo>/<int:pk>/editar/', crud.formulario, name='registro_editar'),
    path('registros/<str:tipo>/<int:pk>/eliminar/', crud.eliminar, name='registro_eliminar'),
    path('', views.inicio, name='inicio'),
    path('login/', views.login, name='login'), path('verificar/', views.verificar, name='verificar'), path('logout/', views.logout, name='logout'),
    path('crm/', views.crm, name='crm'), path('crm/nuevo/', views.contacto_form, name='contacto_nuevo'),
    path('crm/sincronizar/', views.sincronizar, name='sincronizar'),
    path('crm/<int:pk>/', views.contacto, name='contacto'), path('crm/<int:pk>/editar/', views.contacto_form, name='contacto_editar'),
    path('crm/<int:pk>/nota/', views.nota, name='nota'), path('crm/<int:pk>/tarea/', views.tarea, name='tarea'),
    path('tareas/<int:pk>/completar/', views.completar_tarea, name='completar_tarea'),
    path('actividad/', views.actividad, name='actividad'), path('usuarios/', views.usuarios, name='usuarios'),
    path('usuarios/<int:pk>/', views.usuario, name='usuario'), path('usuarios/<int:pk>/estado/', views.estado_usuario, name='estado_usuario'),
    path('organizaciones/', views.organizaciones, name='organizaciones'), path('organizaciones/<int:pk>/estado/', views.estado_organizacion, name='estado_organizacion'),
    path('inteligencia/', views.inteligencia, name='inteligencia'), path('donativos/', views.donativos, name='donativos'),
    path('oportunidades/', views.oportunidades, name='oportunidades'), path('controles/', views.controles, name='controles'),
    path('salud/', views.salud, name='salud'),
]
