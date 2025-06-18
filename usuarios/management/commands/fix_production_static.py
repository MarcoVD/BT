# usuarios/management/commands/fix_production_static.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.contrib.staticfiles import finders
import os
import shutil
import glob


class Command(BaseCommand):
    help = 'Diagnostica y soluciona problemas de collectstatic para producción'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recolección limpiando staticfiles primero',
        )
        parser.add_argument(
            '--verify-only',
            action='store_true',
            help='Solo verifica, no hace cambios',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('🚀 CONFIGURACIÓN PARA PRODUCCIÓN - COLLECTSTATIC')
        )
        self.stdout.write('=' * 60)

        # Verificar configuración actual
        self.check_configuration()

        # Verificar archivos fuente
        self.check_source_files()

        # Verificar staticfiles actuales
        self.check_current_staticfiles()

        if not options['verify_only']:
            # Ejecutar collectstatic
            self.run_collectstatic(force=options['force'])

            # Verificar resultado
            self.verify_result()

        # Dar recomendaciones
        self.provide_recommendations()

    def check_configuration(self):
        self.stdout.write('\n📋 CONFIGURACIÓN ACTUAL:')

        self.stdout.write(f'  DEBUG: {settings.DEBUG}')
        self.stdout.write(f'  STATIC_URL: {settings.STATIC_URL}')

        if hasattr(settings, 'STATICFILES_DIRS'):
            self.stdout.write(f'  STATICFILES_DIRS: {list(settings.STATICFILES_DIRS)}')

            # Verificar que las carpetas existen
            for static_dir in settings.STATICFILES_DIRS:
                exists = os.path.exists(static_dir)
                status = '✅' if exists else '❌'
                self.stdout.write(f'    {status} {static_dir}')
        else:
            self.stdout.write('  ❌ STATICFILES_DIRS no configurado')

        if hasattr(settings, 'STATIC_ROOT'):
            self.stdout.write(f'  STATIC_ROOT: {settings.STATIC_ROOT}')
            static_root_exists = os.path.exists(settings.STATIC_ROOT)
            status = '✅' if static_root_exists else '❌'
            self.stdout.write(f'    {status} Carpeta existe')
        else:
            self.stdout.write('  ❌ STATIC_ROOT no configurado')

        # Verificar STATICFILES_FINDERS
        if hasattr(settings, 'STATICFILES_FINDERS'):
            self.stdout.write(f'  STATICFILES_FINDERS configurados: ✅')
        else:
            self.stdout.write(f'  ❌ STATICFILES_FINDERS no configurado')

    def check_source_files(self):
        self.stdout.write('\n📁 ARCHIVOS FUENTE EN static/:')

        if not settings.STATICFILES_DIRS:
            self.stdout.write('  ❌ STATICFILES_DIRS no configurado')
            return

        static_dir = settings.STATICFILES_DIRS[0]

        # Archivos específicos que fallan según el error
        critical_files = [
            'css/image-cropper.css',
            'js/perfil-interesado.js',
            'js/image-cropper.js',
            'css/styles.css',
            'js/main.js'
        ]

        self.stdout.write('  🔍 Archivos críticos:')
        for file_path in critical_files:
            full_path = os.path.join(static_dir, file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                self.stdout.write(f'    ✅ {file_path} ({size} bytes)')
            else:
                self.stdout.write(f'    ❌ {file_path} NO EXISTE')

        # Contar todos los archivos CSS y JS
        css_files = glob.glob(os.path.join(static_dir, '**/*.css'), recursive=True)
        js_files = glob.glob(os.path.join(static_dir, '**/*.js'), recursive=True)

        self.stdout.write(f'  📊 Total archivos CSS: {len(css_files)}')
        self.stdout.write(f'  📊 Total archivos JS: {len(js_files)}')

    def check_current_staticfiles(self):
        self.stdout.write('\n📦 ARCHIVOS EN staticfiles/:')

        if not hasattr(settings, 'STATIC_ROOT') or not settings.STATIC_ROOT:
            self.stdout.write('  ❌ STATIC_ROOT no configurado')
            return

        static_root = settings.STATIC_ROOT

        if not os.path.exists(static_root):
            self.stdout.write('  ⚠️  Carpeta staticfiles/ no existe')
            return

        # Contar archivos actuales
        css_files = glob.glob(os.path.join(static_root, '**/*.css'), recursive=True)
        js_files = glob.glob(os.path.join(static_root, '**/*.js'), recursive=True)

        self.stdout.write(f'  📊 Archivos CSS actuales: {len(css_files)}')
        self.stdout.write(f'  📊 Archivos JS actuales: {len(js_files)}')

        # Verificar archivos específicos
        critical_files = [
            'css/image-cropper.css',
            'js/perfil-interesado.js',
            'js/image-cropper.js'
        ]

        self.stdout.write('  🔍 Archivos críticos en staticfiles:')
        for file_path in critical_files:
            full_path = os.path.join(static_root, file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                self.stdout.write(f'    ✅ {file_path} ({size} bytes)')
            else:
                self.stdout.write(f'    ❌ {file_path} NO EXISTE')

    def run_collectstatic(self, force=False):
        self.stdout.write('\n🔄 EJECUTANDO COLLECTSTATIC:')

        if force and hasattr(settings, 'STATIC_ROOT') and os.path.exists(settings.STATIC_ROOT):
            self.stdout.write('  🧹 Limpiando staticfiles/ existente...')
            try:
                shutil.rmtree(settings.STATIC_ROOT)
                self.stdout.write('    ✅ Carpeta limpiada')
            except Exception as e:
                self.stdout.write(f'    ❌ Error limpiando: {e}')

        self.stdout.write('  🚀 Ejecutando collectstatic...')

        try:
            # Ejecutar collectstatic con verbosidad
            call_command('collectstatic',
                         verbosity=2,
                         interactive=False,
                         clear=force)
            self.stdout.write('    ✅ collectstatic completado')
        except Exception as e:
            self.stdout.write(f'    ❌ Error en collectstatic: {e}')

    def verify_result(self):
        self.stdout.write('\n✅ VERIFICACIÓN DE RESULTADO:')

        if not hasattr(settings, 'STATIC_ROOT'):
            self.stdout.write('  ❌ STATIC_ROOT no configurado')
            return

        static_root = settings.STATIC_ROOT

        # Verificar archivos críticos
        critical_files = [
            'css/image-cropper.css',
            'js/perfil-interesado.js',
            'js/image-cropper.js',
            'css/styles.css',
            'js/main.js'
        ]

        success_count = 0
        for file_path in critical_files:
            full_path = os.path.join(static_root, file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                self.stdout.write(f'  ✅ {file_path} ({size} bytes)')
                success_count += 1
            else:
                self.stdout.write(f'  ❌ {file_path} FALTA')

        # Resumen
        total_files = len(critical_files)
        if success_count == total_files:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 ¡ÉXITO! Todos los archivos críticos están disponibles ({success_count}/{total_files})')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'\n⚠️  PROBLEMA: Solo {success_count}/{total_files} archivos críticos disponibles')
            )

    def provide_recommendations(self):
        self.stdout.write('\n💡 RECOMENDACIONES:')

        # Verificar si faltan archivos críticos
        missing_files = []
        if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
            critical_files = [
                'css/image-cropper.css',
                'js/perfil-interesado.js',
                'js/image-cropper.js'
            ]

            for file_path in critical_files:
                full_path = os.path.join(settings.STATIC_ROOT, file_path)
                if not os.path.exists(full_path):
                    missing_files.append(file_path)

        if missing_files:
            self.stdout.write('  1. Archivos faltantes después de collectstatic:')
            for file_path in missing_files:
                self.stdout.write(f'     ❌ {file_path}')
            self.stdout.write('     Ejecuta: python manage.py fix_production_static --force')
        else:
            self.stdout.write('  ✅ Todos los archivos críticos están disponibles')

        self.stdout.write('  2. Para producción con servidor web:')
        self.stdout.write(f'     Configura servidor para servir desde: {settings.STATIC_ROOT}')

        self.stdout.write('  3. Para verificar URLs:')
        self.stdout.write('     Servidor: python manage.py runserver')
        self.stdout.write('     Probar: http://localhost:8000/static/css/image-cropper.css')

        if settings.DEBUG:
            self.stdout.write('  ⚠️  ATENCIÓN: DEBUG=True - Cambiar a False en producción')

        self.stdout.write('\n🔧 COMANDOS ÚTILES:')
        self.stdout.write('  - Diagnóstico: python manage.py fix_production_static --verify-only')
        self.stdout.write('  - Forzar recolección: python manage.py fix_production_static --force')
        self.stdout.write('  - Solo collectstatic: python manage.py collectstatic --clear')