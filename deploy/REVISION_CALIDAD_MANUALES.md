# Revisión de calidad contable, fiscal, presentación y acceso

Revisión del responsable: hallazgos en los borradores 77 y 78, ambos pendientes.
Estado de este informe: correcciones publicadas y verificadas en producción. Condiciones comerciales pendientes de confirmación del responsable.

## Resultado

Se corrigieron los dos borradores solicitados y se conservaron sus originales,
títulos, organizaciones, autores y estado pendiente. La generación cuenta ahora
con una base técnica acotada y controles de regresión que rechazan determinadas
afirmaciones incorrectas antes de guardar, registrando el consumo del intento.
La aprobación también comprueba esos hallazgos. **No es una verificación fiscal
exhaustiva ni acredita que las demás afirmaciones sean correctas.**

Las pruebas reales, realizadas durante la corrección y registradas con la huella del prompt de cada llamada, confirman que el prompt no elimina las alucinaciones: se
hicieron seis generaciones iniciales y dos repeticiones focalizadas con datos
ficticios, en Inventarios, Bancos y Clientes, distintos giros y regímenes. Sumaron
49,968 tokens reportados por el proveedor. Al reproducir las salidas con los
controles finales, cuatro quedan rechazadas y cuatro no presentan los errores
específicos cubiertos. Ninguna se considera validada profesionalmente por ello.
Los consumos y documentos de esa matriz no se insertaron en la base productiva.

## Atención de los hallazgos

| Punto | Cambio y evidencia | Límite |
|---|---|---|
| IVA fronterizo | La base distingue tasa cero, exención y estímulo de tasa efectiva 8%, sujeto a requisitos y vigencia. El caso original 77 se detecta y su texto se corrigió. | No presume elegibilidad de una organización. |
| LISR | Métodos en artículo 41; costo de lo vendido de PM en 39; pérdida de valor de mercancías en 27 XX y requisitos; no 27 XI/XII ni 28 XIII. Se detecta además la falsa asociación de 27 XX con créditos incobrables y la inclusión del costeo directo entre las opciones de 41. | Un artículo pertinente no demuestra por sí solo que proceda una deducción. |
| RESICO PF | El borrador 78 separa registro contable, ISR sin deducciones conforme a 113-E e IVA sujeto a análisis independiente. Se elimina la promesa de una deducción futura por destrucción o donación. | Verificar reglas administrativas y hechos del contribuyente. |
| Normas | Referencias con edición/versiones, localización y fuentes. NIC 2: se distingue VNR de valor razonable; NIIF 13 no se sugiere por defecto para inventarios ordinarios. | NIF C-4, edición 2026: párrafos pendientes de verificación en ejemplar licenciado. No se simuló acceso a ese texto. |
| Presentación | Viñetas reconocidas tras párrafos; código preservado; asientos multicuenta identificados como tales; mayores individuales mantienen su rótulo. Word conserva juntos asientos cortos y repite encabezados. Referencias largas ya no desbordan en móvil. | Revisión visual con LibreOffice y Chromium, no con Microsoft Word ni todos los navegadores. |
| Catálogo/tablero | «Cuentas propias» distingue el contador de la referencia SAT disponible sin importación. Nuevas selecciones SAT usan claves oficiales del archivo de referencia; variantes históricas como 101.0 se conservan en documentos e identifican con su agrupador equivalente para evitar duplicados. | Los códigos propios no se normalizan ni fusionan. |
| Uso, privacidad y acceso | Página pública `/uso-y-seguridad/`; documentación de roles y datos enviados. Solo lectura no puede mutar documentos por POST. Vistas y Word usan caché privada/no-store. Se bloquean imágenes remotas del cuerpo; logos privados conservan su ruta autenticada. Se identifica el apoyo de IA en los documentos. | Autorización comercial formal y contratos/proveedores requieren revisión del responsable. |

## Pruebas y archivos

- 230 pruebas de cuentas, catálogo y donaciones en PostgreSQL aislado: pasan.
- 47 pruebas del panel privado: pasan.
- Controles focalizados de privacidad/cache y roles: pasan también en PostgreSQL.
- Bases de prueba distintas de producción; sin cobros ni operaciones de pasarelas.
- Matriz de ocho casos exportada desde una base SQLite ficticia: ocho Word y
  dieciséis PDF (impresión Chromium y renderizado del Word con LibreOffice),
  86 páginas; revisión de estructura sin palabras fuera de página y revisión
  visual de páginas representativas, tablas y listas. Las salidas erróneas se
  conservaron solo como evidencia de QA, no para entrega a clientes.
