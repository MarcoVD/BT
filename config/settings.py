import os
from pathlib import Path
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-!8==@fr40w4j1g=0(i!rn!qwtxp2lewg5$lwjr-gsz#069kfrg')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

#  ALLOWED_HOSTS CORREGIDO PARA PRODUCCIÓN
if DEBUG:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
else:
    ALLOWED_HOSTS = [
        os.getenv('DOMAIN', 'localhost'),
        f"www.{os.getenv('DOMAIN', 'localhost')}",
        '127.0.0.1',
        'localhost'
    ]

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    # Apps propias
    'usuarios',
    # Apps de terceros
    'crispy_forms',
    #Protección contra fuerza Bruta
    # 'axes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'axes.middleware.AxesMiddleware',  # Protección contra fuerza bruta 
    
]
# AUTHENTICATION_BACKENDS = [
#     'axes.backends.AxesStandaloneBackend',
#     # 'django.contrib.auth.backends.ModelBackend',  # Si usas autenticación de Django normal
# ]



#  CONFIGURACIÓN DE SEGURIDAD PARA PRODUCCIÓN
if not DEBUG:
    # SSL/HTTPS Settings
    # SECURE_SSL_REDIRECT = True
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Security Headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

    # Cookie Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict' #proteccion csrf
    # CSRF_COOKIE_SECURE = True
    # CSRF_COOKIE_SAMESITE
    # Asegurar que las peticiones AJAX funcionen correctamente
    CSRF_COOKIE_HTTPONLY = False  # Permitir acceso desde JavaScript para peticiones AJAX
    # CSRF_COOKIE_SAMESITE = 'Lax'  # Permitir peticiones AJAX desde el mismo sitio
    
# Configuración personalizada para timeout de sesión
SESSION_TIMEOUT_SETTINGS = {
    'TIMEOUT_MINUTES': 15,           # Tiempo total de inactividad
    'WARNING_MINUTES': 2,            # Advertencia antes del logout
    'CHECK_INTERVAL_SECONDS': 30,    # Frecuencia de verificación
    'ENABLE_SERVER_SIDE_TIMEOUT': True,  # Habilitar middleware de timeout
}
    

AXES_FAILURE_LIMIT = 5 #Bloquea tras 5 intentos fallidos
AXES_COOLOFF_TIME = 1 #Tiempo en hrs
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

#  DATABASE CONFIGURATION - PRODUCCIÓN Y DESARROLLO
if DEBUG:
    # Configuración para desarrollo
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
else:
    # Configuración para producción
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'bolsa_trabajo'),
            'USER': os.getenv('DB_USER', 'bolsa_admin'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'sslmode': 'prefer',
            },
        }
    }

AUTH_USER_MODEL = 'usuarios.Usuario'

# Password validation
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
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DECIMAL_SEPARATOR = '.'
THOUSAND_SEPARATOR = ','

#  CONFIGURACIÓN DE ARCHIVOS ESTÁTICOS CORREGIDA
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

#  Carpeta donde collectstatic reunirá todos los archivos
if DEBUG:
    STATIC_ROOT = BASE_DIR / 'staticfiles'
else:
    STATIC_ROOT = '/var/www/bolsa-trabajo/staticfiles'

#  FINDERS NECESARIOS
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# CONFIGURACIÓN DE ARCHIVOS MEDIA
MEDIA_URL = '/media/'

if DEBUG:
    MEDIA_ROOT = BASE_DIR / 'media'
else:
    MEDIA_ROOT = '/var/www/bolsa-trabajo/media'

#  EMAIL CONFIGURATION
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("Usando EMAIL_BACKEND de consola para desarrollo")
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'marcovazquezdelgado.movilidad@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'jufg zcao sdzs hsof')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Bolsa de Trabajo <marcovazquezdelgado.movilidad@gmail.com>')

SITE_ID = 1

#  CONFIGURACIÓN DE LOGGING MEJORADA
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log' if DEBUG else '/var/log/django/bolsa-trabajo.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'usuarios': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
        'django.core.mail': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

#  JAZZMIN SETTINGS (mantener igual)
JAZZMIN_SETTINGS = {
    "site_title": "Bolsa de Trabajo Admin",
    "site_header": "Bolsa de Trabajo",
    "site_brand": "Administración",
    "site_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "welcome_sign": "Bienvenido al panel de administración de la Bolsa de Trabajo",
    "search_model": ["usuarios.Usuario", "usuarios.Vacante"],
    "topmenu_links": [
        {"name": "Inicio del Sitio", "url": "index", "permissions": ["auth.view_user"]},
        {"model": "usuarios.Vacante"},
        {"model": "usuarios.Secretaria"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["usuarios", "auth"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "usuarios": "fas fa-briefcase",
        "usuarios.usuario": "fas fa-user-plus",
        "usuarios.interesado": "fas fa-user-tie",
        "usuarios.reclutador": "fas fa-user-shield",
        "usuarios.secretaria": "fas fa-building",
        "usuarios.vacante": "fas fa-file-invoice-dollar",
        "usuarios.postulacion": "fas fa-paper-plane",
        "usuarios.categoria": "fas fa-tags",
    },
    "show_ui_builder": False,
}

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
    "theme": "darkly",
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

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'index'

#  CONFIGURACIÓN ESPECÍFICA PARA WEASYPRINT (PDFs)
if not DEBUG:
    # En producción, WeasyPrint necesita rutas absolutas
    import subprocess
    import sys

    try:
        subprocess.run([sys.executable, '-c', 'import weasyprint'], check=True)
    except subprocess.CalledProcessError:
        print("⚠️  WeasyPrint no está instalado correctamente")

#  CONFIGURACIÓN DE CACHE (OPCIONAL PARA PRODUCCIÓN)
if not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': '/var/tmp/django_cache',
        }
    }

#  CONFIGURACIÓN DE SESIONES
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# 15 minutos
SESSION_COOKIE_AGE = 900
# Cierra sesión cuando el navegador es cerrado
SESSION_EXPIRE_AT_BROWSER_CLOSE = True 
# Guarda la sesión  en cada peticion para manetener el timeout actualizado
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_NAME = 'bolsa_trabajo_sessionid'