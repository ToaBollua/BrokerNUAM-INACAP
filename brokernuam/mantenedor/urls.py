from django.urls import path
from . import views

urlpatterns = [
    path('', views.QualificationListView.as_view(), name='qualification_list'),
    path('create/', views.create_qualification, name='create_qualification'),
    path('update/<int:pk>/', views.update_qualification, name='update_qualification'),
    path('delete/<int:pk>/', views.QualificationDeleteView.as_view(), name='delete_qualification'),
    path('bulk_load/', views.bulk_load, name='bulk_load'),
]
