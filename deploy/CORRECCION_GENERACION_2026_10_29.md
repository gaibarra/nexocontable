# Recuperación de generación — 29/10/2026

Se corrigió el flujo que presentaba el mensaje genérico de validación de estructura,
referencias o asientos como un error que debía resolver el usuario.

## Cambios

- La petición al proveedor activa `response_format: json_object` en generación
  estructurada y usa temperatura 0.2. La instrucción incluye un esquema válido con
  los identificadores realmente disponibles; no propone F1/F2 inexistentes.
- La bibliografía contable no consultada queda en el anexo del servidor y no se
  mezcla con instrucciones del modelo. Se mantiene la instantánea documental.
- Se acepta un objeto JSON completo envuelto en un único bloque de código. No se
  eliminan referencias desconocidas ni se ajustan cifras para forzar un resultado.
- La validación identifica causas internas: formato, estructura, referencia fuera
  del conjunto autorizado, área incorrecta, cita libre, importes o asiento, etc.
- Se corrigen falsos positivos por la palabra artículos en contexto comercial y
  por negaciones explícitas de cumplimiento normativo.
- Ante una respuesta rechazada se realiza un único intento adicional con la causa
  y las instrucciones originales. No se reenvía el texto rechazado al proveedor.
  Se conservan los controles de referencias, contabilidad e impuestos.
- Presupuesto total de intentos de validación: hasta 90 segundos según configuración,
  con tiempos por proveedor acotados y un máximo de dos generaciones. Se conserva
  el consumo reportado por todos los intentos en un solo registro de uso; los
  errores operativos de cuota o saldo mantienen su explicación específica.
- Si los dos intentos fallan, se conserva la selección durante 30 minutos para el
  mismo usuario y organización. El aviso aparece junto al selector, con referencia
  GEN, y el botón abre la confirmación de la misma cuenta. Se evita el modal técnico
  de la captura. El incidente queda en actividad; las correcciones exitosas también.
- La ventana de avance explica que el documento se verificará y podrá ajustarse.

## Verificación

265 pruebas de cuentas, catálogo y donativos en PostgreSQL aislado; las 47 pruebas
privadas anteriores del panel permanecen aplicables (312 en conjunto).
Se añadieron pruebas de modo JSON, recuperación sin eludir controles, suma de
consumo, límite de dos intentos, selección y aviso, limpieza de la incidencia,
expiración/aislamiento y ausencia de referencias ficticias en el esquema.

Ocho casos reales de IA, todos con datos ficticios: seis familias iniciales más
Terrenos y Otros pasivos a corto plazo. Los ocho completaron la validación; dos
necesitaron corrección automática. Esto no garantiza éxito en toda respuesta ni
sustituye la revisión profesional del contenido.

Navegador real a 390 y 1440 píxeles: rechazo simulado de ambos intentos, ausencia del
modal técnico, cuenta conservada, botón que abre su confirmación y ausencia de
desbordamiento. Evidencias privadas: output/biblioteca/recuperacion/.

No se cambiaron manuales existentes, aprobaciones, pagos ni el esquema de datos.
Se publicaron los archivos estáticos y se reiniciaron ambos servicios. Comprobación
final de HTTPS, estado de servicios y coincidencia de JavaScript servido.

Documentación oficial del modo JSON del proveedor consultada:
https://api-docs.deepseek.com/guides/json_mode/
