import logging
from contextvars import ContextVar
from django.db import transaction

actor_actual = ContextVar('panel_actor', default=None)
logger = logging.getLogger(__name__)


def registrar(categoria, accion, actor=None, organizacion_id=None, referencia='', detalle='', **kwargs):
    from .models import Evento
    try:
        Evento.objects.create(categoria=categoria, accion=accion, actor_id=actor or actor_actual.get(),
                              organizacion_id=organizacion_id, referencia=str(referencia)[:100],
                              detalle=str(detalle)[:400], **kwargs)
    except Exception:
        logger.exception('No se pudo guardar un evento de auditoría')


def al_confirmar(**datos):
    datos.setdefault('actor', actor_actual.get())
    transaction.on_commit(lambda: registrar(**datos), robust=True)
