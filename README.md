# Manual Contable AI

Manual Contable AI es una plataforma web Django para contadores en Mexico. Permite registrar usuarios profesionales, crear organizaciones o clientes, cargar catalogos de cuentas, validar cuentas contra el Codigo Agrupador SAT y generar manuales contables con inteligencia artificial.

La aplicacion esta pensada como una plataforma comunitaria tipo SaaS multi-tenant: varios contadores pueden usar la misma instalacion, cada uno trabajando con sus propias organizaciones y catalogos.

## Estado del proyecto

El proyecto ya cuenta con una base funcional de MVP/beta:

- Registro, login y perfil profesional CPC.
- Organizaciones multi-tenant.
- Membresias por rol.
- Invitaciones seguras por token temporal.
- Catalogos de cuentas por organizacion.
- Importacion de catalogos desde CSV o Excel.
- Validacion contra Codigo Agrupador SAT.
- Generacion de manuales contables con OpenAI.
- Edicion, aprobacion y eliminacion de manuales.
- Donativos con Mercado Pago.
- Configuracion de produccion con Gunicorn, Nginx, systemd, Supervisor y Certbot.

## Tabla de contenido

- [Utilidad](#utilidad)
- [Arquitectura](#arquitectura)
- [Stack tecnico](#stack-tecnico)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Modelo multi-tenant](#modelo-multi-tenant)
- [Requisitos](#requisitos)
- [Instalacion local](#instalacion-local)
- [Variables de entorno](#variables-de-entorno)
- [Base de datos](#base-de-datos)
- [Carga del Codigo Agrupador SAT](#carga-del-codigo-agrupador-sat)
- [Comandos utiles](#comandos-utiles)
- [Flujos principales](#flujos-principales)
- [Importacion de catalogos](#importacion-de-catalogos)
- [Generacion de manuales con IA](#generacion-de-manuales-con-ia)
- [Donativos con Mercado Pago](#donativos-con-mercado-pago)
- [Tests](#tests)
- [Despliegue en produccion](#despliegue-en-produccion)
- [Seguridad](#seguridad)
- [Documentacion adicional](#documentacion-adicional)
- [Pendientes recomendados](#pendientes-recomendados)

## Utilidad

La aplicacion ayuda a contadores, despachos y organizaciones a producir documentacion contable operativa a partir de su catalogo de cuentas.

Caso de uso principal:

1. Un contador se registra en la plataforma.
2. Crea una organizacion, despacho, empresa o cliente.
3. Carga el catalogo de cuentas de esa organizacion.
4. La plataforma valida las cuentas contra el Codigo Agrupador SAT.
5. El contador selecciona cuentas especificas.
6. OpenAI genera un manual contable contextualizado por giro y regimen fiscal.
7. El manual puede consultarse, editarse, aprobarse o eliminarse.

Los manuales generados incluyen secciones como introduccion, NIF relacionadas, aspectos fiscales, ejemplos practicos, materialidad documental, razon de negocios y conclusiones.

## Arquitectura

La aplicacion esta construida como un monolito Django modular. La separacion por apps mantiene aisladas las responsabilidades principales:

- `cuentas`: usuarios, autenticacion, perfiles CPC, tenants, membresias e invitaciones.
- `catalogo`: Codigo Agrupador SAT, catalogos de cuentas, importacion y manuales contables.
- `donaciones`: donativos, preferencias de pago y webhooks de Mercado Pago.
- `manual_contable_ai`: configuracion general del proyecto Django.
- `templates`: templates base compartidos.
- `static`: assets estaticos de la aplicacion.
- `deploy`: archivos de despliegue para produccion.

Arquitectura de produccion prevista:

```text
Cliente -> HTTPS/Nginx -> Unix socket -> Gunicorn -> Django -> PostgreSQL
                                      -> OpenAI API
                                      -> Mercado Pago API
```

## Stack tecnico

Dependencias principales detectadas en `requirements.txt`:

- Python 3.
- Django 5.1.4.
- PostgreSQL con `psycopg2-binary`.
- Gunicorn.
- WhiteNoise.
- OpenAI SDK.
- Mercado Pago SDK.
- OpenPyXL.
- Markdown.
- Bleach.
- Requests / HTTPX.
- python-decouple / python-dotenv / django-environ.

Frontend:

- Templates Django server-rendered.
- Tailwind CSS via CDN.
- SweetAlert2 via CDN.
- Google Fonts (`Inter` y `Outfit`).

## Estructura del proyecto

```text
manual_contable_ai/
├── manage.py
├── requirements.txt
├── PLAN_EVOLUCION.md
├── ANALISIS_APLICACION.md
├── README.md
├── manual_contable_ai/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── cuentas/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── middleware.py
│   ├── backends.py
│   └── templates/
├── catalogo/
│   ├── models.py
│   ├── views.py
│   ├── importador.py
│   ├── urls.py
│   ├── templatetags/
│   └── templates/
├── donaciones/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
├── templates/
│   ├── base.html
│   ├── base_app.html
│   ├── base_public.html
│   └── emails/
├── static/
├── staticfiles/
├── media/
└── deploy/
    ├── deploy.sh
    ├── gunicorn.conf.py
    ├── manual_contable.service
    ├── manual_contable_supervisor.conf
    └── nginx_manual_contable.conf
```

## Modelo multi-tenant

El proyecto usa un enfoque de base de datos compartida con aislamiento por `tenant_id`.

Modelos principales:

- `PerfilCPC`: perfil profesional del usuario.
- `Tenant`: organizacion, empresa, despacho o cliente.
- `MembresiaTenant`: relacion usuario-tenant con rol.
- `InvitacionAcceso`: token temporal para establecer contrasena.
- `CodigoAgrupador`: catalogo SAT global compartido.
- `CatalogoCuentas`: cuentas propias de cada tenant.
- `ManualContable`: manual generado para un tenant.
- `Donativo`: registro de donativos via Mercado Pago.

El tenant activo se guarda en la sesion como `tenant_id`. El middleware `cuentas.middleware.TenantMiddleware` verifica que el usuario tenga acceso al tenant e inyecta `request.tenant` y `request.user_rol`.

Rutas exentas de tenant activo:

- `/admin/`
- `/registro/`
- `/login/`
- `/logout/`
- `/perfil/`
- `/organizaciones/`
- `/donar/`
- `/api/`
- `/invitacion/`
- `/`

## Requisitos

Para desarrollo local:

- Python 3.10+ recomendado.
- PostgreSQL.
- `pip` y `venv`.
- Credenciales de OpenAI si se va a probar la generacion de manuales.
- Credenciales de Mercado Pago si se va a probar el flujo de donativos.

Para produccion:

- Ubuntu 22.04+ o Debian 12+.
- PostgreSQL instalado.
- Nginx.
- Certbot.
- Dominio apuntando al servidor.
- Usuario del sistema con permisos sobre el proyecto.

## Instalacion local

Desde la raiz del proyecto:

```bash
cd /home/gaibarra/manual_contable_ai
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Crear el archivo `.env` con las variables necesarias. Ver la seccion [Variables de entorno](#variables-de-entorno).

Aplicar migraciones:

```bash
python manage.py migrate
```

Crear superusuario:

```bash
python manage.py createsuperuser
```

Colectar estaticos si se desea validar configuracion de produccion local:

```bash
python manage.py collectstatic --noinput
```

Ejecutar servidor de desarrollo:

```bash
python manage.py runserver
```

Abrir:

```text
http://127.0.0.1:8000/
```

## Variables de entorno

El proyecto lee configuracion sensible desde variables de entorno usando `python-decouple`.

Ejemplo de `.env` para desarrollo:

```env
DJANGO_SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=mconta
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=4000

MERCADOPAGO_ACCESS_TOKEN=
MERCADOPAGO_WEBHOOK_SECRET=

DEFAULT_FROM_EMAIL=Manual Contable AI <noreply@manualcontable.online>

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

Notas:

- `DJANGO_SECRET_KEY` es obligatorio.
- `DB_PASSWORD` es obligatorio en la configuracion actual.
- Configurar la clave del proveedor elegido: `OPENAI_API_KEY` o `DEEPSEEK_API_KEY`.
- En `DEBUG=True`, los correos se envian a consola usando el backend de Django.
- En `DEBUG=False`, se usa SMTP real.
- En produccion, `DEBUG` debe ser `False` y `ALLOWED_HOSTS` debe incluir el dominio real.

## Base de datos

La configuracion por defecto espera PostgreSQL:

```env
DB_NAME=mconta
DB_USER=postgres
DB_HOST=localhost
DB_PORT=5432
```

Ejemplo de creacion manual de base de datos:

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE mconta;
CREATE USER mconta_user WITH PASSWORD 'change-me';
GRANT ALL PRIVILEGES ON DATABASE mconta TO mconta_user;
\q
```

Actualizar `.env` con el usuario creado:

```env
DB_NAME=mconta
DB_USER=mconta_user
DB_PASSWORD=change-me
DB_HOST=localhost
DB_PORT=5432
```

Aplicar migraciones:

```bash
python manage.py migrate
```

## Carga del Codigo Agrupador SAT

El catálogo oficial SAT se carga automáticamente al entrar a las pantallas de
catálogo o manuales. Se incluye la referencia del Anexo 24 de 2026 (1,066 códigos),
obtenida de https://sidof.segob.gob.mx/notas/docFuente/5778160 y guardada en
`catalogo/data/sat_2026.json`. No requiere captura manual ni conexión externa por
cada usuario. La carga agrega los códigos faltantes sin duplicar registros ni
modificar relaciones existentes. La referencia está versionada: futuras publicaciones
requieren actualizar ese archivo; no se promete sincronización diaria con el SAT.

Sin catálogo propio, la pantalla de generación permite seleccionar directamente
cuentas SAT. El manual conserva su selección SAT sin crear cuentas propias.

Aplicar las migraciones nuevas antes de iniciar la versión actualizada:

```bash
python manage.py migrate
```

## Comandos utiles

Desarrollo:

```bash
source venv/bin/activate
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py shell
python manage.py collectstatic --noinput
```

Tests:

```bash
python manage.py test
python manage.py test cuentas
python manage.py test catalogo
python manage.py test donaciones
```

Produccion con systemd:

```bash
sudo systemctl status manual_contable
sudo systemctl restart manual_contable
sudo journalctl -u manual_contable -f
sudo systemctl reload nginx
sudo tail -f /var/log/nginx/manual_contable_error.log
```

## Flujos principales

### Registro y onboarding

1. Usuario entra a `/registro/`.
2. Crea cuenta con email, contrasena y datos profesionales.
3. La aplicacion inicia sesion automaticamente.
4. El usuario crea su primera organizacion.
5. La organizacion queda seleccionada como tenant activo.

### Login

1. Usuario entra a `/login/`.
2. Puede autenticarse con email o username.
3. Si tiene organizaciones activas, se selecciona la primera automaticamente.
4. Se redirige al dashboard.

### Organizaciones

Desde `/organizaciones/`, el usuario puede ver sus tenants activos, cambiar el tenant seleccionado, crear nuevas organizaciones o editar aquellas donde tiene permisos suficientes.

### Equipo

Propietarios y contadores pueden registrar colegas en una organizacion. El sistema crea o reutiliza el usuario, asigna membresia y envia un enlace temporal para establecer contrasena.

### Catalogo de cuentas

Con un tenant activo, el usuario puede:

- Ver cuentas.
- Buscar por cuenta, descripcion o codigo agrupador.
- Agregar cuentas individuales.
- Subir catalogos completos.
- Descargar plantilla CSV.
- Eliminar cuentas.

### Manuales

Con cuentas cargadas, el usuario puede seleccionar cuentas y generar un manual con IA. Luego puede:

- Ver detalle.
- Editar titulo y contenido.
- Aprobar.
- Eliminar.

## Importacion de catalogos

Ruta principal:

```text
/catalogo/subir/
```

Formatos soportados:

- `.csv`
- `.xlsx`

La pantalla de importación incluye una guía de preparación y descarga de plantilla.
La primera fila contiene los encabezados sin acentos, en cualquier orden, y cada
fila siguiente contiene una cuenta.

| Columna | Obligatoria | Formato |
| --- | --- | --- |
| `cuenta` | Sí | Texto no vacío, máximo 20 caracteres. Conservar ceros iniciales y separadores. |
| `descripcion` | Sí | Texto no vacío con el nombre de la cuenta; admite acentos y espacios. |
| `nivel` | No; recomendado | Entero de 1 a 20, sin decimales. Profundidad de la cuenta. |
| `codigoagrupador` | No | Texto con un código SAT existente, por ejemplo `102.01`. Vacío u omitido solicita sugerencia. |
| `nivel1`, `nivel2`, `nivel3`, `nivel4` | No | Componentes de jerarquía: cada valor es un entero no negativo o una celda vacía. El cero cuenta como presente. Son alternativos a `nivel`. |

En Excel usar la hoja activa, con encabezados en la fila 1, sin títulos previos ni
celdas combinadas. Configurar cuentas y códigos SAT como Texto **antes** de pegar
los datos; cambiar el formato después no recupera los ceros perdidos. En CSV usar
UTF-8 y coma como separador (no punto y coma); las descripciones con comas van
entre comillas dobles. Usar una sola fila por cuenta. Las filas válidas se importan
aunque otras tengan errores; el resultado indica qué filas corregir.
Formatos: CSV UTF-8 y Excel `.xlsx` (no `.xls`). Conservar números de cuenta y
códigos SAT como texto en Excel para preservar ceros y decimales.

```csv
cuenta,descripcion,nivel,codigoagrupador
1000,Caja,1,
1000.01,Caja y efectivo,2,
1100,Bancos,1,
1100.01,Bancos nacionales,2,
```

La importación del catálogo propio es opcional. El usuario elige todos los niveles
o un máximo entre 1 y 20. Se importan las cuentas hasta ese máximo y se omiten las
más profundas; las cuentas existentes fuera de esa selección no se eliminan.
La profundidad se obtiene de `nivel`, del último campo `nivel1` a `nivel4`
presente (incluido cero), o del número de segmentos separados por punto, guion o
barra. Los códigos sin separadores deben indicar `nivel` para filtrar su jerarquía.

Si falta `codigoagrupador`, se sugiere una relación por similitud del nombre,
normalizando acentos y puntuación. No se interpreta el número propio como SAT.
Las coincidencias ambiguas quedan pendientes. La similitud mostrada no es una
probabilidad ni validación fiscal. El usuario puede confirmar o corregir la relación
en el catálogo antes de generar un manual. Los códigos SAT explícitos se validan;
un código inexistente produce un error por fila. Los archivos se importan sin
mezclar automáticamente cuentas de plantillas por giro.

La unicidad sigue siendo `tenant + cuenta`; una cuenta existente se actualiza.

## Generacion de manuales con IA

Ruta principal:

```text
/catalogo/generar-manual/
```

La generacion usa:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_MAX_TOKENS`

El prompt incluye informacion del tenant:

- Nombre de la organizacion.
- Giro.
- Regimen fiscal.
- Cuentas seleccionadas.
- Codigo Agrupador SAT.

La respuesta de OpenAI se guarda como `ManualContable` y queda asociada al tenant y al usuario que la creo.

Advertencia operativa: la llamada a OpenAI es sincronica. Manuales grandes pueden tardar y mantener ocupada la request. En produccion, Gunicorn y Nginx tienen timeouts extendidos, pero a futuro conviene mover este flujo a tareas en segundo plano.

## Donativos con Mercado Pago

Ruta principal:

```text
/donar/
```

Rutas asociadas:

```text
/donar/exito/
/donar/error/
/donar/pendiente/
/donar/webhook/
```

El flujo es:

1. Usuario elige monto sugerido o personalizado.
2. La aplicacion crea un `Donativo` pendiente.
3. Se crea una preferencia en Mercado Pago.
4. El usuario es redirigido a Mercado Pago.
5. Mercado Pago notifica el resultado al webhook.
6. El webhook valida firma y actualiza estado.

Montos sugeridos actuales:

- 50 MXN.
- 100 MXN.
- 200 MXN.
- 500 MXN.

Validaciones:

- Monto minimo: 10 MXN.
- Monto maximo: 100,000 MXN.
- Firma HMAC SHA256 si `MERCADOPAGO_WEBHOOK_SECRET` esta configurado.

## Tests

Hay pruebas existentes para flujos criticos:

- `cuentas/tests.py`: invitaciones, tokens de contrasena y edicion de tenant.
- `catalogo/tests.py`: eliminacion de cuentas solo por POST.
- `donaciones/tests.py`: firma de webhook y aprobacion de donativo.

Ejecutar todas las pruebas:

```bash
python manage.py test
```

Ejecutar por app:

```bash
python manage.py test cuentas
python manage.py test catalogo
python manage.py test donaciones
```

## Despliegue en produccion

Los archivos de despliegue estan en `deploy/`.

| Archivo | Proposito |
| --- | --- |
| `deploy.sh` | Script automatizado de deploy. |
| `gunicorn.conf.py` | Configuracion de Gunicorn. |
| `manual_contable.service` | Servicio systemd principal. |
| `manual_contable_supervisor.conf` | Configuracion alternativa con Supervisor. |
| `nginx_manual_contable.conf` | Reverse proxy Nginx con SSL y estaticos. |

### Deploy automatico

Requisitos previos:

- Ubuntu 22.04+ o Debian 12+.
- PostgreSQL instalado y base `mconta` creada.
- `.env` configurado correctamente.
- DNS apuntando a la IP del servidor.

Ejecutar:

```bash
sudo bash deploy/deploy.sh manualcontable.online tu@email.com
```

Despues del deploy:

```bash
source venv/bin/activate
python manage.py createsuperuser
```

Verificar:

```bash
sudo systemctl status manual_contable
sudo journalctl -u manual_contable -f
sudo systemctl status nginx
```

### Actualizar una instalación existente

Con el código actualizado y `.env` configurado, ejecutar desde el proyecto:

```bash
sudo bash deploy/deploy.sh --update
```

Este modo instala las dependencias como el propietario de `manage.py`, valida Django
y las migraciones incluidas, aplica las migraciones pendientes, carga la referencia
SAT, recopila estáticos y reinicia `manual_contable`. Comprueba que el servicio quede
activo. No descarga código ni modifica Nginx, certificados o configuración de servicios.

Con Supervisor: `sudo bash deploy/deploy.sh --update --manager supervisor`.
Para omitir dependencias ya instaladas: agregar `--skip-install`.
Si el usuario del servicio difiere del propietario de `manage.py`, usar
`sudo APP_USER=usuario bash deploy/deploy.sh --update`.
`SERVICE_NAME` permite indicar otro nombre de servicio.

Si falla una fase, se detiene sin continuar al reinicio. Las migraciones ya aplicadas
se conservan; no realiza reversión automática. La comprobación final verifica el
estado del proceso; comprobar también la aplicación desde su URL habitual.

### Deploy manual resumido

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx supervisor postgresql-client libpq-dev

cd /home/gaibarra/manual_contable_ai
source venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput

sudo cp deploy/manual_contable.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable manual_contable
sudo systemctl restart manual_contable

sudo ln -sf /etc/nginx/sites-available/manual_contable /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

sudo certbot --nginx -d manualcontable.online -d www.manualcontable.online --email tu@email.com --agree-tos
```

## Seguridad

Medidas presentes:

- Variables sensibles fuera del codigo.
- `DEBUG` configurable por entorno.
- `ALLOWED_HOSTS` configurable.
- Cookies seguras en produccion.
- Redireccion HTTPS en produccion.
- HSTS en produccion.
- CSRF middleware activo.
- Autenticacion requerida en vistas internas.
- Backend de autenticacion por email o username.
- Tenant activo validado contra membresia del usuario.
- Tokens de invitacion con expiracion y uso unico.
- Webhook de Mercado Pago con validacion de firma.
- Nginx bloquea archivos ocultos y `.env`.

Recomendaciones:

- No subir `.env` al repositorio.
- Usar `DEBUG=False` en produccion.
- Usar claves fuertes y rotarlas si se exponen.
- Configurar SMTP real antes de invitar usuarios en produccion.
- Revisar permisos por rol antes de abrir la plataforma a mas usuarios.

## Documentacion adicional

- `ANALISIS_APLICACION.md`: analisis de utilidad, arquitectura y recomendaciones tecnicas.
- `PLAN_EVOLUCION.md`: vision y roadmap de evolucion hacia plataforma comunitaria SaaS.
- `.agent/workflows/deploy.md`: guia detallada de despliegue.

## Pendientes recomendados

Estos son los puntos tecnicos identificados para robustecer el proyecto:

1. Agregar `.env.example` sin secretos reales.
2. Mantener actualizada la referencia oficial versionada del SAT.
3. Centralizar permisos por rol para operaciones de tenant, catalogo y manuales.
4. Mover generacion de manuales con OpenAI a tareas en segundo plano si el volumen crece.
5. Agregar pruebas para importacion CSV/Excel, generacion de manuales, aislamiento multi-tenant y permisos por rol.
6. Revisar si `tenant=null` en modelos contables sigue siendo necesario despues de migrar datos historicos.
7. Considerar auditoria de acciones importantes: creacion, edicion, aprobacion y eliminacion de manuales y cuentas.

## Licencia

No se encontro informacion de licencia en el repositorio.

## Proveedor alternativo de IA: DeepSeek

La generación permite elegir el proveedor en el servidor. Los usuarios conservan el
mismo botón **Generar con IA** y reciben mensajes neutrales; las claves nunca se
solicitan en el navegador. Se usa la API compatible con OpenAI de DeepSeek:
https://api-docs.deepseek.com/

Para usar DeepSeek, agregar al `.env` del servidor:

```dotenv
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=REEMPLAZAR_CON_CLAVE_REAL
DEEPSEEK_MODEL=deepseek-flash
DEEPSEEK_MAX_TOKENS=8192
AI_FALLBACK_PROVIDER=
AI_TIMEOUT_SECONDS=90
```

`DEEPSEEK_MODEL` permite ajustar el modelo habilitado en la cuenta. OpenAI sigue
siendo el proveedor predeterminado; su clave es opcional cuando solo se usa DeepSeek.

Para mantener OpenAI como principal y usar DeepSeek automáticamente si falla:

```dotenv
AI_PROVIDER=openai
AI_FALLBACK_PROVIDER=deepseek
```

En ese caso configurar ambas claves. También se admite el orden inverso. El
respaldo solo se intenta ante errores del proveedor, clave ausente o respuestas
vacías/incompletas. Cada proveedor se intenta una vez y recibe el mismo contexto
contable. Si ambos fallan, no se guarda un manual. El proveedor utilizado y los
códigos de error se registran en el servidor, sin claves ni contenido contable.
El timeout es por solicitud HTTP; mantenerlo por debajo del timeout del servidor.

Después de cambiar la configuración o desplegar el código:

```bash
sudo systemctl restart manual_contable
```

Pruebas de proveedores sin llamadas reales ni acceso a la base de datos:

```bash
DEBUG=False venv/bin/python manage.py test catalogo.test_ia catalogo.tests.ManualGenerationErrorTests
```

La integración con DeepSeek desactiva explícitamente `thinking` para destinar el
presupuesto de salida al manual final. Las respuestas truncadas no se guardan:
se informa al usuario que reduzca las cuentas seleccionadas o solicite al
administrador ampliar `DEEPSEEK_MAX_TOKENS`. Los registros incluyen el motivo de
finalización y el uso de tokens, sin registrar el contenido de las respuestas.

## Identidad del despacho y presentación de manuales

- **Mi despacho** (`/mi-despacho/`): identidad del titular, reutilizada por sus empresas.
- **Presentación de la empresa** (`/organizaciones/<id>/presentacion/`): composición,
  logo y datos visibles. Pueden editarla propietarios y contadores de esa empresa.
- Los borradores usan los datos vigentes. Aprobar fija una copia de la identidad;
  **Actualizar presentación** requiere vista previa y confirmación, y deja una
  auditoría. Ninguna de estas operaciones llama a la IA.
- La descarga de Word ahora es un `.docx` nativo con logos integrados. La ruta
  de exportación se conserva; cambia su extensión y tipo de contenido.
- Los logos normalizados se guardan en `PRIVATE_MEDIA_ROOT` (`private_media/`),
  fuera de `/media/` y `/static/`. Se sirven por una vista autenticada. No borres
  logos reemplazados: pueden formar parte de manuales aprobados. Respalda este
  directorio junto con la base de datos.

Para actualizar una instalación: instalar `requirements.txt`, ejecutar
`manage.py migrate` y `manage.py collectstatic --noinput`, y **reiniciar por
completo** el servicio (la recarga de workers no actualiza modelos precargados).
La migración fija los datos de los aprobados anteriores sin añadirles logos.

Pruebas de personalización, aislamiento y Word sin llamadas de IA:

```bash
DEBUG=False venv/bin/python manage.py test catalogo.test_presentacion
```

## Recuperación de contraseña

En **Iniciar sesión → ¿Olvidaste tu contraseña?**, el usuario solicita un correo
con un enlace HTTPS de un solo uso, válido durante una hora. Después de cambiar
la contraseña debe iniciar sesión de nuevo. Los correos desconocidos no revelan
si existe una cuenta. Si el servidor de correo no conecta, se muestra el mismo
aviso temporal para todas las direcciones, antes de buscar cuentas.

El envío utiliza el SMTP configurado. Para Gmail, `EMAIL_HOST_PASSWORD` debe
contener una contraseña de aplicación vigente, generada con la verificación en
dos pasos de Google. Actualizarla directamente en `.env`, sin compartirla en el
chat ni guardarla en el repositorio. Se conserva Gmail en el puerto 587 con TLS.
`PASSWORD_RESET_DOMAIN` permite configurar el dominio canónico de los enlaces
(predeterminado: `manualcontable.online`).

Comprobar la autenticación sin enviar correos:

```bash
DEBUG=False venv/bin/python manage.py verificar_correo
```

Después de actualizar `.env`, reiniciar completamente `manual_contable` para
que el servicio cargue la nueva credencial. Pruebas sin mensajes reales:

```bash
DEBUG=False venv/bin/python manage.py test cuentas.test_password_reset
```
# nexocontable
