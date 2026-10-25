# Analisis de la Aplicacion Manual Contable AI

Fecha de analisis: 2 de junio de 2026

## Resumen general

Manual Contable AI es una plataforma web Django orientada a contadores en Mexico. Su objetivo principal es permitir que usuarios profesionales registren organizaciones, carguen catalogos de cuentas, validen esas cuentas contra el Codigo Agrupador SAT y generen manuales contables con inteligencia artificial contextualizados por giro y regimen fiscal.

La aplicacion tambien incluye gestion de equipos por organizacion, invitaciones de acceso por correo y un modulo de donativos mediante Mercado Pago.

No se encontro un archivo `README.md` en la raiz del proyecto; este analisis se basa en el codigo fuente, dependencias, configuracion y el documento `PLAN_EVOLUCION.md`.

## Utilidad de la aplicacion

La aplicacion sirve para:

1. Registrar contadores o usuarios profesionales con perfil CPC.
2. Crear una o varias organizaciones, despachos, empresas o clientes.
3. Trabajar por organizacion activa mediante un esquema multi-tenant.
4. Subir catalogos de cuentas por CSV o Excel.
5. Validar cada cuenta contra un catalogo global del SAT.
6. Generar manuales contables con OpenAI para cuentas seleccionadas.
7. Editar, consultar, aprobar y eliminar manuales generados.
8. Invitar colegas a una organizacion mediante enlaces temporales.
9. Recibir donativos via Mercado Pago.

El caso de uso central es: un contador crea una organizacion, carga su catalogo contable, selecciona cuentas especificas y obtiene un manual con secciones fiscales, NIF, ejemplos de asientos y recomendaciones documentales de materialidad para Mexico.

## Arquitectura general

La aplicacion esta construida como un monolito Django 5 dividido en apps funcionales:

- `cuentas`: autenticacion, perfiles CPC, organizaciones, membresias, seleccion de tenant e invitaciones.
- `catalogo`: codigos SAT, catalogos de cuentas por tenant, importacion CSV/Excel y generacion de manuales con IA.
- `donaciones`: donativos, checkout de Mercado Pago y webhook de confirmacion.

El enrutador principal se encuentra en `manual_contable_ai/urls.py` y conecta:

- `/admin/` con el administrador de Django.
- `/` con la app `cuentas`.
- `/catalogo/` con la app `catalogo`.
- `/donar/` con la app `donaciones`.

La configuracion principal esta en `manual_contable_ai/settings.py`. El stack detectado incluye:

- Django 5.1.4.
- PostgreSQL mediante `psycopg2-binary`.
- WhiteNoise para archivos estaticos.
- OpenAI SDK para generacion de contenido.
- Mercado Pago SDK para donativos.
- OpenPyXL para importacion Excel.
- Markdown y Bleach para renderizado o saneamiento de contenido.
- Gunicorn y Nginx para despliegue en produccion.

## Modelo multi-tenant

La arquitectura multi-tenant utiliza una sola base de datos compartida con aislamiento por `tenant_id`. Cada organizacion se modela como un `Tenant`, y los datos operativos se relacionan con ese tenant.

Modelos principales en `cuentas/models.py`:

- `PerfilCPC`: extiende al usuario de Django con datos profesionales, como nombre completo, cedula, especialidad, ciudad, estado, telefono y experiencia.
- `Tenant`: representa una organizacion, despacho, empresa o cliente.
- `MembresiaTenant`: relaciona usuarios con tenants y asigna roles.
- `InvitacionAcceso`: token temporal para establecer contrasena mediante invitacion.

Roles disponibles en membresias:

- `propietario`.
- `contador`.
- `auxiliar`.
- `solo_lectura`.

El tenant activo se guarda en la sesion como `tenant_id` y se inyecta en cada request como `request.tenant` mediante `cuentas/middleware.py`. Si un usuario autenticado intenta entrar a una ruta que requiere tenant y no tiene uno activo, el middleware lo redirige a la lista de organizaciones.

## Dominio contable

Los modelos contables estan en `catalogo/models.py`:

