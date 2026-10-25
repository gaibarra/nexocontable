"""Prompt builders for manual generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from catalogo.models import CatalogoCuentas
from cuentas.models import Tenant


@dataclass(frozen=True)
class ManualPromptContext:
    tenant_nombre: str
    giro: str
    regimen: str
    cuentas_listado: str


REFERENCE_BLOCK = """Referencias y estándares sugeridos:
- NIF mexicanas aplicables emitidas por el CINIF/IMCP, según la naturaleza de la cuenta.
- NIIF/IFRS aplicables emitidas por el IASB, cuando resulten relevantes por tipo de operación o comparabilidad internacional.
- Ley del Impuesto sobre la Renta (LISR).
- Ley del Impuesto al Valor Agregado (LIVA).
- Código Fiscal de la Federación (CFF), incluyendo materialidad, razón de negocios y soporte documental.
- Criterios y guías del SAT cuando aporten contexto práctico verificable.

Reglas de citación:
- Cita únicamente normas realmente aplicables a la cuenta.
- Si una NIIF/IFRS no aplica directamente, omítela.
- No inventes nombres, números de norma ni artículos.
- Cuando no exista certeza razonable, escribe "referencia por verificar" en lugar de afirmar una cita específica.
- Al final de cada cuenta, agrega una mini-sección de "Referencias" con las normas concretas utilizadas.
"""


PROFESSIONAL_STYLE_BLOCK = """Estilo y formato:
- Redacta con tono profesional, técnico y prudente.
- Evita repeticiones, lenguaje genérico y explicaciones superficiales.
- La aplicación ya incorpora identidad de la empresa, título, fecha y estado del documento: no los repitas como portada ni ficha introductoria. Usa el giro y el régimen fiscal para adaptar el análisis, sin repetirlos como datos generales.
- Presenta el código y la descripción de cada cuenta una sola vez al abrir su sección. Evita repetir la misma descripción como subtítulo y como ficha de código SAT; distingue el código SAT cuando sea diferente al de la cuenta.
- Usa encabezados consistentes y secciones numeradas.
- Prioriza claridad operativa para contador, auditor y dirección financiera.
- Mantén una estructura homogénea para todas las cuentas.
- Usa listas y tablas solo cuando mejoren la lectura.
"""


NIIF_SUGERIDAS = {
    'activo_corriente': [
        'NIC 2 - Inventarios',
        'NIIF 9 - Instrumentos financieros',
        'NIIF 7 - Instrumentos financieros: información a revelar',
        'NIIF 13 - Valor razonable',
    ],
    'efectivo_y_equivalentes': [
        'NIC 7 - Estado de flujos de efectivo',
        'NIIF 9 - Instrumentos financieros',
        'NIIF 7 - Instrumentos financieros: información a revelar',
    ],
    'cuentas_por_cobrar': [
        'NIIF 9 - Instrumentos financieros',
        'NIIF 7 - Instrumentos financieros: información a revelar',
        'NIIF 15 - Ingresos de contratos con clientes',
    ],
    'propiedad_planta_equipo': [
        'NIC 16 - Propiedades, planta y equipo',
        'NIC 23 - Costos por préstamos',
        'NIIF 13 - Valor razonable',
        'NIIF 16 - Arrendamientos',
    ],
    'intangibles': [
        'NIC 38 - Activos intangibles',
        'NIC 36 - Deterioro del valor de los activos',
        'NIIF 3 - Combinaciones de negocios',
    ],
    'pasivo_y_provisiones': [
        'NIC 37 - Provisiones, pasivos contingentes y activos contingentes',
        'NIIF 9 - Instrumentos financieros',
        'NIIF 16 - Arrendamientos',
    ],
    'patrimonio': [
        'NIC 1 - Presentación de estados financieros',
        'NIC 32 - Instrumentos financieros: presentación',
        'NIIF 9 - Instrumentos financieros',
    ],
    'ingresos': [
        'NIIF 15 - Ingresos de contratos con clientes',
        'NIC 1 - Presentación de estados financieros',
    ],
    'costo_y_gasto': [
        'NIC 2 - Inventarios',
        'NIIF 15 - Ingresos de contratos con clientes',
        'NIC 16 - Propiedades, planta y equipo',
    ],
    'arrendamientos': [
        'NIIF 16 - Arrendamientos',
        'NIC 17 - Arrendamientos (referencia histórica)',
        'NIC 1 - Presentación de estados financieros',
    ],
    'general': [
        'NIC 1 - Presentación de estados financieros',
        'NIC 8 - Políticas contables, cambios en estimaciones contables y errores',
    ],
}


def _sugerir_niif_ifrs(cuenta: CatalogoCuentas) -> list[str]:
    texto = f"{cuenta.cuenta} {cuenta.descripcion or ''} {cuenta.codigoagrupador.codigoagrupador} {cuenta.codigoagrupador.nombre}".lower()

    if any(palabra in texto for palabra in ['caja', 'banco', 'efectivo', 'tesorer']):
        return NIIF_SUGERIDAS['efectivo_y_equivalentes']
    if any(palabra in texto for palabra in ['cliente', 'cuenta por cobrar', 'deudor', 'anticipo']):
        return NIIF_SUGERIDAS['cuentas_por_cobrar']
    if any(palabra in texto for palabra in ['inventario', 'almacen', 'existencia', 'mercanc']):
        return NIIF_SUGERIDAS['activo_corriente']
    if any(palabra in texto for palabra in ['activo fijo', 'equipo', 'maquinaria', 'vehiculo', 'inmueble', 'mobiliario']):
        return NIIF_SUGERIDAS['propiedad_planta_equipo']
    if any(palabra in texto for palabra in ['intangible', 'licencia', 'software', 'marca', 'patente']):
        return NIIF_SUGERIDAS['intangibles']
    if any(palabra in texto for palabra in ['provision', 'pasivo', 'acreedor', 'impuesto por pagar', 'cuenta por pagar']):
        return NIIF_SUGERIDAS['pasivo_y_provisiones']
    if any(palabra in texto for palabra in ['capital', 'utilidad retenida', 'resultado', 'patrimonio']):
        return NIIF_SUGERIDAS['patrimonio']
    if any(palabra in texto for palabra in ['ingreso', 'venta', 'ventas', 'honorario', 'servicio prestado']):
        return NIIF_SUGERIDAS['ingresos']
    if any(palabra in texto for palabra in ['costo', 'gasto', 'egreso', 'sueldo', 'nómina', 'nomina']):
        return NIIF_SUGERIDAS['costo_y_gasto']
    if any(palabra in texto for palabra in ['arrendamiento', 'renta', 'leasing']):
        return NIIF_SUGERIDAS['arrendamientos']
    return NIIF_SUGERIDAS['general']


ACCOUNT_SECTION_BLOCK = """Para cada cuenta, incluye estas secciones:
1. Introducción profesional: uso, naturaleza y finalidad contable.
2. NIF mexicanas aplicables: menciona la norma, título y por qué aplica.
3. NIIF/IFRS aplicables: incluye solo estándares internacionales que realmente aporten comparabilidad o sustento técnico.
4. Aspectos fiscales: LISR, LIVA, CFF u otras disposiciones relevantes.
5. Materialidad y razón de negocios: documentación soporte, evidencia operativa y riesgos.
    - Incluye por lo menos 2 casos prácticos de materialidad distintos.
    - El primer caso debe ser una operación ordinaria con su documentación soporte principal.
    - El segundo caso debe ser un escenario de riesgo, ajuste, revisión SAT, provisión, contrato o cadena documental más compleja.
    - Para cada caso, explica qué evidencia se conserva, qué valida la razón de negocios y qué riesgo fiscal existe si faltan soportes.
    - Menciona el efecto práctico de no acreditar materialidad, sin caer en generalidades.
