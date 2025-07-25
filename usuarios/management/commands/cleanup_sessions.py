# usuarios/management/commands/cleanup_sessions.py
# CREAR ESTA ESTRUCTURA DE CARPETAS:
# usuarios/
#   management/
#     __init__.py
#     commands/
#       __init__.py
#       cleanup_sessions.py

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Limpia sesiones expiradas y tokens de recuperación antiguos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Eliminar sesiones más antiguas que X días (por defecto: 7)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se eliminaría sin hacer cambios'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Fecha límite
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Limpiando sesiones anteriores a: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}'
            )
        )

        # Limpiar sesiones expiradas
        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
        expired_count = expired_sessions.count()
        
        if not dry_run:
            expired_sessions.delete()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Eliminadas {expired_count} sesiones expiradas')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'🔍 Se eliminarían {expired_count} sesiones expiradas')
            )

        # Limpiar sesiones antiguas (no expiradas pero muy viejas)
        old_sessions = Session.objects.filter(expire_date__lt=cutoff_date)
        old_count = old_sessions.count()
        
        if not dry_run:
            old_sessions.delete()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Eliminadas {old_count} sesiones antiguas')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'🔍 Se eliminarían {old_count} sesiones antiguas')
            )

        # Limpiar tokens de recuperación expirados (de la implementación anterior)
        try:
            from usuarios.models import Usuario
            
            # Tokens de verificación expirados
            expired_verification = Usuario.objects.filter(
                verification_token_expires__lt=timezone.now(),
                verification_token__isnull=False
            )
            verification_count = expired_verification.count()
            
            if not dry_run:
                expired_verification.update(
                    verification_token=None,
                    verification_token_expires=None
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Limpiados {verification_count} tokens de verificación expirados')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'🔍 Se limpiarían {verification_count} tokens de verificación')
                )

            # Tokens de recuperación de contraseña expirados
            expired_reset = Usuario.objects.filter(
                password_reset_token_expires__lt=timezone.now(),
                password_reset_token__isnull=False
            )
            reset_count = expired_reset.count()
            
            if not dry_run:
                expired_reset.update(
                    password_reset_token=None,
                    password_reset_token_expires=None
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Limpiados {reset_count} tokens de recuperación expirados')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'🔍 Se limpiarían {reset_count} tokens de recuperación')
                )

            # Reiniciar contadores de intentos antiguos (más de 24 horas)
            old_attempts = Usuario.objects.filter(
                last_password_reset_attempt__lt=timezone.now() - timedelta(hours=24),
                password_reset_attempts__gt=0
            )
            attempts_count = old_attempts.count()
            
            if not dry_run:
                old_attempts.update(password_reset_attempts=0)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Reiniciados {attempts_count} contadores de intentos')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'🔍 Se reiniciarían {attempts_count} contadores de intentos')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al limpiar tokens de usuario: {str(e)}')
            )

        # Resumen final
        total_cleaned = expired_count + old_count + verification_count + reset_count + attempts_count
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Limpieza completada exitosamente. Total de elementos limpiados: {total_cleaned}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'\n🔍 Simulación completada. Total de elementos a limpiar: {total_cleaned}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    'Para ejecutar la limpieza real, ejecuta el comando sin --dry-run'
                )
            )