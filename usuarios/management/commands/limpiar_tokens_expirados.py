# usuarios/management/commands/limpiar_tokens_expirados.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Limpia tokens de verificación de email expirados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué tokens se limpiarían sin ejecutar la limpieza',
        )

    def handle(self, *args, **options):
        # Encontrar usuarios con tokens expirados
        usuarios_con_tokens_expirados = Usuario.objects.filter(
            verification_token__isnull=False,
            verification_token_expires__lt=timezone.now()
        )

        count = usuarios_con_tokens_expirados.count()

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Se limpiarían {count} tokens expirados')
            )
            for usuario in usuarios_con_tokens_expirados:
                self.stdout.write(f'  - {usuario.email} (expiró: {usuario.verification_token_expires})')
        else:
            # Limpiar los tokens expirados
            usuarios_con_tokens_expirados.update(
                verification_token=None,
                verification_token_expires=None
            )

            self.stdout.write(
                self.style.SUCCESS(f'Limpiados {count} tokens expirados exitosamente')
            )


