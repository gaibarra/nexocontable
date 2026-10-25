from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from catalogo.models import ManualContable, UsoIA
from cuentas.models import Tenant
from .models import Contacto, Evento, Tarea


@transaction.atomic
def sincronizar_usuario(user):
    if not user.email or not user.is_active:
        return None
    email = user.email.strip().lower()
    contacto = Contacto.objects.filter(Q(usuario=user) | Q(email__iexact=email)).first()
    if contacto and contacto.usuario_id not in (None, user.pk):
        return None
    total = ManualContable.objects.filter(creado_por=user).count()
    etapa = ('recurrente' if total >= 2 else 'manual' if total else
             'organizacion' if Tenant.objects.filter(propietario=user).exists() else 'registrado')
    if contacto is None:
        contacto = Contacto(nombre=user.get_full_name() or user.username, email=email,
                            usuario=user, origen='Registro en plataforma', etapa=etapa)
    else:
        contacto.usuario = user
        orden = [key for key, _ in Contacto.ETAPAS[:6]]
        if contacto.etapa in orden and orden.index(etapa) > orden.index(contacto.etapa):
            contacto.etapa = etapa
    contacto.save()
    return contacto


def pulso():
    ahora = timezone.now()
    desde = ahora - timedelta(days=30)
    errores = Evento.objects.filter(fecha__gte=ahora - timedelta(hours=24), estado_http__gte=500).count()
    pendientes = Tarea.objects.filter(completada=False, vence__lte=timezone.localdate()).count()
    sin_activar = get_user_model().objects.filter(is_active=True, date_joined__lte=ahora-timedelta(days=3),
                                                 tenants_propios__isnull=True).count()
    return {
        'errores': errores, 'pendientes': pendientes, 'sin_activar': sin_activar,
        'nuevos': get_user_model().objects.filter(date_joined__gte=desde).count(),
        'manuales': ManualContable.objects.filter(fecha_creacion__gte=desde).count(),
        'tokens': UsoIA.objects.filter(fecha__gte=desde).aggregate(n=Sum('tokens_total'))['n'] or 0,
    }


def radar():
    ahora = timezone.now()
    usuarios = get_user_model().objects.filter(is_active=True).annotate(
        organizaciones=Count('tenants_propios', distinct=True), documentos=Count('manualcontable', distinct=True))
    return [
        ('Sin primera organización', 'Registro de hace al menos tres días sin organización propia.',
         usuarios.filter(date_joined__lte=ahora-timedelta(days=3), organizaciones=0).order_by('date_joined')[:30]),
        ('Sin primer manual', 'Tiene organización y lleva al menos siete días registrado sin manuales propios.',
         usuarios.filter(date_joined__lte=ahora-timedelta(days=7), organizaciones__gt=0, documentos=0).order_by('date_joined')[:30]),
        ('Sin acceso reciente', 'Último inicio de sesión hace más de treinta días.',
         usuarios.filter(last_login__lt=ahora-timedelta(days=30)).order_by('last_login')[:30]),
    ]
