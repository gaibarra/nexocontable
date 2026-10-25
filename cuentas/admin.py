from django.contrib import admin
from .models import PerfilCPC, Tenant, MembresiaTenant


class MembresiaTenantInline(admin.TabularInline):
    model = MembresiaTenant
    extra = 1
    autocomplete_fields = ['usuario']


@admin.register(PerfilCPC)
class PerfilCPCAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'usuario', 'especialidad', 'estado', 'ciudad', 'fecha_registro')
    list_filter = ('especialidad', 'estado', 'fecha_registro')
    search_fields = ('nombre_completo', 'usuario__email', 'cedula_profesional', 'ciudad')
    readonly_fields = ('fecha_registro',)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rfc', 'giro', 'regimen_fiscal', 'propietario', 'activo', 'fecha_creacion')
    list_filter = ('giro', 'regimen_fiscal', 'activo', 'estado')
    search_fields = ('nombre', 'rfc', 'propietario__email')
    readonly_fields = ('fecha_creacion',)
    inlines = [MembresiaTenantInline]


@admin.register(MembresiaTenant)
class MembresiaTenantAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tenant', 'rol', 'fecha_ingreso')
    list_filter = ('rol',)
    search_fields = ('usuario__email', 'tenant__nombre')
    autocomplete_fields = ['usuario', 'tenant']