- `CodigoAgrupador`: catalogo global del SAT, compartido por todos los tenants.
- `CatalogoCuentas`: catalogo de cuentas propio de cada tenant.
- `ManualContable`: manual generado por IA para un tenant especifico.

Una decision importante es que `CatalogoCuentas` define unicidad por `tenant` y `cuenta`. Esto permite que diferentes organizaciones tengan la misma clave contable, pero evita duplicados dentro de una misma organizacion.

`CatalogoCuentas` y `ManualContable` todavia permiten `tenant = null` a nivel de campo, probablemente por compatibilidad con migraciones previas. Sin embargo, ambos modelos ejecutan validacion en `clean()` para exigir tenant al guardar.

## Importacion de catalogos

La logica de importacion esta en `catalogo/importador.py`.

Soporta:

- Archivos CSV.
- Archivos Excel `.xlsx` y `.xls`.
- Descarga de plantilla CSV.

Columnas requeridas:

- `cuenta`.
- `descripcion`.
- `codigoagrupador`.

Columnas opcionales de niveles:

- `nivel1`.
- `nivel2`.
- `nivel3`.
- `nivel4`.

Durante la importacion, cada fila se valida contra `CodigoAgrupador`. Si el codigo agrupador no existe en el catalogo SAT global, la fila se reporta como error. Si la cuenta ya existe para el tenant, se actualiza; si no existe, se crea.

## Generacion de manuales con IA

La generacion de manuales se encuentra en `catalogo/views.py`, principalmente en la funcion `generar_contenido_manual`.

El proceso es:

1. El usuario selecciona una o varias cuentas del tenant activo.
2. La aplicacion arma un listado con cuenta, descripcion y codigo SAT.
3. Se construye un prompt dinamico con el nombre de la organizacion, giro y regimen fiscal.
4. Se llama a OpenAI usando `client.chat.completions.create`.
5. El resultado se guarda como `ManualContable`.
6. El usuario puede consultar, editar, aprobar o eliminar el manual.

El prompt solicita secciones como:

- Introduccion.
- Analisis de NIF aplicables.
- Aspectos fiscales.
- Ejemplos practicos con asientos contables.
- Materialidad de operaciones y razon de negocios.
- Conclusion.

El enfoque es util porque adapta el contenido a la organizacion y no genera un texto generico aislado.

## Gestion de usuarios y equipos

La app `cuentas` implementa:

- Registro de usuario con perfil CPC.
- Login por email o username mediante backend personalizado.
- Dashboard por tenant.
- Edicion de perfil.
- Creacion y edicion de organizaciones.
- Seleccion de organizacion activa.
- Gestion de equipo.
- Registro/invitacion de colegas.
- Establecimiento de contrasena mediante token temporal.

Las invitaciones tienen expiracion y uso unico. Cuando se registra un colega, si el usuario no existe se crea con contrasena inutilizable y se envia un enlace para establecerla.

## Donativos con Mercado Pago

El modulo `donaciones` permite recibir donativos en MXN.

Incluye:

- Modelo `Donativo` para registrar monto, donante, estado, referencia de Mercado Pago y datos del webhook.
- Vista `donar` para crear preferencias de pago.
- Paginas de exito, error y pendiente.
- Webhook para confirmar pagos.
- Validacion HMAC SHA256 de firma de Mercado Pago cuando existe `MERCADOPAGO_WEBHOOK_SECRET`.
- Manejo idempotente basico para evitar reprocesar pagos ya aprobados.

Estados de donativo:

- `pendiente`.
- `aprobado`.
- `rechazado`.
- `reembolsado`.

## Frontend

El frontend es server-rendered con templates Django.

Caracteristicas detectadas:

- Tailwind CSS cargado por CDN.
- SweetAlert2 por CDN.
- Fuentes Google `Outfit` e `Inter`.
- Layout autenticado con sidebar.
- Templates separados por app.
- Estilos `prose` para contenido Markdown de manuales.
- Estilos de impresion para manuales.

Templates base:

- `templates/base.html`.
- `templates/base_app.html`.
- `templates/base_public.html`.

