# usuarios/views.py

# Importaciones de Django core
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse, Http404
from django.template.loader import render_to_string
from django.forms import modelformset_factory
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from datetime import date
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
    Categoria,
    Postulacion
)

# Importaciones de formularios locales
from .forms import (
    LoginForm,
    InteresadoRegistroForm,
    SecretariaRegistroForm,
    ReclutadorRegistroForm,
    VacanteForm,
    RequisitoVacanteForm,
    CurriculumForm,
    InteresadoPerfilForm,
    ExperienciaLaboralForm,
    EducacionForm,
    HabilidadInteresadoForm,
    IdiomaInteresadoForm
)


# =========================================
# VISTAS AJAX PARA HABILIDADES - CORREGIDAS
# =========================================

@login_required
def agregar_habilidad_ajax(request):
    """
    Vista AJAX para agregar una nueva habilidad al CV del interesado.

    Parámetros esperados en POST:
    - nombre_habilidad: Nombre de la habilidad (ej: "JavaScript", "Liderazgo")
    - nivel: Nivel de dominio (basico, intermedio, avanzado, experto)

    Returns:
        JsonResponse con success/error y datos de la habilidad creada
    """

    # Validar método y permisos
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
                'descripcion': f'Habilidad: {nombre_habilidad}'
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
# RESTO DE LAS VISTAS (mantener igual)
# =========================================

class LoginView(View):
    """Vista para inicio de sesión de usuarios."""

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
                login(request, user)
                # Redirigir según el rol
                if user.rol == 'interesado':
                    return redirect('perfil_interesado')
                elif user.rol == 'reclutador':
                    # Verificar si el reclutador está aprobado
                    if hasattr(user, 'reclutador') and user.reclutador.aprobado:
                        return redirect('dashboard_reclutador')
                    else:
                        messages.warning(request, 'Tu cuenta de reclutador está pendiente de aprobación.')
                        logout(request)
                        return redirect('login')
                elif user.rol == 'administrador':
                    return redirect('admin:index')
            else:
                messages.error(request, 'Correo o contraseña incorrectos. Intenta nuevamente.')
        return render(request, 'usuarios/login.html', {'form': form})


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
                with transaction.atomic():
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


# usuarios/views.py - Vista actualizada para manejar guardado automático de imagen

