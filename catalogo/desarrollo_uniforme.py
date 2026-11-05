"""Criterios educativos propios por naturaleza, con un contrato común de desarrollo.

No reproduce normas. Las fuentes educativas se delimitan por capítulo y licencia;
los requisitos NIF no consultados conservan su pendiente de revisión profesional.
"""
import re
import unicodedata

VERSION = 'desarrollo-2026-11-05-v1'
MATICES = {
    '108':'La cuenta seleccionada es estimación de incobrables: desarrollar constitución, revisión o aplicación de la estimación, no limitar los ejemplos a una venta y su cobro.',
    '116':'La cuenta seleccionada es estimación de obsolescencia: desarrollar deterioro, conciliación de la correctora y aplicación o revisión; no sustituirla por una compra ordinaria.',
    '151':'La cuenta corresponde a terrenos: no proponer depreciación automática. Usar adquisición y baja, reclasificación o revisión que proceda, con supuestos documentados.',
    '171':'La cuenta es depreciación acumulada, correctora del activo: los ejemplos deben mover esa correctora y conciliar costo y valor en libros.',
    '172':'La cuenta es deterioro acumulado de activos fijos: distinguir pérdida de valor de depreciación sistemática y desarrollar el movimiento de la correctora.',
    '180':'El crédito mercantil necesita comprobar el contexto de adquisición y la norma particular; no reconocer crédito mercantil generado internamente ni amortizarlo automáticamente como una licencia.',
    '183':'La cuenta es amortización acumulada: desarrollar su reconocimiento y aplicación o baja con el activo relacionado; no presentarla como un activo independiente.',
    '187':'La cuenta es PTU diferida: analizar beneficios a empleados y la naturaleza del activo; no sustituir PTU por ISR diferido ni aplicar mecánicamente una tasa de ISR.',
    '257':'La cuenta es PTU diferida de pasivo: analizar beneficios a empleados y el efecto diferido correspondiente, sin convertirlo en ISR diferido.',
    '402':'La cuenta corrige ingresos: desarrollar devolución, descuento o bonificación y su efecto sobre la operación original, no registrarla como una nueva venta.',
    '503':'La cuenta corrige compras: explicar devolución, descuento o bonificación y su efecto sobre inventario o costo, sin duplicar el beneficio.',
    '610':'La cuenta es PTU diferida en resultados: distinguir beneficio a empleados, impuesto a la utilidad y diferencias de periodo.',
    '611':'La cuenta es gasto de ISR: el ejemplo puede desarrollar impuesto causado; no obligar a introducir diferido si los supuestos no contienen diferencias temporales.',
    '613':'La cuenta es gasto por depreciación: desarrollar cargo al gasto y abono a depreciación acumulada, y otro caso de cierre; una compra por sí sola no desarrolla esta cuenta.',
    '614':'La cuenta es gasto por amortización: desarrollar consumo de un derecho con vida útil sustentada y su correctora; no limitar el asiento a la compra del intangible.',
}
EJES = {
    'reconocimiento': 'Reconocimiento y naturaleza',
    'valuacion_inicial': 'Valuación inicial',
    'valuacion_posterior': 'Valuación posterior y cierre',
    'presentacion': 'Presentación y clasificación',
    'revelaciones': 'Revelaciones',
    'baja': 'Baja, aplicación o liquidación',
}


def normalizar(valor):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(valor).lower()) if not unicodedata.combining(c))


def ficha(familia, normas, volumen, localizacion, ejes, evidencia, error, casos):
    assert len(ejes)==6
    return dict(familia=familia, normas=normas, volumen=volumen, localizacion=localizacion,
                ejes=dict(zip(EJES,ejes)), evidencia=evidencia, error=error, casos=casos)


