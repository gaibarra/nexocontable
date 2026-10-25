from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone


class PerfilCPC(models.Model):
    """
    Perfil profesional del Contador Público (Certificado o no).
    Extiende el User de Django con datos profesionales.
    """
    ESPECIALIDAD_CHOICES = [
        ('fiscal', 'Fiscal'),
        ('auditoria', 'Auditoría'),
        ('costos', 'Costos'),
        ('contabilidad_general', 'Contabilidad General'),
        ('finanzas', 'Finanzas'),
        ('nominas', 'Nóminas'),
        ('comercio_exterior', 'Comercio Exterior'),
        ('gubernamental', 'Contabilidad Gubernamental'),
        ('otra', 'Otra'),
    ]

    ESTADOS_MEXICO = [
        ('AGS', 'Aguascalientes'), ('BC', 'Baja California'), ('BCS', 'Baja California Sur'),
        ('CAM', 'Campeche'), ('CHIS', 'Chiapas'), ('CHIH', 'Chihuahua'),
        ('CDMX', 'Ciudad de México'), ('COAH', 'Coahuila'), ('COL', 'Colima'),
        ('DGO', 'Durango'), ('GTO', 'Guanajuato'), ('GRO', 'Guerrero'),
        ('HGO', 'Hidalgo'), ('JAL', 'Jalisco'), ('MEX', 'Estado de México'),
        ('MICH', 'Michoacán'), ('MOR', 'Morelos'), ('NAY', 'Nayarit'),
        ('NL', 'Nuevo León'), ('OAX', 'Oaxaca'), ('PUE', 'Puebla'),
        ('QRO', 'Querétaro'), ('QROO', 'Quintana Roo'), ('SLP', 'San Luis Potosí'),
        ('SIN', 'Sinaloa'), ('SON', 'Sonora'), ('TAB', 'Tabasco'),
        ('TAM', 'Tamaulipas'), ('TLAX', 'Tlaxcala'), ('VER', 'Veracruz'),
        ('YUC', 'Yucatán'), ('ZAC', 'Zacatecas'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_cpc')
    nombre_completo = models.CharField(max_length=255)
    cedula_profesional = models.CharField(max_length=20, blank=True, null=True,
        help_text='Opcional. Cédula profesional de Contador Público.')
    numero_certificacion = models.CharField(max_length=30, blank=True, null=True,
        help_text='Número de certificación ante el IMCP (si aplica).')
    colegio_afiliado = models.CharField(max_length=150, blank=True, null=True,
        help_text='Colegio de Contadores al que pertenece.')
    especialidad = models.CharField(max_length=30, choices=ESPECIALIDAD_CHOICES, default='contabilidad_general')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    ciudad = models.CharField(max_length=100)
    estado = models.CharField(max_length=5, choices=ESTADOS_MEXICO)
    anios_experiencia = models.PositiveIntegerField(default=0, verbose_name='Años de experiencia')
    linkedin_url = models.URLField(blank=True, null=True)
    acepta_terminos = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil CPC'
        verbose_name_plural = 'Perfiles CPC'

    def __str__(self):
        return f"CPC {self.nombre_completo}"


class Tenant(models.Model):
    """
    Organización/Empresa/Despacho. Un CPC puede tener múltiples tenants
    (uno por cada cliente de su despacho).
    """
    GIRO_CHOICES = [
        ('comercial', 'Comercial'),
        ('industrial', 'Industrial'),
        ('servicios', 'Servicios'),
        ('educativo', 'Educativo'),
        ('salud', 'Salud'),
        ('construccion', 'Construcción'),
        ('tecnologia', 'Tecnología'),
        ('agropecuario', 'Agropecuario'),
        ('hoteleria', 'Hotelería y Turismo'),
        ('restaurantes', 'Restaurantes y Alimentos'),
        ('transporte', 'Transporte'),
        ('inmobiliario', 'Inmobiliario'),
        ('ong', 'ONG / Asociación Civil'),
        ('gobierno', 'Gobierno'),
        ('otro', 'Otro'),
    ]

    REGIMEN_CHOICES = [
        ('pm_general', 'Persona Moral - Régimen General'),
        ('pm_sin_fines', 'Persona Moral - Sin Fines de Lucro'),
        ('pf_empresarial', 'Persona Física - Actividad Empresarial'),
        ('pf_profesional', 'Persona Física - Servicios Profesionales'),
        ('pf_plataformas', 'Persona Física - Plataformas Digitales'),
        ('pf_resico', 'Persona Física - RESICO'),
        ('pf_arrendamiento', 'Persona Física - Arrendamiento'),
        ('otro', 'Otro'),
    ]

    nombre = models.CharField(max_length=255, help_text='Nombre de la empresa u organización')
    rfc = models.CharField(max_length=13, blank=True, null=True,
        validators=[RegexValidator(
            regex=r'^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$',
            message='Formato de RFC inválido. Ejemplo: XAXX010101000'
        )],
        help_text='RFC de la organización')
    giro = models.CharField(max_length=20, choices=GIRO_CHOICES, default='servicios')
    sector = models.CharField(max_length=50, blank=True, null=True)
    regimen_fiscal = models.CharField(max_length=20, choices=REGIMEN_CHOICES, default='pm_general')
    direccion = models.TextField(blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=5, choices=PerfilCPC.ESTADOS_MEXICO, blank=True, null=True)
    codigo_postal = models.CharField(max_length=5, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenants_propios')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Organización'
        verbose_name_plural = 'Organizaciones'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class MembresiaTenant(models.Model):
    """
    Relación usuario-tenant con rol.
    Un tenant puede tener múltiples usuarios y un usuario puede estar en múltiples tenants.
    """
    ROL_CHOICES = [
        ('propietario', 'Propietario'),
        ('contador', 'Contador'),
        ('auxiliar', 'Auxiliar Contable'),
        ('solo_lectura', 'Solo Lectura'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='membresias')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='membresias_tenant')
    rol = models.CharField(max_length=15, choices=ROL_CHOICES, default='auxiliar')
    fecha_ingreso = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Membresía'
        verbose_name_plural = 'Membresías'
        unique_together = ('tenant', 'usuario')

    def __str__(self):
        return f"{self.usuario.username} → {self.tenant.nombre} ({self.get_rol_display()})"


class InvitacionAcceso(models.Model):
    """Token de invitación para establecer contraseña con expiración y uso único."""
    token = models.CharField(max_length=128, unique=True, db_index=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitaciones_acceso')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invitaciones_acceso')
    rol = models.CharField(max_length=15, choices=MembresiaTenant.ROL_CHOICES)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invitaciones_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Invitación de Acceso'
        verbose_name_plural = 'Invitaciones de Acceso'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Invitación {self.usuario.email} → {self.tenant.nombre}"

    @property
    def esta_vigente(self):
        return self.usado_en is None and timezone.now() <= self.expira_en


from uuid import uuid4
from .marca_storage import PrivateLogoStorage, ruta_logo


def campos_empresa_default():
    return ['rfc', 'ciudad']


def campos_despacho_default():
    return ['rfc', 'ciudad', 'telefono', 'correo', 'sitio_web']


class LogoDocumento(models.Model):
    """Cada reemplazo crea un archivo nuevo; los aprobados conservan el anterior."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    propietario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='logos_documentales')
    organizacion = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name='logos_documentales')
    ambito = models.CharField(max_length=10, choices=[('despacho', 'Despacho'), ('empresa', 'Empresa')], default='despacho')
    imagen = models.FileField(storage=PrivateLogoStorage(), upload_to=ruta_logo)
    creado_en = models.DateTimeField(auto_now_add=True)


class IdentidadDespacho(models.Model):
    titular = models.OneToOneField(User, on_delete=models.CASCADE, related_name='identidad_despacho')
    nombre = models.CharField('Nombre comercial', max_length=255)
    logo = models.ForeignKey(LogoDocumento, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    rfc = models.CharField('RFC', max_length=13, blank=True)
    direccion = models.CharField('Dirección', max_length=300, blank=True)
    ciudad = models.CharField('Ciudad', max_length=100, blank=True)
    telefono = models.CharField('Teléfono', max_length=30, blank=True)
    correo = models.EmailField('Correo profesional', blank=True)
    sitio_web = models.URLField('Sitio web', blank=True)
    color = models.CharField('Color corporativo', max_length=7, default='#1a365d')

    def __str__(self):
        return self.nombre


class PresentacionEmpresa(models.Model):
    COMPOSICIONES = [('ambos', 'Despacho y empresa'), ('empresa', 'Solo empresa'), ('despacho', 'Solo despacho')]
    organizacion = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='presentacion_documentos')
    logo = models.ForeignKey(LogoDocumento, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    correo = models.EmailField('Correo de la empresa', blank=True)
    sitio_web = models.URLField('Sitio web de la empresa', blank=True)
    composicion = models.CharField('Encabezado', max_length=10, choices=COMPOSICIONES, default='ambos')
    color = models.CharField('Color de la empresa', max_length=7, blank=True)
    campos_empresa = models.JSONField(default=campos_empresa_default)
    campos_despacho = models.JSONField(default=campos_despacho_default)


class ConstanciaPrivacidad(models.Model):
    """Manifestación nueva; no atribuye consentimiento retroactivo a otras cuentas."""
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='constancias_privacidad')
    version = models.CharField(max_length=30)
    contenido_hash = models.CharField(max_length=64)
    fecha = models.DateTimeField(auto_now_add=True)
    canal = models.CharField(max_length=30, default='registro')

    class Meta:
        ordering = ['-fecha', '-pk']
