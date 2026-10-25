"""Registro y resumen del uso de IA, sin estimaciones monetarias ni texto privado."""
from django.db.models import Count, Min, Q, Sum
from .models import UsoIA


def registrar_uso(resultado, usuario, tenant):
    intentos = getattr(resultado, 'consumos', [])
    if not intentos:
        return None

    def suma(campo):
        valores = [i[campo] for i in intentos if i.get(campo) is not None]
        return sum(valores) if valores else None

    return UsoIA.objects.create(
        usuario=usuario, tenant=tenant, organizacion_referencia=tenant.pk, intentos=intentos,
        tokens_entrada=suma('entrada'), tokens_salida=suma('salida'),
        tokens_total=suma('total'), total_parcial=any(i.get('total') is None for i in intentos),
    )


def resumen_uso(usuario):
    datos = UsoIA.objects.filter(usuario=usuario).aggregate(
        tokens=Sum('tokens_total'), registros=Count('pk'),
        sin_dato=Count('pk', filter=Q(total_parcial=True) | Q(tokens_total__isnull=True)),
        manuales=Count('pk', filter=Q(manual_generado=True)),
        organizaciones=Count('organizacion_referencia', distinct=True, filter=Q(manual_generado=True)),
        desde=Min('fecha'),
    )
    return datos


def reporte_uso(registro):
    if registro is None:
        return None
    return {
        'registro': registro,
        'intentos': len(registro.intentos),
        'desglose_completo': all(i.get('entrada') is not None and i.get('salida') is not None
                                for i in registro.intentos),
    }
