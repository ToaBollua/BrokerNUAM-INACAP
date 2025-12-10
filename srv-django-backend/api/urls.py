from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload-csv/', views.upload_csv, name='upload_csv'),
    path('update-factor/', views.update_factor, name='update_factor'),
    path('export/my-data/', views.export_users_data, name='export_data'),
    path('entry/manual/', views.manual_entry, name='manual_entry'),
]