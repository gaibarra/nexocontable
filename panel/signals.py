from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .audit import al_confirmar

WATCHED = {'auth.user', 'cuentas.tenant', 'cuentas.membresiatenant',
           'catalogo.manualcontable', 'catalogo.usoia', 'donaciones.donativo'}


@receiver(post_save, dispatch_uid='panel_evento_guardado')
def guardado(sender, instance, created, raw=False, **kwargs):
    label = sender._meta.label_lower
    if raw or label not in WATCHED:
        return
    org = getattr(instance, 'tenant_id', None)
    if label == 'cuentas.tenant':
        org = instance.pk
    al_confirmar(categoria=label.split('.')[0], accion=f'{label}.{ "creado" if created else "actualizado"}',
                 organizacion_id=org, referencia=instance.pk)


@receiver(post_delete, dispatch_uid='panel_evento_eliminado')
def eliminado(sender, instance, **kwargs):
    if sender._meta.label_lower in WATCHED:
        al_confirmar(categoria=sender._meta.app_label, accion=f'{sender._meta.label_lower}.eliminado',
                     referencia=instance.pk, organizacion_id=getattr(instance, 'tenant_id', None))


@receiver(user_logged_in, dispatch_uid='panel_inicio_sesion')
def inicio(sender, user, **kwargs):
    al_confirmar(categoria='acceso', accion='sesion.inicio', actor=user.pk)


@receiver(user_logged_out, dispatch_uid='panel_cierre_sesion')
def cierre(sender, user, **kwargs):
    if user:
        al_confirmar(categoria='acceso', accion='sesion.cierre', actor=user.pk)


@receiver(post_save, dispatch_uid='panel_sincronizar_etapa_crm')
def actualizar_crm(sender, instance, created, raw=False, **kwargs):
    if raw or not created:
        return
    label = sender._meta.label_lower
    user_id = (instance.pk if label == 'auth.user' else
               instance.propietario_id if label == 'cuentas.tenant' else
               instance.creado_por_id if label == 'catalogo.manualcontable' else None)
    if user_id:
        from django.db import transaction
        from django.contrib.auth import get_user_model
        def actualizar():
            from .services import sincronizar_usuario
            user = get_user_model().objects.filter(pk=user_id).first()
            if user:
                sincronizar_usuario(user)
        transaction.on_commit(actualizar, robust=True)
