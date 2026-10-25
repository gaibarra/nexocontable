from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class AccesoPanel(models.Model):
    ROLES = [('propietario', 'Propietario'), ('soporte', 'Soporte'), ('comercial', 'Comercial'), ('consulta', 'Consulta')]
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='acceso_panel')
    rol = models.CharField(max_length=20, choices=ROLES, default='consulta')
    activo = models.BooleanField(default=True)
    secreto_totp = models.CharField(max_length=64, blank=True)
    ultimo_paso = models.BigIntegerField(default=-1)


class IntentoAcceso(models.Model):
    clave = models.CharField(max_length=64, unique=True)
    intentos = models.PositiveIntegerField(default=0)
    desde = models.DateTimeField()


class Evento(models.Model):
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    organizacion_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    categoria = models.CharField(max_length=30, db_index=True)
    accion = models.CharField(max_length=100, db_index=True)
    referencia = models.CharField(max_length=100, blank=True)
    detalle = models.CharField(max_length=400, blank=True)
    estado_http = models.PositiveSmallIntegerField(null=True, blank=True)
    duracion_ms = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha', '-pk']


class Contacto(models.Model):
    ETAPAS = [('prospecto', 'Prospecto'), ('contactado', 'Contactado'), ('registrado', 'Registrado'),
              ('organizacion', 'Primera organización'), ('manual', 'Primer manual'), ('recurrente', 'Recurrente'),
              ('inactivo', 'Inactivo'), ('perdido', 'Perdido')]
    nombre = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30, blank=True)
    despacho = models.CharField(max_length=255, blank=True)
    origen = models.CharField(max_length=100, default='Registro manual')
    etiquetas = models.CharField(max_length=255, blank=True)
    etapa = models.CharField(max_length=20, choices=ETAPAS, default='prospecto', db_index=True)
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-actualizado_en']
        constraints = [models.UniqueConstraint(Lower('email'), name='panel_contacto_email_ci')]


class Nota(models.Model):
    contacto = models.ForeignKey(Contacto, on_delete=models.CASCADE, related_name='notas')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    texto = models.TextField(max_length=4000)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']


class Tarea(models.Model):
    contacto = models.ForeignKey(Contacto, on_delete=models.CASCADE, related_name='tareas')
    titulo = models.CharField(max_length=255)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    vence = models.DateField(db_index=True)
    completada = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completada', 'vence', '-pk']


class ControlPlataforma(models.Model):
    aviso = models.CharField(max_length=400, blank=True)
    aviso_activo = models.BooleanField(default=False)
    generacion_habilitada = models.BooleanField(default=True)
    limite_diario_usuario = models.PositiveIntegerField(default=0, help_text='0 significa sin límite.')
    actualizado_en = models.DateTimeField(auto_now=True)


class CupoDiario(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dia = models.DateField()
    solicitudes = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['usuario', 'dia'], name='panel_cupo_usuario_dia')]
