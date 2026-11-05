"""Recuperación acotada; conserva validación y consumo sin registrar textos privados."""
import logging
import time
from django.conf import settings
from .biblioteca import validar_respuesta, RespuestaManualInvalida
from .ia import ManualGenerationError
from .revision_tecnica import revisar_contenido

logger=logging.getLogger(__name__)
CORRECCIONES={
 'json_invalido':'Devuelve únicamente un objeto JSON completo y válido.',
 'estructura_principal':'Usa únicamente las diez claves del esquema, incluidas introduccion, politicas, materialidad y conclusion.',
 'referencia_no_autorizada':'Usa exclusivamente identificadores presentes en la biblioteca; si no hay fundamentos, usa referencias vacías y declara el pendiente.',
 'referencia_area_incorrecta':'Vincula cada bloque solo a referencias de su área. Las obligaciones no sustentan tratamiento contable.',
 'cita_libre':'Menciona únicamente claves de normas identificadas en el perfil contable; omite artículos, párrafos, URLs e identificadores F en texto libre. Las referencias van solo en las listas correspondientes.',
 'cumplimiento_no_verificado':'No afirmes cumplimiento normativo. Identifica lo pendiente y los supuestos por verificar.',
 'asiento_desbalanceado':'Recalcula ambos ejemplos: los movimientos deben tener sumas iguales de Debe y Haber, sin omitir contrapartidas.',
 'importe_invalido':'Cada importe debe ser finito, no negativo y con hasta dos decimales. No uses separadores de miles dentro de los valores JSON.',
 'iva_asiento_incompleto':'La explicación afirma registrar IVA, pero no aparece cuantificado en el asiento. Completa la línea de IVA y las contrapartidas con sumas iguales; declara una tasa hipotética y calcula importes. Si el asiento realmente no tiene efecto de IVA, explica ese alcance sin afirmar un registro que no muestras.',
 'desarrollo_incompleto':'Desarrolla todas las secciones: mínimo 1000 palabras, políticas concretas, dos casos de materialidad y dos ejemplos numéricos completos. No llenes el documento de avisos ni omitas conclusiones.',
 'desarrollo_contable_incompleto':'Completa contable.desarrollo con seis campos: reconocimiento, valuacion_inicial, valuacion_posterior, presentacion, revelaciones y baja. Cada campo debe contener al menos 40 palabras distintas, aplicación concreta y evidencia; no dupliques párrafos. Vincula el bloque a sus fundamentos contables disponibles.',
 'ejemplo_fuera_de_alcance':'Los dos ejemplos deben desarrollar la cuenta seleccionada y sus contrapartidas. Para impuestos diferidos utiliza esa cuenta y una tasa expresamente hipotética si se trata de persona física; no una venta genérica.',
 'contenido_tecnico':'Revisa la separación de contabilidad, ISR e IVA y los límites explícitos de cada fundamento. No concedas estímulos ni deducciones por simple registro contable.',
}


def generar_revisado(system,prompt,snapshot,regimen,*,proveedor):
    fin=time.monotonic()+min(90.0,max(2.0,settings.AI_TIMEOUT_SECONDS*2))
    consumos=[];codigo='estructura_principal'
    for intento in range(2):
        restante=fin-time.monotonic()
        if restante<=1:break
        instruccion=prompt if intento==0 else prompt+'\n\nREVISIÓN AUTOMÁTICA: redacta nuevamente con el mismo contexto y el esquema exacto. '+CORRECCIONES.get(codigo,'Respeta los campos y tipos del esquema JSON, sin omitir ni añadir claves.')
        try:
            raw=proveedor(system,instruccion,formato_json=True,presupuesto_segundos=restante)
        except ManualGenerationError as exc:
            # Conservar el error operativo del proveedor y el consumo de lo anterior.
            exc.consumos=consumos+exc.consumos
            raise
        registros=getattr(raw,'consumos',[])
        try:
            resultado=validar_respuesta(raw,snapshot)
            if revisar_contenido(str(resultado),regimen):
                raise RespuestaManualInvalida('contenido_tecnico')
        except RespuestaManualInvalida as exc:
            codigo=exc.codigo
            consumos.extend([{**c,'revision_tecnica':'rechazado','causa':codigo} for c in registros])
            logger.warning('Revisión de manual: intento=%s causa=%s',intento+1,codigo)
            continue
        resultado.consumos=consumos+registros
        if intento:logger.info('Manual corregido automáticamente: intentos=%s',intento+1)
        return resultado
    raise RespuestaManualInvalida(codigo,consumos=consumos)
