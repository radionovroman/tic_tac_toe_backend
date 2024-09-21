from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from .models import Image, SharedGame
from .serializers import ImageSerializer, UserSerializer
from django.contrib.auth import authenticate
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from uuid import uuid4
import logging
from django.db import transaction

# Configure logger
logger = logging.getLogger(__name__)

# ViewSet to handle image uploads and retrieval for authenticated users
class ImageViewSet(viewsets.ModelViewSet):
    serializer_class = ImageSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Image.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user
        new_files = []

        for key in request.FILES:
            file = request.FILES[key]
            filename_key = key.replace('_image', '_word')
            description = request.data.get(filename_key, '')
            new_files.append((file, description))

        existing_images = Image.objects.filter(user=user)
        num_existing_images = existing_images.count()

        if num_existing_images >= 3:
            excess_count = num_existing_images - 3
            images_to_delete = existing_images[:excess_count]
            for img in images_to_delete:
                img.delete()

        for i, (file, description) in enumerate(new_files):
            if i < 3:
                if i < len(existing_images):
                    existing_image = existing_images[i]
                    existing_image.file = file
                    existing_image.description = description
                    existing_image.save()
                else:
                    # Creating a new image with a shareable link
                    image = Image(
                        user=user, 
                        file=file, 
                        description=description, 
                        shared_link=uuid4()  # Generate a unique UUID for the shareable link
                    )
                    image.save()

        return Response(status=status.HTTP_201_CREATED)
    
    

# View to handle user registration
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

# Function to handle user login and token generation
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    else:
        return JsonResponse({'detail': 'Invalid credentials'}, status=400)
    
# View to retrieve the current logged-in user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)

class GameDataView(APIView):
    """
    API view to handle fetching game data based on user customizations
    or shareable link.
    """
    permission_classes = [AllowAny]  # Allow access to everyone for shared links and authenticated users

    def get(self, request, *args, **kwargs):
        shared_link = kwargs.get('shared_link', None)
        user = request.user if request.user.is_authenticated else None
        
        # Case 1: If the request includes a valid shared link (for non-authenticated users)
        if shared_link:
            try:
                # Ensure the shared link is a valid UUID
                shared_uuid = UUID(shared_link, version=4)
                
                # Retrieve the image(s) associated with this shared link
                customizations = Image.objects.filter(shared_link=shared_uuid)
                if not customizations.exists():
                    return Response({'error': 'Customization not found for this link'}, status=status.HTTP_404_NOT_FOUND)
                
                # Build game data from the shared customization
                game_data = {
                    'items': [
                        {'name': image.description, 'image': image.file.url}
                        for image in customizations
                    ],
                    'matches': [],  # Add match-related logic if necessary
                }
                return Response(game_data, status=status.HTTP_200_OK)
            except ValueError:
                return Response({'error': 'Invalid shared link'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Case 2: If the user is authenticated, retrieve their customizations
        if user:
            customizations = Image.objects.filter(user=user)
            if customizations.exists():
                # Build the game data from the authenticated user's customizations
                game_data = {
                    'items': [
                        {'name': image.description, 'image': image.file.url}
                        for image in customizations
                    ],
                    'matches': [],  # Add match-related logic if necessary
                }
            else:
                # Fallback to default data if no customizations exist
                game_data = {
                    'items': [
                        {'name': 'apple', 'image': '/images/apple.jpg'},
                        {'name': 'banana', 'image': '/images/banana.jpg'},
                        {'name': 'cherry', 'image': '/images/cherry.jpg'},
                    ],
                    'matches': [],
                }
            return Response(game_data, status=status.HTTP_200_OK)

        # Default case: User is neither authenticated nor providing a valid shared link
        return Response({'error': 'Unauthorized or invalid link'}, status=status.HTTP_401_UNAUTHORIZED)

# View to handle generating a shareable link for a user's customization
class GenerateShareableLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        logger.info(f"Generating shareable link for user: {user.username}")
        try:
            with transaction.atomic():
                images = Image.objects.filter(user=user).order_by('-id')[:3]
                logger.info(f"Found {images.count()} images for user {user.username}")
                
                if images.exists():
                    shared_game = SharedGame.objects.create(user=user)
                    for image in images:
                        image.shared_game = shared_game
                        image.save()
                    
                    logger.info(f"Updated {images.count()} images with shared game {shared_game.shared_link} for user {user.username}")
                    
                    shareable_link = request.build_absolute_uri(f'/share/{shared_game.shared_link}/')
                    return Response({'shared_link': shareable_link}, status=status.HTTP_200_OK)
                else:
                    logger.warning(f"No images found for user {user.username}")
                    return Response({'error': 'No customizations found for this user'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generating shareable link for user {user.username}: {str(e)}", exc_info=True)
            return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# View to handle access to shared customizations via a shareable link
class SharedCustomizationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, shared_link, *args, **kwargs):
        try:
            shared_game = SharedGame.objects.get(shared_link=shared_link)
            images = Image.objects.filter(shared_game=shared_game)

            if not images.exists():
                logger.warning(f"No images found for shared game {shared_link}")
                return Response({'error': 'No images found for this shared game'}, status=status.HTTP_404_NOT_FOUND)

            serializer = ImageSerializer(images, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except SharedGame.DoesNotExist:
            logger.warning(f"Shared game not found for link {shared_link}")
            return Response({'error': 'Shared game not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving shared game: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

