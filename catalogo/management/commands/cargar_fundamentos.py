"""Carga idempotente de criterios propios comprobados contra textos legislativos oficiales."""
import json
from datetime import date
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from cuentas.models import Tenant
from catalogo.models import FuenteNormativa, VersionFuente, CriterioRevisado, ControlBiblioteca
from catalogo.biblioteca_models import FAMILIAS
from panel.audit import registrar

REGIMEN={
 'pm_general':('Artículos 16, 17, 25 y 27', 'Los ingresos de la persona moral pueden acumularse antes de cobrarse. Las deducciones requieren habilitación y requisitos propios; una salida bancaria o un gasto contable no constituye por sí solo deducción.'),
 'pm_sin_fines':('Artículos 79 y 80', 'La denominación sin fines de lucro no basta: verificar encuadre y requisitos del régimen. Analizar remanente distribuible y supuestos de ingresos sujetos al impuesto; no asumir exención general de todas las operaciones.'),
 'pf_empresarial':('Artículos 102, 103 y 105', 'Analizar ingresos efectivamente percibidos y deducciones autorizadas efectivamente erogadas con requisitos. Las adquisiciones de mercancías tienen reglas propias; no trasladar automáticamente el costo de lo vendido de personas morales.'),
 'pf_profesional':('Artículos 102, 103 y 105', 'Los ingresos se analizan por percepción efectiva; las deducciones deben estar autorizadas, efectivamente erogadas y cumplir requisitos. Separar anticipos, cobros, pagos y registros contables.'),
 'pf_plataformas':('Artículos 113-A y 113-B', 'Identificar ingresos obtenidos mediante plataformas y retenciones aplicables. La opción de pagos definitivos exige condiciones propias; no presumir su ejercicio ni deducir costos automáticamente. Diferenciar cobros directos y por intermediario.'),
 'pf_resico':('Artículo 113-E', 'El ISR de persona física RESICO se determina sobre ingresos efectivamente cobrados sin IVA y sin deducción alguna. Costos, gastos, deterioros, mermas y destrucción no reducen esa base ni crean deducciones futuras. El IVA requiere análisis independiente.'),
 'pf_arrendamiento':('Artículos 114 y 115', 'Verificar que el ingreso corresponda al uso o goce temporal de inmuebles. Los ingresos en crédito se analizan hasta su cobro. Las deducciones autorizadas y la opción legal tienen requisitos propios; no trasladar mecánicas de actividad empresarial.'),
}
ENFOQUE={
 'inventarios':'Distinguir adquisición, existencia, venta, consumo, deterioro, merma y destrucción. No confundir gasto contable con deducción fiscal.',
 'bancos':'Conciliar depósitos y retiros con su origen: cobros, préstamos, aportaciones, pagos o transferencias internas. Un movimiento bancario no determina por sí solo el impuesto.',
 'clientes':'Separar ingreso, derecho de cobro, cobro efectivo y deterioro contable. No deducir automáticamente cuentas incobrables ni cancelar IVA por una estimación.',
 'proveedores':'Distinguir obligación, recepción, pago y requisitos fiscales. La cuenta por pagar no acredita por sí sola una deducción ni el IVA.',
 'ingresos':'Identificar acto, momento de reconocimiento contable, acumulación de ISR y cobro para IVA; no equipararlos automáticamente.',
 'gastos':'Separar gasto contable, erogación, deducibilidad de ISR y acreditamiento de IVA. Documentar naturaleza y relación con la actividad.',
}


