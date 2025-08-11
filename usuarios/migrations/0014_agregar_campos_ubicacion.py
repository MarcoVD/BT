# Crear archivo: usuarios/migrations/0002_agregar_campos_ubicacion.py

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0013_alter_vacante_fecha_limite'),  # Ajustar según tu migración anterior
    ]

    operations = [
        # Agregar nuevos campos de ubicación detallada
        migrations.AddField(
            model_name='interesado',
            name='estado_id',
            field=models.IntegerField(blank=True, null=True, help_text="ID del estado desde catálogo"),
        ),
        migrations.AddField(
            model_name='interesado',
            name='municipio_id',
            field=models.IntegerField(blank=True, null=True, help_text="ID del municipio desde catálogo"),
        ),
        migrations.AddField(
            model_name='interesado',
            name='localidad_id',
            field=models.IntegerField(blank=True, null=True, help_text="ID de la localidad desde catálogo"),
        ),
        migrations.AddField(
            model_name='interesado',
            name='calle_numero',
            field=models.CharField(max_length=200, blank=True, null=True, verbose_name="Calle y número"),
        ),

        # Campos para almacenar nombres legibles
        migrations.AddField(
            model_name='interesado',
            name='estado_nombre',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='interesado',
            name='municipio_nombre',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='interesado',
            name='localidad_nombre',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
    ]