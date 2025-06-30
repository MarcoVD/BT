
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from usuarios.models import Interesado, Curriculum, IdiomaInteresado

User = get_user_model()


def debug_idioma_urls():
    """Función para debuggear las URLs de idiomas"""

    print("🔍 DEBUGGING - Eliminación de Idiomas")
    print("=" * 50)

    # 1. Verificar URLs
    try:
        # Verificar que la URL existe
        url = reverse('eliminar_idioma_ajax', kwargs={'idioma_id': 1})
        print(f"✅ URL generada correctamente: {url}")
    except Exception as e:
        print(f"❌ Error generando URL: {e}")
        return

    # 2. Verificar si hay usuarios interesados
    interesados = Interesado.objects.all()
    print(f"📊 Interesados en DB: {interesados.count()}")

    if interesados.exists():
        primer_interesado = interesados.first()
        print(f"👤 Primer interesado: {primer_interesado.usuario.email}")

        # Verificar curriculum
        if hasattr(primer_interesado, 'curriculum'):
            curriculum = primer_interesado.curriculum
            idiomas = curriculum.idiomas.all()
            print(f"Idiomas en curriculum: {idiomas.count()}")

            for idioma in idiomas:
                print(f"   - {idioma.idioma} (ID: {idioma.id})")

                # Probar URL específica
                try:
                    url_especifica = reverse('eliminar_idioma_ajax', kwargs={'idioma_id': idioma.id})
                    print(f"   ✅ URL para este idioma: {url_especifica}")
                except Exception as e:
                    print(f"   ❌ Error URL específica: {e}")
        else:
            print("❌ Primer interesado no tiene curriculum")

    # 3. Verificar todas las URLs del proyecto
    from django.urls import get_resolver
    resolver = get_resolver()

    print("\n🔗 URLs relacionadas con idiomas:")
    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'url_patterns'):
            for subpattern in pattern.url_patterns:
                if hasattr(subpattern, 'name') and subpattern.name and 'idioma' in subpattern.name:
                    print(f"   - {subpattern.name}: {subpattern.pattern}")


if __name__ == "__main__":
    # Configurar Django
    import os
    import sys
    import django

    # Agregar el directorio del proyecto al path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    # Ejecutar debug
    debug_idioma_urls()