@login_required
def actualizar_perfil_ajax(request):
    """Vista AJAX para actualizar perfil del interesado."""
    if request.method != 'POST' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        interesado = request.user.interesado

        # Verificar si solo se está actualizando la foto
        only_photo = 'foto_perfil' in request.FILES and len(request.POST) <= 2  # Solo CSRF y posiblemente un campo más

        if not only_photo:
            # Actualizar campos de texto solo si no es actualización de foto únicamente
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

        # Validar y procesar foto de perfil
        if 'foto_perfil' in request.FILES:
            foto = request.FILES['foto_perfil']

            # Validar tipo de archivo
            if not foto.name.lower().endswith(('.jpg', '.jpeg')):
                return JsonResponse({
                    'success': False,
                    'error': 'Solo se permiten archivos JPG'
                })

            # Validar tamaño (5MB máximo)
            if foto.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'success': False,
                    'error': 'El archivo es demasiado grande. Máximo 5MB'
                })

            # Para imágenes ya recortadas (blob), no necesitan procesamiento adicional
            # Ya vienen en el tamaño correcto de 160x160px
            interesado.foto_perfil = foto

        interesado.save()

        return JsonResponse({
            'success': True,
            'message': 'Perfil actualizado exitosamente' if not only_photo else 'Imagen guardada exitosamente',
            'data': {
                'nombre_completo': interesado.nombre_completo,
                'telefono': interesado.telefono or 'No especificado',
                'ubicacion': interesado.ubicacion_completa,
                'foto_url': interesado.foto_perfil.url if interesado.foto_perfil else None
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def actualizar_foto_perfil_ajax(request):
    """
    Vista AJAX específica para actualizar solo la foto de perfil del interesado
    """
    try:
        # Verificar que el usuario sea un interesado
        if not hasattr(request.user, 'interesado'):
            return JsonResponse({
                'success': False,
                'error': 'Usuario no autorizado'
            }, status=403)

        interesado = request.user.interesado

        # Verificar que se envió una foto
        if 'foto_perfil' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No se recibió ninguna imagen'
            }, status=400)

        foto_file = request.FILES['foto_perfil']

        # Validar tipo de archivo
        if not foto_file.content_type.startswith('image/'):
            return JsonResponse({
                'success': False,
                'error': 'El archivo debe ser una imagen'
            }, status=400)

        # Validar tamaño del archivo (5MB máximo)
        if foto_file.size > 5 * 1024 * 1024:  # 5MB
            return JsonResponse({
                'success': False,
                'error': 'La imagen no debe superar los 5MB'
            }, status=400)

        # Procesar la imagen
        try:
            # Abrir la imagen con PIL para procesarla
            image = Image.open(foto_file)

            # Convertir a RGB si es necesario (para JPEGs)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')

            # Redimensionar si es muy grande (máximo 800x800 antes de guardar)
            max_size = (800, 800)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Guardar la imagen procesada en memoria
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)

            # Generar nombre único para el archivo
            filename = f"perfil_{interesado.id}_{uuid.uuid4().hex[:8]}.jpg"

            # Eliminar foto anterior si existe
            if interesado.foto_perfil:
                try:
                    # Eliminar archivo físico anterior
                    if default_storage.exists(interesado.foto_perfil.name):
                        default_storage.delete(interesado.foto_perfil.name)
                except Exception as e:
                    # Log el error pero continúa (no es crítico)
                    print(f"Error al eliminar foto anterior: {e}")

            # Guardar nueva foto
            foto_content = ContentFile(output.getvalue(), name=filename)
            interesado.foto_perfil.save(filename, foto_content, save=True)

            # Construir URL completa de la foto
            foto_url = request.build_absolute_uri(interesado.foto_perfil.url)

            return JsonResponse({
                'success': True,
                'message': 'Foto de perfil actualizada correctamente',
                'photo_url': foto_url,
                'photo_name': filename
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al procesar la imagen: {str(e)}'
            }, status=500)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)


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


