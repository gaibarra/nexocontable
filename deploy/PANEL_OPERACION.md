# Torre de Control · Manual Contable

Panel privado en `https://manualcontable.online/panel/`, con diseño, rutas,
proceso Gunicorn, sesión y cookie CSRF propios. Comparte la base PostgreSQL
con la aplicación. El acceso global se implementa en vistas con permisos;
la separación de proceso no equivale a aislamiento de base de datos.

## Estado de entrega

Activación autorizada expresamente el 25 de octubre de 2026 y realizada:
migración del panel aplicada, estáticos publicados, cuenta `gaibarra` autorizada
como propietario, nueve usuarios existentes vinculados al CRM y servicio
principal reiniciado. HTTPS, redirección de visitantes anónimos al acceso
privado y bloqueo de POST sin CSRF comprobados. Las diez pantallas se comprobaron
contra PostgreSQL real, sin crear sesiones que omitan el segundo factor.

El acceso público funciona mediante la puerta de enlace de la aplicación y un
proceso Gunicorn privado. Falta instalar el servicio systemd y la ruta directa
de Nginx con `sudo bash deploy/instalar_panel.sh`: la cuenta de desarrollo
requiere contraseña para `sudo`. Esta etapa elimina la dependencia del proceso
principal para recibir tráfico. No solicitar ni compartir la contraseña por chat.

## Funciones implementadas

- Tablero con datos de usuarios, organizaciones, manuales, tokens y donativos.
- CRM con ocho etapas, búsqueda, etiquetas, origen, responsable, notas y tareas.
- Vinculación por correo sin distinguir mayúsculas, unicidad en base de datos
  y sincronización idempotente. No se combinan usuarios distintos vinculados.
- Progreso automático al registrar usuarios, crear organizaciones y manuales.
  Las etapas Inactivo y Perdido conservan la decisión manual.
- Captura de solicitudes por nombre de ruta y de eventos de negocio después
  de confirmar sus transacciones. No almacena cuerpos, contraseñas, códigos,
  cadenas de consulta ni rutas con tokens de recuperación o invitación.
- Filtros de actividad por fechas, categoría, usuario, organización y error.
- Suspensión y reactivación de usuarios y organizaciones con motivo y auditoría.
  Las cuentas administrativas se protegen de suspensión desde el panel.
- Generación de IA habilitada/pausada, límite diario de solicitudes por usuario
  y avisos en la aplicación. Las reservas se serializan con bloqueo por usuario.
  Se cuentan solicitudes aceptadas incluso si después falla el proveedor;
  las solicitudes iniciadas antes de una pausa pueden terminar.
- Consumo por usuario y detalle de intentos por proveedor; no inventa costos.
- Radar de recorridos pendientes con reglas visibles y revisión manual.
- Estado de base de datos y presencia de configuración de integraciones.
  No realiza envíos, pagos ni llamadas de IA para comprobar las credenciales.

No recupera eventos anteriores a la activación. Un usuario recurrente se define
como usuario con al menos dos manuales propios; es una regla inicial, no una
medición de retención por cohortes. La visualización de adopción muestra la
distribución actual de etapas, no tasas históricas de conversión. El pulso se
calcula al abrir el tablero; no envía resúmenes programados. No se han instalado
monitoreo externo ni alertas por correo/WhatsApp.

## Acceso y recuperación

Las cuentas existentes no tienen acceso por defecto, aunque sean superusuarios.
La autorización se asigna explícitamente desde el servidor:

```bash
DEBUG=False venv/bin/python manage.py acceso_panel gaibarra --rol propietario
```

Roles: propietario (control y CRM), comercial (CRM), soporte (consulta operativa)
y consulta (lectura). La contraseña es la existente. El primer acceso requiere
enrolar una aplicación TOTP y confirmar un código válido. El servidor rechaza
códigos ya usados y limita intentos de contraseña y segundo factor por 15 minutos.
El enrolamiento caduca a los cinco minutos. La sesión privada expira tras una
hora de inactividad; las cuentas inactivas o revocadas se rechazan de inmediato.

La clave TOTP se almacena en la base de datos: restringir acceso a PostgreSQL y
proteger sus respaldos igual que las demás credenciales de autenticación.
La recuperación es administrativa, sin enlaces que omitan el segundo factor:

```bash
DEBUG=False venv/bin/python manage.py acceso_panel gaibarra --restablecer-2fa
DEBUG=False venv/bin/python manage.py acceso_panel nombre_usuario --revocar
```

Restablecer el segundo factor elimina las sesiones existentes de esa cuenta,
incluidas las de la aplicación, y exige configurar TOTP de nuevo. No cambia
contraseñas. No exponer las tablas de acceso, secretos TOTP o sesiones en APIs.

## Activación después de aprobación

1. Revisar el plan de migración y aplicar únicamente los cambios pendientes:

```bash
DEBUG=False venv/bin/python manage.py migrate --plan
DEBUG=False venv/bin/python manage.py migrate --noinput
DEBUG=False venv/bin/python manage.py collectstatic --noinput
DEBUG=False venv/bin/python manage.py acceso_panel gaibarra --rol propietario
```

