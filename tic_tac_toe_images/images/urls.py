# images/urls.py
from django.urls import path
from .views import image_upload_test_view, login_view

urlpatterns = [
    path('upload/test/', image_upload_test_view, name='image_upload_test'),
    path('login/', login_view, name='login'),  # Add this line
   ]

