# usuarios/management/commands/crear_secretaria_movilidad.py
from django.core.management.base import BaseCommand
from usuarios.models import Secretaria


class Command(BaseCommand):
    help = 'Crea la Secretaría de Movilidad como organización principal (ID=1)'

    def handle(self, *args, **options):
        """Crea o actualiza la Secretaría de Movilidad del Estado de México."""

        try:
            # Intentar obtener la secretaría con ID=1
            secretaria, created = Secretaria.objects.get_or_create(
                id=1,
                defaults={
                    'nombre': 'Secretaría de Movilidad del Estado de México',
                    'rfc': 'GEM850101BJ3',  # Ajustar con el RFC real
                    'descripcion': 'Secretaría responsable de la movilidad y transporte en el Estado de México.',
                    'sitio_web': 'https://smovilidad.edomex.gob.mx/',
                    'direccion': 'Av. Gustavo Baz #2160, La Loma, 54060 Tlalnepantla de Baz, Estado de México',
                    'activa': True,
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Secretaría de Movilidad creada exitosamente con ID: {secretaria.id}'
                    )
                )
                self.stdout.write(f'   Nombre: {secretaria.nombre}')
                self.stdout.write(f'   RFC: {secretaria.rfc}')
                self.stdout.write(f'   Sitio web: {secretaria.sitio_web}')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ La Secretaría de Movilidad ya existe con ID: {secretaria.id}'
                    )
                )
                self.stdout.write(f'   Nombre actual: {secretaria.nombre}')

                # Preguntar si quiere actualizar los datos
                actualizar = input('¿Deseas actualizar los datos de la secretaría? (s/n): ')
                if actualizar.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                    secretaria.nombre = 'Secretaría de Movilidad del Estado de México'
                    secretaria.descripcion = 'Secretaría responsable de la movilidad y transporte en el Estado de México.'
                    secretaria.sitio_web = 'https://smovilidad.edomex.gob.mx/'
                    secretaria.direccion = 'Av. Gustavo Baz #2160, La Loma, 54060 Tlalnepantla de Baz, Estado de México'
                    secretaria.activa = True
                    secretaria.save()

                    self.stdout.write(
                        self.style.SUCCESS('✅ Datos de la Secretaría de Movilidad actualizados exitosamente.')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear/actualizar la Secretaría de Movilidad: {str(e)}')
            )

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('INSTRUCCIONES ADICIONALES:')
        self.stdout.write('1. Verifica que el RFC sea correcto')
        self.stdout.write('2. Actualiza la dirección web si es necesario')
        self.stdout.write('3. Todos los reclutadores se registrarán bajo esta secretaría')
        self.stdout.write('=' * 50)

        # marcoanvazquezd@gmail.com