6. Ejemplos prácticos: presenta por lo menos 2 casos distintos y con mayor desarrollo.
    - Cada ejemplo debe incluir contexto operativo realista, supuesto de negocio y objetivo contable.
    - Cada ejemplo debe mostrarse en formato visual de cuentas T, como en una hoja de trabajo: usa una tabla HTML o Markdown real con encabezados "Debe" y "Haber", no texto corrido.
    - Antes de la tabla, indica el nombre de la cuenta T y debajo muestra el asiento contable resumido.
    - Cada renglón de la tabla debe incluir el importe exacto; no dejes columnas vacías cuando corresponda un cargo o un abono.
    - La suma de importes en Debe y Haber debe ser visible y consistente dentro de cada ejemplo.
    - Todos los cargos y todos los abonos del asiento deben aparecer visibles en la tabla; no omitas cuentas de contrapartida ni reemplaces el asiento por un único importe neto.
    - Si el asiento tiene varias partidas, muestra cada partida en su propio renglón para que se vea completo el origen y destino del movimiento.
    - La cuenta T debe contener todos los movimientos relacionados con el caso; si un movimiento afecta varias cuentas, inclúyelas todas de forma consistente en la misma presentación.
    - Mantén el mismo criterio de orden, títulos y separación en todos los ejemplos para que la presentación sea uniforme.
    - En cada ejemplo, indica explícitamente qué NIF mexicana sustenta el tratamiento contable aplicado y menciona el nombre de la NIF junto con una breve razón de aplicación.
    - Cuando aplique, agrega impacto fiscal, documentación soporte y la razón por la que se registra así.
    - Incluye siempre el IVA cuando aplique, mostrando claramente IVA acreditable, IVA trasladado o el tratamiento que corresponda en la cuenta T y en el asiento.
    - Si hay IVA, desglósalo en una línea o columna separada dentro del ejemplo para que se vea el efecto fiscal.
    - Evita ejemplos genéricos o demasiado cortos; da más "carnita" y aterriza el caso al giro de la empresa.
    - El primer ejemplo debe ser una operación cotidiana o transaccional.
    - El segundo ejemplo debe ser diferente al primero y preferentemente de cierre, ajuste, provisión, reclasificación, depreciación, amortización o deterioro.
    - Si la cuenta no admite un ajuste de cierre natural, plantea un caso alterno comparable que siga siendo útil para la práctica profesional.
