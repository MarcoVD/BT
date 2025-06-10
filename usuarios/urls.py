# usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ===========================
    # URLs PRINCIPALES DEL SITIO
    # ===========================
    path('', views.index_view, name='index'),

    # ===========================
    # URLs DE AUTENTICACIÓN
    # ===========================
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ===========================
    # URLs DE REGISTRO
    # ===========================
    path('registro/interesado/', views.InteresadoRegistroView.as_view(), name='registro_interesado'),
    path('registro/reclutador/', views.ReclutadorRegistroView.as_view(), name='registro_reclutador'),

    # ===========================
    # URLs DE PERFILES Y DASHBOARDS
    # ===========================
    path('perfil/interesado/', views.PerfilInteresadoView.as_view(), name='perfil_interesado'),
    path('dashboard/reclutador/', views.DashboardReclutadorView.as_view(), name='dashboard_reclutador'),

    # ===========================
    # URLs PARA GESTIÓN DE VACANTES (RECLUTADORES)
    # ===========================
    path('publicar-vacante/', views.PublicarVacanteView.as_view(), name='publicar_vacante'),
    path('editar-vacante/<int:vacante_id>/', views.EditarVacanteView.as_view(), name='editar_vacante'),
    path('mis-vacantes/', views.MisVacantesView.as_view(), name='mis_vacantes'),
    path('vacante/<int:vacante_id>/postulantes/', views.VerPostulantesView.as_view(), name='ver_postulantes'),
    path('candidato/<int:interesado_id>/perfil/', views.ver_perfil_candidato, name='ver_perfil_candidato'),

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
    path('mi-cv/', views.CrearEditarCVView.as_view(), name='crear_editar_cv'),
    path('mi-cv/previsualizar/', views.previsualizar_cv, name='previsualizar_cv'),
    path('cv/descargar-pdf/', views.descargar_cv_pdf, name='descargar_cv_pdf'),

    # ===========================
    # URLs AJAX PARA ACTUALIZACIÓN DE PERFIL
    # ===========================
    path('ajax/actualizar-perfil/', views.actualizar_perfil_ajax, name='actualizar_perfil_ajax'),
    path('ajax/actualizar-foto-perfil/', views.actualizar_foto_perfil_ajax, name='actualizar_foto_perfil_ajax'),

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
    path('ajax/agregar-notas-postulacion/<int:postulacion_id>/', views.agregar_notas_postulacion,
         name='agregar_notas_postulacion'),

    # ===========================
    # URL DE PRUEBA (TEMPORAL)
    # ===========================
    path('test-urls/', views.test_urls, name='test_urls'),
]