# Generación de un manual por cuenta

Publicado el 25 de octubre de 2026.

- Selección única con controles de radio en SAT y catálogo propio. El servidor
  rechaza más de un valor antes de reservar cuota o invocar la IA, y la función
  de generación vuelve a comprobar el alcance.
- Al seleccionar se abre una vista previa con código, descripción, código SAT,
  organización, giro y régimen. Seleccionar o cancelar no llama al proveedor;
  se envía el formulario al confirmar «Generar manual».
- La búsqueda y el cambio entre las dos vistas del catálogo propio conservan la
  cuenta elegida. La generación se confirma exclusivamente en el modal; se retiró
  la barra fija inferior. Pulsar otra vez la cuenta seleccionada reabre su vista previa.
- El modal mantiene márgenes, desplaza sus datos dentro de la ventana y deja los
  botones visibles. Sus contenidos se asignan como texto, sin interpretar HTML.
- El prompt centra el documento en una cuenta y solicita unas 1400–1800 palabras,
  distribuidas entre todas las secciones, casos y ejemplos. El presupuesto de
  salida configurado se conserva; una respuesta truncada sigue siendo rechazada.
  El objetivo de extensión es una instrucción al modelo, no una garantía de tamaño.
- Los manuales previos de varias cuentas se conservan y continúan disponibles.

Validación: 95 pruebas del catálogo pasan en SQLite y PostgreSQL temporal.
Chromium verifica SAT y catálogo propio, selección única, cancelación/Escape,
conservación al buscar/cambiar vista, envío solo tras confirmar, y modal con
márgenes y botones visibles a 320, 390 y 1440 píxeles. Proveedor simulado en todas
las generaciones de prueba, sin consumo real de IA. Sin nuevas migraciones.

Se recopilaron los archivos estáticos y se reinició el servicio público. La
verificación de producción comprueba renderizado con datos existentes, selección
única y modal, archivos JS/CSS publicados y acceso autenticado al generador.

## Cuentas con manual existente

La selección muestra un warning cuando la cuenta ya dispone de un documento:
si está aprobado, bloquea la generación y permite consultar el vigente; si es
borrador, permite abrirlo para revisión. No se crean duplicados. Se da prioridad
al aprobado aunque haya borradores más recientes. El servidor revalida antes de
reservar cuota y al guardar, incluyendo cuentas cubiertas por manuales conjuntos
antiguos y referencias SAT directas. Las cuentas propias distintas que comparten
agrupador SAT mantienen identidades separadas. El índice de estados solo incluye
la organización activa y se envía mediante JSON escapado.

Validación ampliada: 100 pruebas pasan en SQLite y PostgreSQL. Chromium comprueba
avisos, bloqueo, apertura de documentos y ausencia de llamadas de generación para
SAT/catálogo propio en móvil y escritorio. Sin migraciones ni cambios de estado a
los documentos existentes.

## Modal de avance

El progreso se muestra en un diálogo centrado al confirmar la generación. Está
fuera del formulario y conserva márgenes en escritorio y móvil aunque la página
esté desplazada. Muestra la cuenta, la barra con avance estimado y los pasos de
preparación. No se cierra con Escape mientras la solicitud está pendiente y se
restablece al volver desde la caché del navegador. La respuesta del servidor
reemplaza la página y el modal. El indicador es orientativo y nunca declara
finalizada una generación antes de recibir el resultado.

Validación: 23 pruebas de gestión de manuales pasan. Chromium comprueba ambos
catálogos a 320×568, 390×844 y 1440×900: centrado, márgenes, barra visible con la
página desplazada, actualización del indicador, bloqueo para manual aprobado y
sustitución por el resultado. El envío nativo también se comprobó con respuesta
simulada y una única petición; no se consumió IA real.

## Mensaje de personalización por organización

Mensaje central: «Manuales contables personalizados según el giro, régimen fiscal
y cuenta de cada organización». Se revisaron portada y metadatos, acceso y
registro, organizaciones y ayudas de captura, dashboard, catálogo, selección,
confirmación, avance, edición y consulta, presentación visual, invitaciones y
panel de IA. Las acciones conservan nombres cortos para facilitar su uso.

La generación ya recibía los datos de la organización activa. Ahora el prompt
explicita su uso en políticas, casos y ejemplos, exige identificar supuestos y
evita atribuir al cliente procesos o hechos que no proporcionó. Una prueba
comprueba que la misma cuenta recibe contextos distintos para un restaurante y
una asociación civil, sin mezclar los nombres ni regímenes de las organizaciones.
El texto mantiene la necesidad de revisión profesional y de ajustar el borrador
a la operación real del cliente. La personalización de contenido se explica por
separado de los logos y la presentación visual.

Validación: 141 pruebas públicas y del catálogo, 47 del panel; todas pasan.
Navegador a 320 y 1440 píxeles: portada, registro, acceso, organizaciones,
dashboard, catálogo y modales sin desbordamiento. Invitaciones HTML/texto
renderizadas en ambas variantes, sin enviar mensajes. No se regeneraron manuales
ni se ejecutaron llamadas reales a proveedores de IA. Sin nuevas migraciones.
