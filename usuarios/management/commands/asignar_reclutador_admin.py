from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Asigna un reclutador al grupo ReclutadorAdmin'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email del usuario reclutador')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            # Buscar el usuario
            usuario = Usuario.objects.get(email=email)
            
            # Verificar que sea reclutador
            if usuario.rol != 'reclutador':
                self.stdout.write(
                    self.style.ERROR(f'El usuario {email} no es un reclutador.')
                )
                return
            
            # Verificar que tenga perfil de reclutador
            if not hasattr(usuario, 'reclutador'):
                self.stdout.write(
                    self.style.ERROR(f'El usuario {email} no tiene perfil de reclutador.')
                )
                return
            
            # Obtener el grupo ReclutadorAdmin
            try:
                grupo = Group.objects.get(name='ReclutadorAdmin')
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('El grupo ReclutadorAdmin no existe. Ejecuta primero: python manage.py crear_grupo_reclutador_admin')
                )
                return
            
            # Agregar al grupo
            usuario.groups.add(grupo)
            
            self.stdout.write(
                self.style.SUCCESS(f'Usuario {email} agregado exitosamente al grupo ReclutadorAdmin.')
            )
            
            # Mostrar información del usuario
            reclutador = usuario.reclutador
            self.stdout.write(
                f'\nInformación del usuario:'
                f'\n  - Nombre: {reclutador.nombre_completo}'
                f'\n  - Secretaría: {reclutador.secretaria.nombre}'
                f'\n  - Aprobado: {"Sí" if reclutador.aprobado else "No"}'
                f'\n  - Grupos: {", ".join([g.name for g in usuario.groups.all()])}'
            )
            
        except Usuario.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'No se encontró un usuario con email: {email}')
            )