La experiencia esta orientada a una herramienta administrativa/productiva, no a una SPA.

## Despliegue y operacion

El proyecto incluye configuracion de produccion en `deploy/`:

- `gunicorn.conf.py`: Gunicorn con socket Unix, workers tipo `gthread`, timeout extendido por llamadas a OpenAI y `preload_app`.
- `nginx_manual_contable.conf`: proxy reverso Nginx, SSL con Certbot, servicio de estaticos y media, headers de seguridad y bloqueo de archivos sensibles.
- Configuraciones adicionales para systemd/supervisor y script de deploy.

La app esta pensada para ejecutarse en el dominio `manualcontable.online`.

## Seguridad y configuracion

Puntos positivos detectados:

- Variables sensibles leidas desde entorno con `decouple`.
- `SECRET_KEY`, credenciales de base de datos, OpenAI y Mercado Pago fuera del codigo.
- `DEBUG` configurable.
- Redireccion SSL y cookies seguras en produccion.
- HSTS configurado en produccion.
- Middleware de CSRF activo.
- Login requerido en vistas internas.
- Webhook de Mercado Pago con validacion de firma.
- Tokens de invitacion con expiracion y uso unico.

Puntos a revisar:

- No se encontro documentacion `.env.example` o README con variables requeridas.
- Algunas acciones dependen de validaciones de rol dentro de vistas individuales; a futuro podria convenir centralizar permisos.
- La generacion con OpenAI es sincronica y puede bloquear requests largas.
- El catalogo global SAT requiere carga inicial, pero no se encontraron fixtures o comandos evidentes para poblarlo.

## Tests detectados

Existen pruebas en:

- `cuentas/tests.py`: invitaciones seguras, establecimiento de contrasena, expiracion de tokens y render de edicion de tenant.
- `catalogo/tests.py`: eliminacion de cuentas solo por POST.
- `donaciones/tests.py`: validacion de firma de webhook y aprobacion de donativos con firma valida.

La cobertura es util para flujos criticos recientes, aunque todavia parece parcial frente al total de la aplicacion.

## Estado de madurez

La aplicacion parece estar en una etapa funcional avanzada de MVP o beta. No es solamente una maqueta: ya tiene modelos, formularios, vistas, middleware multi-tenant, importador, integracion OpenAI, integracion Mercado Pago, admin, templates y pruebas.

Su arquitectura es coherente para un SaaS pequeno o mediano:

- Monolito Django modular.
- Base compartida PostgreSQL.
- Aislamiento por foreign key `tenant_id`.
- Templates Django para UI.
- Servicios externos para IA y pagos.
- Despliegue tradicional con Gunicorn y Nginx.

## Recomendaciones tecnicas

1. Crear un `README.md` con instalacion, variables de entorno, migraciones, carga inicial del catalogo SAT y comandos de ejecucion.
2. Agregar un `.env.example` sin secretos reales.
3. Crear un comando de management o fixture documentado para poblar `CodigoAgrupador`.
4. Centralizar permisos por rol para operaciones de tenant, catalogo y manuales.
5. Mover generacion de manuales con OpenAI a tareas en segundo plano si el volumen crece.
6. Agregar mas pruebas para importacion CSV/Excel, generacion de manuales, aislamiento multi-tenant y permisos por rol.
7. Revisar si `tenant=null` en modelos contables aun es necesario despues de migrar datos historicos.
8. Considerar auditoria de acciones importantes: quien crea, edita, aprueba o elimina manuales y cuentas.

## Conclusion

Manual Contable AI es una plataforma SaaS contable para contadores mexicanos. Su nucleo funcional combina gestion multi-tenant de organizaciones, catalogos contables validados contra SAT y generacion de manuales contables con IA. La arquitectura es simple y razonable: un monolito Django modular con PostgreSQL, renderizado server-side, OpenAI para generacion documental y Mercado Pago para donativos.

La aplicacion ya tiene una base util y extensible. Sus siguientes pasos naturales serian documentacion operativa, fortalecimiento de permisos, carga formal del catalogo SAT, mayor cobertura de pruebas y procesamiento asincrono para tareas de IA.
