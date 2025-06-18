# usuarios/management/commands/check_static.py
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import glob


class Command(BaseCommand):
    help = 'Diagnostica problemas con archivos estáticos y media'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('🔍 DIAGNÓSTICO DE ARCHIVOS ESTÁTICOS Y MEDIA')
        )
        self.stdout.write('=' * 50)

        # Verificar configuración
        self.check_settings()

        # Verificar estructura de carpetas
        self.check_directories()

        # Verificar archivos específicos
        self.check_specific_files()

        # Verificar archivos media
        self.check_media_files()

        # Sugerencias
        self.provide_suggestions()

    def check_settings(self):
        self.stdout.write('\n📋 CONFIGURACIÓN ACTUAL:')
        self.stdout.write(f'  DEBUG: {settings.DEBUG}')
        self.stdout.write(f'  STATIC_URL: {settings.STATIC_URL}')
        self.stdout.write(f'  MEDIA_URL: {settings.MEDIA_URL}')

        if hasattr(settings, 'STATICFILES_DIRS'):
            self.stdout.write(f'  STATICFILES_DIRS: {settings.STATICFILES_DIRS}')

        if hasattr(settings, 'STATIC_ROOT'):
            self.stdout.write(f'  STATIC_ROOT: {settings.STATIC_ROOT}')

        if hasattr(settings, 'MEDIA_ROOT'):
            self.stdout.write(f'  MEDIA_ROOT: {settings.MEDIA_ROOT}')

    def check_directories(self):
        self.stdout.write('\n📁 ESTRUCTURA DE CARPETAS:')

        # Verificar carpeta static principal
        static_dir = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None
        if static_dir:
            exists = os.path.exists(static_dir)
            status = '✅' if exists else '❌'
            self.stdout.write(f'  {status} {static_dir} (static principal)')

            if exists:
                # Verificar subcarpetas
                css_dir = os.path.join(static_dir, 'css')
                js_dir = os.path.join(static_dir, 'js')

                css_exists = os.path.exists(css_dir)
                js_exists = os.path.exists(js_dir)

                self.stdout.write(f'    {"✅" if css_exists else "❌"} {css_dir}')
                self.stdout.write(f'    {"✅" if js_exists else "❌"} {js_dir}')

        # Verificar carpeta media
        media_exists = os.path.exists(settings.MEDIA_ROOT)
        status = '✅' if media_exists else '❌'
        self.stdout.write(f'  {status} {settings.MEDIA_ROOT} (media)')

        if media_exists:
            interesados_dir = os.path.join(settings.MEDIA_ROOT, 'interesados')
            interesados_exists = os.path.exists(interesados_dir)
            self.stdout.write(f'    {"✅" if interesados_exists else "❌"} {interesados_dir}')

    def check_specific_files(self):
        self.stdout.write('\n📄 ARCHIVOS ESPECÍFICOS QUE FALLAN:')

        static_dir = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None

        if not static_dir:
            self.stdout.write('  ❌ STATICFILES_DIRS no configurado')
            return

        files_to_check = [
            'css/image-cropper.css',
            'js/perfil-interesado.js',
            'js/image-cropper.js',
            'css/styles.css',
            'js/main.js'
        ]

        for file_path in files_to_check:
            full_path = os.path.join(static_dir, file_path)
            exists = os.path.exists(full_path)
            status = '✅' if exists else '❌'
            self.stdout.write(f'  {status} {file_path}')

            if not exists:
                # Buscar el archivo en otras ubicaciones
                search_pattern = f"**/{os.path.basename(file_path)}"
                found_files = glob.glob(search_pattern, recursive=True)
                if found_files:
                    self.stdout.write(f'      🔍 Encontrado en: {found_files[0]}')

    def check_media_files(self):
        self.stdout.write('\n🖼️ ARCHIVOS MEDIA (IMÁGENES):')

        interesados_dir = os.path.join(settings.MEDIA_ROOT, 'interesados')

        if not os.path.exists(interesados_dir):
            self.stdout.write('  ❌ Carpeta interesados/ no existe')
            return

        # Listar archivos de imagen
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif']
        image_files = []

        for extension in image_extensions:
            pattern = os.path.join(interesados_dir, extension)
            image_files.extend(glob.glob(pattern))

        if image_files:
            self.stdout.write(f'  ✅ {len(image_files)} imagen(es) encontrada(s):')
            for img in image_files[:5]:  # Mostrar solo las primeras 5
                self.stdout.write(f'    - {os.path.basename(img)}')
        else:
            self.stdout.write('  ⚠️  No se encontraron imágenes')

    def provide_suggestions(self):
        self.stdout.write('\n💡 SUGERENCIAS DE SOLUCIÓN:')

        static_dir = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None

        if not static_dir or not os.path.exists(static_dir):
            self.stdout.write('  1. Crear carpeta static:')
            self.stdout.write('     mkdir -p static/css static/js')

        # Verificar archivos faltantes
        missing_files = []
        if static_dir:
            files_to_check = [
                'css/image-cropper.css',
                'js/perfil-interesado.js',
                'js/image-cropper.js'
            ]

            for file_path in files_to_check:
                full_path = os.path.join(static_dir, file_path)
                if not os.path.exists(full_path):
                    missing_files.append(file_path)

        if missing_files:
            self.stdout.write('  2. Archivos faltantes - crear o mover:')
            for file_path in missing_files:
                self.stdout.write(f'     touch static/{file_path}')

        self.stdout.write('  3. Recolectar archivos estáticos:')
        self.stdout.write('     python manage.py collectstatic --noinput')

        self.stdout.write('  4. Verificar configuración de URLs:')
        self.stdout.write('     Asegurar que config/urls.py tenga static() para DEBUG')

        self.stdout.write('  5. Reiniciar servidor:')
        self.stdout.write('     python manage.py runserver')

        self.stdout.write(
            self.style.SUCCESS('\n✅ Ejecuta este comando después de corregir:')
        )
        self.stdout.write(
            self.style.SUCCESS('   python manage.py check_static')
        )