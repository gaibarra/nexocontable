from django.db import models
from django.contrib.auth.models import User


class Donativo(models.Model):
    """Registro de donativos vía Mercado Pago."""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('reembolsado', 'Reembolsado'),
        ('parcial', 'Reembolso parcial'),
        ('contracargo', 'Contracargo'),
        ('cancelado', 'Cancelado'),
        ('en_revision', 'En revisión'),
        ('error_checkout', 'Error de checkout'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='donativos')
    nombre_donante = models.CharField(max_length=255, blank=True)
    email_donante = models.EmailField(blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    referencia_mp = models.CharField(max_length=100, blank=True, null=True,
                                     verbose_name='Referencia Mercado Pago')
    preference_id = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    checkout_clave = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    checkout_url = models.URLField(max_length=2048, blank=True, editable=False)
    collector_mp = models.CharField(max_length=100, blank=True, editable=False)
    pago_actualizado_en = models.DateTimeField(null=True, blank=True, editable=False)
    monto_confirmado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, editable=False)
    monto_reembolsado = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    fecha = models.DateTimeField(auto_now_add=True)
    datos_webhook = models.JSONField(blank=True, null=True,
                                     help_text='Resumen verificado; no almacena tarjetas ni documentos de identificación')

    class Meta:
        verbose_name = 'Donativo'
        verbose_name_plural = 'Donativos'
        ordering = ['-fecha']

    def __str__(self):
        return f"${self.monto} — {self.nombre_donante or 'Anónimo'} ({self.get_estado_display()})"


class PagoMercadoPago(models.Model):
    """Un recurso de pago por intento; el mismo checkout puede tener varios."""
    pago_id = models.CharField(max_length=64, unique=True)
    donativo = models.ForeignKey(Donativo, on_delete=models.PROTECT, related_name='pagos_mp')
    estado = models.CharField(max_length=30)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    reembolsado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actualizado_en = models.DateTimeField()
    resumen = models.JSONField(default=dict)

    class Meta:
        ordering = ['-actualizado_en', '-pk']
