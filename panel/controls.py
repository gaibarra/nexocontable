from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .models import ControlPlataforma, CupoDiario


@transaction.atomic
def reservar_generacion(usuario):
    """Reserva antes de llamar al proveedor; serializa solicitudes del mismo usuario."""
    get_user_model().objects.select_for_update().get(pk=usuario.pk)
    control = ControlPlataforma.objects.filter(pk=1).first()
    if control and not control.generacion_habilitada:
        return 'La generación de manuales está pausada temporalmente por la administración.'
    cupo, _ = CupoDiario.objects.get_or_create(usuario=usuario, dia=timezone.localdate())
    if control and control.limite_diario_usuario and cupo.solicitudes >= control.limite_diario_usuario:
        return 'Alcanzaste el límite diario de solicitudes de IA. Podrás volver a generar mañana.'
    cupo.solicitudes += 1
    cupo.save(update_fields=['solicitudes'])
    return ''


def aviso_plataforma(request):
    if not request.user.is_authenticated:
        return {}
    control = ControlPlataforma.objects.filter(pk=1, aviso_activo=True).first()
    return {'aviso_plataforma': control.aviso if control else ''}
