from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from usuarios.models import Vacante, RequisitoVacante


class Command(BaseCommand):
    help = 'Crea el grupo ReclutadorAdmin con permisos CRUD para todas las vacantes'

    def handle(self, *args, **options):
        # Crear o obtener el grupo ReclutadorAdmin
        grupo, created = Group.objects.get_or_create(name='ReclutadorAdmin')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Grupo "{grupo.name}" creado exitosamente.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'El grupo "{grupo.name}" ya existe.')
            )

        # Obtener permisos para el modelo Vacante
        content_type_vacante = ContentType.objects.get_for_model(Vacante)
        permisos_vacante = Permission.objects.filter(content_type=content_type_vacante)
        
        # Obtener permisos para el modelo RequisitoVacante
        content_type_requisito = ContentType.objects.get_for_model(RequisitoVacante)
        permisos_requisito = Permission.objects.filter(content_type=content_type_requisito)
        
        # Agregar todos los permisos al grupo
        todos_los_permisos = list(permisos_vacante) + list(permisos_requisito)
        grupo.permissions.set(todos_los_permisos)
        
        self.stdout.write(
            self.style.SUCCESS(f'Se agregaron {len(todos_los_permisos)} permisos al grupo.')
        )
        
        # Mostrar los permisos agregados
        self.stdout.write('\nPermisos asignados al grupo ReclutadorAdmin:')
        for permiso in todos_los_permisos:
            self.stdout.write(f'  - {permiso.name}')
        
        self.stdout.write(
            self.style.SUCCESS('\nConfiguración del grupo ReclutadorAdmin completada.')
        )