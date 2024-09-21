# images/urls.py
from django.urls import path
from .views import image_upload_view, image_list_view

urlpatterns = [
    path('', image_list_view, name='image_list'),
    path('upload/', image_upload_view, name='image_upload'),
]
