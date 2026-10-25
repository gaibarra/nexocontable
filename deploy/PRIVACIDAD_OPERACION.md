# Aviso de privacidad público

Ruta: `https://manualcontable.online/aviso-de-privacidad/`.

Responsable: C.P. Gonzalo Arturo Ibarra Mendoza. Domicilio y correo ARCO
proporcionados expresamente por el titular: Calle 14 núm. 361, colonia
Pedregales de Tanlum, Mérida, Yucatán, México, C.P. 97210;
`proyectog40@gmail.com`. No se realizó ningún envío de correo de prueba.

## Referencias y alcance

Se consultó el texto oficial de la Ley Federal de Protección de Datos Personales
en Posesión de los Particulares, publicada el 20 de marzo de 2025 y con última
reforma del 14 de noviembre de 2025, disponible en:
https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf

Se consideraron identidad y domicilio, categorías de datos, finalidades,
limitación y revocación, derechos ARCO, transferencias y cambios al aviso. La ley
vigente define días como días hábiles: 20 para comunicar la determinación y 15
para hacerla efectiva si procede, con las ampliaciones justificadas previstas.
La autoridad referida es la Secretaría Anticorrupción y Buen Gobierno.

El inventario se basó en los modelos y flujos reales: perfiles, organizaciones,
documentos, CRM, registros de acceso, IA, donativos y recursos de terceros.
Se identifican DeepSeek, OpenAI, Gmail/Google, Mercado Pago y los CDN y fuentes
usados por el navegador. No se garantiza residencia mexicana ni un régimen de
conservación idéntico entre proveedores. No se presenta la política general de
DeepSeek como si sustituyera las obligaciones del desarrollador de la aplicación.

El aviso distingue datos de cuenta, documentos y datos financieros de donativos;
no solicita datos sensibles ni incluye una autorización publicitaria general.
El pago se captura en el entorno del proveedor. No se incorporó un banner de
aceptación general de cookies: la aplicación usa cookies propias de sesión y
seguridad y no incorpora rastreo publicitario propio en esta versión.

## Implementación

- Aviso integral público y accesible también para cuentas sin organización.
- Resumen antes de recopilar consentimiento en registro y donativos.
- Enlaces en todas las pantallas públicas, la aplicación autenticada y el flujo
  de generación de IA; aviso específico sobre lo enviado al proveedor de IA.
- Casilla de registro sin premarcar, versión oculta validada y rechazo de
  formularios sin versión o con versión anterior.
- Constancias nuevas en `cuentas.ConstanciaPrivacidad`: usuario, fecha,
  versión, canal y SHA-256 del contenido integral. No se agregan IP o documentos
  de identidad a la constancia y no se atribuye consentimiento retroactivo.
- Las constancias se guardan en la transacción del registro; si falla el alta,
  se revierte también la constancia. La eliminación de la cuenta desvincula su
  referencia de usuario conforme al modelo, sin alterar otros historiales.
- El campo histórico `PerfilCPC.acepta_terminos` se conserva por compatibilidad.
  La casilla actual corresponde al aviso y a las finalidades necesarias; no
  acredita la aceptación de unos términos de uso separados que no se publicaron.

La versión inicial es `2026-10-25`. Una vez publicada, conservar su plantilla
`cuentas/templates/legal/aviso_2026_10_25.html`; para modificaciones materiales,
crear una nueva versión de plantilla y actualizar `VERSION_AVISO`. La huella
incluye los datos públicos y proveedores configurados al aceptar. No cambiar
esos elementos sin revisar la versión y el deber de informar a los usuarios.

## Obligaciones operativas del responsable

El texto publicado y el registro técnico no acreditan por sí solos el
cumplimiento de todas las obligaciones. Corresponde al responsable:

1. Supervisar el buzón designado y tramitar las solicitudes, acreditar identidad
   por medios adecuados y documentar recepción, respuesta y ejecución en plazo.
2. Mantener un procedimiento de bloqueo, supresión, conservación y respaldos
   acorde con cada finalidad y obligación legal. No se implementó un borrado
   automático de cuentas ni se fijaron plazos ficticios de conservación.
3. Revisar y formalizar las condiciones con proveedores, las remisiones y
   transferencias, incluidos sus usos propios y países de tratamiento, y obtener
   las autorizaciones específicas cuando resulten necesarias.
4. Mantener medidas de seguridad y atender las vulneraciones que deban
   notificarse. La atención ARCO por correo es manual; el aviso no crea un
   departamento o una certificación externa inexistentes.
5. Informar y recabar decisiones separadas antes de nuevas finalidades
   publicitarias, transferencias que requieran autorización o tratamientos
   sensibles. Los despachos deben contar con facultades para los datos de
   terceros que carguen; el aviso de plataforma no sustituye el de cada despacho.

## Validación y despliegue

Pruebas: 134 de cuentas, catálogo y donativos, incluidas nueve de privacidad;
45 del panel. Navegador en escritorio y móvil de 390 píxeles, enlaces públicos,
casilla sin premarcar y alta de ejemplo en base aislada. No se invocaron pagos,
IA ni envío de correos durante la prueba visual.

```bash
DEBUG=False DJANGO_SETTINGS_MODULE=panel.public_test_settings venv/bin/python manage.py test cuentas catalogo donaciones --noinput
DEBUG=False DJANGO_SETTINGS_MODULE=panel.test_settings venv/bin/python manage.py test panel --noinput
DEBUG=False venv/bin/python manage.py migrate --noinput
sudo systemctl restart manual_contable manual_contable_panel
```

La migración `cuentas.0004_constanciaprivacidad` solo crea una tabla nueva.
Reiniciar completamente el servicio principal precargado para que descubra la
ruta, el modelo y el contexto; recargar sus workers no basta.
