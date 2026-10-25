from django.contrib import admin
from .models import CodigoAgrupador, CatalogoCuentas, ManualContable, CatalogoPlantilla, CatalogoPlantillaCuenta


@admin.register(CodigoAgrupador)
class CodigoAgrupadorAdmin(admin.ModelAdmin):
    list_display = ('codigoagrupador', 'nombre', 'nivel')
    search_fields = ('codigoagrupador', 'nombre')
    list_filter = ('nivel',)


@admin.register(CatalogoCuentas)
class CatalogoCuentasAdmin(admin.ModelAdmin):
    list_display = ('cuenta', 'descripcion', 'codigoagrupador')
    search_fields = ('cuenta', 'descripcion')
    list_filter = ('codigoagrupador',)


class CatalogoPlantillaCuentaInline(admin.TabularInline):
    model = CatalogoPlantillaCuenta
    extra = 0


@admin.register(CatalogoPlantilla)
class CatalogoPlantillaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'giro', 'regimen_fiscal', 'activo', 'orden')
    list_filter = ('giro', 'regimen_fiscal', 'activo')
    search_fields = ('nombre', 'descripcion')
    inlines = [CatalogoPlantillaCuentaInline]


@admin.register(ManualContable)
class ManualContableAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'creado_por', 'fecha_creacion', 'aprobado')
    list_filter = ('aprobado', 'fecha_creacion')
    search_fields = ('titulo', 'contenido')
    readonly_fields = ('fecha_creacion', 'presentacion_snapshot')


from .models import UsoIA


@admin.register(UsoIA)
class UsoIAAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'tenant', 'tokens_total', 'total_parcial', 'manual_generado')
    list_filter = ('manual_generado', 'total_parcial', 'fecha')
    readonly_fields = ('usuario', 'tenant', 'manual', 'fecha', 'tokens_entrada', 'tokens_salida',
                       'tokens_total', 'total_parcial', 'manual_generado', 'intentos')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
