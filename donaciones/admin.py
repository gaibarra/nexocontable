from django.contrib import admin
from .models import Donativo


@admin.register(Donativo)
class DonativoAdmin(admin.ModelAdmin):
    list_display = ('nombre_donante', 'monto', 'estado', 'referencia_mp', 'fecha')
    list_filter = ('estado', 'fecha')
    search_fields = ('nombre_donante', 'email_donante', 'referencia_mp')
    readonly_fields = ('preference_id', 'referencia_mp', 'datos_webhook', 'fecha')
