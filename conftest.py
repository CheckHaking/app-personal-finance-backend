"""
Configuración global de pytest para el proyecto Personal Finance.
"""
import pytest
import django
from django.conf import settings
import os

# Configurar Django antes de las importaciones
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture(scope='function')
def api_client():
    """Cliente API para las pruebas."""
    return APIClient()


@pytest.fixture
def user_factory(db):
    """Factory para crear usuarios."""
    def create_user(**kwargs):
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
        }
        defaults.update(kwargs)
        
        # Si hay un username único, generar email único también
        if 'username' in kwargs and 'email' not in kwargs:
            defaults['email'] = f"{kwargs['username']}@example.com"
            
        return User.objects.create_user(**defaults)
    return create_user


@pytest.fixture
def user(user_factory):
    """Usuario de prueba por defecto."""
    return user_factory()


@pytest.fixture
def auth_client(api_client, user):
    """Cliente API autenticado con JWT."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    api_client.user = user  # Guardar referencia al usuario
    return api_client


@pytest.fixture
def auth_headers(user):
    """Headers de autenticación JWT."""
    refresh = RefreshToken.for_user(user)
    return {
        'Authorization': f'Bearer {refresh.access_token}'
    }


# Configuración para pytest-django
pytest_plugins = [
    'tests.fixtures.model_factories',
]