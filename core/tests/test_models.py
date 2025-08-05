from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from core.models import Category, Account, Transaction, Transfer

User = get_user_model()


class CategoryModelTest(TestCase):
    """Tests para el modelo Category"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_category(self):
        """Test crear una categoría básica"""
        category = Category.objects.create(
            user=self.user,
            name='Alimentación',
            type='expense',
            description='Gastos de comida',
            color='#FF5733'
        )
        
        self.assertEqual(category.name, 'Alimentación')
        self.assertEqual(category.type, 'expense')
        self.assertEqual(category.user, self.user)
        self.assertEqual(str(category), 'Alimentación')
    
    def test_category_default_values(self):
        """Test valores por defecto de Category"""
        category = Category.objects.create(
            user=self.user,
            name='Test Category'
        )
        
        self.assertEqual(category.type, 'expense')  # Default
        self.assertEqual(category.color, '#000000')  # Default
    
    def test_category_unique_together(self):
        """Test que no se puedan crear categorías duplicadas para el mismo usuario"""
        Category.objects.create(
            user=self.user,
            name='Duplicada'
        )
        
        # Intentar crear otra categoría con el mismo nombre y usuario
        with self.assertRaises(Exception):  # IntegrityError
            Category.objects.create(
                user=self.user,
                name='Duplicada'
            )


class AccountModelTest(TestCase):
    """Tests para el modelo Account"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_bank_account(self):
        """Test crear cuenta bancaria"""
        account = Account.objects.create(
            user=self.user,
            name='Cuenta Corriente',
            type='bank',
            balance=Decimal('1000.00'),
            currency='MXN'
        )
        
        self.assertEqual(account.name, 'Cuenta Corriente')
        self.assertEqual(account.type, 'bank')
        self.assertEqual(account.balance, Decimal('1000.00'))
        self.assertEqual(str(account), 'Cuenta Corriente - Cuenta Bancaria')
    
    def test_create_credit_card(self):
        """Test crear tarjeta de crédito con límite"""
        card = Account.objects.create(
            user=self.user,
            name='Tarjeta Visa',
            type='credit',
            balance=Decimal('-500.00'),  # Deuda
            currency='MXN',
            credit_limit=Decimal('5000.00'),
            closing_date=15,
            payment_date=5
        )
        
        self.assertEqual(card.type, 'credit')
        self.assertEqual(card.credit_limit, Decimal('5000.00'))
        self.assertEqual(card.closing_date, 15)
        self.assertEqual(card.payment_date, 5)
    
    def test_account_default_currency(self):
        """Test moneda por defecto"""
        account = Account.objects.create(
            user=self.user,
            name='Test Account',
            type='cash',
            balance=Decimal('100.00')
        )
        
        self.assertEqual(account.currency, 'MXN')


class TransactionModelTest(TestCase):
    """Tests para el modelo Transaction"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
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
    
    def test_create_expense_transaction(self):
        """Test crear transacción de gasto"""
        transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=self.category,
            transaction_type='expense',
            amount=Decimal('50.00'),
            description='Almuerzo',
            date=date.today()
        )
        
        self.assertEqual(transaction.transaction_type, 'expense')
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.category, self.category)
    
    def test_create_income_transaction(self):
        """Test crear transacción de ingreso"""
        income_category = Category.objects.create(
            user=self.user,
            name='Salario',
            type='income'
        )
        
        transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            category=income_category,
            transaction_type='income',
            amount=Decimal('2000.00'),
            description='Pago de salario',
            date=date.today()
        )
        
        self.assertEqual(transaction.transaction_type, 'income')
        self.assertEqual(transaction.amount, Decimal('2000.00'))


class TransferModelTest(TestCase):
    """Tests para el modelo Transfer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.account1 = Account.objects.create(
            user=self.user,
            name='Cuenta Origen',
            type='bank',
            balance=Decimal('1000.00')
        )
        
        self.account2 = Account.objects.create(
            user=self.user,
            name='Cuenta Destino',
            type='bank',
            balance=Decimal('500.00')
        )
    
    def test_create_transfer(self):
        """Test crear transferencia entre cuentas"""
        transfer = Transfer.objects.create(
            user=self.user,
            from_account=self.account1,
            to_account=self.account2,
            amount=Decimal('200.00'),
            description='Transferencia de prueba',
            date=date.today()
        )
        
        self.assertEqual(transfer.from_account, self.account1)
        self.assertEqual(transfer.to_account, self.account2)
        self.assertEqual(transfer.amount, Decimal('200.00'))
        self.assertIn('200.00', str(transfer))
        self.assertIn('Cuenta Origen', str(transfer))
        self.assertIn('Cuenta Destino', str(transfer))
