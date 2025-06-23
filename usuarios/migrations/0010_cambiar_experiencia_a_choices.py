from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0009_agregar_verificacion_email'),
    ]

    operations = [
        # Cambiar el campo experiencia_minima a choices
        migrations.AlterField(
            model_name='requisitovacante',
            name='experiencia_minima',
            field=models.CharField(
                blank=True,
                choices=[
                    ('0', 'Sin experiencia requerida'),
                    ('1', '1 año'),
                    ('2', '2 años'),
                    ('3', '3 años'),
                    ('4', '4 años'),
                    ('5', '5 años'),
                    ('6', '6 años'),
                    ('7', '7 años'),
                    ('8', '8 años'),
                    ('9', '9 años'),
                    ('10', '10 años'),
                    ('10+', 'Más de 10 años'),
                ],
                max_length=10,
                null=True,
                verbose_name='Años de experiencia mínima'
            ),
        ),
    ]