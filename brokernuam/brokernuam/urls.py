from django.contrib import admin
from django.urls import path, include

# Imports necesarios para servir archivos estáticos en desarrollo
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Añade las URLs de autenticación de Django (para login/logout)
    path('accounts/', include('django.contrib.auth.urls')),

    # Conecta tu aplicación 'mantenedor' a la raíz del sitio
    path('', include('mantenedor.urls')),
]

# --- AÑADE ESTO ---
# Sirve archivos estáticos (CSS, JS, Imágenes) solo durante el desarrollo (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    # Nota: Esto asume que solo tienes un directorio en STATICFILES_DIRS