"""Identificación bibliográfica y guías propias; no reproduce normas licenciadas."""
import re
import unicodedata

CINIF='https://www.cinif.org.mx/files/NORMAS_2019.pdf'
NOMBRES={
 'C-1':'Efectivo y equivalentes de efectivo','C-3':'Cuentas por cobrar','C-4':'Inventarios',
 'C-5':'Pagos anticipados','C-6':'Propiedades, planta y equipo','C-8':'Activos intangibles',
 'C-9':'Provisiones, contingencias y compromisos','C-11':'Capital contable',
 'C-16':'Deterioro de instrumentos financieros por cobrar','C-19':'Instrumentos financieros por pagar',
 'D-1':'Ingresos por contratos con clientes','D-2':'Costos por contratos con clientes',
 'D-3':'Beneficios a los empleados','D-4':'Impuestos a la utilidad','D-5':'Arrendamientos',
 'B-6':'Estado de situación financiera','B-2':'Estado de flujos de efectivo',
 'B-15':'Conversión de monedas extranjeras',
 'C-2':'Inversión en instrumentos financieros','C-7':'Inversiones en asociadas, negocios conjuntos y otras inversiones permanentes',
 'B-3':'Estado de resultado integral','B-4':'Estado de cambios en el capital contable',
 'B-8':'Estados financieros consolidados o combinados','E-1':'Actividades agropecuarias',
 'B-7':'Adquisiciones de negocios',
 'C-20':'Instrumentos financieros para cobrar principal e interés',
}

def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(texto).lower()) if not unicodedata.combining(c))


