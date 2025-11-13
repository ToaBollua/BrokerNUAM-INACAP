# backend/mantenedor/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CalificacionTributariaViewSet

# El Router genera:
# /calificaciones/
# /calificaciones/{id}/
# /calificaciones/previsualizar-csv/
# /calificaciones/carga-masiva/
router = DefaultRouter()
router.register(
    r'calificaciones', 
    CalificacionTributariaViewSet, 
    basename='calificacion'
)

urlpatterns = [
    path('', include(router.urls)),
]