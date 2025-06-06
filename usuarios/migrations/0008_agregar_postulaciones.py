# usuarios/migrations/0008_agregar_postulaciones.py
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0007_eliminar_campo_direccion'),
    ]

    operations = [
        migrations.CreateModel(
            name='Postulacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_postulacion', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(choices=[('enviada', 'Enviada'), ('en_revision', 'En Revisión'), ('preseleccionado', 'Preseleccionado'), ('entrevista', 'En Entrevista'), ('aceptada', 'Aceptada'), ('rechazada', 'Rechazada')], default='enviada', max_length=20)),
                ('mensaje_motivacion', models.TextField(blank=True, help_text='Mensaje opcional del candidato', null=True)),
                ('notas_reclutador', models.TextField(blank=True, help_text='Notas del reclutador', null=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('curriculum', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='postulaciones', to='usuarios.curriculum')),
                ('interesado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='postulaciones', to='usuarios.interesado')),
                ('vacante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='postulaciones', to='usuarios.vacante')),
            ],
            options={
                'verbose_name': 'Postulación',
                'verbose_name_plural': 'Postulaciones',
                'ordering': ['-fecha_postulacion'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='postulacion',
            unique_together={('interesado', 'vacante')},
        ),
    ]