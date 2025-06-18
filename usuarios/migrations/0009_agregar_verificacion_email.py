from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0008_agregar_postulaciones'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='email_verified',
            field=models.BooleanField(default=False, help_text='Indica si el email ha sido verificado'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='verification_token',
            field=models.UUIDField(blank=True, null=True, help_text='Token para verificación de email'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='verification_token_expires',
            field=models.DateTimeField(blank=True, null=True, help_text='Fecha de expiración del token'),
        ),
    ]