from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Lista todos los usuarios del grupo ReclutadorAdmin'

    def handle(self, *args, **options):
        try:
            # Obtener el grupo ReclutadorAdmin
            grupo = Group.objects.get(name='ReclutadorAdmin')
            
            # Obtener todos los usuarios del grupo
            usuarios_admin = Usuario.objects.filter(groups=grupo).select_related('reclutador__secretaria')
            
            if not usuarios_admin.exists():
                self.stdout.write(
                    self.style.WARNING('No hay usuarios asignados al grupo ReclutadorAdmin.')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(f'Usuarios en el grupo ReclutadorAdmin ({usuarios_admin.count()}):')
            )
            self.stdout.write('')
            
            for usuario in usuarios_admin:
                if hasattr(usuario, 'reclutador'):
                    reclutador = usuario.reclutador
                    estado = "✅ Aprobado" if reclutador.aprobado else "❌ No aprobado"
                    activo = "✅ Activo" if usuario.is_active else "❌ Inactivo"
                    
                    self.stdout.write(
                        f'📧 {usuario.email}'
                        f'\n   👤 {reclutador.nombre_completo}'
                        f'\n   🏢 {reclutador.secretaria.nombre}'
                        f'\n   📊 {estado} | {activo}'
                        f'\n   📅 Registrado: {usuario.date_joined.strftime("%d/%m/%Y")}'
                        f'\n'
                    )
                else:
                    self.stdout.write(
                        f'📧 {usuario.email} (Sin perfil de reclutador - ERROR)'
                    )
            
            # Estadísticas
            aprobados = usuarios_admin.filter(reclutador__aprobado=True).count()
            activos = usuarios_admin.filter(is_active=True).count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nEstadísticas:'
                    f'\n  - Total: {usuarios_admin.count()}'
                    f'\n  - Aprobados: {aprobados}'
                    f'\n  - Activos: {activos}'
                )
            )
            
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('El grupo ReclutadorAdmin no existe. Ejecuta primero: python manage.py crear_grupo_reclutador_admin')
            )