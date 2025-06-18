# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
]

# ✅ CONFIGURACIÓN CORRECTA PARA DESARROLLO
if settings.DEBUG:
    # Servir archivos media (imágenes subidas)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # IMPORTANTE: Servir desde static/ (desarrollo), NO desde staticfiles/
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])