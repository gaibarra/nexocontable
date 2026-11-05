"""Comparaciones educativas propias; no reproduce textos de IFRS Foundation."""
VERSION='comparacion-internacional-2026-11-05-v1'
BASE_IFRS='https://www.ifrs.org/issued-standards/list-of-standards/'
NORMAS={
 'NIC 7':('Estado de flujos de efectivo','ias-7-statement-of-cash-flows'),
 'NIC 2':('Inventarios','ias-2-inventories'),
 'NIIF 9':('Instrumentos financieros','ifrs-9-financial-instruments'),
 'NIIF 15':('Ingresos de actividades ordinarias procedentes de contratos con clientes','ifrs-15-revenue-from-contracts-with-customers'),
 'NIC 16':('Propiedades, planta y equipo','ias-16-property-plant-and-equipment'),
 'NIC 38':('Activos intangibles','ias-38-intangible-assets'),
 'NIC 19':('Beneficios a los empleados','ias-19-employee-benefits'),
 'NIC 37':('Provisiones, pasivos contingentes y activos contingentes','ias-37-provisions-contingent-liabilities-and-contingent-assets'),
 'NIIF 16':('Arrendamientos','ifrs-16-leases'),
 'NIC 12':('Impuestos a las ganancias','ias-12-income-taxes'),
 'NIC 32':('Instrumentos financieros: presentación','ias-32-financial-instruments-presentation'),
 'NIC 28':('Inversiones en asociadas y negocios conjuntos','ias-28-investments-in-associates-and-joint-ventures'),
 'NIIF 10':('Estados financieros consolidados','ifrs-10-consolidated-financial-statements'),
}