PERFILES = {
 'caja': ficha('bancos',['C-1','B-6','B-2','B-15'],1,'Secciones 6.2 y 6.2.1; páginas impresas 172–176',[
    'Identificar dinero físico controlado por la organización, propietario y custodio. El cobro carga Caja y el pago la abona. Diferenciar ingreso, anticipo, préstamo y aportación según su origen; los fondos personales o de terceros no se incorporan como recursos propios sin analizar su naturaleza.',
    'Contar billetes y monedas por denominación y registrar pesos por importe nominal. Un vale, pagaré o anticipo a empleado no es efectivo físico. Documentar su origen antes de reclasificarlo como derecho de cobro o gasto; no crear una cuenta por cobrar ficticia para cuadrar.',
    'Conciliar saldo inicial más entradas menos salidas con el arqueo. Investigar diferencias y corte de comprobantes. Si existen divisas, documentar moneda funcional y conversión; la referencia B-15 es condicional, no prueba que el cliente tenga dólares. Un saldo físico negativo requiere investigación.',
    'Separar Caja, Bancos e inversiones en los auxiliares. Examinar restricciones comprobadas y su duración antes de clasificar disponibilidad. Una reserva interna no equivale automáticamente a un embargo. No compensar efectivo con deudas por conveniencia ni presentar vales como billetes.',
    'Preparar composición, monedas, bases de medición y restricciones relevantes; evaluar notas con el ejemplar autorizado. Un arqueo firmado no sustituye revelaciones financieras. La referencia B-2 aporta análisis de flujos cuando proceda: mover dinero de Caja a Bancos no crea ingreso ni gasto.',
    'Registrar salidas contra su destino real y conservar trazabilidad. Investigar faltantes y sobrantes antes de reconocer pérdida, ingreso o responsabilidad del custodio. La cuenta transitoria requiere seguimiento y resolución; no puede ocultar indefinidamente diferencias ni atribuir deudas al empleado sin evidencia.'
 ],'Arqueo por denominación, auxiliar, comprobantes de corte, conciliación, autorizaciones y contratos de restricción, si existen.',
 'No trasladar un plazo extranjero de tres meses como requisito NIF comprobado, ni inferir IVA o deducción del simple movimiento de Caja.',
 ['Cobro documentado y depósito posterior, sin duplicar ingreso.','Arqueo con un vale o diferencia investigada y ajuste justificado.']),
 'bancos': ficha('bancos',['C-1','B-6','B-2','B-15'],1,'Secciones 6.2 y 6.2.1; páginas impresas 172–176',[
    'Identificar cuenta bancaria, titularidad, moneda y disponibilidad. Distinguir depósito por cobranza, transferencia interna, préstamo y aportación. Un depósito no acredita por sí mismo un ingreso; un retiro requiere identificar su beneficiario y causa. El banco y el auxiliar se concilian, no se sustituyen.',
    'Registrar el movimiento por su importe documentado, separando comisiones e impuestos que efectivamente correspondan. Conservar referencia bancaria y fecha de la operación. Si hay divisas, determinar moneda funcional y base de conversión; no aplicar automáticamente un tipo de cambio fiscal al registro contable.',
    'Conciliar libros y estado de cuenta, identificar partidas en tránsito y errores. Registrar comisiones u otros movimientos omitidos únicamente con soporte; un cheque pendiente no genera por sí mismo otro gasto. Verificar restricciones, conversión y antigüedad de partidas al cierre.',
    'Examinar disponibilidad y plazo de restricciones para su clasificación y notas. Un sobregiro requiere analizar si es financiamiento; no netear automáticamente saldos de distintos bancos. Separar instrumentos de inversión que no cumplan la naturaleza de efectivo o equivalente bajo el marco revisado.',
    'Preparar composición por moneda y tipo de cuenta, restricciones materiales, política de medición y conciliación con estados financieros. Documentar movimientos relevantes y riesgos de disponibilidad. Los nombres de bancos y números completos de cuenta no deben divulgarse innecesariamente en el manual.',
    'Documentar transferencia, pago o cancelación con su contrapartida y conciliación final. Revisar cuentas inactivas y diferencias antes de cerrarlas. La transferencia entre cuentas propias no constituye automáticamente un flujo externo; comprobar el conjunto de efectivo considerado y evitar duplicidad.'
 ],'Estados bancarios, conciliación, auxiliares, contratos, confirmaciones y soporte del origen de fondos.',
 'La conciliación no es una autorización para inventar ajustes; la NIF B-15 solo se considera si hay moneda extranjera.',
 ['Cobranza y comisión bancaria separadas.','Conciliación de cierre con movimiento omitido comprobado.']),
 'inversiones': ficha('otra',['C-2','C-20'],1,'Capítulo 8: Intercorporate Investments; secciones 8.1–8.3',[
    'Identificar contrato, instrumento, derechos y objetivo de administración. Diferenciar tenencia para inversión, derecho de cobro contractual y participación con influencia o control. El nombre comercial del producto no determina su categoría contable ni convierte toda inversión en equivalente de efectivo.',
    'Determinar el importe de contratación y separar costos según la clasificación que se haya sustentado. Documentar moneda, vencimiento y condiciones de rendimiento. No imponer un criterio único de costo o valor razonable a todos los instrumentos sin revisar naturaleza y norma particular.',
    'Preparar rendimiento devengado, conciliación de movimientos y evaluación de medición y riesgo. Una cotización no es automáticamente VNR ni una pérdida realizada. Analizar cambios de valor y deterioro conforme a la categoría validada; distinguir movimientos monetarios de cambios de medición.',
    'Clasificar por disponibilidad, vencimiento, finalidad y restricciones comprobadas; separar inversión del efectivo operativo y de participaciones permanentes. No compensar activos con financiamientos sin análisis de los requisitos. Identificar la porción que corresponda a resultados u otro componente del patrimonio.',
    'Preparar tipo de instrumento, política de clasificación y medición, supuestos relevantes, restricciones y riesgos materiales. Documentar fuente y fecha de precios. Si faltan condiciones contractuales o valuación fiable, exponer el supuesto por confirmar en lugar de inventar un rendimiento garantizado.',
    'Conciliar venta, vencimiento o baja con efectivo recibido, rendimientos y valor en libros. Determinar el resultado y los gastos de realización según la clasificación revisada. No confundir una reinversión o un traspaso entre custodios con venta ni eliminar el historial del instrumento.'
 ],'Contrato, posición de custodia, precios fechados, cálculo de rendimientos y política de clasificación.',
 'No recomendar opciones ASPE ni afirmar que todos los instrumentos se miden igual.',
 ['Adquisición de instrumento identificado y rendimiento ilustrativo.','Cierre o vencimiento con conciliación del valor en libros.']),
 'cobrar': ficha('clientes',['C-3','C-16'],1,'Sección 6.3: Receivables, páginas impresas 177–216; excluye 6.6',[
    'Identificar el derecho de cobro, deudor y hecho que lo origina; distinguir cliente, empleado, socio, anticipo y documento con financiamiento. Una factura o un vale no demuestra por sí solo recuperabilidad. Separar el reconocimiento del derecho del cobro y de la estimación de pérdidas.',
    'Documentar importe exigible, vencimiento, moneda, descuentos y condiciones de financiamiento. Evaluar si el instrumento requiere una norma diferente de una cuenta comercial ordinaria. No utilizar la tasa fiscal o una tasa de interés arbitraria para estimar su importe inicial.',
    'Conciliar cobros, notas de crédito y antigüedad; evaluar riesgo y recuperabilidad con evidencia disponible. La estimación de deterioro requiere método y supuestos, no un porcentaje universal. Mantener separado saldo bruto, estimación y baja específica para no duplicar la pérdida.',
    'Clasificar corto y largo plazo según condiciones documentadas y separar partes relacionadas si corresponde. Presentar saldo y estimación con criterio consistente. No netear una deuda del cliente con una obligación distinta sin examinar el derecho y los requisitos aplicables.',
    'Preparar política de reconocimiento, análisis de antigüedad, concentración, garantías y cambios en la estimación que sean relevantes. Explicar método y evidencia. Si el deudor no es cliente comercial, justificar la naturaleza real y no atribuir ventas inexistentes a la organización.',
    'Documentar cobro, cesión, cancelación o baja y evaluar si subsisten derechos o riesgos. Una baja contable no equivale a condonación ni a deducción de ISR. Mantener el soporte de la decisión y evitar eliminar simultáneamente saldo y estimación con cargo duplicado a resultados.'
 ],'Contrato, documento del derecho, auxiliar por deudor, antigüedad, cobranza y cálculo de deterioro.',
 'No equiparar estimación contable con incobrabilidad fiscal ni tratar anticipos a proveedores como ventas a crédito.',
 ['Origen y cobro de un derecho realista para el giro.','Cierre con estimación o baja sustentada, sin duplicar pérdida.']),
 'anticipos': ficha('otra',['C-5'],1,'Sección 2.4 y capítulo 3: conceptos, reconocimiento y estados financieros',[
    'Identificar el pago que otorga un derecho a recibir bienes o servicios y el periodo de aprovechamiento. Distinguir anticipo a proveedor, depósito recuperable y gasto ya consumido. No reconocer un activo únicamente porque el catálogo fiscal lo denomina gasto diferido.',
    'Vincular el desembolso al contrato, factura y prestación futura identificable. Separar importes recuperables y componentes que no correspondan al derecho. El reconocimiento contable del pago no determina por sí mismo deducción de ISR ni acreditamiento de IVA.',
    'Aplicar a gasto o a otro activo conforme se reciben beneficios, con una base de distribución documentada. Evaluar cancelación, incumplimiento y recuperación del remanente. No amortizar automáticamente por porcentajes fiscales ni mantener como activo un servicio que ya se consumió.',
    'Separar por proveedor y concepto; distinguir corto y largo plazo según el periodo restante y naturaleza. No mezclar anticipos entregados con cobros anticipados de clientes. En arrendamientos, el anticipo no demuestra por sí solo reconocimiento de derecho de uso.',
    'Preparar naturaleza de pagos, periodo de aplicación, método de consumo y saldos significativos o sujetos a incertidumbre. Explicar recuperabilidad y cambios de contrato. La existencia de beneficios futuros debe documentarse; no se infiere de un título de cuenta.',
    'Cancelar el derecho al aplicarse, devolverse o perderse, con contrapartida sustentada. Conciliar saldo inicial, pagos, aplicaciones y final. Separar una devolución de anticipo de un ingreso y no continuar distribuyendo el saldo una vez agotado o cancelado el contrato.'
 ],'Contrato, comprobante de pago, calendario de aplicación y confirmación de recepción o devolución.',
 'No registrar anticipos recibidos de clientes como activo ni capitalizar indiscriminadamente gastos preoperativos.',
 ['Pago anticipado de servicio y aplicación del primer periodo.','Cancelación o cierre con saldo pendiente de consumo.']),
 'inventarios': ficha('inventarios',['C-4'],1,'Capítulo 7: Inventory; secciones 7.1–7.4',[
    'Identificar mercancía, materiales, producción en proceso o bienes destinados a venta bajo control de la entidad. Separar mercancía de terceros y anticipos. La presencia física no prueba propiedad: documentar corte, entrega y condiciones comerciales; adaptar unidades a servicios, comercio o restaurante.',
    'Construir costo de adquisición o producción con componentes sustentados, separando impuestos recuperables, desperdicios anormales y gastos que correspondan al periodo. Documentar unidades, descuentos y gastos atribuibles. No equiparar todo desembolso con costo capitalizable ni copiar tasas fiscales al inventario.',
    'Conciliar entradas, salidas y conteo; aplicar consistentemente la fórmula de asignación revisada. Analizar obsolescencia y valor neto realizable con evidencia de precio y costos de terminación y venta. El VNR no es valor razonable ni se fundamenta automáticamente en NIIF 13.',
    'Separar materias primas, proceso, terminados o mercancías según la operación. Identificar deterioro y restricciones significativas, sin duplicar las existencias y su estimación. En un restaurante considerar insumos perecederos; en servicios justificar si hay bienes inventariables en vez de presumirlos.',
    'Preparar política de costos, fórmula aplicada, composición, ajustes y restricciones materiales. Documentar supuestos del VNR y causas de cambios. Las pérdidas físicas y ajustes de valor requieren conciliación; una nota genérica sobre inventarios no explica por sí sola su efecto.',
    'Reconocer salida por venta, consumo, merma, destrucción o devolución según el hecho documentado. Separar el registro contable de requisitos fiscales de destrucción. No recomendar UEPS como política NIF/NIIF ni atribuir métodos fiscales al artículo equivocado de la LISR.'
 ],'Kárdex, recepción, conteos, costos, evidencia de VNR y actas de ajustes o bajas.',
 'No confundir merma, deterioro, destrucción fiscal y costo de ventas; RESICO PF no obtiene deducciones de ISR por esos registros.',
 ['Compra o producción vinculada al giro con salida identificada.','Cierre con deterioro o merma sustentada y conciliación.']),
 'ppe': ficha('otra',['C-6'],1,'Capítulo 9, secciones 9.1–9.4; capítulo 10: Depreciation, Impairment, and Derecognition',[
    'Identificar activo tangible controlado y destinado a uso, no a venta ordinaria. Documentar recepción, disponibilidad y componentes relevantes. Distinguir mantenimiento de mejora o sustitución. Terrenos, equipo instalado y obras en proceso requieren analizar su estado, no una regla uniforme de depreciación.',
    'Construir costo con adquisición y erogaciones directamente atribuibles justificadas. Separar impuestos recuperables y gastos sin relación demostrada. Si hay obligación de retiro, financiamiento o adquisición conjunta, documentar el análisis particular; no incorporar intereses ni presupuestos completos de forma automática.',
    'Preparar depreciación con base, valor residual, vida útil y método coherentes con el uso. Revisar componentes e indicios de deterioro y documentar cambios de estimación. No usar tasas fiscales como justificación de vida útil; el terreno no se deprecia por defecto.',
    'Mostrar costo, depreciación y deterioro de manera conciliable y clasificar obra en proceso según su condición. La depreciación acumulada es correctora del activo, no otro bien ni una deuda. Separar bienes propios de derechos de uso que requieran tratamiento distinto.',
    'Preparar clases de bienes, métodos, vidas útiles, movimientos y restricciones relevantes. Identificar supuestos del deterioro y compromisos cuando correspondan. La política debe explicar cómo se aplicará al tipo de equipo del cliente sin inventar avalúos o fechas de puesta en uso.',
    'Conciliar venta, sustitución, siniestro o retiro contra costo y depreciación acumulada; determinar resultado contable. No depreciar indefinidamente un componente dado de baja ni registrar el precio de venta como utilidad íntegra. Analizar separadamente ISR e IVA del hecho concreto.'
 ],'Factura, acta de puesta en uso, auxiliar de bienes, componentes, depreciación, revisiones de vida útil y baja.',
 'No capitalizar todo mantenimiento ni depreciar terrenos o equiparar depreciación contable y deducción fiscal.',
 ['Adquisición y puesta en uso con depreciación ilustrativa.','Cierre, sustitución de componente o baja con valor en libros.']),
 'intangibles': ficha('otra',['C-8'],1,'Capítulo 11: Intangible Assets and Goodwill; secciones 11.1–11.4',[
    'Identificar derecho o recurso no monetario sin sustancia física y su control. Diferenciar licencia adquirida, servicio, investigación, desarrollo y gasto de organización. Una expectativa de beneficio o el nombre “diferido” no bastan para reconocer un intangible; documentar los criterios específicos a revisar.',
    'Separar precio y costos atribuibles del proyecto de gastos del periodo, capacitación y mantenimiento. En desarrollo interno, documentar fase, viabilidad y evidencia antes de capitalizar. No reconocer una marca creada internamente solo por asignarle una valuación o por registrarla legalmente.',
    'Evaluar vida útil, disponibilidad para uso, amortización y señales de deterioro. Un plazo fiscal no determina automáticamente vida económica. Si se considera vida indefinida, fundamentar y revisar esa conclusión; no usarla como permiso para omitir evaluación de recuperabilidad.',
    'Separar por clase, costo, amortización y deterioro; distinguir anticipos y servicios tecnológicos de activos controlados. Una suscripción de software no se presenta automáticamente como licencia perpetua. Mostrar los saldos de forma que permitan seguir la inversión y su consumo.',
    'Preparar naturaleza del derecho, vida útil, método, cambios y restricciones materiales. Documentar supuestos de proyectos y contratos. Cuando falten los derechos de uso o condiciones del servicio, plantear la comprobación requerida en vez de afirmar que todo software se capitaliza.',
    'Documentar expiración, abandono, venta o sustitución y eliminar los componentes correspondientes del auxiliar. Evaluar el remanente recuperable antes de continuar amortizando. La baja contable no produce por sí misma una deducción fiscal; conciliar sus efectos y evidencia.'
 ],'Contrato de derechos, costos del proyecto por fase, fecha de uso y análisis de amortización o deterioro.',
 'No convertir gastos de organización, publicidad o investigación en activos por su sola denominación SAT.',
 ['Adquisición de derecho identificado y amortización justificada.','Cierre con expiración, abandono o revisión de recuperabilidad.']),
 'deuda': ficha('proveedores',['C-19'],2,'Capítulos 12 y 13: Current Liabilities / Long-Term Financial Liabilities',[
    'Identificar obligación contractual, acreedor y recepción de bienes, servicios o financiamiento. Distinguir deuda comercial determinada, obligación fiscal y provisión incierta. El vencimiento futuro no impide reconocer una obligación ya existente; tampoco una cotización genera automáticamente un pasivo.',
    'Documentar principal, moneda, vencimiento y costos financieros. Analizar si hay financiamiento significativo y la medición que corresponde al contrato. No aplicar valor nominal o valor presente indistintamente a toda deuda; justificar el tratamiento del instrumento real seleccionado.',
    'Conciliar pagos, intereses y saldo con el acreedor y contrato. Si procede costo amortizado, sustentar tasa y calendario; si hay divisas, analizar conversión. Una refinanciación exige evaluar sus condiciones, no solo cambiar fecha de vencimiento en el auxiliar.',
    'Separar corto y largo plazo con base contractual y situación al cierre, identificando garantías y condiciones relevantes. No netear proveedores con activos por conveniencia. Si la cuenta es correctora o tiene saldo deudor, investigar anticipo, devolución o error antes de mantenerlo como deuda.',
    'Preparar condiciones, vencimientos, moneda, garantías e incumplimientos relevantes. Explicar política de medición y cambios materiales. No publicar datos personales de acreedores innecesarios en ejemplos; usar supuestos ficticios que respeten la naturaleza del contrato.',
    'Dar de baja por liquidación, cancelación o extinción comprobada; analizar modificaciones y conciliación del resultado. No cancelar por antigüedad sin acreditar extinción ni confundir un pago con gasto nuevo. Separar condonación, descuento comercial y diferencia de cambio.'
 ],'Contrato, recepción, auxiliares por acreedor, confirmaciones, calendario financiero y comprobantes de liquidación.',
 'No aplicar automáticamente NIF C-9 a todo proveedor ni reconocer gasto dos veces al registrar y pagar.',
 ['Recepción o financiamiento y reconocimiento de obligación.','Pago, cierre con intereses o modificación contractual sustentada.']),
 'anticipos_recibidos': ficha('ingresos',['D-1'],2,'Secciones 12.3.4 y 12.4.1: Customer Deposits / Unearned Revenues',[
    'Identificar cobro previo y compromiso con el cliente. Diferenciar anticipo por contrato, depósito reembolsable y venta ya cumplida. Recibir efectivo no prueba que el ingreso esté devengado; evaluar la prestación pendiente y los derechos de devolución.',
    'Conciliar dinero recibido, contrato, comprobante e impuestos que correspondan. Separar el pasivo de los importes fiscales sin asumir que el momento contable coincide con el de ISR o IVA. No presentar el anticipo recibido como pago anticipado del activo.',
    'Revisar cumplimiento, devoluciones, cambios de alcance y saldos envejecidos. Aplicar al ingreso conforme se sustente el cumplimiento del compromiso, no por una fecha arbitraria ni por agotarse la caja. Documentar obligaciones todavía pendientes y análisis de estimaciones.',
    'Mostrar la obligación con clientes y clasificar por plazo y naturaleza. No netear con cuentas por cobrar sin evaluar requisitos. Un depósito exigible de vuelta no se clasifica automáticamente igual que una obligación de prestar servicios; justificar la diferencia.',
    'Preparar naturaleza de compromisos, criterio de aplicación, saldos significativos y restricciones o reembolsos. Explicar qué se recibió y qué queda por entregar. No afirmar la existencia de contratos o hitos del cliente que no se hayan capturado.',
    'Conciliar aplicación a ingreso, devolución o cancelación documentada contra el pasivo. Evitar duplicar el ingreso al facturar, cobrar y entregar. El saldo no se vuelve ingreso por ser antiguo; la extinción del derecho del cliente requiere sustento.'
 ],'Contrato, recibo de anticipo, hitos de entrega y conciliación de aplicaciones o devoluciones.',
 'No confundir anticipos de clientes con activos ni igualar devengo contable y cobro fiscal.',
 ['Cobro previo a prestar un servicio.','Cumplimiento o devolución con aplicación del pasivo.']),
 'ingresos': ficha('ingresos',['D-1'],1,'Capítulo 5: Revenue; secciones 5.1–5.3',[
    'Identificar contrato, bienes o servicios comprometidos y momento de cumplimiento. Distinguir una venta de un anticipo, préstamo o aportación. En servicios continuos analizar evidencia de avance; en comercio y restaurantes, entrega y devoluciones. No derivar ingreso únicamente de la factura o el cobro.',
    'Determinar contraprestación y componentes documentados; analizar descuentos, devoluciones y variabilidad. Separar impuestos cobrados por cuenta de autoridades cuando corresponda. Si existen compromisos distintos, justificar la asignación; no reconocer el importe bruto sin examinar la actuación como principal o agente.',
    'Revisar cumplimiento, ajustes de precio, devoluciones y estimaciones al cierre, conciliando ingreso, derechos de cobro y anticipos. El deterioro de un derecho de cobro no se presenta automáticamente como devolución de venta. Evitar cambios de estimación usados para adelantar ingresos.',
    'Separar ingresos ordinarios, bonificaciones y conceptos de otra naturaleza según la operación. Conciliar saldos de contrato y cuentas por cobrar. No mezclar IVA con ventas netas ni presentar financiamiento o aportaciones del titular como ingreso de clientes.',
    'Preparar políticas de reconocimiento, clases de operación, criterios de avance y juicios significativos. Explicar incertidumbre de contraprestaciones y compromisos pendientes cuando corresponda. La nota debe permitir entender el giro sin afirmar que todos los servicios siguen el mismo momento de reconocimiento.',
    'Registrar devoluciones, cancelaciones y finalización del contrato con soporte y conciliación de sus saldos. Evitar repetir ingreso al cobro si ya se devengó. Determinar efectos contables y fiscales por separado, sin presumir tasa de IVA o elegibilidad para estímulos.'
 ],'Contrato, evidencia de entrega o avance, contraprestación, comprobantes y conciliación de anticipos y cobros.',
 'No tratar descuentos sobre ingresos como un nuevo ingreso ni aplicar tasa cero por ubicación fronteriza.',
 ['Servicio o entrega ordinaria con contraprestación identificada.','Cierre con devolución, cambio de estimación o aplicación de anticipo.']),
 'gastos': ficha('gastos',['B-3'],1,'Sección 2.4 y capítulo 3: conceptos, reconocimiento y estados financieros',[
    'Identificar consumo de bienes o servicios del periodo y su relación con la operación. Separar gasto, activo pendiente de consumo, distribución al propietario y pago de una deuda. La etiqueta del catálogo no determina por sí sola reconocimiento ni deducibilidad.',
    'Documentar importe devengado y componentes que corresponden al consumo. Separar impuestos recuperables y partidas de capital. Si hay costos de un contrato con clientes, evaluar la norma particular antes de utilizarla; no extender NIF D-2 a todos los gastos de administración o venta.',
    'Revisar corte, servicios recibidos sin factura, estimaciones y aplicaciones de anticipos. Un pago posterior no vuelve a generar el gasto ya reconocido. Conciliar acumulaciones y reversos para evitar omisiones o duplicidad y evaluar si existe un activo mal clasificado.',
    'Clasificar por naturaleza o función conforme a la política aplicable y mantener consistencia. Separar gastos financieros, costos y partidas de otro tipo cuando sea pertinente. No compensar con ingresos sin justificar el criterio ni ocultar erogaciones al agruparlas indiscriminadamente.',
    'Preparar política de reconocimiento, composición relevante, estimaciones y cambios que expliquen el resultado. La relación con la actividad debe ser verificable; una descripción genérica de “gastos varios” no documenta el hecho ni garantiza su tratamiento fiscal.',
    'Aplicar, liquidar o revertir el saldo según su origen y evidencia, distinguiendo corrección de error y nueva operación. La clasificación como no deducible no elimina el gasto contable real. En RESICO PF no atribuir deducciones de ISR a su registro.'
 ],'Recepción del servicio, comprobante, autorización, corte, auxiliar y conciliación de devengos y pagos.',
 'No aplicar D-2 a todo gasto ni usar la falta de deducibilidad para omitir una operación contable real.',
 ['Gasto devengado vinculado al giro con pago separado.','Cierre con servicio recibido pendiente de factura o aplicación de anticipo.']),
 'costos': ficha('gastos',['C-4'],1,'Capítulos 1 y 7: operaciones comerciales e inventarios',[
    'Identificar costo de bienes vendidos o servicios prestados y distinguir compra, inventario y consumo. La cuenta de compras no significa que todo lo adquirido se haya vendido. En servicios, documentar recursos consumidos y su relación con entregables; no inventar existencias por analogía con comercio.',
    'Construir costo con cantidades y componentes sustentados, separando impuestos recuperables y gastos del periodo. Justificar asignación de costos indirectos sin incorporar desperdicio anormal automáticamente. La cuenta de devolución sobre compras requiere reflejar su efecto sobre la operación original.',
    'Conciliar inventario inicial, entradas, producción, salidas y final, o la hoja de costos del servicio. Revisar ajustes y corte para evitar duplicar costo al comprar y al vender. No equiparar la fórmula contable con un método fiscal sin comprobar régimen y periodo.',
    'Separar costo de venta, activos pendientes de consumo, devoluciones y gastos de otra función. Explicar el sistema periódico o permanente cuando sea pertinente y conciliarlo con auxiliares. No presentar un costo de baja de activo fijo como mercancía vendida ordinariamente.',
    'Preparar composición, método de determinación, criterios de asignación y variaciones relevantes. Documentar cambios y bases de distribución. Si la actividad no mantiene inventarios, explicar el alcance de la referencia C-4 y señalar la norma particular por confirmar para el costo del servicio.',
    'Reconocer salida o aplicación a resultados cuando corresponda al hecho documentado; ajustar devoluciones y cancelaciones contra el origen. Separar pérdida por deterioro, merma y costo ordinario. No concluir que todo costo contable reduce el ISR de cualquier régimen.'
 ],'Hoja de costos, kárdex o tiempos del servicio, cantidades, comprobantes y conciliación de consumo y ventas.',
 'No deducir automáticamente compras ni trasladar costo de lo vendido de persona moral a todo régimen.',
 ['Venta o servicio con determinación del costo y contrapartidas.','Cierre con conciliación, devolución o diferencia de costos documentada.']),
 'impuestos': ficha('otra',['B-6'],2,'Secciones 12.3.5 y 15.1: impuestos por pagar y causado; solo conceptos, sin reglas extranjeras',[
    'Identificar tributo, periodo, autoridad y naturaleza del derecho u obligación. Separar impuesto propio, traslado, retención, saldo a favor y pago provisional. Un saldo en el auxiliar no acredita derecho de devolución ni la existencia de un crédito fiscal exigible.',
    'Conciliar base, tasa, importe y documento de la operación con las disposiciones fiscales autorizadas disponibles. El criterio educativo solo organiza el registro, no establece tasas mexicanas. Separar impuesto recuperable, costo y gasto según su naturaleza y los requisitos efectivamente revisados.',
    'Conciliar auxiliares, declaraciones, pagos, retenciones y aplicaciones al cierre. Investigar diferencias de periodo y la recuperabilidad de saldos a favor. No compensar o acreditar tributos por el solo hecho de que el software muestre ambos saldos; verificar procedencia jurídica y evidencia.',
    'Mostrar derechos y obligaciones por su naturaleza y vencimiento, evitando compensaciones no sustentadas. La NIF B-6 es referencia de presentación, no fundamento de una tasa, estímulo o acreditamiento. Distinguir impuesto causado y diferido si se trata de impuestos a la utilidad.',
    'Preparar composición, periodos, conciliaciones y contingencias relevantes. Explicar las diferencias entre libros y declaraciones. No afirmar que la entidad es elegible para una devolución, subsidio o estímulo sin hechos y fundamento aplicables; señalar la verificación fiscal concreta que falta.',
    'Registrar pago, aplicación, devolución o extinción comprobada contra el derecho u obligación correspondiente. Mantener trazabilidad con declaración y acuse. Una diferencia contable no autoriza una condonación ni un ingreso, y la baja no resuelve por sí sola el tratamiento fiscal.'
 ],'Declaración y acuse, cálculo por periodo, comprobantes, pagos y conciliación con auxiliares.',
 'No usar B-6 como norma de valuación fiscal ni inventar elegibilidad para estímulos, compensaciones o devoluciones.',
 ['Operación y segregación del impuesto documentado.','Conciliación del periodo y aplicación o pago con soporte.']),
 'impuestos_utilidad': ficha('impuestos_diferidos',['D-4'],2,'Capítulo 15: Income Taxes, secciones 15.1–15.6; sin tasas extranjeras',[
    'Distinguir impuesto causado por el resultado fiscal del periodo y efectos diferidos por diferencias temporales. Identificar activo, pasivo o gasto según la cuenta seleccionada. Una diferencia permanente no genera automáticamente impuesto diferido; el código 185 es activo y el 259 es pasivo.',
    'Comparar valor contable y base fiscal por partida y documentar la reversión esperada. Identificar la tasa aplicable con sustento, sin presumir tasa corporativa para persona física. Un ejemplo puede usar una tasa expresamente hipotética para mostrar la mecánica, sin convertirla en asesoría fiscal.',
    'Revisar diferencias temporales, cambio de tasas y recuperabilidad de activos con evidencia de resultados fiscales futuros. No reconocer activo solo para cuadrar el gasto. Para un activo, valor contable mayor a base fiscal suele originar diferencia imponible; analizar inversamente las obligaciones.',
    'Separar impuesto causado, diferido y pagos provisionales; conciliar su efecto en resultados u otros componentes según su origen. No registrar un pasivo dentro del activo 185. La compensación de activos y pasivos requiere revisar condiciones normativas, no basta una misma autoridad fiscal.',
    'Preparar conciliación del gasto, diferencias y supuestos de recuperabilidad, tasas y cambios materiales. Documentar partidas no reconocidas o sujetas a evaluación según la norma revisada. La explicación del método no demuestra que existan diferencias reales en la organización.',
    'Registrar reversión, aplicación o ajuste de recuperación a partir de las partidas que le dieron origen. No tratar el diferido como pago de ISR ni agregar IVA a su asiento. Para RESICO PF, el efecto contable no crea deducciones de ISR ni permite importar reglas de otro régimen.'
 ],'Conciliación contable-fiscal, bases por partida, calendario de reversión, tasas sustentadas y recuperabilidad.',
 'No confundir permanente con temporal, activo 185 con pasivo 259, ni diferido con impuesto pagado.',
 ['Reconocimiento causado o diferido que corresponda a la cuenta; tasa hipotética explícita para PF.','Reversión o ajuste de recuperabilidad de esa misma naturaleza.']),
 'empleados': ficha('gastos',['D-3'],2,'Capítulo 12, sección 12.3.6; capítulo 16: beneficios a empleados',[
    'Identificar servicios de empleados y obligación de compensación, diferenciando nómina, beneficios de largo plazo y PTU. Un anticipo o préstamo a empleado es un derecho por analizar, no una remuneración automática. Una provisión de nómina puede ser obligación determinada, sin adoptar mecánicamente C-9.',
    'Documentar periodo trabajado, base contractual, prestaciones y retenciones. Separar gasto bruto, obligaciones con empleado y terceros, y pago neto. Si existe beneficio de largo plazo que requiera valuación especializada, no sustituirla por un porcentaje arbitrario de nómina.',
    'Conciliar acumulaciones, pagos, retenciones y cierre del periodo. Revisar estimaciones de beneficios y cambios con soporte contractual o técnico; PTU y sus posibles efectos diferidos requieren tratamiento específico. No trasladar tasas o planes extranjeros descritos en libros educativos a México.',
    'Separar gasto, obligaciones laborales, retenciones y contribuciones por naturaleza y plazo. No clasificar todo importe relacionado con empleados como sueldo. Identificar qué parte necesita análisis fiscal o de seguridad social propio y no fundamentarla únicamente en el tratamiento contable.',
    'Preparar política, clases de beneficios, estimaciones y compromisos relevantes. Proteger datos personales en los ejemplos y utilizar trabajadores ficticios. Señalar información actuarial pendiente cuando sea necesaria sin afirmar que toda prestación requiere el mismo tipo de cálculo.',
    'Conciliar pago, liquidación o reversión con el pasivo y comprobantes. No repetir gasto al pagar lo ya devengado ni cancelar obligaciones por falta de efectivo. Separar los efectos de cambios de estimación y acuerdos de terminación según su naturaleza documentada.'
 ],'Contrato, nómina, recibos, incidencias, retenciones, conciliaciones y valuación técnica cuando proceda.',
 'No aplicar automáticamente C-9 por la palabra provisión ni confundir préstamo a empleado con beneficio laboral.',
 ['Devengo de prestación con retenciones separadas.','Cierre, pago o revisión de estimación documentada.']),
 'provisiones': ficha('otra',['C-9'],2,'Secciones 12.5–12.7: provisiones, compromisos, presentación y notas',[
    'Identificar obligación presente surgida de hechos previos y analizar incertidumbre de importe o fecha. Distinguir deuda contractual determinada, provisión y contingencia. Una intención de gastar o una reserva voluntaria de administración no acredita por sí sola obligación reconocible.',
    'Documentar estimación, escenarios y evidencia disponible sobre obligación y salida de recursos. Analizar el efecto del tiempo cuando corresponda al marco aplicable. No escoger un porcentaje arbitrario de ventas ni registrar el escenario más alto sin explicar la base de la estimación.',
    'Revisar hechos, estimaciones y resolución al cierre. Actualizar el análisis con evidencia y evitar mantener provisiones agotadas o sin causa. No usar provisiones como mecanismo para suavizar resultados; distinguir cambio de estimación de corrección de un error.',
    'Separar provisiones de acreedores determinados y clasificar según naturaleza y plazo. Una contingencia puede requerir revelación en lugar de reconocimiento; justificar la evaluación. No compensar un reembolso esperado con la obligación sin revisar criterios y evidencia de ambos.',
    'Preparar naturaleza, incertidumbre, conciliación y supuestos materiales con cuidado de no divulgar datos sensibles innecesarios. La ausencia de una cifra cierta no autoriza omitir todo análisis. Identificar información legal o técnica requerida para una conclusión específica.',
    'Aplicar la provisión al desembolso que la originó o revertirla con sustento cuando deje de proceder. No consumirla para gastos ajenos ni confundir su utilización con un gasto nuevo. La contabilización no garantiza deducibilidad fiscal ni resolución favorable de una controversia.'
 ],'Hecho que origina obligación, evaluación legal o técnica, escenarios, conciliación y autorizaciones.',
 'No equiparar todo proveedor con provisión ni toda contingencia con pasivo reconocido.',
 ['Hecho y estimación explícitamente hipotéticos con soporte descrito.','Reestimación, aplicación o reversión justificada.']),
 'arrendamientos': ficha('otra',['D-5'],2,'Secciones 17.1, 17.3.2 y 17.5: conceptos, enfoque IFRS y notas; excluye opciones ASPE',[
    'Examinar contrato, activo identificado, control del uso y posición de arrendador o arrendatario. Distinguir arrendamiento, servicio y pago anticipado. La sola palabra renta no prueba un derecho de uso ni determina las exenciones que podrían aplicar bajo el marco mexicano.',
    'Documentar plazo, pagos, opciones y bases de medición que requiera la clasificación revisada. Si procede derecho de uso y pasivo, explicar componentes y tasa sustentada. No capitalizar toda factura de renta ni inventar tasa, contrato u opción ejercitable del cliente.',
    'Conciliar pagos, intereses, consumo del derecho y modificaciones del contrato cuando correspondan. Revisar plazo y supuestos con soporte. Las exenciones u opciones extranjeras del libro no se trasladan automáticamente a NIF; confirmar tratamiento específico en el ejemplar autorizado.',
    'Separar anticipos, derecho de uso, pasivo y gasto según el análisis del contrato. Clasificar vencimientos y no netear pagos futuros con el activo por conveniencia. Para arrendador, no utilizar sin adaptación el asiento del arrendatario.',
    'Preparar naturaleza de contratos, política, plazos, juicios y compromisos relevantes. Distinguir supuestos ilustrativos de condiciones reales. Cuando falten datos contractuales, indicar exactamente qué información cambia el análisis en vez de convertir la falta de datos en una prohibición de desarrollar ejemplos.',
    'Documentar terminación, modificación o cumplimiento y conciliar activo y obligación si fueron reconocidos. No dar de baja solo el pasivo dejando intacto el derecho sin analizar la operación. Separar tratamiento contable de IVA y deducción de rentas en el régimen aplicable.'
 ],'Contrato y anexos, pagos, plazo, opciones, tasa sustentada y conciliación del derecho y obligación.',
 'No aplicar automáticamente NIIF 16 o una excepción extranjera como requisito NIF comprobado.',
 ['Contrato hipotético con rol, plazo y pagos explícitos.','Cierre, pago o modificación con conciliación completa.']),
 'capital': ficha('otra',['C-11','B-4'],2,'Capítulo 14: Share Capital',[
    'Identificar aportación, retiro, reserva, resultado acumulado o resultado del ejercicio y documentación que lo respalda. Distinguir patrimonio y obligación de reembolso. El dinero entregado por un socio no es automáticamente capital: examinar acuerdo, derechos y condiciones de devolución.',
    'Documentar importe, instrumento y forma de aportación; separar efectivo y aportaciones en especie con base de medición revisada. No confundir capital contable, capital social y cuentas fiscales. Una valuación propuesta no sustituye el análisis de los derechos y acuerdos.',
    'Conciliar movimientos, resultados, reservas y distribuciones con los acuerdos y registros. No reconocer aumentos patrimoniales por simples traspasos entre cuentas propias. Las reservas requieren naturaleza y sustento; no constituyen por sí mismas gasto, pasivo ni efectivo separado.',
    'Separar componentes patrimoniales y movimientos según su naturaleza. Una obligación de reembolso o dividendo decretado exige analizar su clasificación; no mantenerlo como capital por el solo origen societario. La NIF B-4 se identifica como referencia complementaria de los cambios en patrimonio.',
    'Preparar composición, movimientos, restricciones y derechos relevantes. Documentar conciliación con acuerdos y resultado del ejercicio. Para persona física, adaptar la explicación a su estructura sin inventar acciones, asambleas o reservas legales de una sociedad inexistente.',
    'Registrar distribución, reducción, reclasificación o cierre de resultados con soporte. Separar movimiento patrimonial, pago y posibles obligaciones fiscales. No equiparar CUCA o CUFIN con capital contable ni afirmar que toda devolución al titular está libre de ISR.'
 ],'Acuerdos, comprobantes de aportación, auxiliar de patrimonio y conciliación de resultados y distribuciones.',
 'No reconocer aportaciones como ventas ni usar CUCA/CUFIN como sustitutos del patrimonio contable.',
 ['Aportación o movimiento patrimonial documentado.','Cierre o distribución con soporte y separación fiscal.']),
 'participaciones': ficha('otra',['C-7','B-8'],1,'Capítulo 8: Intercorporate Investments; conceptos de participación e influencia',[
    'Identificar participación, derechos de voto, influencia, control y propósito. Una acción aislada y una inversión con control no siguen automáticamente la misma mecánica. Documentar relación y normas particulares por revisar; no inferir control del nombre de la empresa o del porcentaje sin analizar derechos.',
    'Documentar costo, contraprestación y derechos adquiridos, separando operaciones que requieran análisis de combinación de negocios. La referencia C-7 orienta participaciones de su alcance; B-8 es condicional al análisis de control y consolidación, no una regla para toda inversión.',
    'Conciliar resultados atribuibles, dividendos, cambios de participación y deterioro según el método validado. No reconocer el dividendo y la participación en resultados como ingreso duplicado. No usar una cotización bursátil como sustituto automático del valor contable bajo cualquier método.',
    'Separar inversión, correctora de deterioro y resultados; identificar si se preparan estados individuales o consolidados. No mezclar consolidación con medición de la inversión individual. Las eliminaciones requieren sustento y no convierten cuentas de terceros en recursos propios.',
    'Preparar naturaleza de relación, método, restricciones y cambios materiales. Identificar información financiera utilizada, fechas y supuestos. Si falta análisis de control o estados de la participada, exponer ese dato por verificar y usar un supuesto ilustrativo acotado.',
    'Conciliar venta, pérdida de influencia o cambio de control y evaluar el tratamiento aplicable. No eliminar parcialmente la inversión sin revisar efecto en resultados y componentes acumulados. Separar el tratamiento fiscal de enajenación del método contable de participación.'
 ],'Títulos, acuerdos, derechos, análisis de control y estados financieros de la participada.',
 'No aplicar el mismo método a toda acción ni duplicar ingreso por dividendos y participación.',
 ['Adquisición con derechos e influencia explícitos.','Cierre con participación o cambio sustentado de inversión.']),
 'especializada': ficha('otra',[],1,'Sección 2.4 y capítulo 3: conceptos generales; no cubre normativa sectorial específica',[
    'Identificar qué representa el saldo, control, derecho u obligación y la actividad especializada. Separar denominación del catálogo y sustancia económica. No forzar C-6, C-8 u otra norma particular solo por parecido del nombre; documentar el marco sectorial que debe confirmarse.',
    'Describir la operación y construir un importe ilustrativo con documentos y componentes identificables. La base de medición sectorial queda sujeta a identificación y revisión, sin elegir por defecto costo, valor razonable o VNR. No presentar esa incertidumbre como una política ya aprobada.',
    'Conciliar movimientos y evidencia al cierre, distinguiendo cambio físico, devengo y cambio de medición. Explicar qué hechos activarían una estimación o ajuste y qué especialista o norma requiere confirmación. La ausencia de fuente particular no autoriza inventar un párrafo normativo.',
    'Determinar preliminarmente si la partida corresponde a activo, obligación, resultado o control extracontable y justificarlo con los hechos. No convertir un registro de control en saldo financiero automáticamente. Si faltan condiciones decisivas, plantear alternativas condicionadas claramente separadas.',
    'Preparar naturaleza, supuestos, incertidumbres y políticas pendientes de definición. Identificar de manera visible la falta de comprobación sectorial y los datos necesarios. Desarrollar explicación útil sin declarar cumplimiento, ni atribuir la guía conceptual a una norma particular no identificada.',
    'Describir el hecho de realización, aplicación o extinción y la evidencia requerida antes de una baja. Conciliar el auxiliar y sus contrapartidas. Los ejemplos usan supuestos pedagógicos explícitos y señalan la decisión normativa pendiente; no habilitan una aprobación por mera aceptación.'
 ],'Documento de la operación, auxiliar, descripción de sustancia y revisión sectorial documentada.',
 'No presumir cobertura especializada de activos biológicos, fideicomisos o crédito mercantil por similitud.',
 ['Operación ilustrativa con naturaleza y límites expresos.','Cierre con conciliación y decisión técnica por confirmar.']),
 'orden': ficha('otra',[],1,'Sección 2.4 y capítulo 3: distinción de elementos financieros y registros de control',[
    'Identificar si la cuenta solo controla bases fiscales, bienes de terceros o compromisos y no un elemento reconocido en estados financieros. Distinguir el registro de orden del activo, obligación o resultado subyacente. La codificación SAT no convierte CUFIN, CUCA o una base fiscal en patrimonio contable.',
    'Documentar la base de control, unidades y periodo con un papel de trabajo; los cálculos fiscales deben apoyarse en disposiciones autorizadas para ese régimen. El libro educativo no determina actualización, factores o requisitos mexicanos. No inventar un importe de crédito fiscal o estímulo.',
    'Conciliar movimientos, aplicaciones y saldo de control con los documentos de origen. Separar correcciones fiscales y movimientos financieros; no crear ingreso o gasto para cuadrar cuentas de orden. Si el hecho subyacente sí exige reconocimiento, analizarlo en su cuenta financiera con su norma particular.',
    'Mantener registros de control diferenciados de activo, pasivo y resultados. No sumar mecánicamente la cuenta de orden al balance. En consignación, distinguir propiedad y custodia; para bases fiscales, aclarar que su saldo no es efectivo ni una obligación por ese mismo importe.',
    'Preparar propósito, método de conciliación y compromisos o contingencias relevantes. No existe una NIF particular asignada automáticamente a toda cuenta de orden; analizar el hecho subyacente. La información en notas no sustituye el registro financiero cuando sea exigible por la operación.',
    'Documentar aplicación, devolución, cancelación o extinción de la base controlada sin fabricar un resultado financiero. Si se utilizan cuentas de orden deudora y acreedora, identificarlas como tales y conciliar ambas. No añadir IVA a un simple traspaso de control sin operación gravada.'
 ],'Papel de trabajo de control, fundamento fiscal pertinente, documentos de terceros y conciliación de saldos.',
 'No presentar CUFIN, CUCA, pérdidas fiscales o bienes ajenos como recursos propios ni afirmar estímulos sin requisitos.',
 ['Registro ilustrativo de control con contracuenta de orden explícita.','Aplicación o cancelación de control sin inventar un ingreso financiero.']),
 'general': ficha('otra',[],1,'Sección 2.4 y capítulo 3: naturaleza, reconocimiento y estados financieros',[
    'Identificar el hecho económico, derechos, obligaciones y quién controla el recurso. Una cuenta propia con nombre ambiguo no determina una NIF. Separar activo, pasivo, patrimonio, resultado y control; justificar la hipótesis utilizada y solicitar los datos que cambiarían esa identificación.',
    'Construir el importe de la operación con componentes y documentos identificados, sin escoger una base de medición normativa por intuición. Distinguir contraprestación, impuestos y costos asociados. El supuesto educativo debe declarar sus límites y no presentarse como valuación verificada del cliente.',
    'Conciliar saldo inicial, movimientos y final, y explicar qué hechos exigirían revisión de una estimación. Identificar los datos faltantes para la norma particular antes de concluir deterioro, devengo o conversión. No utilizar una advertencia genérica en lugar del análisis de las alternativas.',
    'Justificar su ubicación y plazo con los hechos capturados, sin compensar saldos distintos para simplificar. Si la naturaleza permanece indeterminada, describir clasificaciones posibles condicionadas. La presentación no suple la decisión de reconocimiento y medición de la norma específica.',
    'Preparar naturaleza, política propuesta, supuestos e incertidumbres relevantes. Explicar información que permitiría una decisión profesional y mantener el pendiente de identificación normativa visible. No asignar B-6 como si fuera una norma universal de valuación ni inventar un estándar aplicable.',
    'Describir aplicación, realización o extinción según el supuesto y conservar evidencia del ajuste. Conciliar contrapartidas sin dar de baja derechos por simple antigüedad. Si se identifica una operación especializada, requerir comprobación particular antes de afirmar su tratamiento definitivo.'
 ],'Descripción de operación, contrato o comprobante, auxiliar y nota de identificación normativa pendiente.',
 'No esconder una cuenta sin clasificar bajo una norma de presentación ni afirmar cobertura por analogía.',
 ['Operación ilustrativa con naturaleza y supuesto expresamente delimitados.','Cierre con conciliación y revisión de la hipótesis de clasificación.']),
}


