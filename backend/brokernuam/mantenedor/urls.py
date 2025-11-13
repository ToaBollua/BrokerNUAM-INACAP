from rest_framework.routers import DefaultRouter
from .views import QualificationViewSet

router = DefaultRouter()
router.register(r'calificaciones', QualificationViewSet, basename='calificaciones')


urlpatterns = router.urls
