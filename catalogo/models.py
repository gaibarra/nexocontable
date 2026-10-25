from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from cuentas.models import Tenant


class CodigoAgrupador(models.Model):
    """
    Catálogo global del SAT — Código Agrupador.
    Es compartido entre todos los tenants.
    """
    id = models.AutoField(primary_key=True)
    nivel = models.IntegerField(null=False)
    codigoagrupador = models.CharField(max_length=10, null=False, unique=True)
    nombre = models.CharField(max_length=255, null=False)

    class Meta:
        verbose_name = 'Código Agrupador SAT'
        verbose_name_plural = 'Códigos Agrupadores SAT'
        ordering = ['codigoagrupador']

    def __str__(self):
        return f"{self.codigoagrupador} - {self.nombre}"


class CatalogoPlantilla(models.Model):
    """
    Plantilla reutilizable de catálogo de cuentas por tipo de empresa.
    """
    GIRO_CHOICES = Tenant.GIRO_CHOICES
    REGIMEN_CHOICES = Tenant.REGIMEN_CHOICES

    nombre = models.CharField(max_length=255)
    giro = models.CharField(max_length=20, choices=GIRO_CHOICES)
    regimen_fiscal = models.CharField(max_length=20, choices=REGIMEN_CHOICES, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plantilla de Catálogo'
        verbose_name_plural = 'Plantillas de Catálogo'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class CatalogoPlantillaCuenta(models.Model):
    """
    Cuentas base asociadas a una plantilla de catálogo.
    """
    plantilla = models.ForeignKey(CatalogoPlantilla, on_delete=models.CASCADE, related_name='cuentas')
    cuenta = models.CharField(max_length=20)
    descripcion = models.TextField(blank=True, null=True)
    codigoagrupador = models.ForeignKey(CodigoAgrupador, on_delete=models.CASCADE, db_index=True)
    nivel1 = models.IntegerField(null=True, blank=True)
    nivel2 = models.IntegerField(null=True, blank=True)
    nivel3 = models.IntegerField(null=True, blank=True)
    nivel4 = models.IntegerField(null=True, blank=True)
    orden = models.PositiveIntegerField(default=0)
    es_recomendada = models.BooleanField(default=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cuenta de Plantilla'
        verbose_name_plural = 'Cuentas de Plantilla'
        ordering = ['orden', 'cuenta']
        unique_together = ('plantilla', 'cuenta')
        constraints = [
            models.UniqueConstraint(fields=['plantilla', 'cuenta'], name='uniq_plantilla_cuenta'),
        ]

    def __str__(self):
        return f"{self.cuenta} - {self.descripcion}"


class CatalogoCuentas(models.Model):
    """
    Catálogo de cuentas de cada organización (tenant).
    Cada cuenta está vinculada al código agrupador del SAT.
    """
    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='cuentas',
                               null=True, blank=True)  # null=True para migración de datos existentes
    nivel1 = models.IntegerField(null=True, blank=True)
    nivel2 = models.IntegerField(null=True, blank=True)
    nivel3 = models.IntegerField(null=True, blank=True)
    nivel4 = models.IntegerField(null=True, blank=True)
    cuenta = models.CharField(max_length=20, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    codigoagrupador = models.ForeignKey(CodigoAgrupador, on_delete=models.PROTECT, db_index=True, null=True, blank=True)
    nivel = models.PositiveSmallIntegerField(default=1)
    relacion_sugerida = models.BooleanField(default=False)
    confianza_relacion = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Cuenta del Catálogo'
        verbose_name_plural = 'Catálogo de Cuentas'
        ordering = ['cuenta']
        unique_together = ('tenant', 'cuenta')

    def clean(self):
        super().clean()
        if self.tenant_id is None:
            raise ValidationError({'tenant': 'La cuenta debe pertenecer a una organización (tenant).'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cuenta} - {self.descripcion}"


class ManualContable(models.Model):
    """
    Manual contable generado por IA para un tenant específico.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='manuales',
                               null=True, blank=True)  # null=True para migración
    titulo = models.CharField(max_length=255)
    cuentas = models.ManyToManyField('CatalogoCuentas')
    codigos_sat = models.ManyToManyField(CodigoAgrupador, blank=True)
    contenido = models.TextField()
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    aprobado = models.BooleanField(default=False)
    presentacion_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Manual Contable'
        verbose_name_plural = 'Manuales Contables'
        ordering = ['-fecha_creacion']

    def clean(self):
        super().clean()
        if self.tenant_id is None:
            raise ValidationError({'tenant': 'El manual debe pertenecer a una organización (tenant).'})
        if self.pk and self.cuentas.exclude(tenant=self.tenant).exists():
            raise ValidationError({'cuentas': 'Todas las cuentas del manual deben pertenecer al mismo tenant.'})

    def save(self, *args, **kwargs):
        if self.aprobado and not self.presentacion_snapshot and self.tenant_id:
            from .presentacion import construir_presentacion
            self.presentacion_snapshot = construir_presentacion(self.tenant)
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'presentacion_snapshot'}
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


class UsoIA(models.Model):
    """Historial de generaciones; se conserva al eliminar un manual o una empresa."""
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='usos_ia')
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, related_name='usos_ia')
    manual = models.ForeignKey(ManualContable, on_delete=models.SET_NULL, null=True, blank=True, related_name='usos_ia')
    organizacion_referencia = models.PositiveBigIntegerField(null=True, editable=False)
    fecha = models.DateTimeField(auto_now_add=True)
    tokens_entrada = models.PositiveBigIntegerField(null=True, blank=True)
    tokens_salida = models.PositiveBigIntegerField(null=True, blank=True)
    tokens_total = models.PositiveBigIntegerField(null=True, blank=True)
    total_parcial = models.BooleanField(default=False)
    manual_generado = models.BooleanField(default=False)
    intentos = models.JSONField(default=list)

    class Meta:
        verbose_name = 'Consumo de IA'
        verbose_name_plural = 'Consumos de IA'
        ordering = ['-fecha', '-pk']
        indexes = [models.Index(fields=['usuario', 'fecha'], name='usoia_usuario_fecha_idx')]


class CambioPresentacionManual(models.Model):
    manual = models.ForeignKey(ManualContable, on_delete=models.CASCADE, related_name='cambios_presentacion')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    anterior = models.JSONField(default=dict)
    nueva = models.JSONField(default=dict)

    class Meta:
        ordering = ['-fecha', '-pk']
