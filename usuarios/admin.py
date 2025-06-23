# usuarios/admin.py - SECCIÓN ACTUALIZADA
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Usuario, Interesado, Reclutador, Secretaria, Categoria, Vacante, RequisitoVacante, Postulacion


class InteresadoInline(admin.StackedInline):
    model = Interesado
    can_delete = False
    verbose_name_plural = 'Información de Interesado'


class ReclutadorInline(admin.StackedInline):
    model = Reclutador
    can_delete = False
    verbose_name_plural = 'Información de Reclutador'


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Extras'), {'fields': ('rol', 'activo')}),
        (_('Email Verification'), {
            'fields': ('email_verified', 'verification_token', 'verification_token_expires'),
            'classes': ('collapse',),
        }),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2', 'rol'),
            },
        ),
    )

    # Configuración de la lista
    list_display = (
        'email', 'first_name', 'last_name', 'rol',
        'email_verified_display', 'is_staff', 'activo', 'date_joined'
    )
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'rol',
        'email_verified', 'groups', 'date_joined'
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)
    readonly_fields = ('verification_token', 'verification_token_expires')

    def email_verified_display(self, obj):
        """Muestra el estado de verificación de email con colores."""
        if obj.email_verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Verificado</span>'
            )
        else:
            # Verificar si tiene token expirado
            if obj.verification_token_expires and obj.verification_token_expires < timezone.now():
                return format_html(
                    '<span style="color: red; font-weight: bold;">✗ Token Expirado</span>'
                )
            elif obj.verification_token:
                return format_html(
                    '<span style="color: orange; font-weight: bold;">⏳ Pendiente</span>'
                )
            else:
                return format_html(
                    '<span style="color: red; font-weight: bold;">✗ No Verificado</span>'
                )

    email_verified_display.short_description = 'Email Verificado'
    email_verified_display.admin_order_field = 'email_verified'

    def get_inlines(self, request, obj=None):
        if obj:
            if obj.rol == 'interesado':
                return [InteresadoInline]
            elif obj.rol == 'reclutador':
                return [ReclutadorInline]
        return []

    actions = ['marcar_email_verificado', 'limpiar_tokens_expirados']

    def marcar_email_verificado(self, request, queryset):
        """Acción para marcar emails como verificados manualmente."""
        updated = queryset.update(
            email_verified=True,
            verification_token=None,
            verification_token_expires=None
        )
        self.message_user(request, f'{updated} usuarios marcados como verificados.')

    marcar_email_verificado.short_description = "Marcar emails como verificados"

    def limpiar_tokens_expirados(self, request, queryset):
        """Acción para limpiar tokens expirados."""
        tokens_expirados = queryset.filter(
            verification_token__isnull=False,
            verification_token_expires__lt=timezone.now()
        )
        updated = tokens_expirados.update(
            verification_token=None,
            verification_token_expires=None
        )
        self.message_user(request, f'{updated} tokens expirados limpiados.')

    limpiar_tokens_expirados.short_description = "Limpiar tokens expirados"


# Resto de los modelos admin permanecen igual...
@admin.register(Secretaria)
class SecretariaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rfc', 'activa', 'fecha_registro')
    list_filter = ('activa',)
    search_fields = ('nombre', 'rfc')
    date_hierarchy = 'fecha_registro'


@admin.register(Interesado)
class InteresadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido_paterno', 'apellido_materno', 'usuario', 'telefono', 'municipio')
    list_filter = ('municipio',)
    search_fields = ('nombre', 'apellido_paterno', 'apellido_materno', 'usuario__email')

    def nombre_completo(self, obj):
        return obj.nombre_completo

    nombre_completo.short_description = 'Nombre Completo'


@admin.register(Reclutador)
class ReclutadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido_paterno', 'apellido_materno', 'secretaria', 'cargo', 'aprobado')
    list_filter = ('aprobado', 'secretaria')
    search_fields = ('nombre', 'apellido_paterno', 'apellido_materno', 'usuario__email', 'secretaria__nombre')
    list_editable = ('aprobado',)

    def nombre_completo(self, obj):
        return obj.nombre_completo

    nombre_completo.short_description = 'Nombre Completo'


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


class RequisitoVacanteInline(admin.StackedInline):
    model = RequisitoVacante
    can_delete = False
    verbose_name_plural = 'Requisitos de la Vacante'


@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = (
        'titulo', 'secretaria', 'reclutador', 'categoria',
        'estado_vacante', 'tipo_empleo', 'fecha_publicacion', 'fecha_limite', 'municipio'
    )
    list_filter = (
        'estado_vacante', 'tipo_empleo', 'modalidad', 'categoria',
        'secretaria', 'aprobada', 'destacada', 'municipio'
    )
    search_fields = ('titulo', 'descripcion', 'reclutador__nombre', 'secretaria__nombre')
    date_hierarchy = 'fecha_publicacion'
    readonly_fields = ('fecha_publicacion', 'fecha_actualizacion')
    inlines = [RequisitoVacanteInline]


# usuarios/admin.py - SECCIÓN ACTUALIZADA PARA RequisitoVacante

@admin.register(RequisitoVacante)
class RequisitoVacanteAdmin(admin.ModelAdmin):
    list_display = ('vacante', 'educacion_minima', 'experiencia_display', 'fecha_vacante')
    list_filter = ('experiencia_minima', 'vacante__categoria')
    search_fields = ('vacante__titulo', 'descripcion_requisitos', 'educacion_minima')
    readonly_fields = ('fecha_vacante',)

    def experiencia_display(self, obj):
        """Muestra la experiencia de forma más clara."""
        return obj.experiencia_display

    experiencia_display.short_description = 'Experiencia Mínima'
    experiencia_display.admin_order_field = 'experiencia_minima'

    def fecha_vacante(self, obj):
        """Muestra la fecha de publicación de la vacante."""
        return obj.vacante.fecha_publicacion.strftime("%d/%m/%Y")

    fecha_vacante.short_description = 'Fecha de Vacante'
    fecha_vacante.admin_order_field = 'vacante__fecha_publicacion'


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = ('interesado', 'vacante', 'estado', 'fecha_postulacion')
    list_filter = ('estado', 'fecha_postulacion', 'vacante__categoria')
    search_fields = ('interesado__nombre', 'interesado__apellido_paterno', 'vacante__titulo')
    readonly_fields = ('fecha_postulacion', 'fecha_actualizacion')