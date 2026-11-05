# Biblioteca de fundamentos — entrega del 29 de octubre de 2026

## Estado publicado

Activada en producción con 140 criterios propios, 48 combinaciones explícitas
(seis familias por los ocho regímenes disponibles), tres versiones de fuentes
fiscales y dos registros bibliográficos contables pendientes. La cobertura inicial
es **parcial**, no una validación fiscal o contable integral.

Fuentes fiscales comprobadas: textos oficiales consolidados de LISR (reforma
impresa 01/04/2024), LIVA (12/11/2021) y CFF (09/04/2026). Los metadatos y SHA-256
están en catalogo/data/fundamentos_2026_10_29/. La base delimita su periodo revisado
desde la fecha de carga, sin confundirla con la entrada en vigor de las leyes.
Se revisaron las localizaciones cargadas y las diferencias de los ocho regímenes;
reglamentos, RMF, anexos, transitorios y operaciones especiales requieren
comprobación particular. El régimen Otro exige identificar el régimen real.

Permisos: explicaciones propias y referencias de textos legislativos oficiales,
con base documentada en LFDA artículo 14, fracción VIII, edición oficial con reforma
impresa 14/05/2026. No se incorporaron anotaciones editoriales protegidas ni textos
NIF/NIIF completos. Los registros CINIF/IFRS son bibliográficos y sus permisos de
procesamiento permanecen desconocidos. No se adquirieron licencias.

## Uso en el panel

/panel/fuentes/ permite consultar fuentes, versiones, permisos, criterios y avisos.
Todos los roles privados pueden consultar después de MFA; solo el propietario
puede crear, editar borradores, publicar, retirar y activar o desactivar el flujo.
Las versiones y los criterios publicados son inmutables: crear una nueva revisión
y retirar expresamente la anterior cuando corresponda. No borrar el historial.

La cobertura Completa significa revisión integral del área para esa familia,
régimen y periodo; no simplemente haber localizado un artículo. Mantener Parcial
mientras existan disposiciones o supuestos esenciales sin comprobar.

La publicación requiere fecha de revisión y evidencia de vigencia. Permitir una
consulta no equivale a permitir almacenamiento, envío a IA o reproducción: el
selector requiere los cuatro permisos comprobados. El contenido de fuentes con
permisos desconocidos no ingresa a los prompts; su identificación bibliográfica
puede conservarse. Los criterios son explicaciones propias, no copias de libros.

## Generación y aprobación

La generación selecciona por familia, régimen y fecha actual de referencia; no
acepta una fecha arbitraria enviada por el navegador. La cuenta de otra familia
conserva cobertura pendiente. La IA devuelve JSON con áreas separadas, dos casos
ilustrativos, referencias F y movimientos. El servidor comprueba estructura,
identificadores, correspondencia de área, cantidades finitas no negativas,
centavos y equilibrio de asientos. Construye los títulos, tablas y referencias.
Las citas libres, enlaces o identificadores fuera del conjunto autorizado y los
errores técnicos conocidos provocan rechazo; se conserva el consumo informado.

Esto NO comprueba exhaustivamente que cada explicación fiscal sea semánticamente
correcta o que un supuesto refleje hechos reales del cliente. La revisión
profesional sigue siendo esencial incluso cuando las validaciones automáticas
pasan. La biblioteca no convierte una NIIF en sustituto automático de una NIF.

Cada manual nuevo conserva fecha y una instantánea inmutable. Un propietario o
contador autorizado documenta cada pendiente con disposición, edición,
localización, fecha de consulta y conclusión de aplicabilidad. Se vincula a una
huella del contenido y de la instantánea; no basta marcar una casilla. No se
solicitan archivos de libros protegidos. La verificación individual no publica
criterios globales. La aprobación registra autor, fecha y huella.

Editar contenido devuelve el manual a borrador e invalida las verificaciones para
la nueva huella. Cambiar solo el título conserva la revisión. El administrador
Django tampoco permite cambiar la aprobación, identidad o instantánea ni crear
manuales eludiendo el flujo de generación. Los manuales anteriores conservan su
contenido y aprobación y muestran que no tenían evaluación de fuentes al generarse;
una aprobación nueva con el flujo activo exige revisión integral documentada.

