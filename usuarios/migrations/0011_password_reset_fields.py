# usuarios/migrations/0002_add_password_reset_fields.py
# CREAR ESTE ARCHIVO EN LA CARPETA usuarios/migrations/

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),  # Ajusta según tu migración anterior
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='password_reset_token',
            field=models.CharField(
                blank=True, 
                help_text='Token para recuperación de contraseña', 
                max_length=100, 
                null=True
            ),
        ),
        migrations.AddField(
            model_name='usuario',
            name='password_reset_token_expires',
            field=models.DateTimeField(
                blank=True, 
                help_text='Fecha de expiración del token de recuperación', 
                null=True
            ),
        ),
        migrations.AddField(
            model_name='usuario',
            name='password_reset_attempts',
            field=models.IntegerField(
                default=0, 
                help_text='Número de intentos de recuperación en las últimas 24 horas'
            ),
        ),
        migrations.AddField(
            model_name='usuario',
            name='last_password_reset_attempt',
            field=models.DateTimeField(
                blank=True, 
                help_text='Fecha del último intento de recuperación', 
                null=True
            ),
        ),
    ]