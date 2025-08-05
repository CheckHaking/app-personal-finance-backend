from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from datetime import date
from core.models import Category, Account, Transaction, Transfer

User = get_user_model()


class BaseAPITestCase(APITestCase):
    """Clase base para tests de API con autenticación"""
    
    def setUp(self):
        """Configuración inicial con usuario autenticado"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear token JWT para autenticación
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Configurar cliente con autenticación
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')


class CategoryViewSetTest(BaseAPITestCase):
    """Tests para CategoryViewSet"""
    
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(
            user=self.user,
            name='Alimentación',
            type='expense',
            color='#FF5733'
        )
    
    def test_list_categories(self):
        """Test listar categorías del usuario"""
        url = '/api/v1/categories/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Alimentación')
    
    def test_create_category(self):
        """Test crear nueva categoría"""
        url = '/api/v1/categories/'
        data = {
            'name': 'Transporte',
            'type': 'expense',
            'description': 'Gastos de transporte',
            'color': '#00FF00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Transporte')
        self.assertEqual(Category.objects.count(), 2)
    
    def test_update_category(self):
        """Test actualizar categoría"""
        url = f'/api/v1/categories/{self.category.id}/'
        data = {
            'name': 'Comida Actualizada',
            'type': 'expense',
            'color': '#FF0000'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Comida Actualizada')
    
    def test_delete_category(self):
        """Test eliminar categoría"""
        url = f'/api/v1/categories/{self.category.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)
    
    def test_categories_filtered_by_user(self):
        """Test que solo se muestran categorías del usuario autenticado"""
        # Crear otro usuario con categoría
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        Category.objects.create(
            user=other_user,
            name='Categoría de otro usuario'
        )
        
        url = '/api/v1/categories/'
        response = self.client.get(url)
        
        # Solo debe ver su propia categoría
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Alimentación')


class AccountViewSetTest(BaseAPITestCase):
    """Tests para AccountViewSet"""
    
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            user=self.user,
            name='Cuenta Corriente',
            type='bank',
            balance=Decimal('1000.00')
        )
    
    def test_list_accounts(self):
        """Test listar cuentas del usuario"""
        url = '/api/v1/accounts/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Cuenta Corriente')
    
    def test_create_account(self):
        """Test crear nueva cuenta"""
        url = '/api/v1/accounts/'
        data = {
            'name': 'Tarjeta de Crédito',
            'type': 'credit',
            'balance': '-500.00',
            'currency': 'MXN',
            'credit_limit': '5000.00',
            'closing_date': 15,
            'payment_date': 5
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Tarjeta de Crédito')
        self.assertEqual(Account.objects.count(), 2)


class TransactionViewSetTest(BaseAPITestCase):
    """Tests para TransactionViewSet"""
    
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            user=self.user,
            name='Cuenta Test',
            type='bank',
            balance=Decimal('1000.00')
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Alimentación',
            type='expense'
        )
        self.transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            transaction_type='expense',
            amount=Decimal('50.00'),
            description='Almuerzo',
            date=date.today()
        )
    
    def test_list_transactions(self):
        """Test listar transacciones del usuario"""
        url = '/api/v1/transactions/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['description'], 'Almuerzo')
    
    def test_create_transaction(self):
        """Test crear nueva transacción"""
        url = '/api/v1/transactions/'
        data = {
            'account': self.account.id,
            'category': self.category.id,
            'transaction_type': 'expense',
            'amount': '25.00',
            'description': 'Café',
            'date': str(date.today())
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Café')
        self.assertEqual(Transaction.objects.count(), 2)


class AuthenticationTest(APITestCase):
    """Tests para autenticación"""
    
    def test_unauthenticated_request(self):
        """Test que las requests sin autenticación sean rechazadas"""
        url = '/api/v1/categories/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_invalid_token(self):
        """Test que tokens inválidos sean rechazados"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        url = '/api/v1/categories/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