def perfil(cuenta, familia):
    descripcion=str(getattr(cuenta,'descripcion','') or getattr(getattr(cuenta,'codigoagrupador',None),'nombre','') or 'Cuenta seleccionada')
    codigo=str(getattr(cuenta,'cuenta','') or getattr(getattr(cuenta,'codigoagrupador',None),'codigoagrupador',''))
    sat=str(getattr(getattr(cuenta,'codigoagrupador',None),'codigoagrupador',''))
    t=normalizar(descripcion)
    claves=[];internacionales=[]
    razon='Identificar reconocimiento, valuación, presentación y revelaciones según la operación concreta.'
    guia='Desarrolla políticas y ejemplos útiles; distingue los hechos reales de los supuestos ilustrativos y aplica el tratamiento al tipo de organización.'
    if sat.split('.')[0] in ('185','259') or ('impuesto' in t and 'diferid' in t):
        claves=['D-4'];internacionales=['NIC 12 — Impuestos a las ganancias']
        razon='Analizar impuesto causado y diferido, bases contables y fiscales, diferencias temporales, reversión y recuperabilidad; distinguirlos de diferencias permanentes.'
        guia='''Desarrolla el método de activos y pasivos: comparar valor contable y base fiscal, separar diferencias temporales y permanentes, determinar activo o pasivo diferido y su reversión. Para un activo, valor contable mayor a base fiscal suele dar diferencia imponible; para un pasivo la relación se analiza a la inversa. No todo desfase da lugar a activo: evaluar recuperabilidad y excepciones. Proponer conciliación y revelaciones. Para persona física no presumir tasa corporativa fija ni aplicar automáticamente 30%; usar una tasa numérica expresamente HIPOTÉTICA para enseñar la mecánica, cuya estimación al revertir requiere análisis del régimen y periodo. Para RESICO no derivar deducciones de diferencias contables. El asiento de ISR diferido no causa IVA por sí mismo. No negar el desarrollo porque falten datos reales: construir dos supuestos completos y explícitos, uno de reconocimiento y otro de reversión o recuperabilidad, con contrapartidas de impuesto diferido. No presentar una venta o compra genérica como ejemplo de esta cuenta.'''
    elif 'anticipad' in t:
        claves=['C-5'];razon='Distinguir el derecho a recibir bienes o servicios de un gasto ya devengado.'
        if 'arrendam' in t: guia+=' Para rentas anticipadas distinguir el anticipo del análisis del contrato de arrendamiento; no presumir que el anticipo es por sí solo un activo por derecho de uso.'
    elif 'arrendam' in t or 'leasing' in t:
        claves=['D-5'];internacionales=['NIIF 16 — Arrendamientos'];razon='Evaluar contrato, posición de arrendador o arrendatario y derechos y obligaciones antes de definir el registro.'
    elif familia=='inventarios':
        claves=['C-4'];internacionales=['NIC 2 — Inventarios'];razon='Analizar costo, valor neto realizable, bajas y revelaciones; el VNR no equivale a valor razonable.'
        guia+=' Desarrollar valuación y deterioro; no recomendar UEPS/LIFO como política NIF/NIIF ni confundir mermas con destrucción fiscal.'
    elif familia=='bancos':
        claves=['C-1'];internacionales=['NIC 7 — Estado de flujos de efectivo'];razon='Distinguir efectivo disponible, equivalentes, restricciones y conciliación; presentación de flujos solo si es pertinente.'
    elif familia=='clientes':
        claves=['C-3','C-16'];internacionales=['NIIF 9 — Instrumentos financieros'];razon='Separar derecho de cobro, estimación de deterioro, cobro y baja; no equiparar deterioro con incobrabilidad fiscal.'
    elif familia=='proveedores':
        claves=['C-19'];internacionales=['NIIF 9 — Instrumentos financieros'];razon='Distinguir una obligación comercial documentada de una provisión incierta; analizar pago y baja.'
    elif familia=='ingresos':
        claves=['D-1'];internacionales=['NIIF 15 — Ingresos de actividades ordinarias procedentes de contratos con clientes'];razon='Analizar contratos y cumplimiento de obligaciones; separar reconocimiento contable de cobro y acumulación fiscal.'
    elif 'nomina' in t or 'sueldo' in t or 'emplead' in t:
        claves=['D-3'];internacionales=['NIC 19 — Beneficios a los empleados'];razon='Identificar obligaciones por servicios de empleados y su naturaleza antes de reconocer gasto y pasivo.'
    elif any(x in t for x in ('terreno','equipo','maquinaria','edificio','vehiculo')):
        claves=['C-6'];internacionales=['NIC 16 — Propiedades, planta y equipo'];razon='Analizar reconocimiento, componentes, vida útil y baja. El terreno no se deprecia por defecto.'
    elif any(x in t for x in ('intangible','software','patente')):
        claves=['C-8'];internacionales=['NIC 38 — Activos intangibles'];razon='Distinguir un recurso identificable de un gasto; evaluar vida útil y amortización.'
    elif any(x in t for x in ('capital','patrimonio')):
        claves=['C-11'];razon='Separar aportaciones, reembolsos y resultados; no confundir aportaciones con ingresos por ventas.'
    elif 'provision' in t or 'contingenc' in t:
        claves=['C-9'];internacionales=['NIC 37 — Provisiones, pasivos contingentes y activos contingentes'];razon='Evaluar obligación y estimación; separar provisión reconocida y contingencia por revelar.'
    elif 'pasivo' in t or 'pagar' in t or 'acreedor' in t:
        claves=['C-19','C-9'];razon='Evaluar si existe obligación contractual determinada o incertidumbre propia de una provisión; no aplicar ambas mecánicas automáticamente.'
    elif familia=='gastos':
        claves=['D-2','B-6'];razon='Los costos por contratos requieren evaluar el contrato; otros gastos requieren identificar primero su naturaleza y la norma particular. No aplicar D-2 a todo gasto.'
    else:
        claves=['B-6'];razon='Referencia de presentación; identificar la norma de reconocimiento específica antes de aprobar, sin atribuir a la presentación un criterio de valuación.'
    if familia=='impuestos_diferidos' and sat.split('.')[0]=='185':
        guia+=' IMPORTANTE: en el catálogo SAT, 185 pertenece al ACTIVO. No registrar un pasivo diferido en 185. Ambos ejemplos deben desarrollar un ACTIVO por impuesto diferido: primero su reconocimiento con recuperación sustentada y después su reversión o ajuste por recuperabilidad. Puedes explicar el pasivo para comparación, pero corresponde a su cuenta de pasivo (agrupador SAT 259), no a 185.'
    if familia=='impuestos_diferidos' and sat.split('.')[0]=='259':
        guia+=' IMPORTANTE: el agrupador SAT 259 corresponde al PASIVO. Desarrollar reconocimiento y reversión de pasivo diferido; no clasificar un activo en esta cuenta.'
    es_caja = familia=='bancos' and ('caja' in t or sat.split('.')[0]=='101')
    razones={}
    if es_caja:
        claves=['C-1','B-6','B-2','B-15']
        razones={
            'C-1':'Referencia principal para analizar reconocimiento, valuación, presentación y revelaciones del efectivo y sus equivalentes.',
            'B-6':'Complementaria al presentar el saldo y evaluar clasificación y restricciones en el estado de situación financiera.',
            'B-2':'Complementaria cuando se prepara el estado de flujos; distinguir movimientos internos y cobros o pagos externos.',
            'B-15':'Condicionada a operaciones o saldos en moneda extranjera; no presumir que existen divisas en esta organización.',
        }
        guia+=' Desarrollar la aplicación a Caja: importe nominal en pesos, control y propiedad, separación de vales y derechos de cobro, restricciones, presentación y notas. Conciliar arqueo y auxiliar. El cobro carga Caja y el pago la abona; comprobar que la explicación y el asiento coinciden. No convertir todo cobro en ingreso ni todo faltante en deuda de un empleado. No copiar umbrales ni opciones ASPE como si fueran requisitos NIF.'
    from .desarrollo_uniforme import categoria, PERFILES, paquete
    tipo=categoria(cuenta);tecnico=PERFILES[tipo]
    claves=list(tecnico['normas'])
    if tipo=='especializada' and sat.split('.')[0]=='158':claves=['E-1']
    if tipo=='especializada' and sat.split('.')[0]=='180':claves=['B-7']
    comparaciones={
        'caja':['NIC 7 — Estado de flujos de efectivo'], 'bancos':['NIC 7 — Estado de flujos de efectivo'],
        'inventarios':['NIC 2 — Inventarios'], 'cobrar':['NIIF 9 — Instrumentos financieros'],
        'inversiones':['NIIF 9 — Instrumentos financieros'], 'deuda':['NIIF 9 — Instrumentos financieros'],
        'ingresos':['NIIF 15 — Ingresos de actividades ordinarias procedentes de contratos con clientes'],
        'anticipos_recibidos':['NIIF 15 — Ingresos de actividades ordinarias procedentes de contratos con clientes'],
        'ppe':['NIC 16 — Propiedades, planta y equipo'], 'intangibles':['NIC 38 — Activos intangibles'],
        'empleados':['NIC 19 — Beneficios a los empleados'], 'provisiones':['NIC 37 — Provisiones, pasivos contingentes y activos contingentes'],
        'arrendamientos':['NIIF 16 — Arrendamientos'], 'impuestos_utilidad':['NIC 12 — Impuestos a las ganancias'],
    }
    internacionales=comparaciones.get(tipo,[])
    razon='Referencia identificada según la naturaleza de la operación; comprobar alcance, requisitos y edición antes de concluir su aplicación.'
    razones.update({'B-3':'Referencia de presentación de resultados; no establece por sí sola reconocimiento o valuación de todo gasto.',
                    'B-4':'Complementaria para presentar cambios en el patrimonio; no convierte cuentas fiscales en capital contable.',
                    'B-8':'Condicionada al análisis de control y a la preparación de estados consolidados; no se aplica automáticamente a toda inversión.'})
    if tipo=='bancos':
        razones['B-15']='Condicionada a saldos u operaciones en moneda extranjera; confirmar moneda funcional y condiciones antes de aplicarla.'
    if tipo=='inversiones':
        razones.update({'C-2':'Posible referencia según tipo de instrumento y objetivo; confirmar su alcance antes de elegir medición.',
                        'C-20':'Posible referencia para instrumentos destinados a cobrar principal e interés; no aplica automáticamente a toda inversión.'})
    if tipo=='costos':
        razones['C-4']='Pertinente si existen bienes inventariables; para servicios sin inventarios identificar la norma del costo particular, sin forzar C-4.'
    guia+=' Criterios específicos para esta naturaleza: '+' '.join(tecnico['ejes'].values())+' Error que evitar: '+tecnico['error']+' Escenarios propuestos: '+' / '.join(tecnico['casos'])
    resultado={'categoria':tipo,'guia_tecnica':paquete(tipo),'sat':sat,'codigo':codigo,'descripcion':descripcion,'normas':[{'clave':'NIF '+c,'titulo':NOMBRES[c],'razon':razones.get(c,razon),'url':CINIF} for c in claves],
            'internacionales':internacionales,'guia':guia,'estado':'Identificación bibliográfica oficial; párrafos y requisitos de la edición aplicable por contrastar. No se reproduce el texto completo.'}
    if es_caja:
        from .guia_caja import paquete
        resultado['aplicacion_propia']=paquete()
    from .desarrollo_uniforme import MATICES
    if sat.split('.')[0] in MATICES:
        matiz=MATICES[sat.split('.')[0]]
        resultado['guia_tecnica']['enfoque']=matiz
        resultado['guia']+=' '+matiz
    from .comparacion_internacional import paquete as comparacion
    resultado['comparacion_internacional']=comparacion(tipo,resultado)
    resultado['internacionales']=[n['clave']+' — '+n['titulo'] for n in resultado['comparacion_internacional']['normas']]
    return resultado


