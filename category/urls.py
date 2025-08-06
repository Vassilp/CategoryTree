from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, SimilarityViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'similarities', SimilarityViewSet, basename='similarity')

urlpatterns = [
    path('', include(router.urls)),
]
