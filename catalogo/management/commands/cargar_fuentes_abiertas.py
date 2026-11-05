"""Fuentes educativas CC BY; no reemplazan la normativa mexicana."""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from cuentas.models import Tenant
from catalogo.models import FuenteNormativa, VersionFuente, CriterioRevisado
from catalogo.biblioteca_models import FAMILIAS
from catalogo.guia_caja import LOCALIZACION

GUIAS={
 'inventarios':(1,'Capítulo 7: Inventory','Separar costo de adquisición, costo de ventas, existencia y deterioro. Comparar costo con importe recuperable de la venta después de costos necesarios. Controles de entradas, salidas y conteos; no trasladar métodos no admitidos por el marco mexicano.'),
 'bancos':(1,LOCALIZACION,'Explicación educativa propia: reconocer efectivo controlado, registrar cobros como cargos y pagos como abonos. Medir billetes en pesos por importe nominal, separar vales y derechos de cobro, analizar restricciones y presentar notas. Distinguir efectivo físico, saldos bancarios y equivalentes. No trasladar umbrales de ASPE/IFRS al marco mexicano sin revisión. La segregación de custodia y registro es un control propuesto; la NIF no se sustituye por un arqueo.'),
 'clientes':(1,'Sección 6.3: Receivables, páginas impresas 177–216; excluye sección 6.6','Documentar derechos de cobro, vencimiento y riesgo crediticio. Distinguir estimación de deterioro y baja individual; diseñar conciliaciones y seguimiento de cobranza.'),
 'proveedores':(2,'Capítulos 12 y 13: Current Liabilities / Long-Term Financial Liabilities','Distinguir recepción de bienes o servicios, obligación contractual, pago y baja. Una deuda comercial determinada difiere de una provisión incierta; conciliar saldos con acreedores.'),
 'ingresos':(1,'Capítulo 5: Revenue','Identificar contratos y cumplimiento de compromisos con clientes, separar cobros anticipados e ingreso devengado, devoluciones y descuentos. No confundir reconocimiento contable con obligación fiscal.'),
 'gastos':(1,'Capítulos 2 y 3: Conceptual Framework / Financial Reports','Distinguir consumo del periodo, activo pendiente de consumo y pago. Documentar el vínculo con operaciones y separar políticas contables de deducciones fiscales.'),
 'impuestos_diferidos':(2,'Capítulo 15, secciones 15.2, 15.3, 15.4 y 15.6; páginas impresas 135–151','Explicación educativa propia: diferencias temporales revierten en periodos futuros; las permanentes no producen impuesto diferido. Comparar valor contable y base fiscal, analizar signo de la diferencia para activos y pasivos y estimar efectos al revertir. Evaluar recuperabilidad de activos y cambios en tasas; no usar una tasa extranjera ni corporativa para toda persona física. La tasa ilustrativa se declara hipotética. Distinguir registro del impuesto diferido y pago del impuesto causado.'),
 'otra':(1,'Capítulos 2 y 3: Conceptual Framework / Financial Reports','Identificar naturaleza del recurso u obligación, reconocimiento, valuación, presentación y revelaciones. Construir procedimientos y ejemplos propios sin presentar los criterios generales como sustituto de una norma particular.'),
}

class Command(BaseCommand):
    help='Incorpora fuentes abiertas verificadas y criterios educativos propios, con atribución.'

    @transaction.atomic
    def handle(self,*args,**kwargs):
        data=json.loads((Path(__file__).parents[2]/'data/fuentes_abiertas_2026_10_29.json').read_text());versiones={};anteriores=[]
        for e in data:
            f,_=FuenteNormativa.objects.get_or_create(url=e['url'],defaults={'titulo':e['titulo'],'emisor':e['autores'],'naturaleza':'contable','fiscal':False})
            edicion=e['edicion']+(' · alcance 2026-11-05: excluye sección 6.6' if e['volumen']==1 else '')
            v=f.versiones.filter(huella_documento=e['sha256'],edicion=edicion,publicado=True,retirado=False).first()
            if not v:
                v=VersionFuente.objects.create(fuente=f,edicion=edicion,publicada_el=e['publicacion'],vigente_desde=timezone.localdate(),publicado=True,revisado_en=timezone.now(),consulta='permitido',almacenamiento='permitido',envio_ia='permitido',reproduccion='permitido',huella_documento=e['sha256'],evidencia_permisos=f"{e['autores']}. {e['licencia']}: {e['url_licencia']}. Licencia comprobada en {e['localizacion_licencia']}. {e['alcance']}",evidencia_vigencia='Edición educativa 2021-A, no norma mexicana vigente ni actualización fiscal. Consulta y licencia comprobadas el '+str(timezone.localdate())+'. La aplicabilidad actual de NIF/NIIF sigue sujeta a revisión profesional.')
            versiones[e['volumen']]=v
            if e['volumen']==1:
                anteriores.extend(f.versiones.filter(publicado=True,retirado=False,edicion=e['edicion'],huella_documento=e['sha256']).exclude(pk=v.pk))
        n=0
        for familia,_ in FAMILIAS:
            vol,loc,texto=GUIAS[familia]
            for reg,_ in Tenant.REGIMEN_CHOICES:
                if CriterioRevisado.objects.filter(version=versiones[vol],familia=familia,regimen=reg).exists(): continue
                CriterioRevisado.objects.create(version=versiones[vol],familia=familia,regimen=reg,area='contable',titulo='Guía educativa propia: '+familia,localizacion=loc,explicacion=texto,condiciones='Adaptación conceptual con ejemplos propios y atribución. Confirmar operación real, marco y régimen fiscal; usar supuestos completos cuando falten cifras. Identificar las NIF pertinentes sin atribuir verificación de párrafos no consultados.',excepciones='El libro no es una NIF mexicana ni reemplaza su texto autorizado. No trasladar reglas ASPE, legislación canadiense, tasas, opciones o excepciones extranjeras a México. No reutilizar citas de normas de terceros. En volumen 1 queda excluida la sección 6.6 / Appendix A (CC BY-NC-SA 3.0): no almacenar su texto, enviarlo a IA ni reproducirlo para este uso comercial.',vigente_desde=timezone.localdate(),publicado=True,revisado_en=timezone.now(),cobertura='parcial')
                n+=1
        for anterior in anteriores:
            anterior.retirado=True
            anterior.save(update_fields=['retirado'])
        self.stdout.write(f'Criterios educativos nuevos: {n}; dos fuentes CC BY 4.0 con atribución.')
