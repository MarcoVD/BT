from django.core.management.base import BaseCommand
from django.utils import timezone
from usuarios.models import Vacante


class Command(BaseCommand):
    help = 'Cierra automáticamente las vacantes que han llegado a su fecha límite'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué vacantes se cerrarían sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        hoy = timezone.now().date()
        
        # Buscar vacantes publicadas que han llegado a su fecha límite
        vacantes_vencidas = Vacante.objects.filter(
            estado_vacante='publicada',
            fecha_limite__lt=hoy
        )

        if not vacantes_vencidas.exists():
            self.stdout.write(
                self.style.SUCCESS('No se encontraron vacantes vencidas para cerrar.')
            )
            return

        count = vacantes_vencidas.count()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Se cerrarían {count} vacante(s):')
            )
            for vacante in vacantes_vencidas:
                self.stdout.write(
                    f'  - ID {vacante.id}: {vacante.titulo} (vencida: {vacante.fecha_limite})'
                )
        else:
            # Cerrar las vacantes vencidas
            vacantes_cerradas = Vacante.cerrar_vacantes_vencidas()
            
            if vacantes_cerradas > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Se cerraron exitosamente {vacantes_cerradas} vacante(s) vencida(s).'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No se pudieron cerrar las vacantes vencidas.')
                )