class Command(BaseCommand):
    help='Carga base revisada de seis familias por ocho regímenes; cobertura inicial parcial.'

    def add_arguments(self,p):
        p.add_argument('--evidencias',required=True,help='Directorio de metadatos JSON de textos oficiales consultados.')

    @transaction.atomic
    def handle(self,*args,**options):
        carpeta=Path(options['evidencias']); versiones={}; hoy=timezone.localdate()
        # No descarga ni incorpora normas contables protegidas.
        for key,titulo in [('LISR','Ley del Impuesto sobre la Renta'),('LIVA','Ley del Impuesto al Valor Agregado'),('CFF','Código Fiscal de la Federación')]:
            try: e=json.loads((carpeta/(key+'.json')).read_text())
            except (OSError,ValueError): raise CommandError('Falta evidencia de consulta: '+key)
            if e.get('url')!=f'https://www.diputados.gob.mx/LeyesBiblio/pdf/{key}.pdf' or len(e.get('sha256',''))!=64: raise CommandError('Evidencia inválida: '+key)
            fuente,_=FuenteNormativa.objects.get_or_create(url=e['url'],defaults={'titulo':titulo,'emisor':'Congreso de la Unión / Cámara de Diputados','naturaleza':'ley','fiscal':True})
            v=fuente.versiones.filter(publicado=True,huella_documento=e['sha256']).first()
            if not v:
                v=VersionFuente.objects.create(fuente=fuente,edicion=e['edicion'],vigente_desde=hoy,
                    consulta='permitido',almacenamiento='permitido',envio_ia='permitido',reproduccion='permitido',
                    evidencia_permisos='Textos legislativos oficiales: LFDA artículo 14 fracción VIII, comprobado en edición oficial '+json.loads((carpeta/'LFDA.json').read_text())['edicion']+'. Se utilizan explicaciones propias y localizaciones, sin incorporar marcas, anotaciones editoriales o materiales protegidos de terceros.',
                    evidencia_vigencia='Consulta técnica del texto consolidado oficial el '+str(hoy)+'. SHA-256 registrado. La fecha inicial delimita el periodo revisado por esta base, no afirma que sea la fecha de entrada en vigor de la ley. Transitorios, reglamentos, RMF, anexos y operaciones especiales se mantienen pendientes de comprobación específica. No se certifica cobertura fiscal integral.',
                    huella_documento=e['sha256'],revisado_en=timezone.now(),publicado=True)
            versiones[key]=v
        for titulo,emisor,url,edicion in [
            ('NIF mexicanas','CINIF','https://cinif.org.mx/normatividad_NIF2026.php','NIF 2026; texto completo no consultado en ejemplar autorizado'),
            ('Normas internacionales de contabilidad','IFRS Foundation','https://www.ifrs.org/issued-standards/list-of-standards/','Metadatos del catálogo oficial; edición y párrafos por verificar')]:
            fuente,_=FuenteNormativa.objects.get_or_create(url=url,defaults={'titulo':titulo,'emisor':emisor,'naturaleza':'contable','fiscal':False})
            if not fuente.versiones.filter(edicion=edicion).exists():
                VersionFuente.objects.create(fuente=fuente,edicion=edicion,vigente_desde=hoy,publicado=True,revisado_en=timezone.now(),evidencia_vigencia='Solo se registró la referencia bibliográfica pública. No se verificó el texto completo ni su aplicabilidad. Permisos de procesamiento sin comprobar; contenido excluido de prompts y reproducción.')
        creados=0
        for familia,_ in FAMILIAS:
            for regimen,_ in Tenant.REGIMEN_CHOICES:
                criterios=[('CFF','obligaciones','Documentación y trazabilidad','Artículos 28, 29, 29-A y 30', 'Verificar obligaciones de contabilidad, comprobantes fiscales, requisitos del comprobante y conservación de documentación según el supuesto y contribuyente. No atribuir efectos fiscales al documento sin comprobar la operación real y sus requisitos.')]
                if regimen!='otro':
                    local,explicacion=REGIMEN[regimen]
                    criterios.append(('LISR','isr','ISR: '+dict(Tenant.REGIMEN_CHOICES)[regimen],local,explicacion))
                criterios.append(('LIVA','iva','IVA: acto, cobro y acreditamiento','Artículos 1, 1-B, 2-A, 5, 9, 15 y 20', 'Identificar acto gravado, tasa cero o exención según bienes o servicios y requisitos. La ubicación fronteriza no determina tasa cero; no presumir elegibilidad para estímulos. El cobro efectivo y el acreditamiento tienen condiciones propias. No aplicar 16% a toda operación ni trasladar la base de ISR al IVA.'))
                if familia=='inventarios' and regimen=='pm_general':
                    criterios.append(('LISR','isr','Inventarios de persona moral: reglas específicas','Artículos 39 y 41; artículo 27 fracción XX', 'Costo de lo vendido sujeto a la mecánica de persona moral. Los métodos fiscales enumerados son PEPS, costo identificado, costo promedio y detallista; el costeo directo no figura en esa lista. La pérdida de valor de mercancías exige requisitos propios: el deterioro contable no genera automáticamente deducción por destrucción.'))
                if familia=='clientes' and regimen=='pm_general':
                    criterios.append(('LISR','isr','Créditos incobrables: requisitos','Artículo 25 fracción V y artículo 27 fracción XV', 'La deducción de créditos incobrables exige los supuestos y requisitos fiscales aplicables. Una estimación contable de deterioro no prueba por sí sola el derecho a deducir.'))
                for key,area,titulo,loc,exp in criterios:
                    if CriterioRevisado.objects.filter(version=versiones[key],familia=familia,regimen=regimen,titulo=titulo).exists(): continue
                    CriterioRevisado.objects.create(version=versiones[key],familia=familia,regimen=regimen,area=area,titulo=titulo,localizacion=loc,explicacion=exp+' '+ENFOQUE.get(familia, 'Separar criterios contables y efectos fiscales; verificar el tratamiento de la operación y régimen concretos.'),
                        condiciones='Comprobar hechos, periodo, pertenencia al régimen, requisitos, retenciones y reglas particulares antes de aplicar. La clasificación de la cuenta no determina por sí sola el tratamiento fiscal.',
                        excepciones='Cobertura parcial: revisar transitorios DOF, reglamentos, RMF y anexos vigentes. Operaciones internacionales, estímulos, deducciones especiales y elegibilidad no quedan automáticamente comprobados. Para régimen Otro se requiere identificar primero el régimen real.',
                        vigente_desde=hoy,publicado=True,revisado_en=timezone.now(),cobertura='parcial')
                    creados+=1
        ControlBiblioteca.objects.get_or_create(pk=1)
        registrar('fuentes','biblioteca.carga_inicial',detalle=f'Criterios propios cargados: {creados}. Revisión técnica acotada, sin aprobación profesional de manuales.')
        self.stdout.write(f'Criterios nuevos: {creados}; activación conservada; cobertura parcial explícita.')
