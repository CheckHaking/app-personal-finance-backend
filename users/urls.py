from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserViewSet, LogoutView, UserProfileView

# Creamos un router y registramos nuestro viewset con él.
# El endpoint para registrar usuarios será /api/v1/auth/register/
router = DefaultRouter()
router.register(r'register', UserViewSet, basename='register')

# Las URLs de la API son determinadas automáticamente por el router.
urlpatterns = [
    # Rutas para la obtención y refresco de tokens JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Ruta para el logout (invalidación del token de refresco)
    path('logout/', LogoutView.as_view(), name='auth_logout'),

    # Ruta para obtener información del usuario autenticado
    path('me/', UserProfileView.as_view(), name='user_profile'),

    # Incluye las rutas del router (para el registro)
    path('', include(router.urls)),
]
