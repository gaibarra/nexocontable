from django.db import models
from django.contrib.auth.models import User


class Donativo(models.Model):
    """Registro de donativos vía Mercado Pago."""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('reembolsado', 'Reembolsado'),
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
    fecha = models.DateTimeField(auto_now_add=True)
    datos_webhook = models.JSONField(blank=True, null=True,
                                     help_text='Datos crudos del webhook de Mercado Pago')

    class Meta:
        verbose_name = 'Donativo'
        verbose_name_plural = 'Donativos'
        ordering = ['-fecha']

    def __str__(self):
        return f"${self.monto} — {self.nombre_donante or 'Anónimo'} ({self.get_estado_display()})"
