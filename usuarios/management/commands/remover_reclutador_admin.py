from django.contrib.auth.models import Group


def es_reclutador_admin(usuario):
    """
    Verifica si un usuario pertenece al grupo ReclutadorAdmin.
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.rol != 'reclutador':
        return False
    
    return usuario.groups.filter(name='ReclutadorAdmin').exists()


def puede_ver_todas_las_vacantes(usuario):
    """
    Verifica si un usuario puede ver todas las vacantes (no solo las suyas).
    """
    return es_reclutador_admin(usuario) or usuario.is_superuser


def puede_editar_vacante(usuario, vacante):
    """
    Verifica si un usuario puede editar una vacante específica.
    
    Un usuario puede editar una vacante si:
    - Es el reclutador propietario de la vacante
    - Es un ReclutadorAdmin
    - Es un superusuario
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    if usuario.rol == 'reclutador':
        # Si es el reclutador propietario
        if hasattr(usuario, 'reclutador') and vacante.reclutador == usuario.reclutador:
            return True
        
        # Si es ReclutadorAdmin
        if es_reclutador_admin(usuario):
            return True
    
    return False


def filtrar_vacantes_por_permisos(usuario, queryset):
    """
    Filtra un queryset de vacantes según los permisos del usuario.
    
    - ReclutadorAdmin: Ve todas las vacantes
    - Reclutador normal: Solo ve sus propias vacantes
    """
    if not usuario.is_authenticated:
        return queryset.none()
    
    if usuario.is_superuser:
        return queryset
    
    if usuario.rol == 'reclutador':
        if es_reclutador_admin(usuario):
            # ReclutadorAdmin ve todas las vacantes
            return queryset
        elif hasattr(usuario, 'reclutador'):
            # Reclutador normal solo ve sus vacantes
            return queryset.filter(reclutador=usuario.reclutador)
    
    return queryset.none()


def obtener_vacantes_editables(usuario):
    """
    Obtiene todas las vacantes que el usuario puede editar.
    """
    from .models import Vacante
    
    if not usuario.is_authenticated:
        return Vacante.objects.none()
    
    if usuario.is_superuser:
        return Vacante.objects.all()
    
    if usuario.rol == 'reclutador':
        if es_reclutador_admin(usuario):
            # ReclutadorAdmin puede editar todas las vacantes
            return Vacante.objects.all()
        elif hasattr(usuario, 'reclutador'):
            # Reclutador normal solo puede editar sus vacantes
            return Vacante.objects.filter(reclutador=usuario.reclutador)
    
    return Vacante.objects.none()