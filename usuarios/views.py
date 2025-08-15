import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.generic import View
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse, Http404
from django.template.loader import render_to_string
from django.forms import modelformset_factory
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from datetime import timedelta, date
# Verificacion de correo - IMPORTACIONES CORREGIDAS
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.contrib.sites.shortcuts import get_current_site  # AGREGADO
from django.urls import reverse
from django.conf import settings
import logging
import base64   #NECESARIO PARA PODER MANEJAR IMAGENES (DESCARGAR EL CV CON IMAGENES)

Usuario = get_user_model()
# CONFIGURAR LOGGER
logger = logging.getLogger(__name__)

# Importaciones para manejo de archivos e imágenes
from weasyprint import HTML
from io import BytesIO
from PIL import Image
import io
import os
import uuid

# Importaciones de modelos locales - ORGANIZADAS Y COMPLETAS
from .models import (
    # Modelos de usuarios
    Usuario,
    Interesado,
    Reclutador,
    Secretaria,

    # Modelos de CV y curriculum
    Curriculum,
    ExperienciaLaboral,
    Educacion,
    Habilidad,  # ← MODELO PRINCIPAL DE HABILIDADES
    HabilidadInteresado,  # ← RELACIÓN MANY-TO-MANY CON NIVEL
    IdiomaInteresado,

    # Modelos de vacantes y postulaciones
    Vacante,
    RequisitoVacante,
    Postulacion
)
# Importar utilidades de permisos
from .utils import (
    es_reclutador_admin,
    puede_ver_todas_las_vacantes,
    puede_editar_vacante,
    filtrar_vacantes_por_permisos,
    obtener_vacantes_editables
)
# Importaciones de formularios locales
from .forms import (
    LoginForm,
    InteresadoRegistroForm,
    ReclutadorRegistroForm,
    VacanteForm,
    RequisitoVacanteForm,
    CurriculumForm,
    InteresadoPerfilForm,
    ExperienciaLaboralForm,
    EducacionForm,
    IdiomaInteresadoForm,
    RecuperarContrasenaForm, 
    RestablecerContrasenaForm, 
    ReenviarRecuperacionForm
)

@login_required
@require_http_methods(["POST"])
def extend_session_ajax(request):
    """
    Vista AJAX para extender la sesión del usuario activo.
    """
    try:
        # Validar que la petición sea AJAX con contenido JSON
        if not request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'Petición inválida'
            }, status=400)

        # Parsear datos JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Datos JSON inválidos'
            }, status=400)

        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Usuario no autenticado'
            }, status=401)

        # Extender la sesión
        request.session.modified = True
        
        # Opcional: Actualizar última actividad en el modelo de usuario
        try:
            request.user.ultimo_acceso = timezone.now()
            request.user.save(update_fields=['ultimo_acceso'])
        except Exception as e:
            # Log el error pero no fallar la petición
            logger.warning(f"No se pudo actualizar ultimo_acceso para usuario {request.user.id}: {e}")

        # Log de la acción
        logger.info(f"Sesión extendida para usuario {request.user.email} ({request.user.id})")

        return JsonResponse({
            'success': True,
            'message': 'Sesión extendida exitosamente',
            'timestamp': timezone.now().isoformat(),
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'rol': request.user.rol
            }
        })

    except Exception as e:
        logger.error(f"Error en extend_session_ajax: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@login_required
def session_status_ajax(request):
    """
    Vista AJAX para verificar el estado de la sesión.
    Útil para verificar si la sesión sigue activa.
    """
    try:
        # Información básica de la sesión
        session_info = {
            'authenticated': request.user.is_authenticated,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'session_key': request.session.session_key,
            'session_age': request.session.get_expiry_age(),  # Segundos hasta expiración
            'session_expires_at': request.session.get_expiry_date().isoformat() if hasattr(request.session, 'get_expiry_date') else None,
            'timestamp': timezone.now().isoformat()
        }

        # Si el usuario está autenticado, agregar más información
        if request.user.is_authenticated:
            session_info.update({
                'user': {
                    'email': request.user.email,
                    'rol': request.user.rol,
                    'ultimo_acceso': request.user.ultimo_acceso.isoformat() if request.user.ultimo_acceso else None,
                    'fecha_registro': request.user.fecha_registro.isoformat() if hasattr(request.user, 'fecha_registro') else None
                }
            })

        return JsonResponse({
            'success': True,
            'session': session_info
        })

    except Exception as e:
        logger.error(f"Error en session_status_ajax: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener estado de sesión'
        }, status=500)


# Opcional: Middleware personalizado para timeout de sesión
class SessionTimeoutMiddleware:
    """
    Middleware para manejar timeout de sesión a nivel del servidor.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Timeout en segundos (15 minutos = 900 segundos)
        self.session_timeout = 900

    def __call__(self, request):
        # Procesar la petición antes de la vista
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            now = timezone.now().timestamp()

            if last_activity:
                # Verificar si ha pasado el tiempo límite
                if now - last_activity > self.session_timeout:
                    # Cerrar sesión automáticamente
                    from django.contrib.auth import logout
                    logout(request)
                    logger.info(f"Sesión cerrada automáticamente por timeout para usuario {request.user.email}")
                    
                    # Si es petición AJAX, devolver respuesta JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'Sesión expirada',
                            'redirect': '/login/'
                        }, status=401)

            # Actualizar última actividad
            request.session['last_activity'] = now

        response = self.get_response(request)
        return response



@login_required
def agregar_habilidad_ajax(request):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido. Solo se acepta POST.'
        })

    if request.user.rol != 'interesado':
        return JsonResponse({
            'success': False,
            'error': 'Solo los interesados pueden agregar habilidades.'
        })

    try:
        # Obtener el curriculum del interesado
        interesado = request.user.interesado

        # Verificar que existe el curriculum
        if not hasattr(interesado, 'curriculum'):
            return JsonResponse({
                'success': False,
                'error': 'Primero debes crear tu curriculum.'
            })

        curriculum = interesado.curriculum

        # Obtener datos del formulario
        nombre_habilidad = request.POST.get('nombre_habilidad', '').strip()
        nivel = request.POST.get('nivel', '').strip()

        # Validar datos requeridos
        if not nombre_habilidad:
            return JsonResponse({
                'success': False,
                'error': 'El nombre de la habilidad es requerido.'
            })

        if not nivel:
            return JsonResponse({
                'success': False,
                'error': 'El nivel de dominio es requerido.'
            })

        # Validar que el nivel sea válido
        niveles_validos = ['basico', 'intermedio', 'avanzado', 'experto']
        if nivel not in niveles_validos:
            return JsonResponse({
                'success': False,
                'error': f'Nivel no válido. Debe ser uno de: {", ".join(niveles_validos)}'
            })

        # Verificar si la habilidad ya existe para este curriculum
        habilidad_existente = HabilidadInteresado.objects.filter(
            curriculum=curriculum,
            habilidad__nombre=nombre_habilidad
        ).first()

        if habilidad_existente:
            return JsonResponse({
                'success': False,
                'error': f'Ya tienes registrada la habilidad "{nombre_habilidad}". Puedes editarla desde la lista.'
            })

        # Obtener o crear la habilidad en el catálogo general
        habilidad_catalogo, created = Habilidad.objects.get_or_create(
            nombre=nombre_habilidad,
            defaults={
                'descripcion': f'{nombre_habilidad}'
            }
        )

        # Crear la relación entre el curriculum y la habilidad con su nivel
        habilidad_interesado = HabilidadInteresado.objects.create(
            curriculum=curriculum,
            habilidad=habilidad_catalogo,
            nivel=nivel
        )

        # Preparar respuesta exitosa
        return JsonResponse({
            'success': True,
            'message': f'Habilidad "{nombre_habilidad}" agregada exitosamente.',
            'habilidad': {
                'id': habilidad_interesado.id,
                'nombre': habilidad_catalogo.nombre,
                'nivel': habilidad_interesado.get_nivel_display(),
                'nivel_codigo': habilidad_interesado.nivel
            }
        })

    except Exception as e:
        # Log del error para debugging (en producción usar logging)
        print(f"Error en agregar_habilidad_ajax: {str(e)}")

        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        })


@login_required
def eliminar_habilidad_ajax(request, habilidad_id):
    """
    Vista AJAX para eliminar una habilidad del CV del interesado.

    Args:
        habilidad_id: ID de la HabilidadInteresado a eliminar

    Returns:
        JsonResponse con success/error
    """

    # Validar método y permisos
    if request.method != 'DELETE':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido. Solo se acepta DELETE.'
        })

    if request.user.rol != 'interesado':
        return JsonResponse({
            'success': False,
            'error': 'Solo los interesados pueden eliminar habilidades.'
        })

    try:
        # Obtener el curriculum del interesado
        interesado = request.user.interesado

        if not hasattr(interesado, 'curriculum'):
            return JsonResponse({
                'success': False,
                'error': 'No tienes un curriculum creado.'
            })

        curriculum = interesado.curriculum

        # Buscar la habilidad que pertenece al curriculum del usuario
        habilidad_interesado = get_object_or_404(
            HabilidadInteresado,
            id=habilidad_id,
            curriculum=curriculum
        )

        # Guardar nombre para el mensaje
        nombre_habilidad = habilidad_interesado.habilidad.nombre

        # Eliminar la habilidad
        habilidad_interesado.delete()

        return JsonResponse({
            'success': True,
            'message': f'Habilidad "{nombre_habilidad}" eliminada exitosamente.'
        })

    except Exception as e:
        # Log del error para debugging
        print(f"Error en eliminar_habilidad_ajax: {str(e)}")

        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar la habilidad: {str(e)}'
        })

# =========================================
#funcion que define la recuperacion de contraseña
def send_password_reset_email(request, user):
    """
    Envía el correo de recuperación de contraseña.
    """
    try:
        # Generar token de recuperación
        user.generate_password_reset_token()

        # Obtener el dominio actual
        current_site = get_current_site(request)
        domain = current_site.domain

        # Construir la URL de restablecimiento
        reset_url = request.build_absolute_uri(
            reverse('restablecer_contrasena', kwargs={'token': user.password_reset_token})
        )

        # Preparar el contexto para el template del correo
        context = {
            'user': user,
            'reset_url': reset_url,
            'domain': domain,
            'site_name': 'Bolsa de Trabajo - Estado de México',
            'expires_minutes': 30,
            'attempts_remaining': user.get_remaining_reset_attempts(),
        }

        # Renderizar el contenido del correo
        html_message = render_to_string('emails/recuperar_contrasena_email.html', context)
        plain_message = strip_tags(html_message)

        # Configurar el asunto
        subject = 'Recuperación de Contraseña - Bolsa de Trabajo Estado de México'

        # Enviar el correo
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Correo de recuperación enviado exitosamente a {user.email}")
        return True

    except Exception as e:
        logger.error(f"Error enviando correo de recuperación a {user.email}: {str(e)}")
        print(f"ERROR DETALLADO: {str(e)}")
        return False


class RecuperarContrasenaView(View):
    """
    Vista para solicitar recuperación de contraseña.
    """
    template_name = 'emails/recuperar_contrasena.html'
    form_class = RecuperarContrasenaForm

    def get(self, request):
        """Muestra el formulario de recuperación."""
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Procesa la solicitud de recuperación."""
        form = self.form_class(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            user = form.get_user()
            
            # Por seguridad, siempre mostramos mensaje de éxito
            # independientemente de si el email existe o no
            if user:
                try:
                    email_enviado = send_password_reset_email(request, user)
                    
                    if email_enviado:
                        # Mostrar página de éxito
                        context = {
                            'email_enviado': True,
                            'email_destino': email,
                        }
                        return render(request, self.template_name, context)
                    else:
                        messages.error(request, 
                            'Error al enviar el correo. Inténtalo nuevamente en unos minutos.')
                        
                except ValueError as e:
                    # Error por límite de intentos
                    messages.error(request, str(e))
                    
                except Exception as e:
                    logger.error(f"Error en recuperación de contraseña: {str(e)}")
                    messages.error(request, 
                        'Error interno del servidor. Inténtalo nuevamente más tarde.')
            else:
                # Usuario no existe, pero mostramos mensaje genérico por seguridad
                context = {
                    'email_enviado': True,
                    'email_destino': email,
                }
                return render(request, self.template_name, context)

        # Si hay errores en el formulario, volver a mostrarlo
        return render(request, self.template_name, {'form': form})


class RestablecerContrasenaView(View):
    """
    Vista para restablecer la contraseña usando el token.
    """
    template_name = 'emails/restablecer_contrasena.html'
    result_template = 'emails/resultado_restablecimiento.html'

    def get(self, request, token):
        """Muestra el formulario de restablecimiento."""
        try:
            # Buscar usuario con el token
            user = Usuario.objects.filter(password_reset_token=token).first()

            if not user:
                return render(request, self.result_template, {
                    'success': False,
                    'warning': True,
                    'title': 'Token Inválido',
                    'message': 'El enlace de recuperación no es válido.',
                    'show_retry': True,
                })

            # Verificar si el token es válido y no ha expirado
            if not user.is_password_reset_token_valid(token):
                return render(request, self.result_template, {
                    'success': False,
                    'warning': True,
                    'title': 'Enlace Expirado',
                    'message': 'El enlace de recuperación ha expirado. Los enlaces son válidos por 30 minutos.',
                    'show_retry': True,
                })

            # Token válido, mostrar formulario
            form = RestablecerContrasenaForm(user=user)
            return render(request, self.template_name, {
                'form': form,
                'token': token,
                'user': user,
            })

        except Exception as e:
            logger.error(f"Error en restablecimiento de contraseña: {str(e)}")
            return render(request, self.result_template, {
                'success': False,
                'title': 'Error',
                'message': 'Ocurrió un error al procesar tu solicitud. Inténtalo nuevamente.',
                'show_retry': True,
            })

    def post(self, request, token):
        """Procesa el restablecimiento de contraseña."""
        try:
            # Buscar usuario con el token
            user = Usuario.objects.filter(password_reset_token=token).first()

            if not user or not user.is_password_reset_token_valid(token):
                return render(request, self.result_template, {
                    'success': False,
                    'warning': True,
                    'title': 'Token Inválido o Expirado',
                    'message': 'El enlace de recuperación no es válido o ha expirado.',
                    'show_retry': True,
                })

            # Procesar formulario
            form = RestablecerContrasenaForm(user=user, data=request.POST)

            if form.is_valid():
                try:
                    # Guardar nueva contraseña
                    form.save()

                    # Log de la acción
                    logger.info(f"Contraseña restablecida exitosamente para usuario {user.email}")

                    # Mostrar mensaje de éxito
                    return render(request, self.result_template, {
                        'success': True,
                        'title': 'Contraseña Restablecida',
                        'message': 'Tu contraseña ha sido restablecida exitosamente. Ahora puedes iniciar sesión con tu nueva contraseña.',
                    })
                    
                except Exception as save_error:
                    logger.error(f"Error al guardar nueva contraseña para {user.email}: {str(save_error)}")
                    form.add_error('new_password1', 'Error al guardar la nueva contraseña. Inténtalo nuevamente.')

            # Si hay errores en el formulario, volver a mostrarlo
            return render(request, self.template_name, {
                'form': form,
                'token': token,
                'user': user,
            })

        except Exception as e:
            logger.error(f"Error procesando restablecimiento: {str(e)}")
            return render(request, self.result_template, {
                'success': False,
                'title': 'Error',
                'message': 'Ocurrió un error al restablecer tu contraseña. Inténtalo nuevamente.',
                'show_retry': True,
            })


class ReenviarRecuperacionView(View):
    """
    Vista para reenviar el correo de recuperación.
    """
    template_name = 'emails/recuperar_contrasena.html'

    def post(self, request):
        """Reenvía el correo de recuperación."""
        form = ReenviarRecuperacionForm(request.POST)
        
        if form.is_valid():
            user = form.get_user()
            
            if user:
                try:
                    email_enviado = send_password_reset_email(request, user)
                    
                    if email_enviado:
                        messages.success(request, 
                            'Se ha reenviado el correo de recuperación exitosamente.')
                        
                        context = {
                            'email_enviado': True,
                            'email_destino': user.email,
                        }
                        return render(request, self.template_name, context)
                    else:
                        messages.error(request, 
                            'Error al reenviar el correo. Inténtalo nuevamente.')
                        
                except ValueError as e:
                    messages.error(request, str(e))
                except Exception as e:
                    logger.error(f"Error reenviando recuperación: {str(e)}")
                    messages.error(request, 'Error interno del servidor.')
            else:
                messages.error(request, 'Usuario no encontrado.')

        # Redirigir de vuelta al formulario
        return redirect('recuperar_contrasena')
# Función utilitaria para limpiar tokens expirados (opcional, para comando de mantenimiento)
def cleanup_expired_tokens():
    """
    Limpia tokens de recuperación expirados.
    Puede ejecutarse como tarea programada.
    """
    now = timezone.now()
    
    # Limpiar tokens de verificación expirados
    expired_verification = Usuario.objects.filter(
        verification_token_expires__lt=now,
        verification_token__isnull=False
    )
    verification_count = expired_verification.update(
        verification_token=None,
        verification_token_expires=None
    )
    
    # Limpiar tokens de recuperación expirados
    expired_reset = Usuario.objects.filter(
        password_reset_token_expires__lt=now,
        password_reset_token__isnull=False
    )
    reset_count = expired_reset.update(
        password_reset_token=None,
        password_reset_token_expires=None
    )
    
    # Reiniciar contadores de intentos antiguos (más de 24 horas)
    old_attempts = Usuario.objects.filter(
        last_password_reset_attempt__lt=now - timedelta(hours=24),
        password_reset_attempts__gt=0
    )
    attempts_count = old_attempts.update(
        password_reset_attempts=0
    )
    
    logger.info(f"Tokens limpiados: {verification_count} verificación, {reset_count} recuperación, {attempts_count} intentos reiniciados")
    
    return {
        'verification_tokens_cleaned': verification_count,
        'reset_tokens_cleaned': reset_count,
        'attempts_reset': attempts_count
    }
###################################
#FIN DE RECUPERACION DE CONTRASEÑA 
###################################

def send_verification_email(request, user):
    try:
        # Generar token de verificación
        user.generate_verification_token()

        # Obtener el dominio actual
        current_site = get_current_site(request)
        domain = current_site.domain

        # Construir la URL de verificación
        verification_url = request.build_absolute_uri(
            reverse('verificar_email', kwargs={'token': user.verification_token})
        )

        # Preparar el contexto para el template del correo
        context = {
            'user': user,
            'verification_url': verification_url,
            'domain': domain,
            'site_name': 'Bolsa de Trabajo - Estado de México',
            'expires_hours': 24,
        }
        html_message = render_to_string('emails/verificacion_email.html', context)
        plain_message = strip_tags(html_message)

        # Configurar el asunto según el rol
        if user.rol == 'interesado':
            subject = 'Verifica tu cuenta - Bolsa de Trabajo Estado de México'
        else:
            subject = 'Verifica tu cuenta de Reclutador - Bolsa de Trabajo Estado de México'

        # ✅ ENVIAR EL CORREO CON MANEJO DE ERRORES MEJORADO
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,  # ✅ Cambiar a False para ver errores
        )

        logger.info(f"Correo de verificación enviado exitosamente a {user.email}")
        return True

    except Exception as e:
        logger.error(f"Error enviando correo de verificación a {user.email}: {str(e)}")
        print(f"ERROR DETALLADO: {str(e)}")  # ✅ Para debugging
        return False

