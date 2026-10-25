# Generated manually to seed initial catalog templates.

from django.db import migrations


def crear_plantillas(apps, schema_editor):
    CodigoAgrupador = apps.get_model('catalogo', 'CodigoAgrupador')
    CatalogoPlantilla = apps.get_model('catalogo', 'CatalogoPlantilla')
    CatalogoPlantillaCuenta = apps.get_model('catalogo', 'CatalogoPlantillaCuenta')

    codigos = {
        obj.codigoagrupador: obj
        for obj in CodigoAgrupador.objects.filter(codigoagrupador__in=['101', '102.01', '201.01', '401'])
    }

    plantillas = [
        {
            'nombre': 'Plantilla Comercial Base',
            'giro': 'comercial',
            'descripcion': 'Estructura base para empresas comerciales.',
            'orden': 10,
            'cuentas': [
                ('1000', 'Caja y bancos', '101', 1, None, None, None, 10),
                ('1100', 'Bancos', '102.01', 1, 1, None, None, 20),
                ('1200', 'Clientes', '201.01', 1, 2, None, None, 25),
                ('1300', 'Inventarios', '201.01', 1, 3, None, None, 27),
                ('2000', 'Proveedores', '201.01', 2, None, None, None, 30),
                ('3000', 'Capital contable', '201.01', 3, None, None, None, 35),
                ('4000', 'Ventas', '401', 4, None, None, None, 40),
            ],
        },
        {
            'nombre': 'Plantilla Servicios Base',
            'giro': 'servicios',
            'descripcion': 'Estructura base para empresas de servicios.',
            'orden': 20,
            'cuentas': [
                ('1000', 'Caja y bancos', '101', 1, None, None, None, 10),
                ('1100', 'Bancos', '102.01', 1, 1, None, None, 20),
                ('1250', 'Clientes por servicios', '201.01', 1, 2, None, None, 25),
                ('2000', 'Proveedores', '201.01', 2, None, None, None, 30),
                ('3000', 'Capital contable', '201.01', 3, None, None, None, 35),
                ('4100', 'Ingresos por servicios', '401', 4, None, None, None, 40),
            ],
        },
        {
            'nombre': 'Plantilla Restaurantes Base',
            'giro': 'restaurantes',
            'descripcion': 'Estructura base para restaurantes y alimentos.',
            'orden': 30,
            'cuentas': [
                ('1000', 'Caja y bancos', '101', 1, None, None, None, 10),
                ('1100', 'Bancos', '102.01', 1, 1, None, None, 20),
                ('1300', 'Inventarios de insumos', '201.01', 1, 3, None, None, 25),
                ('2100', 'Proveedores de insumos', '201.01', 2, None, None, None, 30),
                ('3000', 'Capital contable', '201.01', 3, None, None, None, 35),
                ('4100', 'Ventas de alimentos y bebidas', '401', 4, None, None, None, 40),
            ],
        },
        {
            'nombre': 'Plantilla Hoteles Base',
            'giro': 'hoteleria',
            'descripcion': 'Estructura base para hoteles y hospedaje.',
            'orden': 40,
            'cuentas': [
                ('1000', 'Caja y bancos', '101', 1, None, None, None, 10),
                ('1100', 'Bancos', '102.01', 1, 1, None, None, 20),
                ('1400', 'Cuentas por cobrar hospedaje', '201.01', 1, 4, None, None, 25),
                ('2200', 'Proveedores', '201.01', 2, None, None, None, 30),
                ('3000', 'Capital contable', '201.01', 3, None, None, None, 35),
                ('4200', 'Ingresos por hospedaje', '401', 4, None, None, None, 40),
            ],
        },
    ]

    for plantilla_data in plantillas:
        plantilla = CatalogoPlantilla.objects.create(
            nombre=plantilla_data['nombre'],
            giro=plantilla_data['giro'],
            descripcion=plantilla_data['descripcion'],
            activo=True,
            orden=plantilla_data['orden'],
        )

        for cuenta, descripcion, codigo_sat, n1, n2, n3, n4, orden in plantilla_data['cuentas']:
            codigo_obj = codigos.get(codigo_sat)
            if not codigo_obj:
                continue

            CatalogoPlantillaCuenta.objects.create(
                plantilla=plantilla,
                cuenta=cuenta,
                descripcion=descripcion,
                codigoagrupador=codigo_obj,
                nivel1=n1,
                nivel2=n2,
                nivel3=n3,
                nivel4=n4,
                orden=orden,
                es_recomendada=True,
                activa=True,
            )


def revertir_plantillas(apps, schema_editor):
    CatalogoPlantilla = apps.get_model('catalogo', 'CatalogoPlantilla')
    CatalogoPlantilla.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0005_catalogoplantilla_catalogoplantillacuenta'),
    ]

    operations = [
        migrations.RunPython(crear_plantillas, revertir_plantillas),
    ]