# Volumen, localización educativa, normas de comparación, decisiones, contraste y caso propio.
TEMAS={
 'caja':(2,'Capítulo 20, secciones 20.1–20.5; páginas impresas 314–343',['NIC 7'],
    'Definir el conjunto de efectivo y equivalentes, conciliar sus movimientos y separar operación, inversión y financiamiento. Distinguir cobro y pago de ingreso y gasto: la compra de un equipo consume efectivo de inversión, mientras la depreciación no es una nueva salida de dinero.',
    'La NIC 7 trata la presentación de flujos; no es un catálogo de cargos y abonos de Caja. En México, C-1 orienta el análisis del efectivo y B-2 el estado de flujos. Comparar finalidad y clasificación sin asumir correspondencia literal de párrafos, opciones o excepciones entre los dos marcos.',
    'Supuesto propio: saldo inicial de efectivo y equivalentes de $4,000, cobros de clientes de $11,600, pagos operativos de $2,400 y compra de equipo pagada de $6,000. El flujo operativo neto es $9,200, el de inversión es −$6,000 y el de financiamiento es $0: variación de $3,200 y saldo final de $7,200. Un depósito de $5,000 de Caja a una cuenta propia de Bancos no agrega otro flujo externo si ambos integran ese mismo conjunto. Una depreciación de $800 tampoco reduce por sí misma los $7,200. Las cifras son ilustrativas; no constituyen una operación real ni un cálculo de impuestos.'),
 'bancos':(2,'Capítulo 20, secciones 20.1–20.5; páginas impresas 314–343',['NIC 7'],
    'Conciliar el saldo bancario con el conjunto de efectivo y equivalentes y explicar la variación del periodo por actividades. Diferenciar transferencias propias, comisiones, cobros y financiamientos; una conciliación bancaria no sustituye al estado de flujos ni permite netear entradas y salidas sin analizar su naturaleza.',
    'La comparación más directa para el estado de flujos mexicano es B-2, complementada por C-1 para la composición del efectivo. Revisar especialmente equivalentes, restricciones, sobregiros, flujos en divisas e intereses y dividendos; no importar automáticamente opciones internacionales a las políticas mexicanas.',
    'Supuesto propio: una cobranza de $15,000 aumenta el efectivo; transferir después $8,000 a otra cuenta propia cambia su ubicación, pero no vuelve a aumentar los recursos del conjunto. Si además se paga un préstamo por $3,000, el cierre debe explicar por separado cobranza y devolución de financiamiento, no tratar la devolución del principal como gasto operativo. Conciliar el importe final con auxiliares y estado de situación financiera.'),
 'inventarios':(1,'Capítulo 7: Inventory; secciones 7.1–7.4',['NIC 2'],
    'Analizar costo, asignación a las unidades, reconocimiento del consumo o venta y prueba de valor neto realizable. La comparación ayuda a distinguir un ajuste de precio esperado de una pérdida física y a documentar qué costos de terminación y venta se descontaron para estimar el VNR.',
    'Relacionar el análisis con C-4, contrastando componentes del costo, fórmulas de asignación, deterioro, reversión y revelaciones en sus ediciones aplicables. No equiparar VNR y valor razonable ni usar la referencia internacional como autorización para UEPS. Los métodos fiscales mexicanos requieren su propia revisión.',
    'Supuesto propio: inventario con costo de $10,000, precio de venta esperado de $9,800 y costos necesarios de terminación y venta de $600. El VNR ilustrativo es $9,200 y la diferencia frente al costo es $800. El caso permite revisar el ajuste contable; no convierte esos $800 en deducción fiscal ni sustituye la evidencia del precio y los costos.'),
 'cobrar':(1,'Sección 6.3: Receivables, páginas impresas 177–216; excluye sección 6.6',['NIIF 9'],
    'Distinguir derecho contractual, medición y deterioro por riesgo de crédito. Analizar vencimientos, evidencia de pago, garantías y experiencia de recuperación; el reconocimiento de pérdidas no requiere confundir un incumplimiento probable con la extinción del derecho. Una cuenta comercial y un préstamo con financiamiento necesitan análisis de alcance distinto.',
    'Contrastar con C-3 y C-16, identificando las simplificaciones y criterios que correspondan al instrumento. Una matriz ilustrativa de riesgo no se presenta como porcentaje normativo universal. La baja, cesión y medición pueden requerir análisis adicional; incobrabilidad fiscal y pérdida crediticia contable no son equivalentes.',
    'Supuesto propio: cartera ficticia de $20,000 y estimación sustentada de pérdida de $1,200. Se analiza un saldo neto ilustrativo de $18,800, conservando por separado derecho bruto y correctora. Si después se cobra una partida, revisar la estimación y evitar reconocer una segunda pérdida al aplicar la baja.'),
 'inversiones':(1,'Capítulo 8: Intercorporate Investments; secciones 8.1–8.3',['NIIF 9'],
    'Analizar derechos contractuales, finalidad de administración y características de los flujos para decidir la categoría de medición; no asignar valor razonable a todo instrumento por defecto. Separar interés, cobro de principal, cambio de valor y deterioro, documentando cómo se obtiene cada importe.',
    'Relacionar con C-2 o C-20 según el instrumento y confirmar alcance, clasificación, costos de transacción y efectos en resultados o patrimonio. Los nombres de las categorías y las reglas de ambos marcos deben revisarse, no asumirse idénticos. Una inversión con influencia o control exige otras referencias.',
    'Supuesto propio: se adquiere un instrumento por $50,000 que paga $2,000 al cierre. Antes de llamar rendimiento a todo el cobro, separar si devuelve principal, paga interés o realiza una venta. El mismo flujo de efectivo puede originar registros diferentes; el contrato y la categoría contable sustentan la decisión.'),
 'deuda':(2,'Capítulos 12 y 13: Current Liabilities / Long-Term Financial Liabilities',['NIIF 9'],
    'Analizar reconocimiento de obligaciones contractuales, costo financiero, pagos y modificaciones. Distinguir capital e intereses y evaluar la mecánica de medición que corresponda, sin confundir un refinanciamiento con un mero cambio de fecha. El enfoque ayuda a conciliar contrato y valor en libros.',
    'Contrastar con C-19 el alcance, medición, tratamiento de costos de contratación, modificaciones y baja. No aplicar C-9 por el solo hecho de que una cuenta por pagar se haya estimado al cierre; una deuda determinada y una provisión incierta no tienen necesariamente la misma lógica.',
    'Supuesto propio: un pago de $10,500 incluye $10,000 de principal y $500 de intereses ya devengados. La liquidación del principal cancela deuda, no genera nuevamente el gasto del bien o servicio financiado. Revisar el interés y las comisiones con el contrato y no deducirlos fiscalmente por el simple asiento.'),
 'anticipos_recibidos':(2,'Secciones 12.3.4 y 12.4.1: Customer Deposits / Unearned Revenues',['NIIF 15'],
    'Separar el cobro anticipado del cumplimiento de compromisos con el cliente. Identificar qué se ha prometido, cuándo se satisface y si existe obligación de entregar o devolver recursos. La factura o el cobro por sí solos no demuestran cumplimiento contractual.',
    'Relacionar con D-1 y contrastar identificación de compromisos, contraprestación, aplicación y revelaciones. Un depósito reembolsable puede necesitar un análisis distinto de una obligación de entregar servicios. Los efectos de ISR e IVA mexicanos no se desprenden de aplicar la referencia internacional.',
    'Supuesto propio sin efectos fiscales cuantificados: un cliente entrega $12,000 antes del servicio; después se cumple una parte documentada equivalente a $5,000. Revisar aplicación por $5,000 y compromiso pendiente por $7,000 según lo pactado, en vez de reconocer todo el cobro como ingreso. El ejemplo no concede una tasa de IVA ni resuelve la obligación fiscal real.'),
 'ingresos':(1,'Capítulo 5: Revenue; secciones 5.1–5.3',['NIIF 15'],
    'Analizar contrato, promesas al cliente, contraprestación y evidencia de cumplimiento. Distinguir reconocimiento en un momento y desarrollo a lo largo del tiempo solo cuando esté sustentado; un calendario de facturación no prueba por sí mismo avance. Examinar descuentos, devoluciones y actuación como principal o agente.',
    'Relacionar con D-1 y revisar sus requisitos en lugar de afirmar que son intercambiables. La comparación técnica no vuelve ingreso a una aportación o préstamo ni fija la fecha de acumulación de ISR. Si el ingreso es interés, arrendamiento u otro concepto, revisar antes el alcance de la norma propuesta.',
    'Supuesto propio: un contrato ficticio contiene dos entregables por una contraprestación conjunta de $30,000. Documentar la base de asignación y la evidencia de cada entrega antes de determinar el ingreso del periodo. Cobrar todo al inicio no elimina las prestaciones pendientes ni autoriza a reconocer automáticamente los $30,000.'),
 'ppe':(1,'Capítulos 9 y 10: Property, Plant, and Equipment / Depreciation, Impairment, and Derecognition',['NIC 16'],
    'Analizar costo atribuible, componentes, fecha de disponibilidad para uso, vida útil y valor residual. Separar adquisición, depreciación, mantenimiento y baja; distinguir el recurso físico de sus cuentas correctoras. Los impuestos o porcentajes fiscales no sustituyen la estimación del consumo económico.',
    'Relacionar con C-6 y revisar diferencias de modelos posteriores, componentes, sustituciones y revelaciones. No trasladar a México una opción internacional de revaluación por el solo hecho de encontrarla en el libro. El deterioro requiere su análisis particular y el terreno no se deprecia automáticamente.',
    'Supuesto propio: equipo con base depreciable de $48,000 y vida útil hipotética de 48 meses produce $1,000 mensuales por línea recta. Comparar si fecha de inicio, componentes y residual están sustentados. El cálculo no establece una vida normativa ni una deducción de ISR; la cuenta seleccionada determina si se desarrolla el activo, el gasto o la correctora.'),
 'intangibles':(1,'Capítulo 11: Intangible Assets and Goodwill; secciones 11.1–11.4',['NIC 38'],
    'Examinar identificabilidad, control y beneficios del derecho; separar servicio contratado, licencia adquirida y desarrollo interno. Diferenciar fases de investigación y desarrollo y documentar la decisión de reconocer activo o gasto. Llamar al desembolso inversión no demuestra que cumpla criterios de reconocimiento.',
    'Relacionar con C-8 y contrastar condiciones de reconocimiento, vida útil, amortización, deterioro y revelaciones. No aplicar automáticamente modelos internacionales ni reconocer marcas internas por una valuación comercial. El crédito mercantil requiere su contexto particular y no se equipara a una licencia.',
    'Supuesto propio: una licencia identificada cuesta $24,000 y se utiliza durante 24 meses, sin residual en el caso ilustrativo. El reparto lineal sería $1,000 mensual si la vida y el patrón de consumo fueran adecuados. Una suscripción anual de servicios tecnológicos no se convierte por esa analogía en un intangible controlado.'),
 'empleados':(2,'Sección 12.3.6 y capítulo 16: Employee Payables / Pensions and Other Employment Benefits',['NIC 19'],
    'Analizar obligación por servicios recibidos, plazo de liquidación y naturaleza de los beneficios. Separar remuneraciones del periodo y compromisos de largo plazo; identificar cuándo una estimación especializada es necesaria. El pago neto no equivale al gasto total y un préstamo al trabajador no es automáticamente remuneración.',
    'Relacionar con D-3 y contrastar alcance, valuación y presentación. PTU, obligaciones laborales e impuestos retenidos mexicanos requieren distinción; no importar planes, tasas o supuestos laborales extranjeros. La comparación no reemplaza legislación laboral, fiscal o de seguridad social aplicable.',
    'Supuesto propio: una nómina ficticia devenga $15,000 y se pagan $12,500 al empleado después de retenciones y conceptos documentados de $2,500. Conciliar gasto, obligación con el empleado y saldos con terceros sin reconocer dos veces el costo al efectuar el pago.'),
 'provisiones':(2,'Secciones 12.5–12.7: provisiones, compromisos, presentación y notas',['NIC 37'],
    'Distinguir obligación presente, incertidumbre y evidencia de una posible salida de recursos. Separar provisión reconocida, contingencia por revelar y compromiso que no constituye obligación actual. Una reserva voluntaria para futuros gastos no adquiere carácter de pasivo por cambiar su nombre.',
    'Relacionar con C-9 y contrastar condiciones de reconocimiento, base de estimación, actualización y revelaciones. No convertir una contingencia en deuda cierta ni aplicar porcentajes de ventas sin evidencia. El registro contable no determina por sí solo deducibilidad fiscal ni el resultado de una controversia.',
    'Supuesto propio: se estima una obligación por $8,000 y posteriormente evidencia nueva sustenta $6,500. Analizar el ajuste de $1,500 como revisión de estimación, sin utilizar la provisión para cubrir un gasto ajeno. La existencia y el método de estimación se declaran supuestos, no hechos del cliente.'),
 'arrendamientos':(2,'Secciones 17.1, 17.3.2 y 17.5; excluye opciones ASPE',['NIIF 16'],
    'Analizar activo identificado, control del uso, papel contractual y plazo. Distinguir servicio, anticipo y arrendamiento; separar principal, costo financiero y consumo del derecho cuando se justifique ese modelo. El nombre renta y una factura periódica no resuelven por sí solos el análisis del contrato.',
    'Relacionar con D-5 y contrastar alcance, excepciones, plazo, medición y modificaciones sin importar automáticamente opciones internacionales. El asiento del arrendatario no se utiliza como si fuera del arrendador. La tasa y el plazo no se inventan como si fueran condiciones reales.',
    'Supuesto propio: en un modelo previamente justificado, un pago de $2,000 se integra por $1,700 de principal y $300 de interés. Revisar su relación con la tabla del pasivo y registrar por separado el consumo del derecho si procede. La separación es ilustrativa y no acredita la tasa efectiva ni el tratamiento fiscal de las rentas.'),
 'impuestos_utilidad':(2,'Capítulo 15: Income Taxes; secciones 15.1–15.6',['NIC 12'],
    'Separar impuesto corriente y diferido; comparar base fiscal y valor contable y analizar diferencias temporales y permanentes. Una diferencia permanente no produce automáticamente un diferido. Revisar reversión esperada y recuperabilidad, en vez de registrar activos únicamente para ajustar la carga de resultados.',
    'Relacionar con D-4 y revisar alcance, excepciones, tasas, compensación y reconocimiento de activos. En México la determinación de ISR depende del régimen y del periodo; no se aplica una tasa corporativa universal a personas físicas. La comparación tampoco genera deducciones para RESICO PF.',
    'Supuesto educativo con tasa exclusivamente hipotética de 25%: diferencia temporal deducible de $4,000 produciría un efecto de $1,000 si fueran procedentes su reconocimiento y recuperación. La cifra enseña la mecánica, no establece tasa mexicana ni prueba que el activo deba reconocerse. Distinguir la cuenta de activo 185 del pasivo 259.'),
 'capital':(2,'Capítulo 14: Complex Financial Instruments',['NIC 32'],
    'Analizar derechos y obligaciones del instrumento para diferenciar patrimonio y pasivo, más allá de su denominación legal. Documentar aportaciones, distribuciones y condiciones de reembolso. Un recurso recibido del propietario no se transforma automáticamente en ingreso ni en capital permanente.',
    'Relacionar con C-11 y la presentación de cambios en patrimonio; contrastar condiciones contractuales y obligaciones de restitución. La comparación internacional no determina CUCA, CUFIN ni los efectos fiscales de dividendos. Para persona física no inventar acciones o acuerdos societarios que no correspondan.',
    'Supuesto propio: se reciben $20,000 del titular. Si el acuerdo sustenta aportación patrimonial, analizar ese componente; si obliga a restituir el importe en una fecha cierta, revisar la naturaleza de la obligación. El mismo efectivo no justifica indistintamente ambas clasificaciones.'),
 'participaciones':(1,'Capítulo 8: Intercorporate Investments; conceptos de influencia y control',['NIC 28','NIIF 10'],
    'Identificar derechos de voto, acuerdos, influencia y control antes de escoger método. Distinguir inversión en estados individuales, participación en resultados y consolidación. La titularidad de una acción o un porcentaje aislado no resuelve por sí mismo el alcance del análisis.',
    'Relacionar con C-7 y, si existe control y procede consolidación, con B-8. No asumir equivalencia de requisitos ni combinar técnicas de estados individuales y consolidados. Un dividendo y el reconocimiento de participación pueden requerir ajustes para evitar duplicar un mismo resultado.',
    'Supuesto propio: una participación ilustrativa del 30% en una entidad no demuestra por sí sola control. Examinar derechos y acuerdos antes de usar resultados de la participada. Si se ilustra participación sobre una utilidad de $10,000, el cálculo de $3,000 requiere primero justificar método, base y ajustes aplicables.'),
}