El anexo común aparece en pantalla, Word y PDF del navegador. Distingue consulta
central pendiente de verificación profesional particular. No se declara
cumplimiento NIF por ausencia de hallazgos automáticos.

## Monitoreo diario

Tarea instalada en el crontab de gaibarra: 09:20 UTC, equivalente a 03:20 de Ciudad
de México. Se conservaron las tareas anteriores. Ejecuta
`deploy/comprobar_fuentes.sh`, con bloqueo para evitar solapamientos y DEBUG=False.
La salida se guarda en output/biblioteca/operacion/monitor.log.

Solo consulta fuentes fiscales registradas con consulta/almacenamiento permitidos,
en hosts oficiales HTTPS autorizados; controla redirecciones, tiempos y tamaño.
Compara SHA-256 de archivos. Una diferencia puede ser editorial o técnica: no
supone una reforma. Los cambios y fallos generan alertas deduplicadas en el panel,
sin publicar interpretaciones ni alterar manuales. No se envían correos.

Al documentar un cambio confirmado, el propietario señala vigencia y deja la lista
de manuales potencialmente afectados. Estos muestran el nuevo pendiente sin
sobrescribir su documento ni retirar automáticamente una aprobación histórica.
Una fuente no registrada no está cubierta por el monitoreo.

## Pruebas y evidencias

- 257 pruebas de cuentas, catálogo y donativos, en PostgreSQL aislado.
- 47 pruebas privadas del panel: 304 en total.
- Matriz automatizada de 48 combinaciones en giros comercial/servicios y
  restaurantes para Inventarios; pruebas de fechas, permisos, fuentes retiradas,
  referencias inventadas, asientos, aprobación, roles, MFA y aislamiento.
- Trece llamadas reales a IA con datos ficticios y 58,018 tokens reportados.
  Las primeras seis fueron rechazadas por incumplir estructura o referencias.
  Tras reforzar instrucciones, cinco de seis pasaron; un ensayo dirigido final de
  Clientes pasó. Se obtuvieron muestras válidas de las seis familias. Los siete
  rechazos no se guardaron como manuales. No es una tasa garantizada de éxito.
- Seis DOCX, seis PDF del navegador y seis PDF de previsualización de Word mediante
  LibreOffice: 46 páginas, sin palabras fuera del límite de página. Revisión visual
  de muestras y hojas de contacto; no se probó Microsoft Word nativo.
- Comprobación de ancho 390/1440 sin desbordamientos y formulario de revisión
  accesible; corrección para mantener el anexo de fundamentos unido al imprimir.

Evidencias privadas en output/biblioteca/; ninguna sesión de prueba corresponde a
producción. No se crearon empresas ficticias ni manuales en producción durante
estas pruebas. No se ejecutaron cobros ni se cambiaron pagos históricos.

## Despliegue y reversión

Migraciones aditivas 0014 y 0015 del catálogo, carga idempotente de criterios,
collectstatic y reinicio de los servicios público y privado. Antes de migrar se
creó respaldo privado completo y huellas de todos los manuales; las huellas
coincidieron después del despliegue. La primera consulta del monitor no detectó
cambios ni errores. Se comprobó acceso anónimo protegido, render privado y estado
activo de ambos servicios.

Para revertir la generación estructurada, desactivar Nuevo flujo desde el panel.
Las tablas e instantáneas permanecen. No revertir migraciones ni restaurar el
respaldo completo sobre actividad nueva. Los documentos con instantánea mantienen
los controles de revisión. Los archivos de respaldo son privados, con modo 600,
y están excluidos de Git.

## Actualización posterior: recuperación automática

La generación estructurada activa ahora el modo JSON del proveedor y realiza un
único intento correctivo cuando falla la validación. Se conservan referencias,
cuadres y consumo de ambos intentos. El aviso final conserva la cuenta seleccionada
y una referencia de incidente, sin mostrar al usuario el mensaje técnico genérico.
Consultar CORRECCION_GENERACION_2026_10_29.md para límites y pruebas actualizadas.