def categoria(cuenta):
    """El agrupador SAT prima sobre el código interno; el nombre afina subcuentas."""
    agrupador=getattr(cuenta,'codigoagrupador',None)
    sat=str(getattr(agrupador,'codigoagrupador',''))
    texto=normalizar(str(getattr(cuenta,'descripcion','') or '')+' '+str(getattr(agrupador,'nombre','') or ''))
    raiz=sat.split('.')[0]
    if raiz.isdigit():
        n=int(raiz)
        if n>=800:return 'orden'
        if n in (185,259,611):return 'impuestos_utilidad'
        if n in (187,210,211,215,255,257,605,607,610):return 'empleados'
        if n in (110,111,112,113,114,118,119,207,208,209,212,213,216):return 'impuestos'
        if n in (203,206,253,260):return 'anticipos_recibidos'
        if n in (109,120):return 'anticipos'
        if n in (105,106,107,108,184,186):return 'cobrar'
        if n in (115,116,117):return 'inventarios'
        if n in (188,189,608,609):return 'participaciones'
        if n in (158,180,217,258):return 'especializada'
        if 151<=n<=172 or n in (505,613):return 'ppe'
        if 173<=n<=183 or n==614:return 'intangibles'
        if 301<=n<=306 or n==214:return 'capital'
        if n in (101,102):return 'caja' if n==101 else 'bancos'
        if n in (103,104,190,702):return 'inversiones'
        if n in (201,202,204,205,251,252,254):return 'deuda'
        if n in (401,403) and 'arrendam' in texto:return 'arrendamientos'
        if n in (401,403) and any(x in texto for x in ('interes','dividendo','rendimiento financiero')):return 'inversiones'
        if 401<=n<=403:return 'ingresos'
        if 501<=n<=504:return 'costos'
    if ('impuesto' in texto or 'isr' in texto) and 'diferid' in texto:return 'impuestos_utilidad'
    if any(x in texto for x in ('biologic','credito mercantil','fideicomis')):return 'especializada'
    if any(x in texto for x in ('cobros anticipad','anticipo de cliente','anticipo del cliente','ingresos anticipad')):return 'anticipos_recibidos'
    if any(x in texto for x in ('pagos anticipad','anticipo a proveedor','renta pagada por anticipado')):return 'anticipos'
    if any(x in texto for x in ('por cobrar','deudor','incobrab','prestamo a empleado','cliente')):return 'cobrar'
    if 'caja' in texto:return 'caja'
    if 'banco' in texto or 'efectivo' in texto:return 'bancos'
    if any(x in texto for x in ('depreciacion','equipo','maquinaria','terreno','edificio','vehiculo','mobiliario')):return 'ppe'
    if any(x in texto for x in ('amortizacion','intangible','software','patente','preoperativ','gastos diferidos','gastos de organizacion')):return 'intangibles'
    if 'arrendam' in texto or 'leasing' in texto:return 'arrendamientos'
    if any(x in texto for x in ('nomina','sueldo','beneficio a empleado','ptu','salario','vacacion','aguinaldo')):return 'empleados'
    if 'impuesto' in texto or 'retencion' in texto:return 'impuestos'
    if 'provision' in texto or 'contingenc' in texto:return 'provisiones'
    if any(x in texto for x in ('proveedor','por pagar','acreedor','prestamo')):return 'deuda'
    if any(x in texto for x in ('inventar','almacen','mercancia')):return 'inventarios'
    if 'capital' in texto or 'patrimonio' in texto:return 'capital'
    if 'inversion' in texto or 'instrumento financiero' in texto:return 'inversiones'
    if any(x in texto for x in ('ingreso','venta','producto financiero','otros productos')):return 'ingresos'
    if 'costo' in texto:return 'costos'
    if 'gasto' in texto:return 'gastos'
    if raiz.isdigit():
        n=int(raiz)
        if n in (601,602,603,604,606,612,701,703):return 'gastos'
        if n in (702,704):return 'ingresos'
    return 'general'