def paquete(tipo,perfil):
    from .desarrollo_uniforme import PERFILES
    if tipo=='costos':base=TEMAS['inventarios']
    elif tipo in TEMAS:base=TEMAS[tipo]
    else:
        p=PERFILES[tipo]
        base=(p['volumen'],p['localizacion'],[],
          'Identificar la sustancia del hecho, los derechos u obligaciones y la evidencia antes de escoger un estándar internacional. Una cuenta del catálogo mexicano no siempre tiene una NIC o NIIF exclusiva. Distinguir reconocimiento financiero, presentación y registros de control; no asignar una norma por semejanza del nombre.',
          'El marco mexicano se aplica según la naturaleza de la operación. La falta de una referencia internacional específica no elimina el análisis contable ni autoriza a usar una norma de presentación como regla universal de medición. Documentar el fundamento particular y el alcance de cualquier comparación.',
          'Supuesto propio: un pago de $6,000 puede corresponder a consumo del periodo, un derecho a recibir servicios o restitución de una deuda. Explicar contrato y hecho económico antes de elegir activo, gasto o cancelación de pasivo. Si solo se trata de una base fiscal o de control, no convertirla automáticamente en un elemento de estados financieros.')
    vol,localizacion,claves,decision,contraste,caso=base
    if tipo=='anticipos':
        decision='No hay una NIC o NIIF exclusiva para todos los pagos anticipados. Analizar el derecho recibido, el servicio pendiente y su consumo. Una regla internacional sobre ingresos del proveedor no se aplica automáticamente a quien paga; examinar si el hecho deriva en inventario, intangible, servicio o un derecho reembolsable.'
        contraste='Relacionar la revisión mexicana con C-5 y comprobar la norma del activo o gasto al aplicarse el anticipo. La comparación conceptual distingue pago y consumo, pero no determina deducción fiscal, IVA ni plazo de amortización. El régimen del cliente y su contrato requieren comprobación separada.'
        caso='Supuesto propio: se pagan $6,000 por tres meses de un servicio que se consume uniformemente. Después del primer mes, un reparto ilustrativo de $2,000 dejaría $4,000 pendientes de consumo. El periodo y el patrón son hipótesis explícitas; no una regla universal ni un reconocimiento automático de activo sin derecho sustentado.'
    elif tipo=='gastos':
        decision='No existe una norma internacional única que resuelva todo gasto de administración o venta. Clasificar su naturaleza y distinguir consumo, adquisición de activo, nómina, financiamiento y arrendamiento antes de escoger referencia. Un pago y un gasto pueden pertenecer a periodos distintos sin que ello suponga un error.'
        contraste='La presentación del resultado no sustituye requisitos de reconocimiento de cada operación. En México tampoco D-2 aplica automáticamente a cualquier gasto. Comparar devengo y evidencia con la norma particular identificada, sin importar opciones de un libro extranjero ni atribuir efecto fiscal al asiento.'
        caso='Supuesto propio: un servicio de $3,000 se recibe al cierre y se paga el mes siguiente. Separar reconocimiento del gasto y obligación de su liquidación para no reconocer el gasto dos veces. Confirmar recepción y contrato; el ejemplo no demuestra deducibilidad ni acreditamiento de impuestos.'
    elif tipo=='impuestos':
        decision='Separar impuesto a la utilidad, IVA, retenciones, anticipos y estímulos antes de buscar una referencia internacional. Una norma internacional sobre impuesto a las ganancias no determina tasas, acreditamientos o devoluciones de IVA mexicano. La cuenta de control fiscal no se vuelve instrumento contractual por llamarse cuenta por cobrar.'
        contraste='La norma mexicana de presentación ayuda a exponer derechos y obligaciones, pero el nacimiento y aplicación del crédito fiscal requiere disposiciones mexicanas verificables. La comparación educativa organiza conciliación y clasificación; no homologa tributos de países distintos ni atribuye al cliente una elegibilidad no comprobada.'
        caso='Supuesto propio: el auxiliar muestra $1,600 por un impuesto recuperable y una declaración todavía no conciliada. Revisar periodo, origen y requisitos antes de reconocer una aplicación o devolución. La igualdad numérica de un impuesto a favor y otro por pagar no autoriza su compensación automática.'
    elif tipo=='orden':
        decision='Las cuentas mexicanas de orden y las bases CUCA o CUFIN no tienen una correspondencia automática con una NIC o NIIF. Distinguir control fiscal, custodia y compromisos de los elementos que se reconocen en estados financieros. La existencia del registro auxiliar no prueba propiedad ni obligación por ese mismo importe.'
        contraste='Evaluar el hecho subyacente y sus posibles revelaciones sin sumar las cuentas de orden al balance. La comparación internacional no reemplaza el fundamento fiscal mexicano ni prescribe un número SAT. Si un hecho sí reúne condiciones de reconocimiento financiero, analizarlo en su cuenta y con su norma particular.'
        caso='Supuesto propio: se custodian bienes de terceros documentados por $10,000 y luego se devuelven bienes por $4,000. El control remanente sería $6,000; no constituye automáticamente inventario propio, ingreso, costo o dinero disponible. Conciliar las cuentas de control y la evidencia de custodia sin fabricar un resultado financiero.'
    elif tipo=='especializada':
        decision='Una operación especializada puede necesitar estándares internacionales específicos y datos que el nombre del agrupador no proporciona. Identificar actividad, recurso, derechos y modelo de negocio; no aplicar por analogía la regla de equipo a un activo biológico ni la de una licencia al crédito mercantil.'
        contraste='Mantener visible la identificación normativa pendiente cuando no se cuenta con una fuente educativa especializada publicada. La guía general explica qué decisión y documentación faltan; no establece medición sectorial ni prueba que un marco internacional o mexicano haya sido satisfecho.'
        caso='Supuesto propio: un recurso se registra por $25,000, pero aún no se conoce si pertenece a la entidad o solo se administra por encargo. Identificar contrato, control y obligaciones antes de escoger un criterio de reconocimiento o valuación. Una cifra disponible no justifica seleccionar costo o valor razonable por conveniencia.'
    if tipo=='costos':
        contraste+=' Para costos de servicios sin bienes inventariables, revisar el alcance antes de aplicar NIC 2; no forzar la comparación por el nombre costo.'
    return dict(version=VERSION,categoria=tipo,volumen=vol,localizacion=localizacion,
        normas=[dict(clave=k,titulo=NORMAS[k][0],url=BASE_IFRS+NORMAS[k][1]+'/') for k in claves],
        alcance=decision,contraste=contraste,caso=caso,
        revision='Documentar marco de información elegido, edición, fecha efectiva, operación y decisión revisada. Verificar requisitos y localización exacta en ejemplar autorizado antes de declarar cumplimiento. La guía educativa de 2021 aporta conceptos y ejemplos; no acredita por sí misma reformas posteriores ni autoriza el tratamiento de textos IFRS protegidos.',
        cuenta=str(perfil.get('codigo',''))+' — '+str(perfil.get('descripcion','')))


