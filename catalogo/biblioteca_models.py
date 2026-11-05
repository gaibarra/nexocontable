"""Biblioteca versionada. Los textos publicados no se sobrescriben."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

FAMILIAS = [(x, x.replace('_', ' ').title()) for x in ('inventarios', 'bancos', 'clientes', 'proveedores', 'ingresos', 'gastos', 'impuestos_diferidos', 'otra')]
PERMISOS = [('desconocido', 'Sin comprobar'), ('permitido', 'Permitido'), ('prohibido', 'No autorizado')]


class PublicacionInmutable(models.Model):
    publicado = models.BooleanField(default=False)
    retirado = models.BooleanField(default=False)
    revisor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    revisado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            anterior = type(self).objects.get(pk=self.pk)
            if anterior.publicado:
                for field in self._meta.concrete_fields:
                    if field.name != 'retirado' and getattr(anterior, field.attname) != getattr(self, field.attname):
                        raise ValidationError('La publicación es inmutable: crea una nueva versión.')
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.publicado:
            raise ValidationError('Retira la publicación sin borrar su historial.')
        return super().delete(*args, **kwargs)


class FuenteNormativa(models.Model):
    titulo = models.CharField(max_length=200)
    emisor = models.CharField(max_length=160)
    naturaleza = models.CharField(max_length=25, choices=[('ley', 'Ley o reglamento'), ('regla', 'Regla administrativa'), ('orientacion', 'Orientación'), ('contable', 'Norma contable')])
    url = models.URLField(max_length=600)
    fiscal = models.BooleanField(default=False)

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if self.pk and self.versiones.filter(publicado=True).exists():
            old = type(self).objects.get(pk=self.pk)
            if any(getattr(self, f.attname) != getattr(old, f.attname) for f in self._meta.concrete_fields):
                raise ValidationError('La fuente publicada se conserva; registra una nueva fuente.')
        self.full_clean()
        super().save(*args, **kwargs)


class VersionFuente(PublicacionInmutable):
    fuente = models.ForeignKey(FuenteNormativa, on_delete=models.PROTECT, related_name='versiones')
    edicion = models.CharField(max_length=200)
    publicada_el = models.DateField(null=True, blank=True)
    vigente_desde = models.DateField()
    vigente_hasta = models.DateField(null=True, blank=True)
    consulta = models.CharField(max_length=15, choices=PERMISOS, default='desconocido')
    almacenamiento = models.CharField(max_length=15, choices=PERMISOS, default='desconocido')
    envio_ia = models.CharField(max_length=15, choices=PERMISOS, default='desconocido')
    reproduccion = models.CharField(max_length=15, choices=PERMISOS, default='desconocido')
    evidencia_permisos = models.TextField(blank=True, max_length=3000)
    huella_documento = models.CharField(max_length=64, blank=True)
    evidencia_vigencia = models.TextField(max_length=3000, blank=True)

    def clean(self):
        if self.vigente_hasta and self.vigente_hasta < self.vigente_desde:
            raise ValidationError('El periodo de vigencia no es válido.')
        if any(getattr(self, x) == 'permitido' for x in ('consulta', 'almacenamiento', 'envio_ia', 'reproduccion')) and not self.evidencia_permisos.strip():
            raise ValidationError('Documenta el fundamento de los permisos.')
        if self.publicado and (not self.revisado_en or not self.evidencia_vigencia.strip()):
            raise ValidationError('Publicar requiere revisión y evidencia de vigencia.')

    def __str__(self):
        return f'{self.fuente} — {self.edicion}'


class CriterioRevisado(PublicacionInmutable):
    version = models.ForeignKey(VersionFuente, on_delete=models.PROTECT, related_name='criterios')
    familia = models.CharField(max_length=20, choices=FAMILIAS)
    perfil_tecnico = models.CharField(max_length=40, blank=True, default='', db_index=True)
    regimen = models.CharField(max_length=20)
    area = models.CharField(max_length=15, choices=[('isr', 'ISR'), ('iva', 'IVA'), ('obligaciones', 'Obligaciones'), ('contable', 'Contable')])
    titulo = models.CharField(max_length=200)
    localizacion = models.CharField(max_length=250)
    explicacion = models.TextField(max_length=5000)
    condiciones = models.TextField(max_length=3000)
    excepciones = models.TextField(max_length=3000)
    vigente_desde = models.DateField()
    vigente_hasta = models.DateField(null=True, blank=True)
    cobertura = models.CharField(max_length=15, choices=[('parcial', 'Parcial'), ('completa', 'Completa')], default='parcial')

    def clean(self):
        from cuentas.models import Tenant
        if self.perfil_tecnico:
            from .desarrollo_uniforme import PERFILES
            if self.perfil_tecnico not in PERFILES or PERFILES[self.perfil_tecnico]['familia'] != self.familia:
                raise ValidationError({'perfil_tecnico':'El perfil técnico debe existir y corresponder a su familia.'})
        if self.regimen not in dict(Tenant.REGIMEN_CHOICES):
            raise ValidationError('Régimen no admitido.')
        if self.vigente_hasta and self.vigente_hasta < self.vigente_desde:
            raise ValidationError('Periodo no válido.')
        if self.publicado and (not self.version.publicado or self.version.retirado or not self.revisado_en):
            raise ValidationError('Requiere versión publicada y revisión documentada.')
        if self.publicado and self.vigente_desde < self.version.vigente_desde:
            raise ValidationError('El criterio no puede preceder a su versión.')

    def __str__(self):
        return f'F{self.pk}: {self.titulo} / {self.familia} / {self.regimen}'


class ControlBiblioteca(models.Model):
    activa = models.BooleanField(default=False)
    actualizado_en = models.DateTimeField(auto_now=True)


class AlertaFuente(models.Model):
    fuente = models.ForeignKey(FuenteNormativa, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20)
    detalle = models.CharField(max_length=400)
    huella_detectada = models.CharField(max_length=64, blank=True)
    resuelta = models.BooleanField(default=False)
    revision = models.TextField(blank=True, max_length=2000)
    revisor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='+')
    vigente_desde = models.DateField(null=True, blank=True)
    manuales_afectados = models.JSONField(default=list)


class RevisionFundamentos(models.Model):
    manual = models.ForeignKey('catalogo.ManualContable', on_delete=models.CASCADE, related_name='revisiones_fundamentos')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    huella = models.CharField(max_length=64)
    evidencia = models.JSONField(default=dict)
    tipo = models.CharField(max_length=15, choices=[('verificacion', 'Verificación'), ('aprobacion', 'Aprobación'), ('invalidacion', 'Invalidación'), ('reformulacion', 'Reformulación técnica')])

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('El historial de revisión es inmutable.')
        super().save(*args, **kwargs)
