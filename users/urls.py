from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Creamos un router y registramos nuestro viewset con él.
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

# Las URLs de la API son determinadas automáticamente por el router.
urlpatterns = [
    path('', include(router.urls)),
]