def titulo_cuenta(cuenta):
    p=perfil(cuenta,'otra')
    return f"Manual contable — {p['descripcion']} (Cuenta {p['codigo']})"[:255]


def secciones_normativas(p, uniforme=False):
    normas='\n\n'.join(f"**{n['clave']} — {n['titulo']}.** {n['razon']}" for n in p['normas'])
    internacionales='; '.join(p['internacionales']) if p['internacionales'] else 'Determinar la referencia internacional pertinente según la operación; no se fuerza una equivalencia.'
    desarrollo=''
    if uniforme and p.get('guia_tecnica'):
        from .desarrollo_uniforme import renderizar
        desarrollo='\n\n'+renderizar(p['guia_tecnica'])+'\n\n**Consulta normativa oficial:** [edición NIF 2026 del CINIF](https://cinif.org.mx/normatividad_NIF2026.php). Referencia pendiente de revisión profesional en ejemplar autorizado; la guía educativa no acredita haber consultado sus párrafos.'
    elif not uniforme and p.get('aplicacion_propia'):
        a=p['aplicacion_propia'];f=a['fuente']
        desarrollo='\n\n'+a['texto']+'\n\n**Fuente educativa y atribución:** '+f['autores']+'. ['+f['titulo']+']('+f['url']+'), '+f['edicion']+', '+f['localizacion']+'. ['+f['licencia']+']('+f['url_licencia']+'). '+a['adaptacion']+' '+f['exclusiones']+'\n\n**Consulta normativa oficial:** [edición NIF 2026 del CINIF](https://cinif.org.mx/normatividad_NIF2026.php). La identificación de títulos usa el [índice oficial histórico del CINIF]('+CINIF+'); no acredita haber consultado los requisitos de la edición actual.'
    internacional='## 3. Referencia internacional\n\n'+internacionales+'. La referencia internacional aporta comparación técnica; no sustituye automáticamente el marco mexicano.'
    if p.get('comparacion_internacional',{}).get('fuentes'):
        from .comparacion_internacional import renderizar
        internacional=renderizar(p['comparacion_internacional'])
    return '## 2. NIF mexicanas aplicables\n\n'+(normas or '**Norma particular por determinar.** La naturaleza capturada no permite asignar una NIF de reconocimiento específica. La guía mantiene el desarrollo y señala la decisión pendiente, sin forzar una equivalencia.')+'\n\n'+p['estado']+desarrollo+'\n\n'+internacional