- Además se exportaron los borradores 77 y 78 corregidos desde sus registros
  reales, conservando sus títulos e identidad. Los archivos se encuentran en
  `output/revision_calidad/manual_77_corregido.docx`, `manual_77_corregido.pdf`,
  `manual_78_corregido.docx` y `manual_78_corregido.pdf`.
- Pruebas visuales a 390 y 1440 píxeles: página pública de uso/seguridad, explicación
  del tablero sin cuentas propias, selección SAT y consulta de borradores.
- Los respaldos originales están en `output/revision_calidad/originales/`, con
  permisos restringidos. `aplicacion_correcciones.json` conserva hashes antes y
  después y confirma estado pendiente y títulos conservados. No se aprobaron.
- Matriz y fuentes: `matriz_final.json`, `revision_exportacion.json` y
  `revision_pdf_estructura.json` en el mismo directorio de revisión.

## Fuentes y comprobaciones

- LISR: PDF oficial consultado, última reforma impresa 01/04/2024; artículos 27 XX,
  39, 41, 103 II, 105 I y 113-E según el régimen. Se contrastaron los pasajes
  concretos; no se presenta el año 2026 como una edición completa verificada.
  https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf
- LIVA: PDF oficial, última reforma impresa 12/11/2021, artículos 1, 2-A y 5;
  reglas particulares deben verificarse según el contribuyente.
  https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf
- SAT, estímulo fronterizo: requisitos, avisos y facturación, no tasa cero por
  ubicación. https://www.sat.gob.mx/minisitio/EstimulosFiscalesFronteraNorteSur/region_fronteriza_norte_iva/index.html
- IAS 2/NIC 2: texto público emitido 2022, párrafos 6–9, 25 y 28–33; contrastar
  edición aplicable y modificaciones posteriores antes de aplicar.
  https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2022/issued/part-a/ias-2-inventories.pdf?bypass=on
- CINIF: edición oficial NIF 2026; acceso completo licenciado no disponible en esta
  revisión. https://cinif.org.mx/normatividad_NIF2026.php

## Condiciones comerciales y operación pendientes

La propuesta está en `deploy/BORRADOR_CONDICIONES_USO_COMERCIAL.md`. Permitiría
incorporar salidas revisadas a servicios contables remunerados, en la medida de
los derechos disponibles, con revisión profesional, divulgación del apoyo de IA y
respeto a derechos de terceros. **No está publicada como contrato y no se supone
aceptada por usuarios existentes.** La constancia del aviso de privacidad no
acredita aceptación de unos términos nuevos. El propietario debe confirmar la
política comercial y su mecanismo de aceptación antes de publicar condiciones.

Se contrastaron los términos específicos de la API de DeepSeek y el Services
Agreement de OpenAI, no una licencia genérica de cualquier chatbot o modelo:

- https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html
- https://openai.com/policies/services-agreement/

La página técnica describe los controles implementados, no una certificación de
seguridad. No se auditó el cifrado en reposo de base/respaldos, su recuperación,
los contratos de tratamiento, plazos efectivos de conservación de cada proveedor
ni una garantía de exclusión de entrenamiento. El frontend mantiene dependencias
CDN descritas en el aviso; revisar autoalojamiento y controles de cadena de
suministro antes de una evaluación integral de seguridad. Esas comprobaciones y
la revisión profesional de las fuentes siguen siendo necesarias antes de una
recomendación comercial amplia.

## Despliegue y reversibilidad

No hay migraciones. Se publican Python, plantillas y CSS, se recopilan estáticos y
se reinicia completamente el proceso público precargado. Los dos contenidos se
actualizaron bajo transacción, comprobando estado pendiente y coincidencia exacta
con el respaldo antes de escribir; se registró la corrección en actividad.

Para restaurar contenido, revisar primero el hash de la versión actual y utilizar
solo el respaldo correspondiente, sin sobrescribir una edición posterior del
usuario. La restauración tampoco debe aprobar automáticamente los documentos.

Comprobación de producción: página de uso/seguridad y portada disponibles por HTTPS, descargas anónimas redirigidas al inicio de sesión, contenido y estado pendiente de 77/78 verificados y respuestas documentales privadas/no-store. No hubo migraciones. Las pruebas de formato finales y sanitización focalizada también pasan.