def paquete(categoria_cuenta):
    from pathlib import Path
    import json
    ficha=PERFILES[categoria_cuenta]
    fuentes=json.loads((Path(__file__).parent/'data/fuentes_abiertas_2026_10_29.json').read_text())
    fuente=next(f for f in fuentes if f['volumen']==ficha['volumen'])
    return dict(version=VERSION,categoria=categoria_cuenta,ejes=ficha['ejes'],evidencia=ficha['evidencia'],
                error=ficha['error'],casos=ficha['casos'],fuente={**fuente,'localizacion':ficha['localizacion']},
                alcance='Explicación educativa propia para decisiones de aplicación; no transcribe NIF/NIIF ni acredita requisitos de su edición autorizada. No se trasladan opciones ASPE, tasas ni umbrales extranjeros. Se excluyen sección 6.6 del volumen 1 y textos de terceros con licencia diferente.')


def renderizar(paquete):
    lineas=['### Guía de aplicación: criterios y decisiones',paquete['alcance']]
    for clave,titulo in EJES.items():
        lineas.extend(['**'+titulo+'.** '+paquete['ejes'][clave]])
    if paquete.get('enfoque'):
        lineas.append('**Aplicación a la subcuenta seleccionada:** '+paquete['enfoque'])
    lineas.extend(['**Evidencia de revisión:** '+paquete['evidencia'],
                  '**Error que debe evitarse:** '+paquete['error'],
                  '**Dos escenarios que desarrollan los ejemplos:** '+ ' / '.join(paquete['casos'])])
    f=paquete['fuente']
    lineas.append('**Fuente educativa y atribución:** '+f['autores']+'. ['+f['titulo']+']('+f['url']+'), '+f['edicion']+', '+f['localizacion']+'. ['+f['licencia']+']('+f['url_licencia']+'). Adaptación propia al español, decisiones y ejemplos nuevos para el contexto mexicano; no es una reproducción del texto NIF.')
    return '\n\n'.join(lineas)
