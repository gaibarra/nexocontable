# Mercado Pago: operación y validación

Actualizado: 25 de octubre de 2026. Correcciones y publicación autorizadas por el
propietario. Integración Checkout Pro mediante Preferences; no utiliza Orders.

## Comportamiento publicado

- El checkout mantiene CSRF y exige un identificador firmado ligado a la sesión,
  vigente una hora. Reenviar el mismo formulario reutiliza la preferencia guardada.
  PostgreSQL serializa las solicitudes simultáneas. Un resultado remoto incierto
  conserva la referencia local y reutiliza la clave de idempotencia al reintentar
  ese formulario; no se supone que la creación de una preferencia sea un cobro.
- Importes entre 10 y 100,000 MXN, finitos y con un máximo de dos decimales. El
  formulario permite centavos. Se valida HTTPS y el dominio de la URL de salida.
- Solo el webhook está exento de CSRF: exige HMAC SHA-256 y secreto configurado.
  Compara el ID firmado con el cuerpo y consulta el recurso por la API autenticada.
  No confía en el estado, importe ni identidad enviados en el cuerpo del webhook.
- Antes de registrar un pago compara referencia, ID, monto, MXN, receptor y entorno.
  En nuevas preferencias guarda el receptor; para una preferencia antigua consulta
  primero sus datos en la API. Las respuestas inconsistentes se rechazan con 409.
- Cada recurso remoto tiene un registro único en `PagoMercadoPago`. Un bloqueo de
  fila y `date_last_updated` evitan duplicados y regresiones de estado. Un intento
  rechazado no sustituye otro pago aprobado del mismo checkout. Si dos intentos
  distintos realmente se pagaron, el neto incluye ambos importes efectivos.
- Se registran aprobaciones, pendientes, rechazos, cancelaciones, revisión,
  devoluciones parciales/totales y contracargos. El panel presenta el neto
  confirmado y las devoluciones. Estos cambios **no ejecutan devoluciones ni
  capturan pagos**: reflejan los estados consultados en Mercado Pago.
- Un error temporal del proveedor o del procesamiento devuelve 503 para permitir
  reintentos. JSON/IDs inválidos: 400; firma inválida: 401; cuerpo excesivo: 413;
  métodos distintos de POST: 405. Los tipos de evento ajenos a `payment` se ignoran.
- Los retornos llevan una referencia firmada, vigente siete días, y muestran el
  estado de la base. `status=approved` no constituye confirmación. El retorno puede
  llegar antes del webhook: en ese caso muestra una verificación pendiente y un
  botón para actualizar. No promete correos que la aplicación no envía.
- No se registra el cuerpo del webhook ni respuestas privadas del SDK. Los nuevos
  resúmenes persistidos omiten tarjetas, documentos de identidad y objetos `payer`;
  solo se conserva el correo válido si falta en el registro del donante.
- Los registros externos, incluidos fallos de checkout con identificador propio,
  quedan protegidos contra edición y eliminación en el CRUD del panel. Los
  donativos manuales conservan su flujo independiente.

## Configuración

Variables de entorno, sin publicar sus valores secretos:

| Variable | Uso |
|---|---|
| `MERCADOPAGO_ACCESS_TOKEN` | Token del receptor; obligatorio |
| `MERCADOPAGO_WEBHOOK_SECRET` | Secreto de firma de la aplicación; obligatorio |
| `MERCADOPAGO_BASE_URL` | Por defecto `https://manualcontable.online`, URL canónica HTTPS |
| `MERCADOPAGO_SANDBOX` | Selecciona checkout de prueba y exige `live_mode=False`; por defecto se infiere del prefijo `TEST-` del token |
| `MERCADOPAGO_COLLECTOR_ID` | Comprobación adicional opcional de la cuenta receptora |
| `MERCADOPAGO_WEBHOOK_TOLERANCE_SECONDS` | Ventana temporal opcional para la firma; por defecto 0 |

La tolerancia temporal está desactivada por defecto para aceptar reentregas
auténticas tardías. Esto no desactiva HMAC: cada evento se autentica, se consulta en
la API y se procesa por versión para que una repetición no revierta estados.
Activar una ventana estricta requiere validar antes la política real de reentrega
del proveedor. El SDK usa timeout de seis segundos y cero reintentos internos;
los reintentos de entrega los gestiona Mercado Pago. El bloqueo PostgreSQL tiene
una espera máxima de tres segundos.

