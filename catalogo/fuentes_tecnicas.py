"""Base acotada revisada contra fuentes oficiales; sin recuperar páginas durante la petición."""
FECHA_REVISION = '2026-10-28'
FUENTES = [
    ('LISR', 'Texto oficial consultado; última reforma impresa 01-04-2024', 'Artículos 41, 27 XX y 113-E', 'https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf'),
    ('LIVA', 'Texto oficial consultado; última reforma impresa 12-11-2021', 'Artículos 1, 2-A y 5', 'https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf'),
    ('SAT: estímulo fronterizo IVA', 'Minisitio vigente; comprobar vigencia y elegibilidad en cada caso', 'Apartados de requisitos y facturación', 'https://www.sat.gob.mx/minisitio/EstimulosFiscalesFronteraNorteSur/region_fronteriza_norte_iva/index.html'),
    ('NIC 2 / IAS 2', 'Texto público emitido, edición 2022; contrastar cambios posteriores antes de entregar', 'Párrafos 6–9, 25 y 28–33', 'https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2022/issued/part-a/ias-2-inventories.pdf?bypass=on'),
    ('NIF C-4', 'Edición NIF 2026 de CINIF', 'Párrafos por verificar en ejemplar licenciado; no se verificó el texto completo de pago', 'https://cinif.org.mx/normatividad_NIF2026.php'),
]


def contexto_tecnico(cuentas, tenant):
    inventario = any('inventar' in ((c.descripcion or '') + ' ' + c.codigoagrupador.nombre).lower() for c in cuentas)
    bloque = '''Controles técnicos obligatorios:
- Separa en cada ejemplo: tratamiento contable, ISR e IVA. Un gasto contable o pérdida por deterioro no crea automáticamente una deducción fiscal.
- La región fronteriza no determina tasa cero de IVA. El estímulo fronterizo puede producir una tasa efectiva de 8% sobre actos elegibles, sujeto a requisitos, avisos, exclusiones y vigencia; no presumir elegibilidad por domicilio. Tasa cero, exención y estímulo son tratamientos distintos. No afirmar que todas las compras causan 16%.
- Cada referencia debe indicar norma/ley, edición o versión realmente consultada, artículo o párrafo comprobable y URL oficial. No inventes párrafos ni digas haber consultado una edición que no recibiste. Distingue referencia comprobada de referencia por verificar. No reproduzcas textos de normas de pago.
'''
    if tenant.regimen_fiscal == 'pf_resico':
        bloque += '''- RESICO persona física: el ISR se determina sobre ingresos efectivamente cobrados, sin IVA y sin deducción alguna, conforme al artículo 113-E de LISR. No deducir costos, mermas o deterioros de esa base ni prometer su deducción futura por destruir o donar bienes. El registro contable se mantiene separado. Analizar el IVA conforme a la LIVA y reglas vigentes que se hayan verificado; no trasladar automáticamente la mecánica de ISR al IVA.
'''
    if tenant.regimen_fiscal == 'pf_empresarial':
        bloque += '- Persona física con actividad empresarial (fuera de RESICO): revisar LISR 103 II y 105 I para adquisiciones y pago efectivo, con todos sus requisitos. No trasladar automáticamente el costo de lo vendido de personas morales a este régimen.\n'
    if inventario:
        bloque += '''- Inventarios ordinarios: distinguir costo y valor neto realizable (VNR). NIC 2, párrafos 6–9: VNR es específico de la entidad y no es sinónimo de valor razonable; no usar la jerarquía de NIIF 13 para justificar su estimación. No recomendar NIIF 13 para inventario ordinario por defecto.
- Métodos fiscales de valuación: LISR artículo 41. Las cuatro opciones del artículo 41 son PEPS, costo identificado, costo promedio y detallista; el costeo directo no figura en esa lista. No atribuirlos a LISR 27 XI/XII. El artículo 39 trata el costo de lo vendido para personas morales. Para pérdida de valor y destrucción, revisar LISR 27 XX y las disposiciones reglamentarias/avisos aplicables; no invocar LISR 28 XIII. LISR 27 XX trata la pérdida de valor de mercancías, no créditos incobrables; estos últimos se tratan en 27 XV. Diferenciar deterioro contable, merma normal, faltante y destrucción fiscal: no tienen consecuencias idénticas.
'''
    bloque += '\nFuentes de apoyo; revisión de la base: ' + FECHA_REVISION + '. La base es acotada y requiere actualización profesional:\n'
    for nombre, edicion, localizacion, url in FUENTES:
        if not inventario and nombre in ('NIC 2 / IAS 2', 'NIF C-4'):
            continue
        if nombre == 'LISR' and not inventario:
            localizacion = 'Artículo 113-E para RESICO persona física; otras referencias por verificar según la cuenta y régimen' if tenant.regimen_fiscal == 'pf_resico' else 'Artículo pertinente por verificar según la cuenta y régimen; no usar reglas de inventarios para bancos o clientes'
        bloque += f'- {nombre} | {edicion} | {localizacion} | {url}\n'
    return bloque
