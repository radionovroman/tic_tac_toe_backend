from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    ImageViewSet, RegisterView, login_view, current_user_view,
    SharedCustomizationView, GenerateShareableLinkView, GameDataView
)

# Set up the router and register the ImageViewSet
router = DefaultRouter()
router.register(r'images', ImageViewSet, basename='image')

# Define urlpatterns
urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('current_user/', current_user_view, name='current_user'),
    path('share/<uuid:shared_link>/', SharedCustomizationView.as_view(), name='shared-customization'),
    path('generate-share-link/', GenerateShareableLinkView.as_view(), name='generate-share-link'),
     # URL for authenticated user to access their game data
    path('game-data/', GameDataView.as_view(), name='game-data'),
    
    # URL for non-authenticated users to access game data via shared link
    path('game-data/shared/<uuid:shared_link>/', GameDataView.as_view(), name='shared-game-data'),
]
