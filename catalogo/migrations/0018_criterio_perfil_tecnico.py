from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalogo', '0017_historial_reformulacion')]
    operations = [migrations.AddField(
        model_name='criteriorevisado', name='perfil_tecnico',
        field=models.CharField(blank=True, default='', max_length=40, db_index=True),
    )]
