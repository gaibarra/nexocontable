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
