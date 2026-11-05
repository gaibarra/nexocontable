# Estructura profesional y fuentes alternativas — 29/10/2026

## Problema y resultado

La versión estructurada anterior reducía el manual a seis bloques y prohibía
mencionar incluso las NIF identificadas. Una respuesta formalmente válida podía
ser breve, carecer de título descriptivo, políticas, casos de materialidad o
conclusión y sustituir el desarrollo por avisos. Se corrigió esa regresión.

La generación usa ahora esquema 2: introducción, perfil NIF, comparación
internacional, reconocimiento/valuación/presentación/revelación, políticas, ISR,
IVA, obligaciones, procedimiento, dos casos de materialidad, dos ejemplos con
asientos y conclusión. El servidor compone título con nombre de cuenta y claves
normativas identificadas; verifica contenido mínimo y conserva las referencias.
El objetivo es 1400–1800 palabras de desarrollo, con piso de 1000. La longitud no
certifica exactitud profesional.

Se admiten variaciones de formato sin perder contenido: referencias vacías
omitidas en secciones propias y pasos de procedimiento. Las referencias conocidas
incluidas en prosa se expanden a su identificación; las desconocidas, los párrafos
inventados, las atribuciones no verificadas y los asientos desbalanceados siguen
siendo rechazados. Se mantiene un solo intento correctivo adicional y el aviso
con selección conservada si no logra completarse.

## Fuentes alternativas comprobadas

Glenn Arnold y Suzanne Kyle, Lyryx Learning, Intermediate Financial Accounting,
volúmenes 1 y 2, versión 2021-A. La licencia CC BY 4.0 y las condiciones de
atribución se verificaron en los preliminares de los PDF originales. No se usaron
reediciones con restricciones comerciales. Datos y SHA-256 persistentes en
catalogo/data/fuentes_abiertas_2026_10_29.json.

- Volumen 1, original:
  https://openlibrary-repo.ecampusontario.ca/jspui/bitstream/123456789/891/3/ArnoldKyle-IntermFinAcct-Vol1-2021A.pdf
- Volumen 2, original:
  https://openlibrary-repo.ecampusontario.ca/jspui/bitstream/123456789/892/3/ArnoldKyle-IntermFinAcct-Vol2-2021A.pdf
- Licencia: https://creativecommons.org/licenses/by/4.0/
- Identificación bibliográfica oficial de claves NIF:
  https://www.cinif.org.mx/files/NORMAS_2019.pdf

Se elaboran explicaciones educativas propias en español y nuevos supuestos para
México. La atribución, licencia y cambios de contexto figuran en el anexo. No se
copian citas de normas de terceros contenidas en el libro. Los libros no son NIF
mexicanas ni verifican por sí solos las disposiciones actuales. La identificación
histórica de una norma no acredita que se hayan comprobado sus párrafos de 2026.
Las NIF pertinentes vuelven a nombrarse y explicarse; el contraste profesional de
su edición aplicable permanece explícito.

Se incorporaron 64 criterios educativos (ocho familias incluidas impuestos
diferidos y otras cuentas, por ocho regímenes), además de 46 criterios fiscales
para las nuevas categorías. Total de la biblioteca: 250 criterios. Las versiones
publicadas anteriores no se modificaron.

## Cuenta 185 y borrador 79

El agrupador SAT 185 corresponde al activo; el pasivo por impuesto diferido no debe
registrarse allí. El perfil identifica NIF D-4, Impuestos a la utilidad, y NIC 12
para comparación, y desarrolla diferencias temporales, recuperabilidad y
reversión. Los ejemplos de 185 incluyen un activo y su reversión/ajuste. Para
persona física las tasas de ejemplo se declaran hipotéticas, sin presumir tasa
corporativa fija ni deducciones por simple registro contable.

El borrador 79 señalado por el usuario se reformuló LOCALMENTE con una muestra
educativa validada del mismo giro, régimen y cuenta. Se remapearon únicamente
referencias coincidentes por fuente/edición/localización/área y se personalizó el
nombre en el servidor. No se envió contexto de esta organización a IA: la revisión
automática había rechazado el intento de hacerlo; la alternativa local permitió
completar la corrección sin ese envío.

El borrador conserva ID, autor y estado pendiente. Tiene título descriptivo y
1807 palabras en el contenido. Su texto, título y snapshot anteriores quedaron
íntegros en un registro inmutable de reformulación y en respaldo privado, con
comprobación de huella para evitar sobreescribir ediciones concurrentes. Una
reformulación aprobada está prohibida. La renovación controlada de snapshot
conserva su inmutabilidad por versión; no está disponible como campo editable del
administrador ni como parámetro del formulario de edición.

La revisión muestra la versión anterior. No se atribuye una aprobación profesional
al autor del documento ni se registra consumo ficticio de IA por la adaptación
local. Las fuentes del nuevo snapshot y los pendientes requieren la revisión
profesional habitual antes de aprobar.

## Validación y despliegue

- 272 pruebas de cuentas, catálogo y donativos en PostgreSQL aislado.
- 47 pruebas privadas del panel: 319 en total.
- Nuevos casos: título descriptivo, NIF D-4/NIC 12, estructura completa, atribución
  CC BY, bloqueo de párrafos inventados, archivo de versiones y protección de
  aprobados, clasificación de 185 y normalización de referencias válidas.
- Muestras reales con datos ficticios de las seis familias y de impuestos
  diferidos; tras los ajustes se obtuvo un manual de Inventarios de 1633 palabras
  y uno de 185 de 1809. Las muestras no equivalen a dictamen profesional.
- Exportación local del borrador corregido: PDF del navegador de 8 páginas y
  previsualización de Word mediante LibreOffice de 5 páginas, con título, normas,
  casos y conclusión, sin palabras fuera de página. Revisión de hoja de contacto.
- Migraciones aditivas/metadatos 0016 y 0017, cargas idempotentes,
  collectstatic y reinicio de ambos servicios. Se conservó activa la biblioteca.

Evidencias privadas en output/biblioteca/desarrollo_completo/. No se cambiaron
manuales aprobados, empresas, pagos ni consentimientos. El resto de borradores no
se reformuló automáticamente. Las nuevas generaciones usan la estructura completa.