@login_required
def eliminar_experiencia_ajax(request, experiencia_id):
    """Vista AJAX para eliminar experiencia laboral."""
    if request.method != 'DELETE' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        curriculum = request.user.interesado.curriculum
        experiencia = get_object_or_404(ExperienciaLaboral, id=experiencia_id, curriculum=curriculum)
        experiencia.delete()

        return JsonResponse({
            'success': True,
            'message': 'Experiencia eliminada exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def eliminar_educacion_ajax(request, educacion_id):
    """Vista AJAX para eliminar educación."""
    if request.method != 'DELETE' or request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    try:
        curriculum = request.user.interesado.curriculum
        educacion = get_object_or_404(Educacion, id=educacion_id, curriculum=curriculum)
        educacion.delete()

        return JsonResponse({
            'success': True,
            'message': 'Educación eliminada exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


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


@login_required
def descargar_cv_pdf(request):
    """Vista para generar y descargar CV en PDF."""
    if request.user.rol != 'interesado':
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')

    interesado = request.user.interesado

    try:
        curriculum = interesado.curriculum
    except Curriculum.DoesNotExist:
        messages.warning(request, 'Primero debes crear tu CV.')
        return redirect('crear_editar_cv')

    # Preparar datos para el PDF
    context = {
        'interesado': interesado,
        'curriculum': curriculum,
        'experiencias': curriculum.experiencias.all(),
        'educaciones': curriculum.educaciones.all(),
        'habilidades': curriculum.habilidades.all(),
        'idiomas': curriculum.idiomas.all(),
    }

    # Renderizar HTML
    html_string = render_to_string('usuarios/cv_pdf_template.html', context)

    # Generar PDF
    try:
        html_doc = HTML(string=html_string)
        pdf_bytes = html_doc.write_pdf()

        # Preparar respuesta
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f"CV_{interesado.nombre}_{interesado.apellido_paterno}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
    except Exception as e:
        messages.error(request, f'Error al generar PDF: {str(e)}')
        return redirect('perfil_interesado')

@login_required
# Agregar esta vista al archivo usuarios/views.py

@login_required
def descargar_cv_pdf_reclutador(request):
    """Vista para que reclutadores descarguen CV de interesados que se postularon a sus vacantes."""

    # Verificar que el usuario sea reclutador
    if request.user.rol != 'reclutador':
        messages.error(request, 'No tienes permiso para descargar CVs.')
        return redirect('index')

    # Verificar que el reclutador esté aprobado
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

        # Verificar que el reclutador tenga permiso para ver este CV
        # (el interesado debe haberse postulado a alguna vacante del reclutador)
        tiene_permiso = Postulacion.objects.filter(
            interesado=interesado,
            vacante__reclutador=request.user.reclutador
        ).exists()

        if not tiene_permiso:
            messages.error(request, 'No tienes permiso para descargar este CV.')
            return redirect('mis_vacantes')

        # Verificar que el interesado tenga CV
        if not hasattr(interesado, 'curriculum'):
            messages.error(request, 'Este interesado no tiene CV disponible.')
            return redirect('mis_vacantes')

        curriculum = interesado.curriculum

        # Verificar que el CV tenga contenido mínimo
        if not curriculum.resumen_profesional and not curriculum.experiencias.exists():
            messages.error(request, 'El CV de este interesado está incompleto.')
            return redirect('mis_vacantes')

        # Preparar datos para el PDF
        context = {
            'interesado': interesado,
            'curriculum': curriculum,
            'experiencias': curriculum.experiencias.all(),
            'educaciones': curriculum.educaciones.all(),
            'habilidades': curriculum.habilidades.all(),
            'idiomas': curriculum.idiomas.all(),
        }

        # Renderizar HTML usando el template existente
        html_string = render_to_string('usuarios/cv_pdf_template.html', context)

        # Generar PDF
        try:
            html_doc = HTML(string=html_string)
            pdf_bytes = html_doc.write_pdf()

            # Preparar respuesta
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"CV_{interesado.nombre}_{interesado.apellido_paterno}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            messages.error(request, f'Error al generar PDF: {str(e)}')
            return redirect('mis_vacantes')

    except Interesado.DoesNotExist:
        messages.error(request, 'Interesado no encontrado.')
        return redirect('mis_vacantes')
    except Exception as e:
        messages.error(request, f'Error interno: {str(e)}')
        return redirect('mis_vacantes')

@method_decorator(login_required, name='dispatch')
class PublicarVacanteView(View):
    """Vista para publicar una nueva vacante."""

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
        vacante_form = VacanteForm(request.POST)
        requisito_form = RequisitoVacanteForm(request.POST)

        if vacante_form.is_valid() and requisito_form.is_valid():
            try:
                with transaction.atomic():
                    # Determinar la acción del usuario
                    accion = request.POST.get('accion')

                    # Crear la vacante
                    vacante = vacante_form.save(commit=False)
                    vacante.secretaria = reclutador.secretaria
                    vacante.reclutador = reclutador

                    # Establecer el estado según la acción
                    if accion == 'guardar_borrador':
                        vacante.estado_vacante = 'borrador'
                        mensaje = 'Vacante guardada como borrador exitosamente.'
                    elif accion == 'publicar':
                        vacante.estado_vacante = 'publicada'
                        vacante.aprobada = True  # Puedes cambiar esto si requieres aprobación admin
                        mensaje = 'Vacante publicada exitosamente.'
                    else:
                        vacante.estado_vacante = 'borrador'
                        mensaje = 'Vacante guardada como borrador exitosamente.'

                    vacante.save()

                    # Crear los requisitos
                    requisito = requisito_form.save(commit=False)
                    requisito.vacante = vacante
                    requisito.save()

                    messages.success(request, mensaje)
                    return redirect('mis_vacantes')

            except Exception as e:
                messages.error(request, f'Error al guardar la vacante: {str(e)}')

        context = {
            'vacante_form': vacante_form,
            'requisito_form': requisito_form,
            'accion': 'crear'
        }
        return render(request, 'usuarios/publicar_vacante.html', context)


@method_decorator(login_required, name='dispatch')
class EditarVacanteView(View):
    """Vista para editar una vacante existente."""

    def get(self, request, vacante_id):
        if request.user.rol != 'reclutador':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        try:
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

        try:
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

        vacante_form = VacanteForm(request.POST, instance=vacante)
        requisito_form = RequisitoVacanteForm(request.POST, instance=requisito)

        if vacante_form.is_valid() and requisito_form.is_valid():
            try:
                with transaction.atomic():
                    # Determinar la acción del usuario
                    accion = request.POST.get('accion')

                    # Actualizar la vacante
                    vacante = vacante_form.save(commit=False)

                    # Establecer el estado según la acción
                    if accion == 'guardar_borrador':
                        vacante.estado_vacante = 'borrador'
                        mensaje = 'Vacante actualizada y guardada como borrador.'
                    elif accion == 'publicar':
                        vacante.estado_vacante = 'publicada'
                        vacante.aprobada = True  # Puedes cambiar esto si requieres aprobación admin
                        mensaje = 'Vacante actualizada y publicada exitosamente.'
                    else:
                        mensaje = 'Vacante actualizada exitosamente.'

                    vacante.save()

                    # Actualizar los requisitos
                    requisito_form.save()

                    messages.success(request, mensaje)
                    return redirect('mis_vacantes')

            except Exception as e:
                messages.error(request, f'Error al actualizar la vacante: {str(e)}')

        context = {
            'vacante_form': vacante_form,
            'requisito_form': requisito_form,
            'vacante': vacante,
            'accion': 'editar'
        }
        return render(request, 'usuarios/publicar_vacante.html', context)


@method_decorator(login_required, name='dispatch')
class MisVacantesView(View):
    """Vista para listar las vacantes del reclutador."""

    def get(self, request):
        if request.user.rol != 'reclutador':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        vacantes = Vacante.objects.filter(
            reclutador=request.user.reclutador
        ).order_by('-fecha_actualizacion')

        context = {
            'vacantes': vacantes
        }
        return render(request, 'usuarios/mis_vacantes.html', context)


def index_view(request):
    """Vista de la página de inicio con vacantes publicadas."""
    # Obtener término de búsqueda
    busqueda = request.GET.get('q', '').strip()

    # Filtro base
    vacantes = Vacante.objects.filter(
        estado_vacante='publicada',
        aprobada=True
    ).select_related('secretaria', 'categoria')

    # Aplicar búsqueda si existe
    if busqueda:
        vacantes = vacantes.filter(
            Q(titulo__icontains=busqueda) |
            Q(categoria__nombre__icontains=busqueda) |
            Q(municipio__icontains=busqueda)
        )

    vacantes = vacantes.order_by('-fecha_publicacion')[:12]
    # Paginación
    paginator = Paginator(vacantes, 2)  # 15 cards por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vacantes': vacantes,
        'total_vacantes': vacantes.count(),
    }
    return render(request, 'usuarios/index.html', context)


def logout_view(request):
    """Vista para cerrar sesión."""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('index')


class InteresadoRegistroView(View):
    """Vista para registro de interesados."""

    def get(self, request):
        form = InteresadoRegistroForm()
        return render(request, 'usuarios/registro_interesado.html', {'form': form})

    def post(self, request):
        form = InteresadoRegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
            return redirect('login')
        return render(request, 'usuarios/registro_interesado.html', {'form': form})


class ReclutadorRegistroView(View):
    """Vista para registro de reclutadores."""

    def get(self, request):
        secretaria_form = SecretariaRegistroForm()
        reclutador_form = ReclutadorRegistroForm()
        return render(request, 'usuarios/registro_reclutador.html', {
            'secretaria_form': secretaria_form,
            'reclutador_form': reclutador_form
        })

    def post(self, request):
        secretaria_form = SecretariaRegistroForm(request.POST)
        reclutador_form = ReclutadorRegistroForm(request.POST)

        if secretaria_form.is_valid() and reclutador_form.is_valid():
            secretaria = secretaria_form.save()
            user = reclutador_form.save(commit=True, secretaria=secretaria)
            messages.success(
                request,
                'Registro exitoso. Tu cuenta será revisada por un administrador. Te notificaremos por email cuando sea aprobada.'
            )
            return redirect('login')

        return render(request, 'usuarios/registro_reclutador.html', {
            'secretaria_form': secretaria_form,
            'reclutador_form': reclutador_form
        })


@method_decorator(login_required, name='dispatch')
class PerfilInteresadoView(View):
    """Vista para ver/editar perfil del interesado con CV integrado."""

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

        context = {
            'interesado': interesado,
            'curriculum': curriculum,
            'experiencias': experiencias,
            'educaciones': educaciones,
            'habilidades': habilidades,
            'idiomas': idiomas,
            'tiene_cv': tiene_cv,
            'es_nuevo': created,
        }
        return render(request, 'usuarios/perfil_interesado.html', context)

    def post(self, request):
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
                # Actualizar información personal del interesado
                interesado.nombre = request.POST.get('nombre', '')
                interesado.apellido_paterno = request.POST.get('apellido_paterno', '')
                interesado.apellido_materno = request.POST.get('apellido_materno', '')
                interesado.telefono = request.POST.get('telefono', '')
                interesado.municipio = request.POST.get('municipio', '')
                interesado.codigo_postal = request.POST.get('codigo_postal', '')

                # Fecha de nacimiento
                fecha_nacimiento = request.POST.get('fecha_nacimiento')
                if fecha_nacimiento:
                    interesado.fecha_nacimiento = fecha_nacimiento

                interesado.save()

                # Actualizar resumen profesional del curriculum
                curriculum.resumen_profesional = request.POST.get('resumen_profesional', '')
                curriculum.save()

                messages.success(request, 'CV actualizado exitosamente.')
                return redirect('perfil_interesado')

        except Exception as e:
            messages.error(request, f'Error al guardar el CV: {str(e)}')

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
            'es_nuevo': created,
        }
        return render(request, 'usuarios/perfil_interesado.html', context)


@method_decorator(login_required, name='dispatch')
class DashboardReclutadorView(View):
    """Vista para dashboard del reclutador."""

    def get(self, request):
        if request.user.rol != 'reclutador':
            messages.error(request, 'No tienes permiso para acceder a esta página.')
            return redirect('index')

        reclutador = request.user.reclutador

        # Calcular estadísticas de vacantes
        vacantes_activas = reclutador.vacantes.filter(estado_vacante='publicada').count()
        vacantes_borradores = reclutador.vacantes.filter(estado_vacante='borrador').count()
        vacantes_cerradas = reclutador.vacantes.filter(estado_vacante='cerrada').count()
        total_vacantes = reclutador.vacantes.count()

        # Obtener las últimas 3 vacantes para mostrar en el dashboard
        ultimas_vacantes = reclutador.vacantes.all().order_by('-fecha_actualizacion')[:3]

        # TODO: Cuando implementemos postulaciones, calcular estas estadísticas
        postulaciones_recibidas = 0  # Placeholder
        postulaciones_nuevas = 0  # Placeholder

        context = {
            'reclutador': reclutador,
            'vacantes_activas': vacantes_activas,
            'vacantes_borradores': vacantes_borradores,
            'vacantes_cerradas': vacantes_cerradas,
            'total_vacantes': total_vacantes,
            'ultimas_vacantes': ultimas_vacantes,
            'postulaciones_recibidas': postulaciones_recibidas,
            'postulaciones_nuevas': postulaciones_nuevas,
        }
        # return render(request, 'usuarios/dashboard_reclutador.html', context)'usuarios/dashboard_reclutador.html', context)

        return render(request, 'usuarios/dashboard_reclutador.html', context)


def detalle_vacante_view(request, vacante_id):
    """
    Muestra los detalles de una vacante específica.
    """
    vacante = get_object_or_404(
        Vacante.objects.select_related('secretaria', 'categoria', 'requisitos'),
        id=vacante_id,
        estado_vacante='publicada',
        aprobada=True
    )

    try:
        requisitos = vacante.requisitos
    except RequisitoVacante.DoesNotExist:
        requisitos = None
    except AttributeError:
        requisitos = None

    # Verificar si el usuario ya se postuló
    ya_postulado = False
    if request.user.is_authenticated and request.user.rol == 'interesado':
        ya_postulado = Postulacion.objects.filter(
            interesado=request.user.interesado,
            vacante=vacante
        ).exists()

    context = {
        'vacante': vacante,
        'requisitos': requisitos,
        'ya_postulado': ya_postulado,
    }
    return render(request, 'usuarios/detalle_vacante.html', context)


@login_required
def postularse_vacante(request, vacante_id):
    """Vista para que un interesado se postule a una vacante."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    if request.user.rol != 'interesado':
        return JsonResponse({'success': False, 'error': 'Solo los interesados pueden postularse'})

    try:
        # Verificar que la vacante existe y está activa
        vacante = get_object_or_404(
            Vacante,
            id=vacante_id,
            estado_vacante='publicada',
            aprobada=True
        )

        interesado = request.user.interesado

        # Verificar que el interesado tiene CV
        if not hasattr(interesado, 'curriculum'):
            return JsonResponse({
                'success': False,
                'error': 'Debes crear tu CV antes de postularte',
                'redirect_url': '/perfil/interesado/'
            })

        curriculum = interesado.curriculum

        # Verificar que tiene información mínima
        if not (interesado.nombre and interesado.apellido_paterno):
            return JsonResponse({
                'success': False,
                'error': 'Completa tu información personal antes de postularte',
                'redirect_url': '/perfil/interesado/'
            })

        # Verificar si ya se postuló
        if Postulacion.objects.filter(interesado=interesado, vacante=vacante).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya te has postulado a esta vacante'
            })

        # Verificar límite de postulantes
        postulaciones_actuales = vacante.postulaciones.count()
        if postulaciones_actuales >= vacante.max_postulantes:
            return JsonResponse({
                'success': False,
                'error': 'Esta vacante ya alcanzó el límite máximo de postulantes'
            })

        # Crear la postulación
        mensaje_motivacion = request.POST.get('mensaje_motivacion', '').strip()

        postulacion = Postulacion.objects.create(
            interesado=interesado,
            vacante=vacante,
            curriculum=curriculum,
            mensaje_motivacion=mensaje_motivacion,
            estado='enviada'
        )

        return JsonResponse({
            'success': True,
            'message': 'Te has postulado exitosamente a esta vacante',
            'postulacion_id': postulacion.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al procesar la postulación: {str(e)}'
        })


@login_required
def mis_postulaciones(request):
    """Vista para ver las postulaciones del interesado."""
    if request.user.rol != 'interesado':
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')

    postulaciones = Postulacion.objects.filter(
        interesado=request.user.interesado
    ).select_related('vacante', 'vacante__secretaria').order_by('-fecha_postulacion')

    context = {
        'postulaciones': postulaciones
    }
    return render(request, 'usuarios/mis_postulaciones.html', context)


# Agregar esta función al final del archivo usuarios/views.py
#
# @login_required
# def retirar_postulacion(request, postulacion_id):
#     """
#     Vista para que un interesado retire su postulación a una vacante.
#
#     Args:
#         postulacion_id: ID de la postulación a retirar
#
#     Returns:
#         JsonResponse con success/error para AJAX requests
#         Redirect para requests normales
#     """
#
#     # Verificar permisos
#     if request.user.rol != 'interesado':
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Solo los interesados pueden retirar postulaciones.'
#             })
#         else:
#             messages.error(request, 'No tienes permiso para realizar esta acción.')
#             return redirect('index')
#
#     try:
#         # Buscar la postulación que pertenece al interesado
#         postulacion = get_object_or_404(
#             Postulacion,
#             id=postulacion_id,
#             interesado=request.user.interesado
#         )
#
#         # Verificar que la postulación se puede retirar
#         # Solo se pueden retirar postulaciones en estado 'enviada' o 'en_revision'
#         estados_retirables = ['enviada', 'en_revision']
#
#         if postulacion.estado not in estados_retirables:
#             error_msg = f'No puedes retirar esta postulación porque está en estado: {postulacion.get_estado_display()}'
#
#             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                 return JsonResponse({
#                     'success': False,
#                     'error': error_msg
#                 })
#             else:
#                 messages.error(request, error_msg)
#                 return redirect('mis_postulaciones')
#
#         # Guardar información para el mensaje
#         vacante_titulo = postulacion.vacante.titulo
#
#         # Eliminar la postulación
#         postulacion.delete()
#
#         # Mensaje de éxito
#         success_msg = f'Has retirado exitosamente tu postulación para "{vacante_titulo}"'
#
#         # Responder según el tipo de request
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': True,
#                 'message': success_msg
#             })
#         else:
#             messages.success(request, success_msg)
#             return redirect('mis_postulaciones')
#
#     except Postulacion.DoesNotExist:
#         error_msg = 'Postulación no encontrada o no tienes permiso para retirarla.'
#
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': False,
#                 'error': error_msg
#             })
#         else:
#             messages.error(request, error_msg)
#             return redirect('mis_postulaciones')
#
#     except Exception as e:
#         # Log del error para debugging
#         print(f"Error en retirar_postulacion: {str(e)}")
#
#         error_msg = f'Error al retirar la postulación: {str(e)}'
#
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': False,
#                 'error': error_msg
#             })
#         else:
#             messages.error(request, error_msg)
#             return redirect('mis_postulaciones')

@login_required
@require_http_methods(["POST", "DELETE"])
def retirar_postulacion(request, postulacion_id):
    """
    Vista para que un interesado retire su postulación a una vacante.

    Args:
        postulacion_id: ID de la postulación a retirar

    Returns:
        JsonResponse con success/error para AJAX requests
        Redirect para requests normales
    """

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


# Agregar estas vistas al final de usuarios/views.py

@method_decorator(login_required, name='dispatch')
# Agregar estas vistas al final de usuarios/views.py

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
            # Obtener la vacante y verificar que pertenezca al reclutador
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

        # Calcular estadísticas actualizadas para la vacante


        postulaciones_vacante = Postulacion.objects.filter(vacante=postulacion.vacante)

        # Contar por estados
        estados = postulaciones_vacante.values('estado').annotate(count=Count('estado'))
        estado_counts = {estado['estado']: estado['count'] for estado in estados}

        # Contar nuevos hoy
        nuevos_hoy = postulaciones_vacante.filter(
            fecha_postulacion__date=date.today()
        ).count()

        estadisticas = {
            'total_postulantes': postulaciones_vacante.count(),
            'nuevos_hoy': nuevos_hoy,
            'en_revision': estado_counts.get('en_revision', 0),
            'entrevista': estado_counts.get('entrevista', 0),
            'aceptados': estado_counts.get('aceptada', 0),
            'rechazados': estado_counts.get('rechazada', 0),
        }

        # Log de la acción (opcional)
        print(f"Reclutador {request.user.email} cambió estado de postulación {postulacion_id} "
              f"de '{estado_anterior}' a '{nuevo_estado}'")

        return JsonResponse({
            'success': True,
            'message': f'Estado actualizado exitosamente',
            'estado_display': estado_display,
            'nuevo_estado': nuevo_estado,
            'postulacion_id': postulacion_id,
            'estadisticas': estadisticas
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
def agregar_notas_postulacion(request, postulacion_id):
    """
    Vista AJAX para agregar notas del reclutador a una postulación.
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        }, status=405)

    if request.user.rol != 'reclutador':
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para esta acción'
        }, status=403)

    try:
        import json
        data = json.loads(request.body)
        notas = data.get('notas', '').strip()

        # Obtener la postulación
        postulacion = get_object_or_404(
            Postulacion,
            id=postulacion_id,
            vacante__reclutador=request.user.reclutador
        )

        # Actualizar las notas
        postulacion.notas_reclutador = notas
        postulacion.save()

        return JsonResponse({
            'success': True,
            'message': 'Notas guardadas exitosamente'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        print(f"Error en agregar_notas_postulacion: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)


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
def agregar_notas_postulacion(request, postulacion_id):
    """
    Vista AJAX para agregar notas del reclutador a una postulación.
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        }, status=405)

    if request.user.rol != 'reclutador':
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para esta acción'
        }, status=403)

    try:
        import json
        data = json.loads(request.body)
        notas = data.get('notas', '').strip()

        # Obtener la postulación
        postulacion = get_object_or_404(
            Postulacion,
            id=postulacion_id,
            vacante__reclutador=request.user.reclutador
        )

        # Actualizar las notas
        postulacion.notas_reclutador = notas
        postulacion.save()

        return JsonResponse({
            'success': True,
            'message': 'Notas guardadas exitosamente'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        print(f"Error en agregar_notas_postulacion: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)


# Agregar esta vista también a usuarios/views.py

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


# Agregar estas vistas al archivo usuarios/views.py


def buscar_vacantes(request):
    """Vista para buscar vacantes con filtros."""

    # Obtener parámetros de búsqueda
    query = request.GET.get('q', '').strip()
    tipo_empleo = request.GET.get('tipo_empleo', '')
    municipio = request.GET.get('municipio', '')

    # Comenzar con todas las vacantes publicadas y aprobadas
    vacantes = Vacante.objects.filter(
        estado_vacante='publicada',
        aprobada=True
    ).select_related('secretaria', 'reclutador', 'categoria')

    # Aplicar filtro de búsqueda por texto
    if query:
        vacantes = vacantes.filter(
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
        vacantes = vacantes.filter(tipo_empleo=tipo_empleo)

    # Aplicar filtro por municipio
    if municipio:
        vacantes = vacantes.filter(municipio=municipio)

    # Ordenar por fecha de publicación (más recientes primero)
    vacantes = vacantes.order_by('-fecha_publicacion')

    # Limitar resultados para mejor rendimiento
    vacantes = vacantes[:50]

    context = {
        'vacantes': vacantes,
        'query': query,
        'tipo_empleo': tipo_empleo,
        'municipio': municipio,
        'total_resultados': len(vacantes),
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
            Q(municipio__icontains=busqueda)
        )

    vacantes = vacantes.order_by('-fecha_publicacion')[:12]

    html = render_to_string('usuarios/vacantes_lista.html', {'vacantes': vacantes})
    return JsonResponse({'html': html})