El endpoint configurado para notificaciones debe ser:
`https://manualcontable.online/donar/webhook/`.

No mezclar compradores, receptores ni credenciales entre entornos. Para una prueba
real del sandbox se necesitan las cuentas y credenciales de prueba del proveedor,
configuradas por un canal seguro. No pegarlas en chats, archivos versionados ni URLs.

## Migración y registros existentes

Migración `donaciones.0002`: agrega identificador de checkout, URL, receptor,
importes netos/reembolsados y fecha del pago, además de la tabla de intentos. No
contiene una migración de datos ni reclasifica estados previos. El neto nullable
mantiene la interpretación original de los aprobados históricos hasta que exista
una conciliación individual mediante una notificación auténtica.

Se respaldaron los campos originales de los 25 registros antes de migrar, en un
archivo local con permisos 0600. La comparación posterior, incluido el resumen
histórico del webhook, confirmó cero cambios y cero registros financieros nuevos.
No se ejecutó una conciliación masiva de los 24 pendientes históricos.

Para incidencias de notificaciones: revisar el identificador del evento en Mercado
Pago y los códigos HTTP del webhook; un retorno pendiente no demuestra un cobro.
La recuperación manual de históricos y cualquier devolución real requieren una
operación específica, ajena a este despliegue. No cambiar estados manualmente para
hacer coincidir el texto de una pantalla.

## Evidencia de validación

- Las 59 pruebas de la auditoría inicial pasan después de las correcciones.
- Suite de donaciones ampliada: 75 pruebas en PostgreSQL; todas pasan, incluidas
  dos carreras reales entre conexiones separadas. En SQLite: 73 pasan y las dos
  carreras se omiten expresamente por requerir bloqueos de PostgreSQL.
- Regresión pública en PostgreSQL: 207 pruebas, todas pasan.
- Panel privado en SQLite: 47 pruebas, todas pasan; incluye totales netos,
  preservación del total histórico y bloqueo del CRUD de checkouts fallidos.
- Navegador Chromium a 390 y 1440 píxeles: formulario con centavos y CSRF,
  preferencia simulada, retorno anterior al webhook, notificaciones HMAC simuladas,
  aprobación, devolución parcial y total, privacidad inicialmente plegada, CLABE
  conservada, contador y ausencia de desbordamiento horizontal. El transporte del
  navegador sustituye el checkout externo por una página local simulada; no es el
  checkout real del proveedor.
- Producción: migración aplicada, servicios público/privado reiniciados, página de
  donativos y acceso al panel disponibles. Webhook con firma deliberadamente
  inválida: 401; GET al webhook: 405; formulario sin CSRF: 403; retorno manipulado:
  sin éxito falso. Panel de donativos y tablero renderizados con la base real.
- `manage.py check`, `makemigrations --check --dry-run` y `git diff --check` sin
  errores. Bases PostgreSQL temporales eliminadas.

Logs locales: `/tmp/mercadopago-correcciones-postgres.log`,
`/tmp/mercadopago-publica-postgres-final.log`, `/tmp/mercadopago-panel-final.log`,
`/tmp/mercadopago-donaciones-sqlite-final.log`. Capturas de navegador:
`/tmp/mp-browser-donar-mobile.png`, `/tmp/mp-browser-donar-desktop.png`,
`/tmp/mp-browser-reembolsado.png`.

**Límite de la validación:** no se ejecutaron compras con cuentas reales del sandbox
ni se observó una entrega auténtica nueva del proveedor después del despliegue.
Los errores de proveedor y cambios financieros se probaron con respuestas
simuladas, nunca con cargos o devoluciones reales. La auditoría previa incluyó una
consulta de solo lectura de un pago productivo existente, no una compra nueva.

## Referencias oficiales

- [Webhooks de Checkout Pro](https://www.mercadopago.com.mx/developers/es/docs/checkout-pro-preferences/additional-content/notifications/webhooks).
- [Preferencias de Checkout Pro](https://www.mercadopago.com.mx/developers/es/reference/online-payments/checkout-pro-preferences/create-preference/post).
- [Estados de pagos](https://www.mercadopago.com.mx/developers/es/docs/checkout-api-payments/response-handling/query-results?scope=prod).