class VerificarEmailView(View):
    """Vista para verificar el email del usuario mediante token."""

    def get(self, request, token):
        """Procesa la verificación del email."""
        try:
            # Buscar usuario con el token
            user = Usuario.objects.filter(verification_token=token).first()

            if not user:
                messages.error(request, 'Token de verificación inválido.')
                return render(request, 'usuarios/verificacion_resultado.html', {
                    'success': False,
                    'title': 'Token Inválido',
                    'message': 'El enlace de verificación no es válido.',
                })

            # Verificar si el token es válido y no ha expirado
            if not user.is_verification_token_valid(token):
                messages.error(request, 'El token de verificación ha expirado.')
                return render(request, 'usuarios/verificacion_resultado.html', {
                    'success': False,
                    'title': 'Token Expirado',
                    'message': 'El enlace de verificación ha expirado. Puedes solicitar uno nuevo.',
                    'show_resend': True,
                    'user_email': user.email,
                })

            # Verificar el email
            user.verify_email()

            # Mensaje de éxito según el rol
            if user.rol == 'interesado':
                success_message = 'Tu cuenta ha sido verificada exitosamente. Ahora puedes iniciar sesión y comenzar a buscar empleos.'
            elif user.rol == 'reclutador':
                success_message = 'Tu cuenta ha sido verificada exitosamente. Tu solicitud de reclutador será revisada por un administrador.'
            else:
                success_message = 'Tu cuenta ha sido verificada exitosamente.'

            messages.success(request, success_message)

            return render(request, 'usuarios/verificacion_resultado.html', {
                'success': True,
                'title': 'Email Verificado',
                'message': success_message,
                'user_role': user.rol,
            })

        except Exception as e:
            logger.error(f"Error en verificación de email: {str(e)}")
            messages.error(request, 'Error interno del servidor.')
            return render(request, 'usuarios/verificacion_resultado.html', {
                'success': False,
                'title': 'Error',
                'message': 'Ocurrió un error al verificar tu cuenta. Inténtalo nuevamente.',
            })


    """Vista para reenviar correo de verificación."""
class ReenviarVerificacionView(View):
    def get(self, request):
        """Muestra formulario para reenviar verificación."""
        return render(request, 'usuarios/reenviar_verificacion.html')

    def post(self, request):
        """Procesa el reenvío de verificación."""
        email = request.POST.get('email', '').strip().lower()

        if not email:
            messages.error(request, 'Por favor ingresa tu correo electrónico.')
            return render(request, 'usuarios/reenviar_verificacion.html')
        try:
            # Buscar usuario con ese email
            user = Usuario.objects.filter(email=email).first()
            if not user:
                # Por seguridad, no revelar si el email existe o no
                messages.success(request,
                                 'Si existe una cuenta con ese correo, recibirás un enlace de verificación en breve.')
                return render(request, 'usuarios/reenviar_verificacion.html')
            # Si ya está verificado
            if user.email_verified:
                messages.info(request, 'Tu cuenta ya está verificada. Puedes iniciar sesión.')
                return redirect('login')
            # Reenviar correo de verificación
            if send_verification_email(request, user):
                messages.success(request,
                                 'Se ha enviado un nuevo enlace de verificación a tu correo electrónico.')
            else:
                messages.error(request,
                               'Error al enviar el correo. Inténtalo nuevamente en unos minutos.')
            return render(request, 'usuarios/reenviar_verificacion.html')
        except Exception as e:
            logger.error(f"Error reenviando verificación: {str(e)}")
            messages.error(request, 'Error interno del servidor.')
            return render(request, 'usuarios/reenviar_verificacion.html')

class InteresadoRegistroView(View):
    """Vista para registro de interesados - ACTUALIZADA CON VERIFICACIÓN."""

    def get(self, request):
        form = InteresadoRegistroForm()
        return render(request, 'usuarios/registro_interesado.html', {'form': form})

    def post(self, request):
        form = InteresadoRegistroForm(request.POST)
        if form.is_valid():
            try:
                # Crear usuario sin verificar
                user = form.save(commit=False)
                user.email_verified = False
                user.save()

                # Crear perfil de interesado
                from .models import Interesado
                Interesado.objects.get_or_create(
                    usuario=user,
                    defaults={
                        'nombre': '',
                        'apellido_paterno': '',
                        'apellido_materno': ''
                    }
                )

                # ✅ ENVIAR CORREO CON MEJOR MANEJO DE ERRORES
                try:
                    email_enviado = send_verification_email(request, user)
                    if email_enviado:
                        messages.success(request,
                                         '¡Registro exitoso! Hemos enviado un enlace de verificación a tu correo electrónico. '
                                         'Revisa tu bandeja de entrada y sigue las instrucciones para activar tu cuenta.')
                    else:
                        messages.warning(request,
                                         'Registro exitoso, pero hubo un problema enviando el correo de verificación. '
                                         'Puedes solicitar un nuevo enlace desde la página de login.')
                except Exception as e:
                    logger.error(f"Error crítico enviando email: {str(e)}")
                    messages.warning(request,
                                     'Registro exitoso, pero hubo un problema enviando el correo de verificación. '
                                     'Puedes solicitar un nuevo enlace desde la página de login.')

                return render(request, 'usuarios/registro_exitoso.html', {
                    'user_email': user.email,
                    'user_role': 'interesado'
                })

            except Exception as e:
                logger.error(f"Error en registro de interesado: {str(e)}")
                messages.error(request, 'Error al crear la cuenta. Inténtalo nuevamente.')

        return render(request, 'usuarios/registro_interesado.html', {'form': form})
# usuarios/views.py - Vista actualizada para registro de reclutadores
class ReclutadorRegistroView(View):
    """Vista para registro de reclutadores - ACTUALIZADA PARA USAR SECRETARÍA FIJA."""

    def get(self, request):
        # Solo necesitamos el formulario del reclutador, no de la secretaría
        reclutador_form = ReclutadorRegistroForm()

        # Obtener la secretaría de movilidad para mostrar en el template
        try:
            secretaria_movilidad = Secretaria.objects.get(id=1)
        except Secretaria.DoesNotExist:
            messages.error(request, 'Error: La Secretaría de Movilidad no está configurada en el sistema.')
            return redirect('index')

        return render(request, 'usuarios/registro_reclutador.html', {
            'reclutador_form': reclutador_form,
            'secretaria_movilidad': secretaria_movilidad,  # Para mostrar info en el template
        })

    def post(self, request):
        reclutador_form = ReclutadorRegistroForm(request.POST)

        if reclutador_form.is_valid():
            try:
                # Obtener la Secretaría de Movilidad (ID=1)
                try:
                    secretaria_movilidad = Secretaria.objects.get(id=1)
                except Secretaria.DoesNotExist:
                    messages.error(request, 'Error: La Secretaría de Movilidad no está configurada.')
                    return render(request, 'usuarios/registro_reclutador.html', {
                        'reclutador_form': reclutador_form
                    })

                # Crear usuario sin verificar
                user = reclutador_form.save(commit=False)
                user.email_verified = False
                user.save()

                # Crear perfil de reclutador asociado a la Secretaría de Movilidad
                from .models import Reclutador
                Reclutador.objects.create(
                    usuario=user,
                    secretaria=secretaria_movilidad,  # ✅ USAR LA SECRETARÍA FIJA
                    nombre=reclutador_form.cleaned_data.get('nombre'),
                    apellido_paterno=reclutador_form.cleaned_data.get('apellido_paterno'),
                    apellido_materno=reclutador_form.cleaned_data.get('apellido_materno'),
                    cargo=reclutador_form.cleaned_data.get('cargo'),
                    telefono=reclutador_form.cleaned_data.get('telefono'),
                    aprobado=False
                )

                # Enviar correo de verificación
                try:
                    email_enviado = send_verification_email(request, user)
                    if email_enviado:
                        messages.success(request,
                                         '¡Registro exitoso! Hemos enviado un enlace de verificación a tu correo electrónico. '
                                         'Después de verificar tu email, tu cuenta será revisada por un administrador.')
                    else:
                        messages.warning(request,
                                         'Registro exitoso, pero hubo un problema enviando el correo de verificación. '
                                         'Puedes solicitar un nuevo enlace desde la página de login.')
                except Exception as e:
                    logger.error(f"Error crítico enviando email: {str(e)}")
                    messages.warning(request,
                                     'Registro exitoso, pero hubo un problema enviando el correo de verificación. '
                                     'Puedes solicitar un nuevo enlace desde la página de login.')

                return render(request, 'usuarios/registro_exitoso.html', {
                    'user_email': user.email,
                    'user_role': 'reclutador'
                })

            except Exception as e:
                logger.error(f"Error en registro de reclutador: {str(e)}")
                messages.error(request, 'Error al crear la cuenta. Inténtalo nuevamente.')

        # Si hay errores, mostrar el formulario con errores
        try:
            secretaria_movilidad = Secretaria.objects.get(id=1)
        except Secretaria.DoesNotExist:
            secretaria_movilidad = None

        return render(request, 'usuarios/registro_reclutador.html', {
            'reclutador_form': reclutador_form,
            'secretaria_movilidad': secretaria_movilidad,
        })


