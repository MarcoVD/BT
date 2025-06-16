import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-!8==@fr40w4j1g=0(i!rn!qwtxp2lewg5$lwjr-gsz#069kfrg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []



INSTALLED_APPS = [
    'jazzmin',  # <-- AÑADIR JAZZMIN AQUÍ ARRIBA
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Para humanizar números y fechas

    # Apps propias
    'usuarios',

    # Apps de terceros
    'crispy_forms',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # Necesario para las sesiones
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Necesario para la autenticación
    'django.contrib.messages.middleware.MessageMiddleware', # Necesario para los mensajes
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # ... otros middlewares que puedas tener ...
]
CRISPY_TEMPLATE_PACK = 'bootstrap5'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bolsa_trabajo',
        'USER': 'bolsa_admin',
        'PASSWORD': '//BT29042025&&',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
# config/settings.py
AUTH_USER_MODEL = 'usuarios.Usuario'

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DECIMAL_SEPARATOR = '.'
THOUSAND_SEPARATOR = ','
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# config/settings.py
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# config/settings.py

# Configuración de correo electrónico (ajustar según proveedor)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # o el servidor SMTP que uses
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'marcovazquezdelgado.movilidad@gmail.com'  # correo desde el que se envían las notificaciones
EMAIL_HOST_PASSWORD = 'tu_contraseña'  # contraseña o clave de aplicación
#DEFAULT_FROM_EMAIL = 'Bolsa de Trabajo <noreply@bolsadetrabajo.example.com>'
DEFAULT_FROM_EMAIL = 'Bolsa de Trabajo marcovazquezdelgado.movilidad@gmail.com>'

# Para desarrollo, puedes usar el backend de consola (muestra emails en la terminal)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#
# # Configuración de logging para depuración (opcional)
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#         },
#     },
#     'loggers': {
#         'usuarios.fields': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#     },
# }

JAZZMIN_SETTINGS = {
    # Título que se muestra en la pestaña del navegador y en la cabecera del login.
    "site_title": "Bolsa de Trabajo Admin",

    # Título en la cabecera principal (puedes usar un texto corto).
    "site_header": "Bolsa de Trabajo",

    # Título en la página de login.
    "site_brand": "Administración",

    # Logo para la página de login y la barra de navegación.
    # Debe estar en una carpeta de archivos estáticos. Ej: 'img/logo.png'
    "site_logo": None,  # "static/assets/img/logo.png",

    # Logo para la página de login en modo oscuro
    "login_logo_dark": None,

    # Clases CSS para aplicar al logo
    "site_logo_classes": "img-circle",

    # Mensaje de bienvenida en la página de inicio del admin.
    "welcome_sign": "Bienvenido al panel de administración de la Bolsa de Trabajo",

    # Modelo a usar para la barra de búsqueda global en la parte superior.
    "search_model": ["usuarios.CustomUser", "usuarios.Vacante"],

    # --- Menú Superior ---
    "topmenu_links": [
        # Link a la página principal del sitio
        {"name": "Inicio del Sitio", "url": "index", "permissions": ["auth.view_user"]},

        # Link a tu modelo de Vacante
        {"model": "usuarios.Vacante"},

        # Link a tu modelo de Secretaria
        {"model": "usuarios.Secretaria"},
    ],

    # --- Menú Lateral (Sidebar) ---
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    # Orden de las aplicaciones en el menú
    "order_with_respect_to": ["usuarios", "auth"],

    # Iconos para las aplicaciones y modelos. Usa los iconos de Font Awesome 5.
    # https://fontawesome.com/v5/search
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "usuarios": "fas fa-briefcase",
        "usuarios.customuser": "fas fa-user-plus",
        "usuarios.interesado": "fas fa-user-tie",
        "usuarios.reclutador": "fas fa-user-shield",
        "usuarios.secretaria": "fas fa-building",
        "usuarios.vacante": "fas fa-file-invoice-dollar",
        "usuarios.postulacion": "fas fa-paper-plane",
        "usuarios.categoria": "fas fa-tags",
        "usuarios.cv": "fas fa-id-card",
        "usuarios.educacion": "fas fa-graduation-cap",
        "usuarios.experiencialaboral": "fas fa-history",
    },

    # Texto que se muestra en la cabecera de la sección de "Informes"
    "show_ui_builder": False,
}

# ----------------- AJUSTES VISUALES DE JAZZMIN (OPCIONAL) -----------------
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "darkly",  # Puedes probar otros temas como "flatly", "cerulean", "litera", etc.
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}