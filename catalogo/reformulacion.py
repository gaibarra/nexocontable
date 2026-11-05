"""Reemplazo explícito de un borrador, preservando su versión previa íntegra."""
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import ManualContable
from .biblioteca import huella
from panel.audit import registrar


@transaction.atomic
def reformular_borrador(pk, resultado, titulo, huella_esperada):
    manual=ManualContable.objects.select_for_update().get(pk=pk)
    if manual.aprobado or huella(manual)!=huella_esperada:
        raise ValidationError('El documento cambió o fue aprobado; se conserva sin modificaciones.')
    snapshot=getattr(resultado,'fundamentos_snapshot',None)
    if not snapshot or snapshot.get('esquema') not in (2,3):
        raise ValidationError('Se requiere generación completa validada con sus fuentes.')
    if snapshot['regimen']!=manual.tenant.regimen_fiscal:
        raise ValidationError('El régimen cambió durante la generación.')
    manual.contenido=str(resultado);manual.titulo=titulo
    manual.fundamentos_snapshot=snapshot;manual.fecha_referencia=snapshot['fecha']
    manual.save(renovar_fundamentos=True)
    registrar('fuentes','borrador.reformulado',organizacion_id=manual.tenant_id,referencia=manual.pk,detalle='Versión anterior archivada; borrador completo generado a solicitud del responsable. No aprobado.')
    return manual
