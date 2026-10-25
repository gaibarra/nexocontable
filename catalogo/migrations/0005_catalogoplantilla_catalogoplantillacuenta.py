# Generated manually to add reusable catalog templates.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0004_alter_catalogocuentas_options_and_more'),
        ('cuentas', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CatalogoPlantilla',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('giro', models.CharField(choices=[('comercial', 'Comercial'), ('industrial', 'Industrial'), ('servicios', 'Servicios'), ('educativo', 'Educativo'), ('salud', 'Salud'), ('construccion', 'Construcción'), ('tecnologia', 'Tecnología'), ('agropecuario', 'Agropecuario'), ('hoteleria', 'Hotelería y Turismo'), ('restaurantes', 'Restaurantes y Alimentos'), ('transporte', 'Transporte'), ('inmobiliario', 'Inmobiliario'), ('ong', 'ONG / Asociación Civil'), ('gobierno', 'Gobierno'), ('otro', 'Otro')], max_length=20)),
                ('regimen_fiscal', models.CharField(blank=True, choices=[('pm_general', 'Persona Moral - Régimen General'), ('pm_sin_fines', 'Persona Moral - Sin Fines de Lucro'), ('pf_empresarial', 'Persona Física - Actividad Empresarial'), ('pf_profesional', 'Persona Física - Servicios Profesionales'), ('pf_plataformas', 'Persona Física - Plataformas Digitales'), ('pf_resico', 'Persona Física - RESICO'), ('pf_arrendamiento', 'Persona Física - Arrendamiento'), ('otro', 'Otro')], max_length=20, null=True)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('activo', models.BooleanField(default=True)),
                ('orden', models.PositiveIntegerField(default=0)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Plantilla de Catálogo',
                'verbose_name_plural': 'Plantillas de Catálogo',
                'ordering': ['orden', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='CatalogoPlantillaCuenta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cuenta', models.CharField(max_length=20)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('nivel1', models.IntegerField(blank=True, null=True)),
                ('nivel2', models.IntegerField(blank=True, null=True)),
                ('nivel3', models.IntegerField(blank=True, null=True)),
                ('nivel4', models.IntegerField(blank=True, null=True)),
                ('orden', models.PositiveIntegerField(default=0)),
                ('es_recomendada', models.BooleanField(default=True)),
                ('activa', models.BooleanField(default=True)),
                ('codigoagrupador', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, to='catalogo.codigoagrupador')),
                ('plantilla', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cuentas', to='catalogo.catalogoplantilla')),
            ],
            options={
                'verbose_name': 'Cuenta de Plantilla',
                'verbose_name_plural': 'Cuentas de Plantilla',
                'ordering': ['orden', 'cuenta'],
                'unique_together': {('plantilla', 'cuenta')},
            },
        ),
    ]