7. Conclusión: mejores prácticas contables y fiscales.
8. Referencias: lista final breve de normas o guías citadas.
"""


def build_accounts_listing(cuentas: Iterable[CatalogoCuentas]) -> str:
    lineas = []
    for cuenta in cuentas:
        linea = f"- {cuenta.cuenta} | {cuenta.descripcion} | Código SAT: {cuenta.codigoagrupador.codigoagrupador} - {cuenta.codigoagrupador.nombre}"
        lineas.append(linea)
    return "\n".join(lineas)


def build_manual_prompts(cuentas: Iterable[CatalogoCuentas], tenant: Tenant) -> tuple[str, str]:
    cuentas_listado = build_accounts_listing(cuentas)
    nombre_org = tenant.nombre
    giro = tenant.get_giro_display()
    regimen = tenant.get_regimen_fiscal_display()
    cuentas_niif = []
    for cuenta in cuentas:
        sugeridas = _sugerir_niif_ifrs(cuenta)
        cuentas_niif.append(
            f"- {cuenta.cuenta}: {', '.join(sugeridas)}"
        )
    niif_referencia = "\n".join(cuentas_niif)

    user_prompt = f"""En el contexto de una organización llamada \"{nombre_org}\",\ndel giro \"{giro}\" y régimen fiscal \"{regimen}\",\ngenera un Manual Contable objetivo, técnico y altamente profesional para las siguientes cuentas:

{cuentas_listado}

NIIF/IFRS sugeridas por cuenta, usa solo las que realmente apliquen:
{niif_referencia}

{ACCOUNT_SECTION_BLOCK}

{REFERENCE_BLOCK}

{PROFESSIONAL_STYLE_BLOCK}

El resultado debe ser homogéneo y bien estructurado, asegurando que TODAS las secciones estén presentes para cada cuenta. La sección de NIIF/IFRS debe limitarse a las normas sugeridas arriba o a equivalentes claramente justificables. Cuando no apliquen, debe indicarse explícitamente que no hay referencia internacional materialmente relevante. La sección de materialidad debe ser especialmente detallada y práctica, contextualizada para el giro \"{giro}\" en México."""

    system_prompt = f"""Eres un experto en contabilidad, NIF mexicanas, NIIF/IFRS y legislación fiscal mexicana. Tienes conocimiento profundo de las reformas fiscales vigentes en 2026 en México, particularmente en lo relativo a materialidad, razón de negocios, el Artículo 69-B del CFF y los criterios del SAT para verificar la sustancia económica de las transacciones.

Tu especialidad abarca el sector \"{giro}\" en México y conoces las particularidades fiscales y contables que aplican a organizaciones con régimen \"{regimen}\".

Debes producir contenido verificable, prudente y profesional. Si una norma internacional no aplica de forma clara, no la fuerces. Cuando sea útil, incluye NIIF/IFRS para comparabilidad, alineación técnica o referencia metodológica."""

    return system_prompt, user_prompt
