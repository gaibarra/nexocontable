# Generated manually to realign PostgreSQL sequences after data seeding.

from django.db import migrations


def realinear_secuencias(apps, schema_editor):
    tables = [
        'catalogo_catalogocuentas',
        'catalogo_catalogoplantilla',
        'catalogo_catalogoplantillacuenta',
    ]

    with schema_editor.connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
            max_id = cursor.fetchone()[0] or 0

            cursor.execute(f"SELECT pg_get_serial_sequence('{table}', 'id')")
            sequence_name = cursor.fetchone()[0]

            if sequence_name:
                cursor.execute(f"SELECT setval(%s, %s, true)", [sequence_name, max_id])


def revertir_secuencias(apps, schema_editor):
    # No se revierte: realinear secuencias es una operación de mantenimiento segura.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0007_alter_catalogoplantilla_id_and_more'),
    ]

    operations = [
        migrations.RunPython(realinear_secuencias, revertir_secuencias),
    ]