def renderizar(p):
    fuentes=p.get('fuentes',[])
    lineas=['## 3. Referencia internacional',
        '**Aplicación a la cuenta '+p['cuenta']+'.** Comparación educativa propia para orientar la revisión; el código de cuenta es interno o SAT y no un código exigido por las NIIF.']
    if p['normas']:
        lineas.append('**Normas de referencia:** '+'; '.join(n['clave']+' — '+n['titulo'] for n in p['normas'])+'.')
    else:
        lineas.append('**Sin equivalencia automática.** Identificar la norma internacional particular a partir de la operación; no se asigna una NIC o NIIF exclusiva por la denominación de esta cuenta.')
    lineas.extend(['### Alcance y utilidad de la comparación',p['alcance'],
                  '### Relación y diferencias por comprobar con las NIF mexicanas',p['contraste']])
    if p['categoria'] in ('caja','bancos'):
        lineas.extend(['### Decisiones para preparar el estado de flujos',
          '**Definir el conjunto y el corte.** Identificar dinero disponible y los instrumentos considerados equivalentes, su liquidez, riesgo y finalidad. No clasificar una inversión como efectivo por su nombre comercial. Las restricciones y condiciones contractuales requieren revisión separada; un libro extranjero no establece automáticamente los requisitos mexicanos.',
          '**Elegir y conciliar la presentación.** El método directo organiza cobros y pagos; el indirecto concilia el resultado con el flujo operativo mediante ajustes documentados. No confundir flujo, utilidad y saldo disponible. Identificar partidas no monetarias y vincular el saldo final de efectivo con el estado de situación financiera.',
          '**Revelaciones y revisión de vigencia.** Preparar composición del efectivo, conciliación y operaciones relevantes sin movimiento monetario; revisar restricciones y movimientos de financiamiento. La clasificación de intereses y dividendos y la transición por [NIIF 18](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-18-presentation-and-disclosure-in-financial-statements/) deben contrastarse según el periodo: su vigencia obligatoria corresponde a periodos anuales iniciados a partir del 1 de enero de 2027, con adopción anticipada permitida. No presentar automáticamente esa modificación futura como obligatoria para el ejercicio 2026.'])
    lineas.extend(['### Ejemplo de aplicación y comprobación',p['caso'],
                  '### Evidencia y límites de la revisión',p['revision']])
    if fuentes:
        for f in fuentes:
            lineas.append('**Fuente educativa autorizada ['+f['id']+']:** '+f['norma']+', '+f['edicion']+', '+f['localizacion']+'. [Consulta del material]('+f['url']+'). '+f.get('atribucion',''))
    if p['normas']:
        lineas.append('**Consulta oficial — identificación y alcance:** '+' · '.join('['+n['clave']+']('+n['url']+')' for n in p['normas'])+'. Los enlaces no acreditan licencia para reproducir el texto íntegro ni consulta de sus párrafos.')
    return '\n\n'.join(lineas)
