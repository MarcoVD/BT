# usuarios/urls.py - URLS ACTUALIZADAS CON VERIFICACIÓN DE EMAIL
from django.urls import path
from django.views.decorators.http import require_POST
from . import views
from .views import autoguardar_resumen_profesional, autoguardar_informacion_personal

urlpatterns = [
    # ===========================
    # URLs PRINCIPALES DEL SITIO
    # ===========================
    path('', views.index_view, name='index'),
    path('buscar/', views.buscar_vacantes, name='buscar_vacantes'),

    # ===========================
    # URLs DE AUTENTICACIÓN
    # ===========================
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

     path('recuperar-contrasena/', views.RecuperarContrasenaView.as_view(), name='recuperar_contrasena'),
     path('restablecer-contrasena/<str:token>/', views.RestablecerContrasenaView.as_view(), name='restablecer_contrasena'),
     path('reenviar-recuperacion/', views.ReenviarRecuperacionView.as_view(), name='reenviar_recuperacion'),
     
     # En la sección de URLs AJAX, agregar:
     path('ajax/extend-session/', views.extend_session_ajax, name='extend_session_ajax'),
     path('ajax/session-status/', views.session_status_ajax, name='session_status_ajax'),

    
    # ===========================
    # URLs DE REGISTRO
    # ===========================
    path('registro/interesado/', views.InteresadoRegistroView.as_view(), name='registro_interesado'),
    path('registro/reclutador/', views.ReclutadorRegistroView.as_view(), name='registro_reclutador'),

    # ===========================
    # URLs DE VERIFICACIÓN DE EMAIL
    # ===========================
    path('verificar-email/<uuid:token>/', views.VerificarEmailView.as_view(), name='verificar_email'),
    path('reenviar-verificacion/', views.ReenviarVerificacionView.as_view(), name='reenviar_verificacion'),

    # ===========================
    # URLs DE PERFILES Y DASHBOARDS
    # ===========================
    path('perfil/interesado/', views.PerfilInteresadoView.as_view(), name='perfil_interesado'),
    path('dashboard/reclutador/', views.DashboardReclutadorView.as_view(), name='dashboard_reclutador'),
    path('ajax/autoguardar_resumen_profesional/', autoguardar_resumen_profesional,
         name='autoguardar_resumen_profesional'),
    path('ajax/autoguardar_informacion_personal/', autoguardar_informacion_personal,
         name='autoguardar_informacion_personal'),

    # ===========================
    # URLs PARA GESTIÓN DE VACANTES (RECLUTADORES)
    # ===========================
    path('publicar-vacante/', views.PublicarVacanteView.as_view(), name='publicar_vacante'),
    path('editar-vacante/<int:vacante_id>/', views.EditarVacanteView.as_view(), name='editar_vacante'),
    path('mis-vacantes/', views.MisVacantesView.as_view(), name='mis_vacantes'),
    path('vacante/<int:vacante_id>/postulantes/', views.VerPostulantesView.as_view(), name='ver_postulantes'),
    path('candidato/<int:interesado_id>/perfil/', views.ver_perfil_candidato, name='ver_perfil_candidato'),

# usuarios/urls.py - AGREGAR ESTAS URLs AL ARCHIVO EXISTENTE
# En la sección de URLs AJAX PARA GESTIÓN DE POSTULACIONES (RECLUTADORES)

    # ===========================
    # URLs AJAX PARA GESTIÓN DE VACANTES (RECLUTADORES)
    # ===========================
    path('ajax/cerrar-vacante/<int:vacante_id>/', views.cerrar_vacante_ajax, name='cerrar_vacante_ajax'),
    path('ajax/reabrir-vacante/<int:vacante_id>/', views.reabrir_vacante_ajax, name='reabrir_vacante_ajax'),
    path('ajax/eliminar-borrador/<int:vacante_id>/', views.eliminar_borrador_ajax, name='eliminar_borrador_ajax'),
    path('ajax/estado-vacante/<int:vacante_id>/', views.obtener_estado_vacante_ajax, name='obtener_estado_vacante_ajax'),
    # ===========================
    # URLs PARA VACANTES (VISUALIZACIÓN)
    # ===========================
    path('vacante/<int:vacante_id>/', views.detalle_vacante_view, name='detalle_vacante'),

    # ===========================
    # URLs PARA POSTULACIONES (INTERESADOS)
    # ===========================
    path('postularse/<int:vacante_id>/', views.postularse_vacante, name='postularse_vacante'),
    path('mis-postulaciones/', views.mis_postulaciones, name='mis_postulaciones'),
    path('retirar-postulacion/<int:postulacion_id>/', views.retirar_postulacion, name='retirar_postulacion'),

    # ===========================
    # URLs PARA GESTIÓN DE CV
    # ===========================
    # path('mi-cv/', views.CrearEditarCVView.as_view(), name='crear_editar_cv'),
    path('mi-cv/previsualizar/', views.previsualizar_cv, name='previsualizar_cv'),
    path('cv/descargar/', views.descargar_cv_pdf, name='descargar_cv_pdf'),
    path('cv/descarga/', views.descargar_cv_pdf_reclutador, name='descargar_cv_pdf_reclutador'),
    # ===========================
    # URLs AJAX PARA ACTUALIZACIÓN DE PERFIL
    # ===========================
    path('ajax/actualizar-foto-perfil/',
         require_POST(views.actualizar_foto_perfil_ajax),
         name='actualizar_foto_perfil_ajax'),

    path('ajax/actualizar-perfil/',
         require_POST(views.actualizar_perfil_ajax),
         name='actualizar_perfil_ajax'),

    path('ajax/actualizar-perfil-completo/',
         require_POST(views.actualizar_perfil_completo_ajax),
         name='actualizar_perfil_completo_ajax'),
    # ===========================
    # URLs AJAX PARA EXPERIENCIA LABORAL
    # ===========================
    path('ajax/experiencia/agregar/', views.agregar_experiencia_ajax, name='agregar_experiencia_ajax'),
    path('ajax/experiencia/editar/<int:experiencia_id>/', views.editar_experiencia_ajax,
         name='editar_experiencia_ajax'),
    path('ajax/experiencia/eliminar/<int:experiencia_id>/', views.eliminar_experiencia_ajax,
         name='eliminar_experiencia_ajax'),

    # ===========================
    # URLs AJAX PARA EDUCACIÓN
    # ===========================
    path('ajax/educacion/agregar/', views.agregar_educacion_ajax, name='agregar_educacion_ajax'),
    path('ajax/educacion/eliminar/<int:educacion_id>/', views.eliminar_educacion_ajax, name='eliminar_educacion_ajax'),
    path('ajax/educacion/editar/<int:educacion_id>/', views.editar_educacion_ajax, name='editar_educacion_ajax'),
    # ===========================
    # URLs AJAX PARA HABILIDADES
    # ===========================
    path('ajax/habilidad/agregar/', views.agregar_habilidad_ajax, name='agregar_habilidad_ajax'),
    path('ajax/habilidad/eliminar/<int:habilidad_id>/', views.eliminar_habilidad_ajax, name='eliminar_habilidad_ajax'),

    # ===========================
    # URLs AJAX PARA IDIOMAS
    # ===========================
    path('ajax/idioma/agregar/', views.agregar_idioma_ajax, name='agregar_idioma_ajax'),
    path('ajax/idioma/eliminar/<int:idioma_id>/', views.eliminar_idioma_ajax, name='eliminar_idioma_ajax'),

    # ===========================
    # URLs AJAX PARA GESTIÓN DE POSTULACIONES (RECLUTADORES)
    # ===========================
    path('ajax/cambiar-estado-postulacion/<int:postulacion_id>/', views.cambiar_estado_postulacion,
         name='cambiar_estado_postulacion'),
    # path('ajax/agregar-notas-postulacion/<int:postulacion_id>/', views.agregar_notas_postulacion,
    #      name='agregar_notas_postulacion'),
    path('ajax/buscar-vacantes/', views.busqueda_vacantes_ajax, name='busqueda_vacantes_ajax'),
    # ===========================

    # ===========================
    # URL DE PRUEBA (TEMPORAL)
    # ===========================
    path('test-urls/', views.test_urls, name='test_urls'),

    # ===========================
    # URLs AJAX PARA CONSULTA DE CÓDIGO POSTAL
    # ===========================
    # usuarios/urls.py - Agregar estas URLs en la sección AJAX

    # ===========================
    # URLs AJAX PARA CONSULTA DE CÓDIGO POSTAL Y UBICACIÓN
    # ===========================
    path('ajax/obtener-datos-por-cp/', views.obtener_datos_por_cp, name='obtener_datos_por_cp'),
    path('ajax/validar-codigo-postal/', views.validar_codigo_postal, name='validar_codigo_postal'),
    path('ajax/guardar-ubicacion/', views.guardar_ubicacion_completa, name='guardar_ubicacion_completa'),
    path('ajax/autoguardar-ubicacion/', views.autoguardar_ubicacion, name='autoguardar_ubicacion'),
    path('ajax/municipios-por-estado/', views.obtener_municipios_por_estado, name='obtener_municipios_por_estado'),
    path('ajax/localidades-por-municipio/', views.obtener_localidades_por_municipio,
         name='obtener_localidades_por_municipio'),
    path('ajax/consultar-codigo-postal/', views.obtener_datos_por_cp, name='consultar_codigo_postal'),
    # URL para compatibilidad con el código existente
    path('ajax/obtener_datos_por_cp/', views.obtener_datos_por_cp, name='obtener_datos_por_cp_legacy'),
    
    # ===========================
    # URLs AJAX PARA VERIFICACIÓN DE CV
    # ===========================
    path('ajax/verificar-estado-cv/', views.verificar_estado_cv_ajax, name='verificar_estado_cv_ajax'),
]