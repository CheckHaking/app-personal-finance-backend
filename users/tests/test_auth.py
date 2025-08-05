from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


class UserRegistrationTest(APITestCase):
    """Tests para registro de usuarios"""
    
    def test_register_user_success(self):
        """Test registro exitoso de usuario"""
        url = '/api/v1/auth/register/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'newuser@example.com')
        self.assertNotIn('password', response.data)  # Password no debe aparecer en respuesta
        
        # Verificar que el usuario se creó en la BD
        user = User.objects.get(username='newuser')
        self.assertTrue(user.check_password('securepassword123'))
    
    def test_register_user_duplicate_username(self):
        """Test registro con username duplicado"""
        # Crear usuario existente
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        url = '/api/v1/auth/register/'
        data = {
            'username': 'existinguser',  # Username duplicado
            'email': 'newemail@example.com',
            'password': 'newpassword123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
    
    def test_register_user_missing_fields(self):
        """Test registro con campos faltantes"""
        url = '/api/v1/auth/register/'
        data = {
            'username': 'incompleteuser'
            # Falta password
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class UserAuthenticationTest(APITestCase):
    """Tests para autenticación JWT"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
    
    def test_login_success(self):
        """Test login exitoso"""
        url = '/api/v1/auth/token/'
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login con credenciales incorrectas"""
        url = '/api/v1/auth/token/'
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh(self):
        """Test refresh de token"""
        # Obtener tokens iniciales
        refresh = RefreshToken.for_user(self.user)
        
        url = '/api/v1/auth/token/refresh/'
        data = {
            'refresh': str(refresh)
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class UserProfileTest(APITestCase):
    """Tests para perfil de usuario"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Autenticar usuario
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_get_user_profile(self):
        """Test obtener perfil del usuario autenticado"""
        url = '/api/v1/auth/me/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertNotIn('password', response.data)
    
    def test_get_profile_unauthenticated(self):
        """Test obtener perfil sin autenticación"""
        self.client.credentials()  # Remover autenticación
        
        url = '/api/v1/auth/me/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTest(APITestCase):
    """Tests para logout"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Obtener tokens
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_logout_success(self):
        """Test logout exitoso"""
        url = '/api/v1/auth/logout/'
        data = {
            'refresh': str(self.refresh)
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
    
    def test_logout_invalid_token(self):
        """Test logout con token inválido"""
        url = '/api/v1/auth/logout/'
        data = {
            'refresh': 'invalid_token'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