# @login_required
@require_http_methods(["GET"])
def obtener_datos_por_cp(request):
    """
    Vista AJAX para obtener datos de ubicación por código postal.
    FUNCIONA PARA CUALQUIER CP DE MÉXICO.
    """
    codigo_postal = request.GET.get('codigo_postal')

    data = {
        'estados': [],
        'municipios': [],
        'localidades': [],
        'success': False,
        'message': ''
    }

    if not codigo_postal:
        data['message'] = 'Código postal requerido'
        return JsonResponse(data)

    # Validar formato (5 dígitos)
    if not codigo_postal.isdigit() or len(codigo_postal) != 5:
        data['message'] = 'El código postal debe tener exactamente 5 dígitos'
        return JsonResponse(data)

    try:
        from .models import Codigos_Postales, Localidades

        # Buscar código postal
        try:
            cp_obj = Codigos_Postales.objects.get(
                codigo_postal=int(codigo_postal),
                estatus=1
            )
        except Codigos_Postales.DoesNotExist:
            data['message'] = f'El código postal {codigo_postal} no existe'
            return JsonResponse(data)

        # Buscar localidades
        localidades = Localidades.objects.filter(
            catalogo_codigo_postal=cp_obj,
            estatus=1
        ).select_related(
            'catalogo_estado',
            'catalogo_municipio',
            'catalogo_tipo_asentamiento'
        ).order_by('localidad')

        if not localidades.exists():
            data['message'] = f'No hay localidades para el código postal {codigo_postal}'
            return JsonResponse(data)

        # Extraer datos únicos
        estados_dict = {}
        municipios_dict = {}

        for localidad in localidades:
            # Estados
            if localidad.catalogo_estado:
                estado_id = localidad.catalogo_estado.id
                if estado_id not in estados_dict:
                    estados_dict[estado_id] = {
                        'id': estado_id,
                        'nombre': localidad.catalogo_estado.estado
                    }

            # Municipios
            if localidad.catalogo_municipio:
                municipio_id = localidad.catalogo_municipio.id
                if municipio_id not in municipios_dict:
                    municipios_dict[municipio_id] = {
                        'id': municipio_id,
                        'nombre': localidad.catalogo_municipio.municipio
                    }

            # Localidades
            tipo_asentamiento = ''
            if localidad.catalogo_tipo_asentamiento:
                tipo_asentamiento = localidad.catalogo_tipo_asentamiento.tipo_asentamiento

            data['localidades'].append({
                'id': localidad.id,
                'nombre': localidad.localidad,
                'tipo_asentamiento': tipo_asentamiento
            })

        # Convertir a listas ordenadas
        data['estados'] = sorted(estados_dict.values(), key=lambda x: x['nombre'])
        data['municipios'] = sorted(municipios_dict.values(), key=lambda x: x['nombre'])

        # Respuesta exitosa
        data['success'] = True
        data['message'] = f'Código postal {codigo_postal} válido'

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error en obtener_datos_por_cp: {str(e)}")
        data['message'] = 'Error interno del servidor'
        return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def autoguardar_ubicacion(request):
    """
    Vista AJAX optimizada para autoguardar ubicación.
    """
    if request.user.rol != 'interesado':
        return JsonResponse({
            'success': False,
            'error': 'Solo los interesados pueden actualizar su ubicación'
        })

    try:
        data = json.loads(request.body)
        interesado = request.user.interesado

        # Lista de campos permitidos para actualizar
        campos_permitidos = [
            'codigo_postal', 'estado_id', 'municipio_id', 'localidad_id',
            'estado_nombre', 'municipio_nombre', 'localidad_nombre',
            'calle_numero'
        ]

        # Actualizar solo los campos que se envíen
        campos_actualizados = []
        for campo in campos_permitidos:
            if campo in data:
                valor = data[campo]

                # Convertir strings vacías a None para campos opcionales
                if isinstance(valor, str) and not valor.strip():
                    valor = None
                elif campo.endswith('_id') and valor:
                    # Convertir IDs a enteros
                    try:
                        valor = int(valor) if valor else None
                    except (ValueError, TypeError):
                        valor = None

                # Solo actualizar si el valor ha cambiado
                valor_actual = getattr(interesado, campo)
                if valor_actual != valor:
                    setattr(interesado, campo, valor)
                    campos_actualizados.append(campo)

        # Guardar solo si hay cambios
        if campos_actualizados:
            interesado.save(update_fields=campos_actualizados)

        return JsonResponse({
            'success': True,
            'message': 'Ubicación actualizada exitosamente',
            'ubicacion_completa': interesado.ubicacion_completa,
            'campos_actualizados': campos_actualizados
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        logger.error(f"Error en autoguardar_ubicacion: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        })


# @login_required
@require_http_methods(["GET"])
def validar_codigo_postal(request):
    """
    Vista AJAX optimizada para validar código postal.
    """
    codigo_postal = request.GET.get('codigo_postal', '').strip()

    if not codigo_postal:
        return JsonResponse({
            'success': False,
            'message': 'Código postal requerido',
            'codigo_error': 'PARAMETRO_FALTANTE'
        })

    # Validar formato (5 dígitos)
    if not codigo_postal.isdigit() or len(codigo_postal) != 5:
        return JsonResponse({
            'success': False,
            'message': 'El código postal debe tener exactamente 5 dígitos numéricos',
            'codigo_error': 'FORMATO_INVALIDO'
        })

    try:
        from .models import Codigos_Postales, Localidades

        # Verificar si existe en la base de datos
        cp_obj = Codigos_Postales.objects.filter(
            codigo_postal=int(codigo_postal),
            estatus=1
        ).first()

        if not cp_obj:
            return JsonResponse({
                'success': False,
                'message': f'El código postal {codigo_postal} no está registrado en nuestra base de datos',
                'codigo_error': 'CP_NO_ENCONTRADO'
            })

        # Verificar que tenga localidades asociadas
        tiene_localidades = Localidades.objects.filter(
            catalogo_codigo_postal=cp_obj,
            estatus=1
        ).exists()

        if not tiene_localidades:
            return JsonResponse({
                'success': False,
                'message': f'El código postal {codigo_postal} no tiene localidades asociadas',
                'codigo_error': 'SIN_LOCALIDADES'
            })

        # Verificar que sea del Estado de México
        localidades_edomex = Localidades.objects.filter(
            catalogo_codigo_postal=cp_obj,
            catalogo_estado__estado__icontains='méxico',
            estatus=1
        ).exists()

        if not localidades_edomex:
            return JsonResponse({
                'success': False,
                'message': f'El código postal {codigo_postal} no pertenece al Estado de México',
                'codigo_error': 'ESTADO_NO_VALIDO'
            })

        return JsonResponse({
            'success': True,
            'message': f'Código postal {codigo_postal} válido',
            'codigo_postal': codigo_postal,
            'cp_id': cp_obj.id
        })

    except Exception as e:
        logger.error(f"Error en validar_codigo_postal: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor al validar el código postal',
            'codigo_error': 'ERROR_INTERNO'
        })


@login_required
@require_POST
def actualizar_ubicacion_completa(request):
    """
    Vista AJAX para actualizar la información de ubicación completa del interesado.
    """
    if request.user.rol != 'interesado':
        return JsonResponse({
            'success': False,
            'error': 'Solo los interesados pueden actualizar su ubicación'
        }, status=403)

    try:
        data = json.loads(request.body)

        interesado = request.user.interesado

        # Actualizar campos
        codigo_postal = data.get('codigo_postal', '').strip()
        estado_id = data.get('estado_id')
        municipio_id = data.get('municipio_id')
        localidad_id = data.get('localidad_id')
        calle = data.get('calle', '').strip()

        # Validar código postal
        if codigo_postal:
            if not codigo_postal.isdigit() or len(codigo_postal) != 5:
                return JsonResponse({
                    'success': False,
                    'error': 'Código postal inválido'
                })
            interesado.codigo_postal = codigo_postal

        # Actualizar campos adicionales si se proporcionan
        if calle:
            # Agregar campo calle al modelo si no existe
            # interesado.calle = calle
            pass

        interesado.save()

        return JsonResponse({
            'success': True,
            'message': 'Ubicación actualizada exitosamente',
            'data': {
                'codigo_postal': interesado.codigo_postal,
                'ubicacion_completa': interesado.ubicacion_completa
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error en actualizar_ubicacion_completa: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)


# usuarios/views.py - Agregar estas vistas para manejo de ubicación

@login_required
@require_POST
def guardar_ubicacion_completa(request):
    """
    Vista AJAX para guardar toda la información de ubicación del interesado.
    """
    if request.user.rol != 'interesado':
        return JsonResponse({
            'success': False,
            'error': 'Solo los interesados pueden actualizar su ubicación'
        }, status=403)

    try:
        data = json.loads(request.body)
        interesado = request.user.interesado

        # Actualizar campos básicos
        codigo_postal = data.get('codigo_postal', '').strip()
        if codigo_postal:
            if not codigo_postal.isdigit() or len(codigo_postal) != 5:
                return JsonResponse({
                    'success': False,
                    'error': 'Código postal inválido'
                })
            interesado.codigo_postal = codigo_postal

        # Actualizar campos de catálogo
        interesado.estado_id = data.get('estado_id') or None
        interesado.municipio_id = data.get('municipio_id') or None
        interesado.localidad_id = data.get('localidad_id') or None

        # Actualizar nombres legibles
        interesado.estado_nombre = data.get('estado_nombre', '').strip() or None
        interesado.municipio_nombre = data.get('municipio_nombre', '').strip() or None
        interesado.localidad_nombre = data.get('localidad_nombre', '').strip() or None

        # Calle y número
        interesado.calle_numero = data.get('calle_numero', '').strip() or None

        interesado.save()

        return JsonResponse({
            'success': True,
            'message': 'Ubicación guardada exitosamente',
            'data': {
                'ubicacion_completa': interesado.ubicacion_completa,
                'ubicacion_basica': interesado.ubicacion_basica
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        logger.error(f"Error en guardar_ubicacion_completa: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)


def obtener_municipios_por_estado(request):
    """
    Vista AJAX para obtener municipios filtrados por estado.
    Útil si se quiere implementar filtros en cascada adicionales.
    """
    estado_id = request.GET.get('estado_id')

    if not estado_id:
        return JsonResponse({
            'success': False,
            'error': 'ID de estado requerido'
        })

    try:
        from .models import Municipios

        municipios = Municipios.objects.filter(
            # Aquí deberías agregar la relación correcta con estados
            # Esto depende de cómo esté estructurada tu BD
            estatus=1
        ).values('id', 'municipio').order_by('municipio')

        return JsonResponse({
            'success': True,
            'municipios': list(municipios)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        })

def obtener_localidades_por_municipio(request):
    """
    Vista AJAX para obtener localidades filtradas por municipio.
    """
    municipio_id = request.GET.get('municipio_id')

    if not municipio_id:
        return JsonResponse({
            'success': False,
            'error': 'ID de municipio requerido'
        })

    try:
        from .models import Localidades

        localidades = Localidades.objects.filter(
            catalogo_municipio_id=municipio_id,
            estatus=1
        ).select_related(
            'catalogo_tipo_asentamiento'
        ).values(
            'id',
            'localidad',
            'catalogo_tipo_asentamiento__tipo_asentamiento'
        ).order_by('localidad')

        localidades_data = []
        for loc in localidades:
            localidades_data.append({
                'id': loc['id'],
                'nombre': loc['localidad'],
                'tipo_asentamiento': loc['catalogo_tipo_asentamiento__tipo_asentamiento'] or ''
            })

        return JsonResponse({
            'success': True,
            'localidades': localidades_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        })

@login_required
@require_POST
def actualizar_codigo_postal_ajax(request):
    """
    Vista AJAX para actualizar el código postal del interesado en la BD.
    Incluye validación automática usando DIPOMEX.
    """
    
    if request.user.rol != 'interesado':
        return JsonResponse({
            'exito': False,
            'error': 'Solo los interesados pueden actualizar su código postal'
        }, status=403)
    
    try:
        import json
        
        # Obtener datos del request
        data = json.loads(request.body)
        codigo_postal = data.get('codigo_postal', '').strip()
        
        if not codigo_postal:
            return JsonResponse({
                'exito': False,
                'error': 'El código postal es requerido'
            }, status=400)
        
        # Validar con DIPOMEX antes de guardar
        from .servicios.api_dipomex import ServicioDipomex
        
        servicio_dipomex = ServicioDipomex()
        resultado_dipomex = servicio_dipomex.consultar_codigo_postal(codigo_postal)
        
        if not resultado_dipomex.get('exito'):
            return JsonResponse({
                'exito': False,
                'error': f'Código postal inválido: {resultado_dipomex.get("error", "Error desconocido")}',
                'codigo_error': resultado_dipomex.get('codigo_error')
            }, status=400)
        
        # Verificar que sea del Estado de México
        estado = resultado_dipomex.get('estado', '')
        if not servicio_dipomex.es_estado_mexico(estado):
            return JsonResponse({
                'exito': False,
                'error': f'Solo se aceptan códigos postales del Estado de México. Este código pertenece a {estado}.',
                'codigo_error': 'ESTADO_NO_VALIDO'
            }, status=400)
        
        # Actualizar el interesado
        interesado = request.user.interesado
        interesado.codigo_postal = codigo_postal
        
        # También actualizar el municipio si coincide con alguno de nuestros choices
        municipio_dipomex = resultado_dipomex.get('municipio', '').lower()
        
        # Buscar coincidencia en nuestros municipios
        municipio_encontrado = None
        for valor, etiqueta in interesado.MUNICIPIOS_ESTADO_MEXICO:
            if municipio_dipomex in etiqueta.lower():
                municipio_encontrado = valor
                break
        
        if municipio_encontrado:
            interesado.municipio = municipio_encontrado
        
        interesado.save()
        
        logger.info(f"Código postal actualizado para usuario {request.user.email}: {codigo_postal}")
        
        respuesta = {
            'exito': True,
            'mensaje': 'Código postal actualizado exitosamente',
            'datos': {
                'codigo_postal': codigo_postal,
                'estado': resultado_dipomex['estado'],
                'municipio': resultado_dipomex['municipio'],
                'municipio_actualizado': municipio_encontrado is not None,
                'ubicacion_completa': interesado.ubicacion_completa
            }
        }
        
        return JsonResponse(respuesta)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'exito': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error en actualizar_codigo_postal_ajax: {str(e)}")
        return JsonResponse({
            'exito': False,
            'error': 'Error interno del servidor'
        }, status=500)

class LoginView(View):
    """Vista para inicio de sesión de usuarios - ACTUALIZADA CON VERIFICACIÓN."""

    def get(self, request):
        form = LoginForm()
        return render(request, 'usuarios/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=email, password=password)

            if user is not None:
                # Verificar si el usuario puede iniciar sesión
                if not user.can_login:
                    if not user.email_verified:
                        messages.warning(request,
                                         'Debes verificar tu correo electrónico antes de iniciar sesión. '
                                         'Revisa tu bandeja de entrada o solicita un nuevo enlace de verificación.')
                        return render(request, 'usuarios/login.html', {
                            'form': form,
                            'show_resend_verification': True,
                            'user_email': user.email
                        })
                    else:
                        messages.error(request, 'Tu cuenta no está activa.')
                        return render(request, 'usuarios/login.html', {'form': form})

                # Usuario puede iniciar sesión
                login(request, user)

                # Redirigir según el rol
                if user.rol == 'interesado':
                    return redirect('perfil_interesado')
                elif user.rol == 'reclutador':
                    # Verificar si el reclutador está aprobado
                    if hasattr(user, 'reclutador') and user.reclutador.aprobado:
                        return redirect('dashboard_reclutador')
                    else:
                        messages.warning(request,
                                         'Tu cuenta de reclutador está pendiente de aprobación por un administrador.')
                        logout(request)
                        return redirect('login')
                elif user.rol == 'administrador':
                    return redirect('admin:index')
            else:
                messages.error(request, 'Correo o contraseña incorrectos. Intenta nuevamente.')

        return render(request, 'usuarios/login.html', {'form': form})
# primer error
@method_decorator(login_required, name='dispatch')
class CrearEditarCVView(View):
    """Vista para crear o editar el CV del interesado."""

    def get(self, request):
        if request.user.rol != 'interesado':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        interesado = request.user.interesado

        # Obtener o crear curriculum
        curriculum, created = Curriculum.objects.get_or_create(
            interesado=interesado,
            defaults={'resumen_profesional': ''}
        )

        # Preparar formularios
        curriculum_form = CurriculumForm(instance=curriculum)
        perfil_form = InteresadoPerfilForm(instance=interesado)

        # Obtener experiencias, educación, habilidades e idiomas existentes
        experiencias = curriculum.experiencias.all()
        educaciones = curriculum.educaciones.all()
        habilidades = curriculum.habilidades.all()
        idiomas = curriculum.idiomas.all()

        context = {
            'curriculum': curriculum,
            'curriculum_form': curriculum_form,
            'perfil_form': perfil_form,
            'experiencias': experiencias,
            'educaciones': educaciones,
            'habilidades': habilidades,
            'idiomas': idiomas,
            'es_nuevo': created,
        }
        return render(request, 'usuarios/crear_editar_cv.html', context)

    def post(self, request):
        if request.user.rol != 'interesado':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        interesado = request.user.interesado
        curriculum, created = Curriculum.objects.get_or_create(
            interesado=interesado,
            defaults={'resumen_profesional': ''}
        )

        curriculum_form = CurriculumForm(request.POST, instance=curriculum)
        perfil_form = InteresadoPerfilForm(request.POST, instance=interesado)

        if curriculum_form.is_valid() and perfil_form.is_valid():
            try:
                # with transaction.atomic():
                    perfil_form.save()
                    curriculum_form.save()
                    messages.success(request, 'CV actualizado exitosamente.')
                    return redirect('crear_editar_cv')
            except Exception as e:
                messages.error(request, f'Error al guardar el CV: {str(e)}')

        # Si hay errores, volver a mostrar el formulario
        experiencias = curriculum.experiencias.all()
        educaciones = curriculum.educaciones.all()
        habilidades = curriculum.habilidades.all()
        idiomas = curriculum.idiomas.all()

        context = {
            'curriculum': curriculum,
            'curriculum_form': curriculum_form,
            'perfil_form': perfil_form,
            'experiencias': experiencias,
            'educaciones': educaciones,
            'habilidades': habilidades,
            'idiomas': idiomas,
            'es_nuevo': created,
        }
        return render(request, 'usuarios/crear_editar_cv.html', context)



# foto de perfil
# En usuarios/views.py - REEMPLAZAR la función actualizar_foto_perfil_ajax

@login_required
def actualizar_foto_perfil_ajax(request):
    """Vista AJAX específica SOLO para actualizar foto de perfil - OPTIMIZADA."""

    # ✅ VERIFICACIÓN ESTRICTA DE MÉTODO
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': f'Método {request.method} no permitido. Solo se acepta POST.'
        }, status=405)  # Method Not Allowed

    # Verificación de usuario autenticado
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Usuario no autenticado'
        }, status=401)

    # Verificación de rol
    if not hasattr(request.user, 'rol') or request.user.rol != 'interesado':
        return JsonResponse({
            'success': False,
            'error': f'Acceso denegado. Rol requerido: interesado'
        }, status=403)

    try:
        interesado = request.user.interesado

        # Validar que se envió una foto
        if 'foto_perfil' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No se recibió ninguna imagen'
            }, status=400)

        foto = request.FILES['foto_perfil']

        # Validar tipo de archivo
        if not foto.name.lower().endswith(('.jpg', '.jpeg')):
            return JsonResponse({
                'success': False,
                'error': 'Solo se permiten archivos JPG'
            }, status=400)

        # Validar tamaño (5MB máximo)
        if foto.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'El archivo es demasiado grande. Máximo 5MB'
            }, status=400)

        # ✅ PROCESO DE GUARDADO OPTIMIZADO
        # Eliminar foto anterior si existe
        if interesado.foto_perfil:
            try:
                from django.core.files.storage import default_storage
                if default_storage.exists(interesado.foto_perfil.name):
                    default_storage.delete(interesado.foto_perfil.name)
                    print(f"✅ Foto anterior eliminada: {interesado.foto_perfil.name}")
            except Exception as e:
                print(f"⚠️ Error al eliminar foto anterior: {e}")

        # Guardar nueva foto
        interesado.foto_perfil = foto
        interesado.save()

        # ✅ CONSTRUCCIÓN CORRECTA Y SEGURA DE URL
        try:
            foto_url = request.build_absolute_uri(interesado.foto_perfil.url)
        except Exception as url_error:
            print(f"❌ Error construyendo URL: {url_error}")
            return JsonResponse({
                'success': False,
                'error': 'Error al generar URL de la imagen'
            }, status=500)

        # ✅ RESPUESTA OPTIMIZADA Y LIMPIA
        response_data = {
            'success': True,
            'message': 'Imagen guardada exitosamente',
            'data': {
                'foto_url': foto_url
            }
        }

        # ✅ HEADERS ADICIONALES PARA EVITAR CACHE
        response = JsonResponse(response_data)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response

    except AttributeError as e:
        print(f"❌ Error de atributo (usuario sin interesado?): {e}")
        return JsonResponse({
            'success': False,
            'error': 'Usuario no tiene perfil de interesado asociado'
        }, status=403)

    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        logger.error(f"Error en actualizar_foto_perfil_ajax: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)

@login_required
def actualizar_perfil_ajax(request):
    """Vista AJAX para actualizar campos de texto del perfil (sin foto)."""
    if request.method != 'POST' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        interesado = request.user.interesado

        # Solo actualizar campos de texto (no foto)
        interesado.nombre = request.POST.get('nombre', interesado.nombre)
        interesado.apellido_paterno = request.POST.get('apellido_paterno', interesado.apellido_paterno)
        interesado.apellido_materno = request.POST.get('apellido_materno', interesado.apellido_materno)
        interesado.telefono = request.POST.get('telefono', interesado.telefono)
        interesado.municipio = request.POST.get('municipio', interesado.municipio)
        interesado.codigo_postal = request.POST.get('codigo_postal', interesado.codigo_postal)

        # Fecha de nacimiento
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        if fecha_nacimiento:
            interesado.fecha_nacimiento = fecha_nacimiento

        interesado.save()

        return JsonResponse({
            'success': True,
            'message': 'Perfil actualizado exitosamente',
            'data': {
                'nombre_completo': interesado.nombre_completo,
                'telefono': interesado.telefono or 'No especificado',
                'ubicacion': interesado.ubicacion_completa,
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# En usuarios/views.py - AGREGAR esta nueva vista

# En usuarios/views.py - REEMPLAZAR la vista anterior con esta corregida

@login_required
def actualizar_perfil_completo_ajax(request):
    """Vista AJAX para actualizar perfil completo desde el modal."""
    if request.method != 'POST' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        interesado = request.user.interesado

        # Actualizar información básica
        interesado.nombre = request.POST.get('nombre', '').strip()
        interesado.apellido_paterno = request.POST.get('apellido_paterno', '').strip()
        interesado.apellido_materno = request.POST.get('apellido_materno', '').strip()
        interesado.telefono = request.POST.get('telefono', '').strip()

        # ✅ CORRECCIÓN: Fecha de nacimiento con manejo de tipos
        fecha_nacimiento = request.POST.get('fecha_nacimiento', '').strip()
        if fecha_nacimiento:
            try:
                # Si viene como string desde el form, Django lo convierte automáticamente
                interesado.fecha_nacimiento = fecha_nacimiento
            except Exception as e:
                logger.warning(f"Error al procesar fecha de nacimiento: {e}")
                # Si hay error, mantener la fecha existente
                pass

        # Información de ubicación
        codigo_postal = request.POST.get('codigo_postal', '').strip()
        if codigo_postal:
            interesado.codigo_postal = codigo_postal

        # IDs de catálogos
        estado_id = request.POST.get('estado_id', '').strip()
        municipio_id = request.POST.get('municipio_id', '').strip()
        localidad_id = request.POST.get('localidad_id', '').strip()

        # Convertir a int o None
        interesado.estado_id = int(estado_id) if estado_id and estado_id.isdigit() else None
        interesado.municipio_id = int(municipio_id) if municipio_id and municipio_id.isdigit() else None
        interesado.localidad_id = int(localidad_id) if localidad_id and localidad_id.isdigit() else None

        # Nombres legibles
        interesado.estado_nombre = request.POST.get('estado_nombre', '').strip() or None
        interesado.municipio_nombre = request.POST.get('municipio_nombre', '').strip() or None
        interesado.localidad_nombre = request.POST.get('localidad_nombre', '').strip() or None

        # Calle y número
        interesado.calle_numero = request.POST.get('calle_numero', '').strip() or None

        interesado.save()

        # ✅ CORRECCIÓN: Formateo seguro de fecha
        fecha_nacimiento_formateada = None
        if interesado.fecha_nacimiento:
            try:
                # Si es un objeto de fecha, usar strftime
                if hasattr(interesado.fecha_nacimiento, 'strftime'):
                    fecha_nacimiento_formateada = interesado.fecha_nacimiento.strftime('%d/%m/%Y')
                else:
                    # Si es string, intentar parsearlo
                    from datetime import datetime
                    fecha_obj = datetime.strptime(str(interesado.fecha_nacimiento), '%Y-%m-%d')
                    fecha_nacimiento_formateada = fecha_obj.strftime('%d/%m/%Y')
            except Exception as e:
                logger.warning(f"Error formateando fecha: {e}")
                fecha_nacimiento_formateada = str(interesado.fecha_nacimiento)

        return JsonResponse({
            'success': True,
            'message': 'Perfil actualizado exitosamente',
            'datos': {
                'nombre_completo': interesado.nombre_completo,
                'telefono': interesado.telefono or 'No especificado',
                'ubicacion_completa': interesado.ubicacion_completa,
                'fecha_nacimiento': fecha_nacimiento_formateada,
            }
        })

    except Exception as e:
        logger.error(f"Error actualizando perfil completo: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        })


@require_POST
@csrf_exempt
def autoguardar_resumen_profesional(request):
    data = json.loads(request.body)
    resumen = data.get('resumen_profesional', '')
    curriculum = request.user.interesado.curriculum
    curriculum.resumen_profesional = resumen
    curriculum.save()
    return JsonResponse({'success': True})

@login_required
def editar_experiencia_ajax(request, experiencia_id):
    """Vista AJAX para editar experiencia laboral."""
    if request.method != 'POST' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        curriculum = request.user.interesado.curriculum
        experiencia = get_object_or_404(ExperienciaLaboral, id=experiencia_id, curriculum=curriculum)

        # Usar la instancia existente para editar
        form = ExperienciaLaboralForm(request.POST, instance=experiencia)

        if form.is_valid():
            experiencia_actualizada = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Experiencia actualizada exitosamente',
                'experiencia': {
                    'id': experiencia_actualizada.id,
                    'empresa': experiencia_actualizada.empresa,
                    'puesto': experiencia_actualizada.puesto,
                    'periodo': experiencia_actualizada.periodo_trabajo
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
@login_required
def agregar_experiencia_ajax(request):
    """Vista AJAX para agregar experiencia laboral."""
    if request.method != 'POST' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        curriculum = request.user.interesado.curriculum
        form = ExperienciaLaboralForm(request.POST)

        if form.is_valid():
            experiencia = form.save(commit=False)
            experiencia.curriculum = curriculum
            experiencia.save()

            return JsonResponse({
                'success': True,
                'message': 'Experiencia agregada exitosamente',
                'experiencia': {
                    'id': experiencia.id,
                    'empresa': experiencia.empresa,
                    'puesto': experiencia.puesto,
                    'periodo': experiencia.periodo_trabajo
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })      
@login_required
def agregar_educacion_ajax(request):
    """Vista AJAX para agregar educación."""
    if request.method != 'POST' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        curriculum = request.user.interesado.curriculum
        form = EducacionForm(request.POST)

        if form.is_valid():
            educacion = form.save(commit=False)
            educacion.curriculum = curriculum
            educacion.save()

            return JsonResponse({
                'success': True,
                'message': 'Educación agregada exitosamente',
                'educacion': {
                    'id': educacion.id,
                    'titulo': educacion.titulo,
                    'institucion': educacion.institucion,
                    'periodo': educacion.periodo_estudio
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
@login_required
def agregar_idioma_ajax(request):
    """Vista AJAX para agregar idioma."""
    if request.method != 'POST' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        curriculum = request.user.interesado.curriculum
        form = IdiomaInteresadoForm(request.POST)

        if form.is_valid():
            idioma = form.save(commit=False)
            idioma.curriculum = curriculum
            idioma.save()

            return JsonResponse({
                'success': True,
                'message': 'Idioma agregado exitosamente',
                'idioma': {
                    'id': idioma.id,
                    'idioma': idioma.idioma,
                    'nivel_general': idioma.nivel_general
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def eliminar_experiencia_ajax(request, experiencia_id):
    """Vista AJAX para eliminar experiencia laboral - VERSIÓN CORREGIDA."""

    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido. Se requiere DELETE o POST.'
        }, status=405)

    if request.user.rol != 'interesado':
        return JsonResponse({
            'success': False,
            'error': 'Solo los interesados pueden eliminar experiencias.'
        }, status=403)

    try:
        if not hasattr(request.user, 'interesado') or not hasattr(request.user.interesado, 'curriculum'):
            return JsonResponse({
                'success': False,
                'error': 'No tienes un curriculum creado.'
            }, status=404)

        curriculum = request.user.interesado.curriculum

        try:
            experiencia = ExperienciaLaboral.objects.get(
                id=experiencia_id,
                curriculum=curriculum
            )
        except ExperienciaLaboral.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Experiencia no encontrada o no tienes permiso para eliminarla.'
            }, status=404)

        # Guardar info antes de eliminar
        puesto = experiencia.puesto
        empresa = experiencia.empresa

        # Eliminar
        experiencia.delete()

        logger.info(f"Experiencia {experiencia_id} eliminada exitosamente para usuario {request.user.email}")

        return JsonResponse({
            'success': True,
            'message': f'Experiencia "{puesto}" en {empresa} eliminada exitosamente.',
            'experiencia_id': experiencia_id,
            'puesto': puesto,
            'empresa': empresa
        })

    except Exception as e:
        logger.error(f"Error eliminando experiencia {experiencia_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def editar_educacion_ajax(request, educacion_id):
    """Vista AJAX para editar educación."""
    if request.method != 'POST' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        curriculum = request.user.interesado.curriculum
        educacion = get_object_or_404(Educacion, id=educacion_id, curriculum=curriculum)

        # Usar la instancia existente para editar
        form = EducacionForm(request.POST, instance=educacion)

        if form.is_valid():
            educacion_actualizada = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Educación actualizada exitosamente',
                'educacion': {
                    'id': educacion_actualizada.id,
                    'titulo': educacion_actualizada.titulo,
                    'institucion': educacion_actualizada.institucion,
                    'periodo': educacion_actualizada.periodo_estudio
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def eliminar_educacion_ajax(request, educacion_id):
    """Vista AJAX para eliminar educación - VERSIÓN CORREGIDA."""

    # ✅ ACEPTAR TANTO DELETE como POST para mayor compatibilidad
    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido. Se requiere DELETE o POST.'
        }, status=405)

    # Verificar permisos
    if request.user.rol != 'interesado':
        return JsonResponse({
            'success': False,
            'error': 'Solo los interesados pueden eliminar educación.'
        }, status=403)

    try:
        # Verificar que el usuario tenga perfil de interesado
        if not hasattr(request.user, 'interesado'):
            return JsonResponse({
                'success': False,
                'error': 'Usuario no tiene perfil de interesado.'
            }, status=403)

        interesado = request.user.interesado

        # Verificar que tenga curriculum
        if not hasattr(interesado, 'curriculum'):
            return JsonResponse({
                'success': False,
                'error': 'No tienes un curriculum creado.'
            }, status=404)

        curriculum = interesado.curriculum

        # ✅ LOGGING PARA DEBUG
        logger.info(f"Intentando eliminar educación {educacion_id} para usuario {request.user.email}")

        # Buscar la educación que pertenece al curriculum del usuario
        try:
            educacion = Educacion.objects.get(
                id=educacion_id,
                curriculum=curriculum
            )
        except Educacion.DoesNotExist:
            logger.warning(f"Educación {educacion_id} no encontrada para usuario {request.user.email}")
            return JsonResponse({
                'success': False,
                'error': 'Educación no encontrada o no tienes permiso para eliminarla.'
            }, status=404)

        # Guardar información para el mensaje antes de eliminar
        titulo_educacion = educacion.titulo
        institucion = educacion.institucion

        # ✅ ELIMINAR LA EDUCACIÓN
        educacion.delete()

        # ✅ LOGGING DE ÉXITO
        logger.info(f"Educación {educacion_id} eliminada exitosamente para usuario {request.user.email}")

        # ✅ RESPUESTA EXITOSA CON INFORMACIÓN DETALLADA
        return JsonResponse({
            'success': True,
            'message': f'Formación "{titulo_educacion}" de {institucion} eliminada exitosamente.',
            'educacion_id': educacion_id,
            'titulo': titulo_educacion,
            'institucion': institucion
        })

    except Exception as e:
        # ✅ LOGGING DE ERROR DETALLADO
        logger.error(f"Error eliminando educación {educacion_id} para usuario {request.user.email}: {str(e)}")
        print(f"Error detallado en eliminar_educacion_ajax: {str(e)}")  # Para debugging local

        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


@login_required
def eliminar_idioma_ajax(request, idioma_id):
    """Vista AJAX para eliminar idioma - VERSIÓN CORREGIDA."""

    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido. Se requiere DELETE o POST.'
        }, status=405)

    if request.user.rol != 'interesado':
        return JsonResponse({
            'success': False,
            'error': 'Solo los interesados pueden eliminar idiomas.'
        }, status=403)

    try:
        if not hasattr(request.user, 'interesado') or not hasattr(request.user.interesado, 'curriculum'):
            return JsonResponse({
                'success': False,
                'error': 'No tienes un curriculum creado.'
            }, status=404)

        curriculum = request.user.interesado.curriculum

        try:
            idioma = IdiomaInteresado.objects.get(
                id=idioma_id,
                curriculum=curriculum
            )
        except IdiomaInteresado.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Idioma no encontrado o no tienes permiso para eliminarlo.'
            }, status=404)

        # Guardar info antes de eliminar
        nombre_idioma = idioma.idioma
        nivel = idioma.nivel_general

        # Eliminar
        idioma.delete()

        logger.info(f"Idioma {idioma_id} eliminado exitosamente para usuario {request.user.email}")

        return JsonResponse({
            'success': True,
            'message': f'Idioma "{nombre_idioma}" ({nivel}) eliminado exitosamente.',
            'idioma_id': idioma_id,
            'idioma': nombre_idioma,
            'nivel': nivel
        })

    except Exception as e:
        logger.error(f"Error eliminando idioma {idioma_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
@login_required
def eliminar_idioma_ajax(request, idioma_id):
    """Vista AJAX para eliminar idioma."""
    if request.method != 'DELETE' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        curriculum = request.user.interesado.curriculum
        idioma = get_object_or_404(IdiomaInteresado, id=idioma_id, curriculum=curriculum)
        idioma.delete()

        return JsonResponse({
            'success': True,
            'message': 'Idioma eliminado exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def previsualizar_cv(request):
    """Vista para previsualizar el CV completo."""
    if request.user.rol != 'interesado':
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')

    interesado = request.user.interesado

    try:
        curriculum = interesado.curriculum
        context = {
            'interesado': interesado,
            'curriculum': curriculum,
            'experiencias': curriculum.experiencias.all(),
            'educaciones': curriculum.educaciones.all(),
            'habilidades': curriculum.habilidades.all(),
            'idiomas': curriculum.idiomas.all(),
        }
        return render(request, 'usuarios/previsualizar_cv.html', context)
    except Curriculum.DoesNotExist:
        messages.warning(request, 'Primero debes crear tu CV.')
        return redirect('crear_editar_cv')


def convertir_imagen_a_base64(ruta_imagen):
    """
    Convierte una imagen a formato base64 para embederla en HTML.
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(ruta_imagen):
            print(f"Archivo no encontrado: {ruta_imagen}")
            return None
        
        # Abrir y procesar la imagen
        with Image.open(ruta_imagen) as img:
            # Convertir a RGB si es necesario (para JPEGs)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionar si es muy grande (máximo 300x300 para CV)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # Guardar en buffer como JPEG
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            # Convertir a base64
            imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{imagen_base64}"
            
    except Exception as e:
        print(f"Error al convertir imagen a base64: {str(e)}")
        return None
@login_required
def descargar_cv_pdf(request):
    """Vista para generar y descargar CV en PDF con imágenes en base64."""
    if request.user.rol != 'interesado':
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')

    interesado = request.user.interesado

    try:
        curriculum = interesado.curriculum
    except Curriculum.DoesNotExist:
        messages.warning(request, 'Primero debes crear tu CV.')
        return redirect('perfil_interesado')

    # ✅ CONVERTIR IMAGEN A BASE64 PARA EMBEDERLA EN HTML
    imagen_base64 = None
    if interesado.foto_perfil and interesado.foto_perfil.name:
        try:
            # Construir ruta completa del archivo
            ruta_completa = os.path.join(settings.MEDIA_ROOT, interesado.foto_perfil.name)
            print(f"Buscando imagen en: {ruta_completa}")  # Debug
            
            # Convertir a base64
            imagen_base64 = convertir_imagen_a_base64(ruta_completa)
            
            if imagen_base64:
                print("✅ Imagen convertida a base64 exitosamente")
            else:
                print("❌ No se pudo convertir la imagen a base64")
                
        except Exception as e:
            print(f"Error al procesar imagen: {e}")
            imagen_base64 = None

    # Preparar datos para el PDF
    context = {
        'interesado': interesado,
        'curriculum': curriculum,
        'experiencias': curriculum.experiencias.all(),
        'educaciones': curriculum.educaciones.all(),
        'habilidades': curriculum.habilidades.all(),
        'idiomas': curriculum.idiomas.all(),
        'imagen_base64': imagen_base64,  # ✅ PASAR IMAGEN EN BASE64
        'request': request,
    }

    # Renderizar HTML
    html_string = render_to_string('usuarios/cv_pdf_template.html', context, request=request)

    # Generar PDF
    try:
        from weasyprint import HTML

        html_doc = HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/'),
            encoding='utf-8'
        )

        pdf_bytes = html_doc.write_pdf(
            optimize_images=True,
            presentational_hints=True
        )

        # Preparar respuesta
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"CV_{interesado.nombre}_{interesado.apellido_paterno}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        print(f"Error al generar PDF: {str(e)}")
        messages.error(request, f'Error al generar PDF: {str(e)}')
        return redirect('perfil_interesado')

@login_required
def descargar_cv_pdf_reclutador(request):
    """Vista para que reclutadores descarguen CV con imágenes en base64."""

    # Verificaciones de permisos
    if request.user.rol != 'reclutador':
        messages.error(request, 'No tienes permiso para descargar CVs.')
        return redirect('index')

    if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
        messages.error(request, 'Tu cuenta de reclutador debe estar aprobada.')
        return redirect('dashboard_reclutador')

    # Obtener el ID del interesado
    interesado_id = request.GET.get('interesado_id')
    if not interesado_id:
        messages.error(request, 'ID de interesado no proporcionado.')
        return redirect('mis_vacantes')

    try:
        # Obtener el interesado
        interesado = get_object_or_404(Interesado, id=interesado_id)

        # Verificar permisos
        tiene_permiso = Postulacion.objects.filter(
            interesado=interesado,
            vacante__reclutador=request.user.reclutador
        ).exists()

        if not tiene_permiso:
            messages.error(request, 'No tienes permiso para descargar este CV.')
            return redirect('mis_vacantes')

        # Verificar que tenga CV
        if not hasattr(interesado, 'curriculum'):
            messages.error(request, 'Este interesado no tiene CV disponible.')
            return redirect('mis_vacantes')

        curriculum = interesado.curriculum

        # ✅ CONVERTIR IMAGEN A BASE64 PARA EMBEDERLA EN HTML
        imagen_base64 = None
        if interesado.foto_perfil and interesado.foto_perfil.name:
            try:
                # Construir ruta completa del archivo
                ruta_completa = os.path.join(settings.MEDIA_ROOT, interesado.foto_perfil.name)
                print(f"Buscando imagen en: {ruta_completa}")  # Debug
                
                # Convertir a base64
                imagen_base64 = convertir_imagen_a_base64(ruta_completa)
                
                if imagen_base64:
                    print("✅ Imagen convertida a base64 exitosamente")
                else:
                    print("❌ No se pudo convertir la imagen a base64")
                    
            except Exception as e:
                print(f"Error al procesar imagen: {e}")
                imagen_base64 = None

        # Preparar datos para el PDF
        context = {
            'interesado': interesado,
            'curriculum': curriculum,
            'experiencias': curriculum.experiencias.all(),
            'educaciones': curriculum.educaciones.all(),
            'habilidades': curriculum.habilidades.all(),
            'idiomas': curriculum.idiomas.all(),
            'imagen_base64': imagen_base64,  # ✅ PASAR IMAGEN EN BASE64
            'request': request,
        }

        # Renderizar HTML
        html_string = render_to_string('usuarios/cv_pdf_template.html', context, request=request)

        # Generar PDF
        try:
            from weasyprint import HTML

            html_doc = HTML(
                string=html_string,
                base_url=request.build_absolute_uri('/'),
                encoding='utf-8'
            )

            pdf_bytes = html_doc.write_pdf(
                optimize_images=True,
                presentational_hints=True
            )

            # Preparar respuesta
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"CV_{interesado.nombre}_{interesado.apellido_paterno}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            print(f"Error al generar PDF: {str(e)}")
            messages.error(request, f'Error al generar PDF: {str(e)}')
            return redirect('mis_vacantes')

    except Interesado.DoesNotExist:
        messages.error(request, 'Interesado no encontrado.')
        return redirect('mis_vacantes')
    except Exception as e:
        print(f"Error interno: {str(e)}")
        messages.error(request, f'Error interno: {str(e)}')
        return redirect('mis_vacantes')  
    
    
@method_decorator(login_required, name='dispatch')
class PublicarVacanteView(View):
    """Vista para publicar una nueva vacante - ACTUALIZADA con validación de título."""

    def get(self, request):
        if request.user.rol != 'reclutador':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
            messages.error(request, 'Tu cuenta de reclutador debe estar aprobada para publicar vacantes.')
            return redirect('dashboard_reclutador')

        vacante_form = VacanteForm()
        requisito_form = RequisitoVacanteForm()

        context = {
            'vacante_form': vacante_form,
            'requisito_form': requisito_form,
            'accion': 'crear'
        }
        return render(request, 'usuarios/publicar_vacante.html', context)

    def post(self, request):
        if request.user.rol != 'reclutador':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
            messages.error(request, 'Tu cuenta de reclutador debe estar aprobada para publicar vacantes.')
            return redirect('dashboard_reclutador')

        reclutador = request.user.reclutador
        
        # Determinar la acción del usuario
        accion = request.POST.get('accion')
        
        # ✅ VALIDACIÓN ESPECÍFICA PARA BORRADORES
        if accion == 'guardar_borrador':
            # Para borradores, solo validar que tenga título
            titulo = request.POST.get('titulo', '').strip()
            
            if not titulo:
                messages.error(request, 'El título de la vacante es obligatorio, incluso para borradores.')
                
                # Mantener los datos del formulario
                vacante_form = VacanteForm(request.POST)
                requisito_form = RequisitoVacanteForm(request.POST)
                
                context = {
                    'vacante_form': vacante_form,
                    'requisito_form': requisito_form,
                    'accion': 'crear'
                }
                return render(request, 'usuarios/publicar_vacante.html', context)
            
            # Para borradores, crear vacante sin validación completa
            try:
                # Crear la vacante directamente
                vacante = Vacante.objects.create(
                    secretaria=reclutador.secretaria,
                    reclutador=reclutador,
                    titulo=titulo,
                    descripcion=request.POST.get('descripcion', ''),
                    categoria_id=request.POST.get('categoria') or None,
                    tipo_empleo=request.POST.get('tipo_empleo', ''),
                    modalidad=request.POST.get('modalidad', 'presencial'),
                    municipio=request.POST.get('municipio', ''),
                    detalles_salario=request.POST.get('detalles_salario', ''),
                    max_postulantes=int(request.POST.get('max_postulantes', 20)),
                    estado_vacante='borrador',
                    aprobada=False
                )
                
                # Campos de salario (pueden estar vacíos en borradores)
                salario_min = request.POST.get('salario_min', '').strip()
                salario_max = request.POST.get('salario_max', '').strip()
                
                if salario_min:
                    try:
                        vacante.salario_min = float(salario_min)
                    except ValueError:
                        pass
                        
                if salario_max:
                    try:
                        vacante.salario_max = float(salario_max)
                    except ValueError:
                        pass
                
                # Fechas (pueden estar vacías en borradores)
                fecha_inicio = request.POST.get('fecha_inicio_estimada')
                if fecha_inicio:
                    vacante.fecha_inicio_estimada = fecha_inicio
                    
                fecha_limite = request.POST.get('fecha_limite')
                if fecha_limite:
                    vacante.fecha_limite = fecha_limite
                
                vacante.save()
                
                # Crear los requisitos
                RequisitoVacante.objects.create(
                    vacante=vacante,
                    descripcion_requisitos=request.POST.get('descripcion_requisitos', ''),
                    educacion_minima=request.POST.get('educacion_minima', ''),
                    experiencia_minima=request.POST.get('experiencia_minima') or None
                )
                
                messages.success(request, f'Borrador "{titulo}" guardado exitosamente. Puedes continuar editándolo después.')
                return redirect('mis_vacantes')
                
            except Exception as e:
                logger.error(f"Error guardando borrador: {str(e)}")
                messages.error(request, f'Error al guardar el borrador: {str(e)}')
                
                # Mostrar formulario con errores
                vacante_form = VacanteForm(request.POST)
                requisito_form = RequisitoVacanteForm(request.POST)
                
                context = {
                    'vacante_form': vacante_form,
                    'requisito_form': requisito_form,
                    'accion': 'crear'
                }
                return render(request, 'usuarios/publicar_vacante.html', context)
        
        else:
            # ✅ PARA PUBLICAR, USAR VALIDACIÓN COMPLETA DE FORMULARIOS
            vacante_form = VacanteForm(request.POST)
            requisito_form = RequisitoVacanteForm(request.POST)

            if vacante_form.is_valid() and requisito_form.is_valid():
                try:
                    # Crear la vacante
                    vacante = vacante_form.save(commit=False)
                    vacante.secretaria = reclutador.secretaria
                    vacante.reclutador = reclutador

                    # Establecer el estado según la acción
                    if accion == 'publicar':
                        vacante.estado_vacante = 'publicada'
                        vacante.aprobada = True
                        mensaje = f'Vacante "{vacante.titulo}" publicada exitosamente.'
                    else:
                        vacante.estado_vacante = 'borrador'
                        mensaje = f'Vacante "{vacante.titulo}" guardada como borrador exitosamente.'

                    vacante.save()

                    # Crear los requisitos
                    requisito = requisito_form.save(commit=False)
                    requisito.vacante = vacante
                    requisito.save()

                    messages.success(request, mensaje)
                    return redirect('mis_vacantes')

                except Exception as e:
                    logger.error(f"Error guardando vacante: {str(e)}")
                    messages.error(request, f'Error al guardar la vacante: {str(e)}')
            else:
                # Mostrar errores de validación
                errores = []
                for field, errors in vacante_form.errors.items():
                    for error in errors:
                        errores.append(f"{field}: {error}")
                for field, errors in requisito_form.errors.items():
                    for error in errors:
                        errores.append(f"{field}: {error}")
                
                if errores:
                    messages.error(request, f"Errores de validación: {', '.join(errores)}")

        # Si llegamos aquí, mostrar el formulario con errores
        context = {
            'vacante_form': vacante_form,
            'requisito_form': requisito_form,
            'accion': 'crear'
        }
        return render(request, 'usuarios/publicar_vacante.html', context)
    
# el

@method_decorator(login_required, name='dispatch')
class EditarVacanteView(View):
    """Vista para editar una vacante existente - ACTUALIZADA con validación de título."""

    def get(self, request, vacante_id):
        if request.user.rol != 'reclutador':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
            messages.error(request, 'Tu cuenta de reclutador debe estar aprobada.')
            return redirect('index')

        try:
            # Verificar permisos: ReclutadorAdmin puede editar cualquier vacante
            if es_reclutador_admin(request.user):
                vacante = Vacante.objects.get(id=vacante_id)
            else:
                # Reclutador normal solo puede editar sus vacantes
                vacante = Vacante.objects.get(
                    id=vacante_id,
                    reclutador=request.user.reclutador
                )
        except Vacante.DoesNotExist:
            messages.error(request, 'Vacante no encontrada o no tienes permiso para editarla.')
            return redirect('mis_vacantes')

        # Obtener o crear requisitos si no existen
        requisito, created = RequisitoVacante.objects.get_or_create(
            vacante=vacante,
            defaults={'descripcion_requisitos': ''}
        )

        vacante_form = VacanteForm(instance=vacante)
        requisito_form = RequisitoVacanteForm(instance=requisito)

        context = {
            'vacante_form': vacante_form,
            'requisito_form': requisito_form,
            'vacante': vacante,
            'accion': 'editar'
        }
        return render(request, 'usuarios/publicar_vacante.html', context)

    def post(self, request, vacante_id):
        if request.user.rol != 'reclutador':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
            messages.error(request, 'Tu cuenta de reclutador debe estar aprobada.')
            return redirect('index')

        try:
            # Verificar permisos: ReclutadorAdmin puede editar cualquier vacante
            if es_reclutador_admin(request.user):
                vacante = Vacante.objects.get(id=vacante_id)
            else:
                # Reclutador normal solo puede editar sus vacantes
                vacante = Vacante.objects.get(
                    id=vacante_id,
                    reclutador=request.user.reclutador
                )
        except Vacante.DoesNotExist:
            messages.error(request, 'Vacante no encontrada o no tienes permiso para editarla.')
            return redirect('mis_vacantes')

        # Obtener o crear requisitos si no existen
        requisito, created = RequisitoVacante.objects.get_or_create(
            vacante=vacante,
            defaults={'descripcion_requisitos': ''}
        )

        # Determinar la acción del usuario
        accion = request.POST.get('accion')
        
        # ✅ VALIDACIÓN ESPECÍFICA PARA BORRADORES
        if accion == 'guardar_borrador':
            # Para borradores, solo validar que tenga título
            titulo = request.POST.get('titulo', '').strip()
            
            if not titulo:
                messages.error(request, 'El título de la vacante es obligatorio, incluso para borradores.')
                
                # Mantener los datos del formulario
                vacante_form = VacanteForm(request.POST, instance=vacante)
                requisito_form = RequisitoVacanteForm(request.POST, instance=requisito)
                
                context = {
                    'vacante_form': vacante_form,
                    'requisito_form': requisito_form,
                    'vacante': vacante,
                    'accion': 'editar'
                }
                return render(request, 'usuarios/publicar_vacante.html', context)
            
            # Para borradores, crear formularios sin validación completa
            try:
                # Actualizar campos básicos directamente
                vacante.titulo = titulo
                vacante.descripcion = request.POST.get('descripcion', '')
                vacante.categoria_id = request.POST.get('categoria') or None
                vacante.tipo_empleo = request.POST.get('tipo_empleo', '')
                vacante.modalidad = request.POST.get('modalidad', '')
                vacante.municipio = request.POST.get('municipio', '')
                
                # Campos de salario (pueden estar vacíos en borradores)
                salario_min = request.POST.get('salario_min', '').strip()
                salario_max = request.POST.get('salario_max', '').strip()
                
                if salario_min:
                    try:
                        vacante.salario_min = float(salario_min)
                    except ValueError:
                        vacante.salario_min = None
                else:
                    vacante.salario_min = None
                    
                if salario_max:
                    try:
                        vacante.salario_max = float(salario_max)
                    except ValueError:
                        vacante.salario_max = None
                else:
                    vacante.salario_max = None
                
                vacante.detalles_salario = request.POST.get('detalles_salario', '')
                
                # Fechas (pueden estar vacías en borradores)
                fecha_inicio = request.POST.get('fecha_inicio_estimada')
                if fecha_inicio:
                    vacante.fecha_inicio_estimada = fecha_inicio
                else:
                    vacante.fecha_inicio_estimada = None
                    
                fecha_limite = request.POST.get('fecha_limite')
                if fecha_limite:
                    vacante.fecha_limite = fecha_limite
                else:
                    vacante.fecha_limite = None
                
                max_postulantes = request.POST.get('max_postulantes')
                if max_postulantes:
                    vacante.max_postulantes = int(max_postulantes)
                else:
                    vacante.max_postulantes = 20  # Valor por defecto
                
                # Establecer estado como borrador
                vacante.estado_vacante = 'borrador'
                vacante.save()
                
                # Actualizar requisitos
                requisito.descripcion_requisitos = request.POST.get('descripcion_requisitos', '')
                requisito.educacion_minima = request.POST.get('educacion_minima', '')
                requisito.experiencia_minima = request.POST.get('experiencia_minima') or None
                requisito.save()
                
                messages.success(request, f'Borrador "{titulo}" guardado exitosamente.')
                return redirect('mis_vacantes')
                
            except Exception as e:
                logger.error(f"Error guardando borrador: {str(e)}")
                messages.error(request, f'Error al guardar el borrador: {str(e)}')
                
                # Mostrar formulario con errores
                vacante_form = VacanteForm(request.POST, instance=vacante)
                requisito_form = RequisitoVacanteForm(request.POST, instance=requisito)
                
                context = {
                    'vacante_form': vacante_form,
                    'requisito_form': requisito_form,
                    'vacante': vacante,
                    'accion': 'editar'
                }
                return render(request, 'usuarios/publicar_vacante.html', context)
        
        else:
            # ✅ PARA PUBLICAR, USAR VALIDACIÓN COMPLETA DE FORMULARIOS
            vacante_form = VacanteForm(request.POST, instance=vacante)
            requisito_form = RequisitoVacanteForm(request.POST, instance=requisito)

            if vacante_form.is_valid() and requisito_form.is_valid():
                try:
                    # Actualizar la vacante
                    vacante_actualizada = vacante_form.save(commit=False)

                    # Establecer el estado según la acción
                    if accion == 'publicar':
                        vacante_actualizada.estado_vacante = 'publicada'
                        vacante_actualizada.aprobada = True
                        mensaje = f'Vacante "{vacante_actualizada.titulo}" actualizada y publicada exitosamente.'
                    else:
                        mensaje = f'Vacante "{vacante_actualizada.titulo}" actualizada exitosamente.'

                    vacante_actualizada.save()

                    # Actualizar los requisitos
                    requisito_form.save()

                    messages.success(request, mensaje)
                    return redirect('mis_vacantes')

                except Exception as e:
                    logger.error(f"Error actualizando vacante: {str(e)}")
                    messages.error(request, f'Error al actualizar la vacante: {str(e)}')
            else:
                # Mostrar errores de validación
                errores = []
                for field, errors in vacante_form.errors.items():
                    for error in errors:
                        errores.append(f"{field}: {error}")
                for field, errors in requisito_form.errors.items():
                    for error in errors:
                        errores.append(f"{field}: {error}")
                
                if errores:
                    messages.error(request, f"Errores de validación: {', '.join(errores)}")

        # Si llegamos aquí, mostrar el formulario con errores
        context = {
            'vacante_form': vacante_form,
            'requisito_form': requisito_form,
            'vacante': vacante,
            'accion': 'editar'
        }
        return render(request, 'usuarios/publicar_vacante.html', context)
@method_decorator(login_required, name='dispatch')
class MisVacantesView(View):
    """Vista para listar las vacantes del reclutador con paginación."""

    def get(self, request):
        if request.user.rol != 'reclutador':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
            messages.error(request, 'Tu cuenta de reclutador debe estar aprobada.')
            return redirect('index')

        es_admin = es_reclutador_admin(request.user)

        # Obtener vacantes según permisos
        if es_admin:
            # ReclutadorAdmin ve todas las vacantes
            vacantes_list = Vacante.objects.all().order_by('-fecha_actualizacion')
        else:
            # Reclutador normal solo ve sus vacantes
            vacantes_list = Vacante.objects.filter(
                reclutador=request.user.reclutador
            ).order_by('-fecha_actualizacion')

        # Crear un objeto Paginator con 5 vacantes por página
        paginator = Paginator(vacantes_list, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'vacantes': page_obj,
            'page_obj': page_obj,
            'es_reclutador_admin': es_admin,
        }

        return render(request, 'usuarios/mis_vacantes.html', context)
def index_view(request):
    """Vista de la página de inicio con vacantes publicadas y paginación."""

    # Obtener término de búsqueda
    busqueda = request.GET.get('q', '').strip()

    # ✅ FILTRO CORREGIDO PARA INCLUIR VACANTES REABIERTA
    vacantes_list = Vacante.objects.filter(
        estado_vacante='publicada',  # ✅ Estado debe ser 'publicada'
        aprobada=True               # ✅ Y debe estar aprobada
    ).select_related('secretaria', 'categoria', 'reclutador').order_by('-fecha_publicacion')

    # ✅ DEBUGGING: Log para verificar vacantes
    if request.user.is_authenticated and request.user.rol == 'reclutador':
        total_publicadas = vacantes_list.count()
        logger.info(f"Total vacantes publicadas y aprobadas: {total_publicadas}")

    # Aplicar búsqueda si existe
    if busqueda:
        vacantes_list = vacantes_list.filter(
            Q(titulo__icontains=busqueda) |
            Q(categoria__nombre__icontains=busqueda) |
            Q(municipio__icontains=busqueda)
        )

    # Configurar paginación - 5 vacantes por página
    paginator = Paginator(vacantes_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vacantes': page_obj,
        'page_obj': page_obj,
        'total_vacantes': paginator.count,
        'busqueda': busqueda,
    }
    return render(request, 'usuarios/index.html', context)


def logout_view(request):
    """Vista para cerrar sesión."""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('index')



@method_decorator(login_required, name='dispatch')
class PerfilInteresadoView(View):
    """Vista para ver/editar perfil del interesado con CV integrado - ACTUALIZADA."""

    def get(self, request):
        if request.user.rol != 'interesado':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        interesado = request.user.interesado

        # Obtener o crear curriculum
        curriculum, created = Curriculum.objects.get_or_create(
            interesado=interesado,
            defaults={'resumen_profesional': ''}
        )

        # Obtener experiencias, educación, habilidades e idiomas existentes
        experiencias = curriculum.experiencias.all()
        educaciones = curriculum.educaciones.all()
        habilidades = curriculum.habilidades.all()
        idiomas = curriculum.idiomas.all()

        # Verificar si existe CV completo
        tiene_cv = hasattr(interesado, 'curriculum')

        # ✅ VERIFICAR COMPLETITUD DEL CV INCLUYENDO UBICACIÓN
        cv_completo = curriculum.is_cv_complete if curriculum else False

        context = {
            'interesado': interesado,
            'curriculum': curriculum,
            'experiencias': experiencias,
            'educaciones': educaciones,
            'habilidades': habilidades,
            'idiomas': idiomas,
            'tiene_cv': tiene_cv,
            'cv_completo': cv_completo,  # ✅ NUEVA VARIABLE
            'es_nuevo': created,
        }
        return render(request, 'usuarios/perfil_interesado.html', context)

    def post(self, request):
        """
        Manejo de POST para guardar información completa del perfil.
        Ahora incluye manejo de ubicación detallada.
        """
        if request.user.rol != 'interesado':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        interesado = request.user.interesado
        curriculum, created = Curriculum.objects.get_or_create(
            interesado=interesado,
            defaults={'resumen_profesional': ''}
        )

        try:
            with transaction.atomic():
                # Actualizar información personal básica
                interesado.nombre = request.POST.get('nombre', '').strip()
                interesado.apellido_paterno = request.POST.get('apellido_paterno', '').strip()
                interesado.apellido_materno = request.POST.get('apellido_materno', '').strip()
                interesado.telefono = request.POST.get('telefono', '').strip()

                # Fecha de nacimiento
                fecha_nacimiento = request.POST.get('fecha_nacimiento')
                if fecha_nacimiento:
                    interesado.fecha_nacimiento = fecha_nacimiento

                # ✅ ACTUALIZAR INFORMACIÓN DE UBICACIÓN COMPLETA
                # Código postal
                codigo_postal = request.POST.get('codigo_postal', '').strip()
                if codigo_postal:
                    interesado.codigo_postal = codigo_postal

                # IDs de catálogos
                interesado.estado_id = request.POST.get('estado_id') or None
                interesado.municipio_id = request.POST.get('municipio_id') or None
                interesado.localidad_id = request.POST.get('localidad_id') or None

                # Nombres legibles
                interesado.estado_nombre = request.POST.get('estado_nombre', '').strip() or None
                interesado.municipio_nombre = request.POST.get('municipio_nombre', '').strip() or None
                interesado.localidad_nombre = request.POST.get('localidad_nombre', '').strip() or None

                # Calle y número
                interesado.calle_numero = request.POST.get('calle_numero', '').strip() or None

                # Municipio legacy (para compatibilidad)
                municipio_legacy = request.POST.get('municipio', '')
                if municipio_legacy:
                    interesado.municipio = municipio_legacy

                interesado.save()

                # Actualizar resumen profesional del curriculum
                curriculum.resumen_profesional = request.POST.get('resumen_profesional', '').strip()
                curriculum.save()

                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('perfil_interesado')

        except Exception as e:
            logger.error(f"Error guardando perfil: {str(e)}")
            messages.error(request, f'Error al guardar el perfil: {str(e)}')

        # Si hay errores, volver a mostrar el formulario con los datos
        experiencias = curriculum.experiencias.all()
        educaciones = curriculum.educaciones.all()
        habilidades = curriculum.habilidades.all()
        idiomas = curriculum.idiomas.all()

        context = {
            'interesado': interesado,
            'curriculum': curriculum,
            'experiencias': experiencias,
            'educaciones': educaciones,
            'habilidades': habilidades,
            'idiomas': idiomas,
            'tiene_cv': True,
            'cv_completo': curriculum.is_cv_complete,
            'es_nuevo': created,
        }
        return render(request, 'usuarios/perfil_interesado.html', context)

# ✅ ACTUALIZAR TAMBIÉN LA VISTA DE AUTOGUARDADO EXISTENTE
@require_POST
@csrf_exempt
def autoguardar_informacion_personal(request):
    """
    Vista existente actualizada para incluir campos de ubicación.
    """
    try:
        data = json.loads(request.body)
        interesado = request.user.interesado

        # Campos básicos existentes
        interesado.nombre = data.get('nombre', '')
        interesado.apellido_paterno = data.get('apellido_paterno', '')
        interesado.apellido_materno = data.get('apellido_materno', '')
        interesado.telefono = data.get('telefono', '')
        interesado.municipio = data.get('municipio', '')  # Campo legacy
        interesado.codigo_postal = data.get('codigo_postal', '')

        fecha_nacimiento = data.get('fecha_nacimiento')
        if fecha_nacimiento:
            interesado.fecha_nacimiento = fecha_nacimiento

        # ✅ NUEVOS CAMPOS DE UBICACIÓN DETALLADA
        interesado.estado_id = data.get('estado_id') or None
        interesado.municipio_id = data.get('municipio_id') or None
        interesado.localidad_id = data.get('localidad_id') or None
        interesado.estado_nombre = data.get('estado_nombre', '').strip() or None
        interesado.municipio_nombre = data.get('municipio_nombre', '').strip() or None
        interesado.localidad_nombre = data.get('localidad_nombre', '').strip() or None
        interesado.calle_numero = data.get('calle_numero', '').strip() or None

        interesado.save()

        return JsonResponse({
            'success': True,
            'message': 'Información personal autoguardada',
            'ubicacion_completa': interesado.ubicacion_completa
        })

    except Exception as e:
        logger.error(f"Error en autoguardar_informacion_personal: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error al autoguardar información'
        })

@method_decorator(login_required, name='dispatch')
@method_decorator(login_required, name='dispatch')
class DashboardReclutadorView(View):
    """Vista para dashboard del reclutador - ACTUALIZADA."""

    def get(self, request):
        if request.user.rol != 'reclutador':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
            messages.error(request, 'Tu cuenta de reclutador debe estar aprobada para acceder al dashboard.')
            return redirect('index')

        reclutador = request.user.reclutador
        es_admin = es_reclutador_admin(request.user)

        # Determinar las vacantes según permisos
        if es_admin:
            # ReclutadorAdmin ve todas las vacantes
            vacantes_queryset = Vacante.objects.all()
            # Para postulaciones, también ve todas
            vacantes_para_postulaciones = Vacante.objects.filter(estado_vacante='publicada')
        else:
            # Reclutador normal solo ve sus vacantes
            vacantes_queryset = reclutador.vacantes.all()
            vacantes_para_postulaciones = reclutador.vacantes.filter(estado_vacante='publicada')

        # Calcular estadísticas de vacantes por estado
        vacantes_activas = vacantes_queryset.filter(estado_vacante='publicada').count()
        vacantes_borradores = vacantes_queryset.filter(estado_vacante='borrador').count()
        vacantes_cerradas = vacantes_queryset.filter(estado_vacante='cerrada').count()
        total_vacantes = vacantes_queryset.count()

        # Obtener las últimas 3 vacantes para mostrar en el dashboard
        ultimas_vacantes = vacantes_queryset.order_by('-fecha_actualizacion')[:3]

        # Total de postulaciones recibidas
        postulaciones_recibidas = Postulacion.objects.filter(
            vacante__in=vacantes_para_postulaciones
        ).count()

        # Postulaciones nuevas (últimas 24 horas)
        from datetime import datetime, timedelta
        hace_24_horas = timezone.now() - timedelta(hours=24)
        postulaciones_nuevas = Postulacion.objects.filter(
            vacante__in=vacantes_para_postulaciones,
            fecha_postulacion__gte=hace_24_horas
        ).count()

        context = {
            'reclutador': reclutador,
            'vacantes_activas': vacantes_activas,
            'vacantes_borradores': vacantes_borradores,
            'vacantes_cerradas': vacantes_cerradas,
            'total_vacantes': total_vacantes,
            'ultimas_vacantes': ultimas_vacantes,
            'postulaciones_recibidas': postulaciones_recibidas,
            'postulaciones_nuevas': postulaciones_nuevas,
            'es_reclutador_admin': es_admin,
        }

        return render(request, 'usuarios/dashboard_reclutador.html', context)

# usuarios/views.py - REEMPLAZAR la función detalle_vacante_view existente

def detalle_vacante_view(request, vacante_id):
    """
    Muestra los detalles de una vacante específica.
    Las vacantes cerradas son visibles pero no permiten postulaciones.
    """
    try:
        # Obtener la vacante con sus relaciones
        vacante = get_object_or_404(
            Vacante.objects.select_related('secretaria', 'categoria', 'reclutador'),
            id=vacante_id
        )

        # Verificar permisos de acceso según el estado de la vacante
        if vacante.estado_vacante == 'borrador':
            # Solo el reclutador propietario puede ver sus borradores
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para ver esta vacante.')
                return redirect('login')

            if request.user.rol != 'reclutador':
                messages.error(request, 'No tienes permiso para ver esta vacante.')
                return redirect('index')

            # Verificar que sea el reclutador propietario
            if not hasattr(request.user, 'reclutador') or vacante.reclutador != request.user.reclutador:
                messages.error(request, 'No tienes permiso para ver esta vacante.')
                return redirect('mis_vacantes')

        elif vacante.estado_vacante == 'publicada':
            # Las vacantes publicadas deben estar aprobadas para el público general
            if not vacante.aprobada:
                # Solo el reclutador propietario puede ver vacantes publicadas no aprobadas
                if (not request.user.is_authenticated or
                        request.user.rol != 'reclutador' or
                        not hasattr(request.user, 'reclutador') or
                        vacante.reclutador != request.user.reclutador):
                    messages.error(request, 'Esta vacante no está disponible.')
                    return redirect('index')

        elif vacante.estado_vacante == 'eliminada':
            # Solo el reclutador propietario puede ver vacantes eliminadas
            if (not request.user.is_authenticated or
                    request.user.rol != 'reclutador' or
                    not hasattr(request.user, 'reclutador') or
                    vacante.reclutador != request.user.reclutador):
                messages.error(request, 'Esta vacante no está disponible.')
                return redirect('index')

        # ✅ Las vacantes CERRADAS son visibles para todos (sin restricciones adicionales)

        # Obtener requisitos de la vacante
        try:
            requisitos = vacante.requisitos
        except RequisitoVacante.DoesNotExist:
            requisitos = None
        except AttributeError:
            requisitos = None

        # Verificar si el usuario ya se postuló y si puede postularse
        ya_postulado = False
        puede_postularse = False

        if request.user.is_authenticated and request.user.rol == 'interesado':
            # ✅ Solo se puede postular a vacantes publicadas, aprobadas Y que no estén cerradas
            if vacante.estado_vacante == 'publicada' and vacante.aprobada:
                ya_postulado = Postulacion.objects.filter(
                    interesado=request.user.interesado,
                    vacante=vacante
                ).exists()
                puede_postularse = True
            # Si está cerrada, puede_postularse permanece False

        # Determinar si es vista de propietario (reclutador viendo su propia vacante)
        es_propietario = (
                request.user.is_authenticated and
                request.user.rol == 'reclutador' and
                hasattr(request.user, 'reclutador') and
                vacante.reclutador == request.user.reclutador
        )

        context = {
            'vacante': vacante,
            'requisitos': requisitos,
            'ya_postulado': ya_postulado,
            'puede_postularse': puede_postularse,
            'es_propietario': es_propietario,
            'estado_vacante': vacante.estado_vacante,
        }

        return render(request, 'usuarios/detalle_vacante.html', context)

    except Vacante.DoesNotExist:
        messages.error(request, 'La vacante solicitada no existe.')
        return redirect('index')
    except Exception as e:
        logger.error(f"Error en detalle_vacante_view: {str(e)}")
        messages.error(request, 'Error al cargar la vacante.')
        return redirect('index')
@login_required
@require_POST
@csrf_protect
def postularse_vacante(request, vacante_id):
    """Vista para que un interesado se postule a una vacante."""
    
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Método no permitido'})
        else:
            messages.error(request, 'Método no permitido.')
            return redirect('index')

    if request.user.rol != 'interesado':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Solo los interesados pueden postularse'})
        else:
            messages.error(request, 'No tienes permisos para postularte.')
            return redirect('index')

    try:
        # Verificar que la vacante existe y está activa
        vacante = get_object_or_404(
            Vacante,
            id=vacante_id,
            estado_vacante='publicada',
            aprobada=True
        )

        interesado = request.user.interesado
        
        # ✅ VERIFICAR QUE EL INTERESADO TIENE CURRICULUM
        if not hasattr(interesado, 'curriculum'):
            error_msg = 'Debes crear tu curriculum antes de postularte.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'redirect_url': '/perfil/interesado/'
                })
            else:
                messages.error(request, error_msg)
                return redirect('perfil_interesado')

        curriculum = interesado.curriculum
        
        # ✅ CAMBIO PRINCIPAL: USAR VALIDACIÓN BÁSICA EN LUGAR DE ESTRICTA
        try:
            # Intentar usar la nueva validación básica
            errores_cv = curriculum.validation_errors_basic
        except AttributeError:
            # Fallback: Si no existe el método, usar validación más permisiva
            errores_cv = []
            
            # Validaciones mínimas esenciales
            if not interesado.nombre or not interesado.nombre.strip():
                errores_cv.append('Nombre')
            if not interesado.apellido_paterno or not interesado.apellido_paterno.strip():
                errores_cv.append('Apellido Paterno')
            if not interesado.telefono or not interesado.telefono.strip():
                errores_cv.append('Teléfono')
            if not interesado.fecha_nacimiento:
                errores_cv.append('Fecha de Nacimiento')
            if not interesado.codigo_postal or not interesado.codigo_postal.strip():
                errores_cv.append('Código Postal')
            if not curriculum.resumen_profesional or not curriculum.resumen_profesional.strip():
                errores_cv.append('Resumen Profesional')
            if not curriculum.habilidades.exists():
                errores_cv.append('Al menos una habilidad')

        if errores_cv:
            error_msg = f'Tu perfil básico está incompleto. Campos faltantes: {", ".join(errores_cv)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'missing_fields': errores_cv,
                    'redirect_url': '/perfil/interesado/'
                })
            else:
                messages.error(request, error_msg)
                return redirect('perfil_interesado')

        # Verificar si ya se postuló
        if Postulacion.objects.filter(interesado=interesado, vacante=vacante).exists():
            error_msg = 'Ya te has postulado a esta vacante'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            else:
                messages.warning(request, error_msg)
                return redirect('detalle_vacante', vacante_id=vacante_id)

        # Verificar límite de postulantes
        postulaciones_actuales = vacante.postulaciones.count()
        if postulaciones_actuales >= vacante.max_postulantes:
            error_msg = 'Esta vacante ya alcanzó el límite máximo de postulantes'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            else:
                messages.error(request, error_msg)
                return redirect('detalle_vacante', vacante_id=vacante_id)

        # Obtener mensaje de motivación
        mensaje_motivacion = request.POST.get('mensaje_motivacion', '').strip()

        # Crear la postulación
        postulacion = Postulacion.objects.create(
            interesado=interesado,
            vacante=vacante,
            curriculum=curriculum,
            mensaje_motivacion=mensaje_motivacion,
            estado='enviada'
        )

        success_msg = 'Te has postulado exitosamente a esta vacante'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': success_msg,
                'postulacion_id': postulacion.id
            })
        else:
            messages.success(request, success_msg)
            return redirect('detalle_vacante', vacante_id=vacante_id)

    except Vacante.DoesNotExist:
        error_msg = 'Vacante no encontrada o no disponible'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        else:
            messages.error(request, error_msg)
            return redirect('index')
            
    except Exception as e:
        logger.error(f"Error en postularse_vacante: {str(e)}")
        error_msg = f'Error al procesar la postulación: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        else:
            messages.error(request, error_msg)
            return redirect('detalle_vacante', vacante_id=vacante_id)

@login_required
def mis_postulaciones(request):
    """Vista para ver las postulaciones del interesado con paginación."""
    if request.user.rol != 'interesado':
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')

    postulaciones_list = Postulacion.objects.filter(
        interesado=request.user.interesado
    ).select_related('vacante', 'vacante__secretaria').order_by('-fecha_postulacion')

    # Configurar paginación - 5 postulaciones por página
    paginator = Paginator(postulaciones_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'postulaciones': page_obj,
        'page_obj': page_obj
    }
    return render(request, 'usuarios/mis_postulaciones.html', context)
@csrf_exempt
@login_required
@require_http_methods(["POST", "DELETE"])
def retirar_postulacion(request, postulacion_id):
    # Verificar permisos
    if request.user.rol != 'interesado':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Solo los interesados pueden retirar postulaciones.'
            }, status=403)
        else:
            messages.error(request, 'No tienes permiso para realizar esta acción.')
            return redirect('index')

    try:
        # Buscar la postulación que pertenece al interesado
        postulacion = get_object_or_404(
            Postulacion,
            id=postulacion_id,
            interesado=request.user.interesado
        )

        # Verificar que la postulación se puede retirar
        # Solo se pueden retirar postulaciones en estado 'enviada' o 'en_revision'
        estados_retirables = ['enviada', 'en_revision']

        if postulacion.estado not in estados_retirables:
            error_msg = f'No puedes retirar esta postulación porque está en estado: {postulacion.get_estado_display()}'

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=400)
            else:
                messages.error(request, error_msg)
                return redirect('mis_postulaciones')

        # Guardar información para el mensaje
        vacante_titulo = postulacion.vacante.titulo

        # Eliminar la postulación
        postulacion.delete()

        # Mensaje de éxito
        success_msg = f'Has retirado exitosamente tu postulación para "{vacante_titulo}"'

        # Responder según el tipo de request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': success_msg
            })
        else:
            messages.success(request, success_msg)
            return redirect('mis_postulaciones')

    except Postulacion.DoesNotExist:
        error_msg = 'Postulación no encontrada o no tienes permiso para retirarla.'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=404)
        else:
            messages.error(request, error_msg)
            return redirect('mis_postulaciones')

    except Exception as e:
        # Log del error para debugging
        print(f"Error en retirar_postulacion: {str(e)}")

        error_msg = f'Error interno del servidor: {str(e)}'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)
        else:
            messages.error(request, error_msg)
            return redirect('mis_postulaciones')


def test_urls(request):
    """Vista de prueba para verificar que las URLs funcionen"""
    return JsonResponse({
        'status': 'OK',
        'message': 'Las URLs están funcionando correctamente',
        'user': str(request.user),
        'method': request.method
    })


@login_required
@require_POST
@csrf_protect
def cerrar_vacante_ajax(request, vacante_id):
    """
    Vista AJAX para cerrar una vacante activa.
    Solo el reclutador propietario puede cerrar sus vacantes.
    """

    # Verificar permisos básicos
    if request.user.rol != 'reclutador':
        return JsonResponse({
            'success': False,
            'error': 'Solo los reclutadores pueden cerrar vacantes.'
        }, status=403)

    if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
        return JsonResponse({
            'success': False,
            'error': 'Tu cuenta de reclutador debe estar aprobada.'
        }, status=403)

    try:
        # Verificar permisos: ReclutadorAdmin puede cerrar cualquier vacante
        if es_reclutador_admin(request.user):
            vacante = get_object_or_404(Vacante, id=vacante_id)
        else:
            # Reclutador normal solo puede cerrar sus vacantes
            vacante = get_object_or_404(
                Vacante,
                id=vacante_id,
                reclutador=request.user.reclutador
            )

        # Verificar que la vacante esté en estado 'publicada'
        if vacante.estado_vacante != 'publicada':
            return JsonResponse({
                'success': False,
                'error': f'No se puede cerrar una vacante en estado "{vacante.get_estado_vacante_display()}".'
            }, status=400)

        # Obtener número actual de postulaciones
        postulaciones_actuales = vacante.postulaciones.count()

        # Cambiar estado a cerrada
        vacante.estado_vacante = 'cerrada'
        vacante.save()

        # Log de la acción
        logger.info(f"Vacante {vacante_id} cerrada por reclutador {request.user.email}")

        return JsonResponse({
            'success': True,
            'message': f'Vacante "{vacante.titulo}" cerrada exitosamente.',
            'nuevo_estado': 'cerrada',
            'nuevo_estado_display': 'Cerrada',
            'postulaciones_actuales': postulaciones_actuales,
            'limite_postulaciones': vacante.max_postulantes,
            'puede_reabrir': postulaciones_actuales < vacante.max_postulantes
        })

    except Exception as e:
        logger.error(f"Error cerrando vacante {vacante_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

@login_required
@require_POST
@csrf_protect
def reabrir_vacante_ajax(request, vacante_id):
    """
    Vista AJAX para reabrir una vacante cerrada.
    Si la fecha límite ya pasó, automáticamente extiende la fecha por 30 días.
    """

    # Verificar permisos básicos
    if request.user.rol != 'reclutador':
        return JsonResponse({
            'success': False,
            'error': 'Solo los reclutadores pueden reabrir vacantes.'
        }, status=403)

    if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
        return JsonResponse({
            'success': False,
            'error': 'Tu cuenta de reclutador debe estar aprobada.'
        }, status=403)

    try:
        # Verificar permisos: ReclutadorAdmin puede reabrir cualquier vacante
        if es_reclutador_admin(request.user):
            vacante = get_object_or_404(Vacante, id=vacante_id)
        else:
            # Reclutador normal solo puede reabrir sus vacantes
            vacante = get_object_or_404(
                Vacante,
                id=vacante_id,
                reclutador=request.user.reclutador
            )

        # Verificar que la vacante esté en estado 'cerrada'
        if vacante.estado_vacante != 'cerrada':
            return JsonResponse({
                'success': False,
                'error': f'No se puede reabrir una vacante en estado "{vacante.get_estado_vacante_display()}".'
            }, status=400)

        # ✅ VALIDACIÓN CRÍTICA: Verificar límite de postulaciones
        postulaciones_actuales = vacante.postulaciones.count()

        if postulaciones_actuales >= vacante.max_postulantes:
            return JsonResponse({
                'success': False,
                'error': f'No se puede reabrir la vacante porque ya alcanzó el límite máximo de {vacante.max_postulantes} postulaciones ({postulaciones_actuales} recibidas).'
            }, status=400)

        # ✅ NUEVA LÓGICA: Verificar y extender fecha límite automáticamente
        fecha_extendida = False
        nueva_fecha_limite = None
        mensaje_fecha = ""

        if vacante.fecha_limite:
            from datetime import date, timedelta
            hoy = date.today()

            if vacante.fecha_limite < hoy:
                # ✅ EXTENDER AUTOMÁTICAMENTE LA FECHA LÍMITE POR 30 DÍAS
                nueva_fecha_limite = hoy + timedelta(days=30)
                vacante.fecha_limite = nueva_fecha_limite
                fecha_extendida = True

                # Formatear fecha para el mensaje
                fecha_formateada = nueva_fecha_limite.strftime('%d de %B de %Y')
                mensaje_fecha = f" La fecha límite se ha extendido automáticamente hasta el {fecha_formateada}."

                logger.info(
                    f"Fecha límite de vacante {vacante_id} extendida automáticamente hasta {nueva_fecha_limite}")

        # Cambiar estado a publicada
        vacante.estado_vacante = 'publicada'
        vacante.save()

        # ✅ MENSAJE PERSONALIZADO SEGÚN SI SE EXTENDIÓ LA FECHA O NO
        if fecha_extendida:
            mensaje_principal = f'Vacante "{vacante.titulo}" reabierta exitosamente.{mensaje_fecha}'
        else:
            mensaje_principal = f'Vacante "{vacante.titulo}" reabierta exitosamente.'

        # Log de la acción
        logger.info(f"Vacante {vacante_id} reabierta por reclutador {request.user.email}")

        return JsonResponse({
            'success': True,
            'message': mensaje_principal,
            'nuevo_estado': 'publicada',
            'nuevo_estado_display': 'Activa',
            'postulaciones_actuales': postulaciones_actuales,
            'limite_postulaciones': vacante.max_postulantes,
            'espacios_disponibles': vacante.max_postulantes - postulaciones_actuales,
            # ✅ INFORMACIÓN ADICIONAL SOBRE LA EXTENSIÓN DE FECHA
            'fecha_extendida': fecha_extendida,
            'nueva_fecha_limite': nueva_fecha_limite.strftime('%Y-%m-%d') if nueva_fecha_limite else None,
            'fecha_limite_formateada': nueva_fecha_limite.strftime('%d de %B de %Y') if nueva_fecha_limite else None
        })

    except Exception as e:
        logger.error(f"Error reabriendo vacante {vacante_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

@login_required
@require_POST
@csrf_protect
def eliminar_borrador_ajax(request, vacante_id):
    """
    Vista AJAX para eliminar permanentemente un borrador.
    Solo se pueden eliminar vacantes en estado 'borrador'.
    """

    # Verificar permisos básicos
    if request.user.rol != 'reclutador':
        return JsonResponse({
            'success': False,
            'error': 'Solo los reclutadores pueden eliminar borradores.'
        }, status=403)

    if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
        return JsonResponse({
            'success': False,
            'error': 'Tu cuenta de reclutador debe estar aprobada.'
        }, status=403)

    try:
        # Verificar permisos: ReclutadorAdmin puede eliminar cualquier borrador
        if es_reclutador_admin(request.user):
            vacante = get_object_or_404(Vacante, id=vacante_id)
        else:
            # Reclutador normal solo puede eliminar sus borradores
            vacante = get_object_or_404(
                Vacante,
                id=vacante_id,
                reclutador=request.user.reclutador
            )

        # Verificar que la vacante esté en estado 'borrador'
        if vacante.estado_vacante != 'borrador':
            return JsonResponse({
                'success': False,
                'error': f'Solo se pueden eliminar borradores. Esta vacante está en estado "{vacante.get_estado_vacante_display()}".'
            }, status=400)

        # Verificar que no tenga postulaciones (por seguridad)
        if vacante.postulaciones.exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar un borrador que tiene postulaciones asociadas.'
            }, status=400)

        # Guardar información para el mensaje
        titulo_vacante = vacante.titulo

        # Eliminar la vacante (esto también elimina los requisitos por cascada)
        vacante.delete()

        # Log de la acción
        logger.info(f"Borrador {vacante_id} eliminado por reclutador {request.user.email}")

        return JsonResponse({
            'success': True,
            'message': f'Borrador "{titulo_vacante}" eliminado permanentemente.',
            'vacante_eliminada': True
        })

    except Exception as e:
        logger.error(f"Error eliminando borrador {vacante_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

@login_required
def obtener_estado_vacante_ajax(request, vacante_id):
    """
    Vista AJAX para obtener el estado actual de una vacante y sus estadísticas.
    Útil para actualizar la interfaz después de acciones.
    """

    if request.user.rol != 'reclutador':
        return JsonResponse({
            'success': False,
            'error': 'Solo los reclutadores pueden consultar el estado de vacantes.'
        }, status=403)

    try:
        # Verificar permisos: ReclutadorAdmin puede consultar cualquier vacante
        if es_reclutador_admin(request.user):
            vacante = get_object_or_404(Vacante, id=vacante_id)
        else:
            # Reclutador normal solo puede consultar sus vacantes
            vacante = get_object_or_404(
                Vacante,
                id=vacante_id,
                reclutador=request.user.reclutador
            )

        # Calcular estadísticas
        postulaciones_actuales = vacante.postulaciones.count()
        puede_reabrir = (
                vacante.estado_vacante == 'cerrada' and
                postulaciones_actuales < vacante.max_postulantes
        )

        # Verificar fecha límite
        fecha_limite_pasada = False
        if vacante.fecha_limite:
            from datetime import date
            fecha_limite_pasada = vacante.fecha_limite < date.today()

        return JsonResponse({
            'success': True,
            'estado': vacante.estado_vacante,
            'estado_display': vacante.get_estado_vacante_display(),
            'postulaciones_actuales': postulaciones_actuales,
            'limite_postulaciones': vacante.max_postulantes,
            'espacios_disponibles': vacante.max_postulantes - postulaciones_actuales,
            'puede_reabrir': puede_reabrir and not fecha_limite_pasada,
            'fecha_limite_pasada': fecha_limite_pasada,
            'titulo': vacante.titulo
        })

    except Exception as e:
        logger.error(f"Error obteniendo estado de vacante {vacante_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

@method_decorator(login_required, name='dispatch')
class VerPostulantesView(View):
    """
    Vista para que los reclutadores vean los postulantes de una vacante específica.
    """

    def get(self, request, vacante_id):
        # Verificar que el usuario sea reclutador
        if request.user.rol != 'reclutador':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        # Verificar que el reclutador esté aprobado
        if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
            messages.error(request, 'Tu cuenta de reclutador debe estar aprobada.')
            return redirect('dashboard_reclutador')

        try:
            # Verificar permisos: ReclutadorAdmin puede ver cualquier vacante
            if es_reclutador_admin(request.user):
                vacante = get_object_or_404(
                    Vacante.objects.select_related('secretaria', 'categoria'),
                    id=vacante_id
                )
            else:
                # Reclutador normal solo puede ver sus vacantes
                vacante = get_object_or_404(
                    Vacante.objects.select_related('secretaria', 'categoria'),
                    id=vacante_id,
                    reclutador=request.user.reclutador
                )
        except Vacante.DoesNotExist:
            messages.error(request, 'Vacante no encontrada o no tienes permiso para verla.')
            return redirect('mis_vacantes')

        # Obtener todas las postulaciones para esta vacante
        postulaciones = Postulacion.objects.filter(
            vacante=vacante
        ).select_related(
            'interesado',
            'curriculum'
        ).prefetch_related(
            'curriculum__habilidades__habilidad'
        ).order_by('-fecha_postulacion')

        # Calcular estadísticas
        estadisticas = self._calcular_estadisticas(postulaciones)

        context = {
            'vacante': vacante,
            'postulaciones': postulaciones,
            'estadisticas': estadisticas,
        }

        return render(request, 'usuarios/ver_postulantes.html', context)

    def _calcular_estadisticas(self, postulaciones):
        """
        Calcula las estadísticas de las postulaciones.
        """

        total_postulantes = postulaciones.count()

        # Contar postulaciones por estado
        estados = postulaciones.values('estado').annotate(count=Count('estado'))
        estado_counts = {estado['estado']: estado['count'] for estado in estados}

        # Contar nuevos hoy
        nuevos_hoy = postulaciones.filter(
            fecha_postulacion__date=date.today()
        ).count()

        return {
            'total_postulantes': total_postulantes,
            'nuevos_hoy': nuevos_hoy,
            'en_revision': estado_counts.get('en_revision', 0),
            'entrevista': estado_counts.get('entrevista', 0),
            'aceptados': estado_counts.get('aceptada', 0),
            'rechazados': estado_counts.get('rechazada', 0),
            'enviadas': estado_counts.get('enviada', 0),
            'preseleccionados': estado_counts.get('preseleccionado', 0),
        }

@login_required
def cambiar_estado_postulacion(request, postulacion_id):
    """
    Vista AJAX para cambiar el estado de una postulación.
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        }, status=405)

    # Verificar que sea un reclutador
    if request.user.rol != 'reclutador':
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para esta acción'
        }, status=403)

    try:
        import json
        data = json.loads(request.body)
        nuevo_estado = data.get('nuevo_estado')

        # Validar que el nuevo estado sea válido
        estados_validos = [choice[0] for choice in Postulacion.ESTADOS_POSTULACION]
        if nuevo_estado not in estados_validos:
            return JsonResponse({
                'success': False,
                'error': 'Estado no válido'
            }, status=400)

        # Obtener la postulación y verificar que pertenezca a una vacante del reclutador
        postulacion = get_object_or_404(
            Postulacion.objects.select_related('vacante', 'interesado'),
            id=postulacion_id,
            vacante__reclutador=request.user.reclutador
        )

        # Guardar el estado anterior para logging
        estado_anterior = postulacion.estado

        # Actualizar el estado
        postulacion.estado = nuevo_estado
        postulacion.save()

        # Obtener el display name del nuevo estado
        estado_display = postulacion.get_estado_display()

        # Log de la acción (opcional)
        print(f"Reclutador {request.user.email} cambió estado de postulación {postulacion_id} "
              f"de '{estado_anterior}' a '{nuevo_estado}'")

        return JsonResponse({
            'success': True,
            'message': f'Estado actualizado exitosamente',
            'estado_display': estado_display,
            'postulacion_id': postulacion_id
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Postulacion.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Postulación no encontrada o no tienes permiso para modificarla'
        }, status=404)
    except Exception as e:
        print(f"Error en cambiar_estado_postulacion: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)
        
@login_required
def ver_perfil_candidato(request, interesado_id):
    """
    Vista para que los reclutadores vean el perfil completo de un candidato.
    Solo puede acceder si el candidato se ha postulado a alguna de sus vacantes.
    """

    # Verificar que sea un reclutador
    if request.user.rol != 'reclutador':
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')

    # Verificar que el reclutador esté aprobado
    if not hasattr(request.user, 'reclutador') or not request.user.reclutador.aprobado:
        messages.error(request, 'Tu cuenta de reclutador debe estar aprobada.')
        return redirect('dashboard_reclutador')

    try:
        # Obtener el interesado
        interesado = get_object_or_404(
            Interesado.objects.select_related('usuario'),
            id=interesado_id
        )

        # Verificar que el candidato se haya postulado a alguna vacante del reclutador
        tiene_postulacion = Postulacion.objects.filter(
            interesado=interesado,
            vacante__reclutador=request.user.reclutador
        ).exists()

        if not tiene_postulacion:
            messages.error(request, 'No tienes permiso para ver este perfil.')
            return redirect('dashboard_reclutador')

        # Obtener o crear curriculum
        curriculum = None
        experiencias = []
        educaciones = []
        habilidades = []
        idiomas = []

        try:
            curriculum = interesado.curriculum
            experiencias = curriculum.experiencias.all().order_by('-fecha_inicio')
            educaciones = curriculum.educaciones.all().order_by('-fecha_inicio')
            habilidades = curriculum.habilidades.select_related('habilidad').all()
            idiomas = curriculum.idiomas.all()
        except Curriculum.DoesNotExist:
            pass

        # Obtener postulaciones del candidato a vacantes del reclutador
        postulaciones_relacionadas = Postulacion.objects.filter(
            interesado=interesado,
            vacante__reclutador=request.user.reclutador
        ).select_related('vacante').order_by('-fecha_postulacion')

        context = {
            'interesado': interesado,
            'curriculum': curriculum,
            'experiencias': experiencias,
            'educaciones': educaciones,
            'habilidades': habilidades,
            'idiomas': idiomas,
            'postulaciones_relacionadas': postulaciones_relacionadas,
            'es_vista_reclutador': True,  # Flag para adaptar el template
        }

        return render(request, 'usuarios/perfil_candidato_reclutador.html', context)

    except Exception as e:
        print(f"Error en ver_perfil_candidato: {str(e)}")
        messages.error(request, 'Error al cargar el perfil del candidato.')
        return redirect('dashboard_reclutador')


def buscar_vacantes(request):
    """Vista para buscar vacantes con filtros y paginación."""

    # Obtener parámetros de búsqueda
    query = request.GET.get('q', '').strip()
    tipo_empleo = request.GET.get('tipo_empleo', '')
    municipio = request.GET.get('municipio', '')

    # ✅ FILTRO CORREGIDO: INCLUIR VACANTES REABIERTA
    vacantes_list = Vacante.objects.filter(
        estado_vacante='publicada',  # ✅ Estado debe ser 'publicada'
        aprobada=True               # ✅ Y debe estar aprobada
    ).select_related('secretaria', 'reclutador', 'categoria').order_by('-fecha_publicacion')

    # Aplicar filtro de búsqueda por texto
    if query:
        vacantes_list = vacantes_list.filter(
            Q(titulo__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(categoria__nombre__icontains=query) |
            Q(secretaria__nombre__icontains=query) |
            Q(requisitos__descripcion_requisitos__icontains=query) |
            Q(requisitos__educacion_minima__icontains=query) |
            Q(requisitos__experiencia_minima__icontains=query)
        ).distinct()

    # Aplicar filtro por tipo de empleo
    if tipo_empleo:
        vacantes_list = vacantes_list.filter(tipo_empleo=tipo_empleo)

    # Aplicar filtro por municipio
    if municipio:
        vacantes_list = vacantes_list.filter(municipio=municipio)

    # Configurar paginación - 5 vacantes por página
    paginator = Paginator(vacantes_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vacantes': page_obj,
        'page_obj': page_obj,
        'query': query,
        'tipo_empleo': tipo_empleo,
        'municipio': municipio,
        'total_resultados': paginator.count,
    }

    return render(request, 'usuarios/index.html', context)

@require_http_methods(["GET"])
def busqueda_vacantes_ajax(request):
    """Vista AJAX para búsqueda en tiempo real."""
    busqueda = request.GET.get('q', '').strip()

    vacantes = Vacante.objects.filter(
        estado_vacante='publicada',
        aprobada=True
    ).select_related('secretaria', 'categoria')

    if busqueda:
        vacantes = vacantes.filter(
            Q(titulo__icontains=busqueda) |
            Q(municipio__icontains=busqueda)|
            Q(categoria__nombre__icontains=busqueda) |
            Q(secretaria__nombre__icontains=busqueda)
        )

    vacantes = vacantes.order_by('-fecha_publicacion')[:12]

    html = render_to_string('usuarios/vacantes_lista.html', {'vacantes': vacantes})
    return JsonResponse({'html': html})