2. Vincular los usuarios existentes desde el botón **Sincronizar usuarios**
   del CRM tras iniciar sesión. Conserva notas, tareas, responsables y estados
   manuales. No envía mensajes ni modifica las cuentas originales.

3. Instalar el servicio y la entrada directa de Nginx:

```bash
sudo bash deploy/instalar_panel.sh
sudo systemctl restart manual_contable
```

El instalador guarda respaldo del archivo del dominio, agrega solo la inclusión
de `/panel/`, valida Nginx antes de recargar y comprueba el socket del panel.
No cambia certificados ni otros dominios. Debe ejecutarse con privilegios de
administrador del sistema; la sesión de desarrollo no tiene `sudo` sin contraseña.
Si falla, el script se detiene; las migraciones ya aplicadas se conservan.
El archivo anterior de Nginx se restaura si falla su validación, el arranque del
servicio o la comprobación del socket. La ruta solo se recarga al responder el
servicio privado.

La aplicación también incluye una puerta de enlace local para `/panel/` que
arranca un proceso privado bajo bloqueo si falta su socket. Solo reenvía las
cookies privadas y conserva la validación CSRF en el proceso receptor.
Este modo facilita la transición; depende del proceso principal para recibir
tráfico. El servicio systemd con la ruta directa de Nginx evita esa dependencia
y reinicia el panel automáticamente, incluso tras reiniciar el servidor.

Después de actualizar código del panel, reiniciar **ambos servicios**. La
recarga de workers de un proceso precargado no actualiza todos los modelos.

## Verificación

```bash
DEBUG=False DJANGO_SETTINGS_MODULE=panel.test_settings venv/bin/python manage.py test panel --noinput
DEBUG=False DJANGO_SETTINGS_MODULE=panel.public_test_settings venv/bin/python manage.py test cuentas catalogo donaciones --noinput
DEBUG=False venv/bin/python manage.py check --deploy
```

Las pruebas usan SQLite temporal y sustituyen las migraciones históricas de
las apps originales que contienen SQL específico de PostgreSQL. La nueva
migración del panel sí se ejecuta en esas pruebas. El bloqueo concurrente con
`select_for_update` requiere PostgreSQL en producción.

Se validaron 26 pruebas del panel, 125 de regresión y un recorrido de navegador
con diez pantallas, creación de contacto, nota, tarea completada y móvil de
390 píxeles sin desbordamiento horizontal. La comprobación visual usó datos
ficticios en una base independiente. La URL pública y la protección de rutas ya
se verificaron tras activar el panel. El titular debe completar el enrolamiento
TOTP al entrar por primera vez. Se añadió una prueba del consumo de IA con
registros de proveedores reales y registros incompletos.

Los eventos crecen con el uso. Respaldar las tablas del CRM y auditoría junto
con la base principal y establecer una política de conservación acorde con
el volumen antes de eliminar registros. No hay borrado automático.

## Acciones en tablas

Las tablas incluyen la columna **Acciones**. Usuarios, organizaciones y contactos
tienen consulta, creación, edición y eliminación. Las notas y tareas se crean
desde el contacto y se consultan, editan o eliminan desde su ficha. Los usuarios
creados por el panel tienen perfil profesional y contraseña validada, sin
permisos administrativos. Al cambiar el propietario de una organización se
actualizan sus membresías: el propietario anterior pasa a contador y el nuevo
recibe la membresía de propietario.

El propietario administra usuarios, organizaciones y donativos manuales; el
propietario y el rol comercial administran el CRM. Soporte y consulta conservan
solo lectura. Las cuentas administrativas, incluida la cuenta propia, están
protegidas de edición y eliminación en estos formularios.

Cada eliminación requiere abrir la vista previa con sus dependencias, escribir
`ELIMINAR #id`, indicar el motivo y enviar un formulario con CSRF y una firma
válida durante quince minutos, vinculada al administrador y al registro.
Si cambian los registros afectados, se exige revisar y confirmar de nuevo.
Eliminar un usuario u organización puede eliminar sus datos dependientes;
la vista previa enumera esa cascada. Eliminar un contacto elimina sus notas y
tareas, pero conserva el usuario vinculado. Los eventos de auditoría se conservan.

Los donativos manuales se pueden crear, editar y eliminar; no generan cobros ni
devoluciones. Los registros con referencias o datos de Mercado Pago son de solo
consulta. La auditoría y los consumos de IA también ofrecen **Ver**, sin acciones
para alterar el historial. Todas las operaciones de escritura verifican permisos
en el servidor y generan un evento de auditoría.

Validación de esta entrega: 44 pruebas del panel, 125 de regresión, recorrido CRUD
en navegador con base aislada y comprobación de tablas con datos reales mediante
consultas de lectura. No requiere migraciones. Para repetir las pruebas:

```bash
DEBUG=False DJANGO_SETTINGS_MODULE=panel.test_settings venv/bin/python manage.py test panel --noinput
DEBUG=False DJANGO_SETTINGS_MODULE=panel.public_test_settings venv/bin/python manage.py test cuentas catalogo donaciones --noinput
```
