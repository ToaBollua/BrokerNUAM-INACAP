from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload-csv/', views.upload_csv, name='upload_csv'),
    path('update-factor/', views.update_factor, name='update_factor'),
]