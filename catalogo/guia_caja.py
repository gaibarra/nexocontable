"""Desarrollo educativo propio: conceptos, decisiones y ejemplos, no texto NIF."""

VERSION = 'caja-2026-11-05'
LOCALIZACION = 'Sección 6.2 y 6.2.1: Cash and Cash Equivalents / Internal Control of Cash; páginas impresas 172–176'
URL_LIBRO = 'https://openlibrary-repo.ecampusontario.ca/jspui/bitstream/123456789/891/3/ArnoldKyle-IntermFinAcct-Vol1-2021A.pdf'
URL_CINIF = 'https://cinif.org.mx/normatividad_NIF2026.php'

DESARROLLO = '''### Aplicación práctica a Caja: reconocimiento y alcance

**La NIF C-1 es la referencia mexicana principal para analizar el efectivo y sus equivalentes.** El desarrollo que sigue es una explicación educativa propia, apoyada en conceptos de contabilidad financiera de acceso autorizado; no es una transcripción ni una comprobación del articulado de la NIF. Su finalidad es convertir la referencia en decisiones de registro y cierre que el contador pueda revisar para esta organización.

**Reconocer lo que la organización controla.** Caja representa billetes, monedas y fondos físicos bajo su control, respaldados por movimientos y por un conteo. El cobro aumenta Caja mediante un cargo; el pago o depósito bancario la disminuye mediante un abono. La contrapartida depende del origen: ingreso, cuenta por cobrar, anticipo de cliente, préstamo o aportación. Recibir dinero no equivale necesariamente a generar ingreso. El dinero personal del titular y los fondos de terceros requieren identificar propiedad, obligación de restitución y tratamiento antes de incorporarlos como recursos propios.

### Valuación y partidas que deben separarse

En una caja denominada en pesos, la guía de registro es su **importe nominal**, comprobado por denominación y cantidad; no se agrega un rendimiento estimado a los billetes. Un saldo negativo de caja física requiere investigar errores, omisiones o clasificación; no representa dinero físicamente disponible. Los vales, pagarés de empleados, anticipos para gastos pendientes de comprobar y cheques posfechados no se cuentan como billetes: debe analizarse el derecho o gasto correspondiente y su reclasificación, conservando soporte.

Una inversión no se convierte en equivalente de efectivo por llamarse “disponible” o por venderse pronto. Deben examinarse finalidad de tesorería, conversión a un importe conocido, liquidez y riesgo de cambios de valor. **No aplicar automáticamente un umbral extranjero de tres meses como requisito mexicano comprobado.** La determinación y la medición del instrumento requieren contrastar el marco aplicable y sus condiciones; la cuenta Caja no sustituye las cuentas de bancos o inversiones.

Si efectivamente se mantienen divisas, separar el auxiliar por moneda, conservar el importe original y documentar moneda funcional, tipo de cambio de la operación y de cierre. La diferencia por conversión requiere análisis y registro; no es una entrada o salida física adicional. La NIF B-15 es una referencia complementaria para ese supuesto. No atribuir a esta organización tenencia de dólares, restricciones o sucursales que no fueron informadas.

### Restricciones, presentación y revelaciones

Identificar si hay dinero bloqueado, embargado, entregado en garantía o con una restricción contractual. **Estar físicamente en caja no garantiza libre disponibilidad.** Examinar el documento que impone la restricción, importe, propósito y duración; evaluar su separación y clasificación de corto o largo plazo con la NIF C-1 y la NIF B-6. Una reserva interna para gastos no se equipara automáticamente a una prohibición legal de uso. No compensar Caja con deudas de proveedores ni con préstamos del titular por mera conveniencia.

Para la nota de estados financieros, preparar composición por caja y moneda, bases de valuación, restricciones relevantes y cambios que expliquen variaciones significativas. Evaluar las revelaciones exigibles y su importancia relativa en el ejemplar autorizado. **Un arqueo firmado es evidencia de control, no reemplaza la nota financiera.** Si no existen restricciones o divisas, documentar la comprobación que sostiene esa conclusión en vez de inventar saldos para completar el formato.

La NIF B-2 se consulta al integrar el estado de flujos: distinguir cobros y pagos por su actividad y conciliar el saldo final con la situación financiera. Un traslado de Caja a Bancos dentro del mismo conjunto de efectivo cambia su ubicación; no constituye por sí mismo ingreso o gasto ni un flujo externo adicional. No utilizar la NIC 7 como autorización automática para sustituir requisitos mexicanos.

### Arqueo, diferencias y cierre: controles propuestos

1. Fijar la fecha y hora de corte; identificar custodio, saldo auxiliar y últimos comprobantes de entrada y salida.
2. Contar por denominación, separar documentos de dinero y conciliar saldo inicial más cobros menos pagos con el efectivo físico.
3. Investigar diferencias contra comprobantes, movimientos duplicados, depósitos y errores de registro. No cargar automáticamente un faltante al empleado ni reconocer un sobrante como venta.
4. Registrar el ajuste que corresponda a la causa acreditada, con autorización y evidencia. Una cuenta transitoria de investigación requiere responsable, seguimiento y resolución; no puede ocultar pérdidas indefinidamente.
5. Revisar clasificación, valuación, restricciones y notas al cierre. La frecuencia de arqueos, los límites de caja y la separación de funciones son controles internos propuestos, que deben adaptarse a la operación.

### Dos decisiones ilustrativas para revisar

**Caso de clasificación:** un auxiliar indica $8,000 y el arqueo encuentra $7,500 en billetes más un vale de empleado por $500. El vale no transforma $500 en efectivo físico. Investigar su origen: si existe un derecho de cobro sustentado, una reclasificación ilustrativa cargaría $500 a la cuenta por cobrar y abonaría $500 a Caja. Sin evidencia del derecho, no crear una cuenta por cobrar ficticia para cuadrar el arqueo; determinar y autorizar el tratamiento de la diferencia.

**Caso de presentación:** se cuentan $20,000, de los cuales $5,000 tienen una restricción contractual comprobada. La disponibilidad libre sería $15,000; el total controlado no aumenta por presentar separadamente la parte restringida. Evaluar clasificación y nota según la duración y naturaleza de la restricción. Ambos casos son hipotéticos, no describen saldos reales y no producen por sí mismos IVA ni una deducción de ISR.

### Evidencia para la revisión profesional

Conservar auxiliar, arqueo, comprobantes de corte, conciliación de diferencias y, cuando existan, contratos de restricción y hoja de conversión. Al revisar la NIF en ejemplar autorizado, registrar edición, ubicación exacta, fecha y conclusión sobre reconocimiento, valuación, presentación y revelaciones. **Referencia pendiente de revisión profesional en ejemplar autorizado.** Esta comprobación valida requisitos normativos concretos; no impide desarrollar explicaciones, procedimientos y ejemplos propios útiles.
'''


def paquete():
    return {
        'version': VERSION,
        'texto': DESARROLLO,
        'fuente': {'autores': 'Glenn Arnold y Suzanne Kyle; Lyryx Learning',
                   'titulo': 'Intermediate Financial Accounting, Volume 1',
                   'edicion': '2021-A', 'localizacion': LOCALIZACION,
                   'url': URL_LIBRO, 'licencia': 'CC BY 4.0',
                   'url_licencia': 'https://creativecommons.org/licenses/by/4.0/',
                   'exclusiones': 'No se utiliza la sección 6.6 / Appendix A, cuya licencia es CC BY-NC-SA 3.0; tampoco citas de normas ni material de terceros con licencia distinta.'},
        'adaptacion': 'Explicaciones redactadas en español, decisiones y cifras nuevas para contexto mexicano. No se incorporan las opciones ASPE ni se atribuyen párrafos a NIF/NIIF no consultadas.',
    }
