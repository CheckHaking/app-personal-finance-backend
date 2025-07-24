from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Endpoints de Autenticación y Usuarios (/api/v1/auth/...)
    path('api/v1/auth/', include('users.urls')),

    # Core app (activado de nuevo)
    path('api/v1/', include('core.urls')),
]
