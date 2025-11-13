# backend/brokernuam/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Asegúrate de que tu API esté prefijada con 'api/'
    path('api/', include('mantenedor.urls')),
    
    # ... otras rutas de api (auth, etc.)
]