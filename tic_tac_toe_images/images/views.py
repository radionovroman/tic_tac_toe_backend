from rest_framework import viewsets
from .models import Image
from .serializers import ImageSerializer
from django.shortcuts import render
from .forms import ImageForm
from django.contrib.auth.decorators import login_required

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('image_upload_test')  # Redirect to the upload page after login
    else:
        form = AuthenticationForm()
    return render(request, 'images/login.html', {'form': form})

@login_required  # Ensure the user is logged in
def image_upload_test_view(request):
    uploaded_image_url = None
    error_message = None

    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create a new Image instance but don't save it yet
                image_instance = form.save(commit=False)
                image_instance.user = request.user  # Set the user to the currently logged-in user
                image_instance.save()  # Now save the instance
                uploaded_image_url = image_instance.file.url  # Get the URL of the uploaded image
                return render(request, 'images/upload_test.html', {
                    'form': form,
                    'success': True,
                    'uploaded_image_url': uploaded_image_url
                })
            except Exception as e:
                error_message = str(e)  # Capture any exceptions
        else:
            error_message = "Form is not valid."
    else:
        form = ImageForm()

    return render(request, 'images/upload_test.html', {
        'form': form,
        'error_message': error_message
    })

class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
