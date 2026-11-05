# Desarrollo uniforme de nuevos manuales — 05/11/2026

Se publica el esquema de generación 3, identificado en la instantánea por
`desarrollo-2026-11-05-v1`. Conserva las diez claves principales y exige seis
apartados en `contable.desarrollo`: reconocimiento, valuación inicial, valuación
posterior y cierre, presentación, revelaciones, y baja/aplicación/liquidación.
Cada apartado debe tener al menos 40 palabras y no ser copia exacta de otro.
El servidor valida texto y referencias antes de componer los apartados editables.
No basta aumentar la extensión total con una sola sección.

La guía educativa de la sección NIF sigue la misma estructura para 23 perfiles:
caja, bancos, inversiones, cobrar, anticipos entregados, inventarios, PPE,
intangibles, deuda, anticipos recibidos, ingresos, gastos, costos, impuestos,
impuestos a la utilidad, empleados, provisiones, arrendamientos, capital,
participaciones, especializada, cuentas de orden y general. Se conserva la
personalización del bloque aplicado, políticas, procedimiento y dos ejemplos.
Las cuentas ambiguas mantienen identificación normativa pendiente, no una NIF
forzada. Las cuentas de orden no se presentan automáticamente como saldos
financieros. No se declara cobertura normativa completa por compartir el formato.

Se corrigen distinciones de naturaleza: anticipos recibidos frente a pagos
anticipados; proveedores frente a provisiones; préstamos a empleados frente a
nómina; gastos de depreciación/amortización frente a correctoras; impuesto causado,
diferido y PTU. Los matices de subcuenta dan instrucciones específicas para
terrenos, correctoras, devoluciones e ISR causado, entre otros. Los códigos internos
no sustituyen el agrupador SAT. Las cuentas propias sin agrupador confirmado se
pueden describir sin inventar un código SAT.

Los dos ejemplos deben identificar el código exacto o la descripción completa
de la cuenta seleccionada. No se aceptan copias idénticas. Si la narración afirma
registrar IVA acreditable o trasladado, debe aparecer cuantificado en los
movimientos; se reconocen los supuestos explícitos de tasa cero/exención y la
ausencia expresamente justificada del registro. Se conservan validaciones de
referencias, cifras finitas, centavos, debe/haber, separación fiscal y hallazgos
conocidos. La recuperación mantiene como máximo dos intentos y el presupuesto
existente; no se eliminan controles para aceptar una respuesta incompleta.

Biblioteca: migración aditiva 0018 añade `perfil_tecnico` a los criterios. La carga
`cargar_desarrollo_uniforme` crea 184 criterios educativos parciales (23 × ocho
regímenes), es idempotente y no cambia publicaciones previas. La selección filtra
perfil, familia, régimen, fecha, publicación, retiro y permisos. Una guía particular
solo se incorpora cuando tiene un criterio de perfil autorizado seleccionado.
El panel permite buscar, consultar y versionar ese alcance; conserva autorización
exclusiva del propietario para escribir y publicar.

Fuentes: Arnold/Kyle/Lyryx, Intermediate Financial Accounting vols. 1 y 2, 2021-A,
con capítulos/secciones identificados, CC BY 4.0 y atribución. Se excluye 6.6 del
volumen 1 y texto de terceros con licencia diferente. No se reproducen NIF/NIIF
ni se trasladan tasas, opciones ASPE o umbrales extranjeros a México. Los nombres
NIF se identifican bibliográficamente y sus requisitos no consultados conservan
revisión profesional pendiente en ejemplar autorizado.

Validación:
- 291 pruebas de catálogo, cuentas y donativos; 47 del panel: 338 aprobadas.
- Matriz de contrato: 23 perfiles × ocho regímenes × comercio/servicios, más ocho
  contextos de restaurantes para Inventarios: 376 combinaciones. Verifica formato,
  selección y validación; no es una auditoría profesional de 376 respuestas IA.
- Revisión de clasificación y seis ejes para 1,127 cuentas SAT sin alias `.0`.
  Ocho entradas de otros activos/pasivos conservan perfil general y pendiente de
  identificación particular; no se presume su sustancia.
- Migración 0018 probada en PostgreSQL aislado con estado previo preparado, avance,
  reversión y preservación de datos. No requiere reejecutar semillas históricas.
- Cuatro muestras reales de IA, exclusivamente ficticias: Inventarios PM general
  comercial, anticipo de cliente PF RESICO servicios, gasto por depreciación PF
  empresarial servicios y cuentas de orden PM general comercial. La revisión de
  primeras muestras originó los controles de IVA omitido y correctoras ajenas.
  Las últimas cuatro muestras quedaron completas; depreciación necesitó un segundo
  intento automático. No se enviaron datos reales de organizaciones.
- Vistas a 390/1440 px sin desbordamiento; Word previsualizado mediante LibreOffice
  y PDF navegador con seis ejes, tablas y enlaces. Ocho PDF inspeccionados sin texto
  fuera de página: 7 páginas por muestra salvo Word de cuentas de orden, 8 páginas.
  No se afirma prueba en Microsoft Word nativo ni exactitud semántica universal.

Despliegue: migración 0018, carga de criterios y reinicio de ambos Gunicorn. La
biblioteca continúa activa. Comprobación posterior de huellas y estados: los 19
manuales existentes permanecen intactos. Las versiones antiguas siguen exportables;
no se regeneraron silenciosamente documentos. Evidencias locales privadas en
`output/biblioteca/uniforme_2026_11_05/`.

Para revertir el código, primero desactivar el flujo de biblioteca y retirar los
criterios de perfil de futuras selecciones; conservar versiones, instantáneas e
historial. No usar un selector antiguo con los perfiles nuevos indiscriminados.
La reversión ordinaria conserva la columna aditiva y los registros.
