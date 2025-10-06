"""
Factory Boy factories para los modelos del proyecto.
"""
import factory
from factory.django import DjangoModelFactory
from factory import fuzzy
from decimal import Decimal
import random
from datetime import datetime, timedelta
from django.utils import timezone
from faker import Faker

from core.models import (
    Category, Account, Transaction, Transfer, Budget, BudgetLine,
    SavingsGoal, Tag, RecurringTransaction, TransactionReceipt,
    SharedExpense, SharedExpenseParticipant, Alert
)
from users.models import User

fake = Faker('es_MX')  # Usar locale mexicano


class UserFactory(DjangoModelFactory):
    """Factory para el modelo User."""
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name', locale='es_MX')
    last_name = factory.Faker('last_name', locale='es_MX')
    is_active = True
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password('testpass123')


class CategoryFactory(DjangoModelFactory):
    """Factory para el modelo Category."""
    class Meta:
        model = Category
        django_get_or_create = ('user', 'name')
    
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('word', locale='es_MX')
    type = fuzzy.FuzzyChoice(['income', 'expense'])
    description = factory.Faker('sentence', locale='es_MX')
    color = factory.Faker('hex_color')


class AccountFactory(DjangoModelFactory):
    """Factory para el modelo Account."""
    class Meta:
        model = Account
    
    user = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(lambda obj: f"{fake.company()} {obj.type}")
    type = fuzzy.FuzzyChoice(['cash', 'bank', 'credit', 'investment', 'virtual'])
    balance = fuzzy.FuzzyDecimal(0, 10000, 2)
    currency = 'MXN'
    is_virtual = False
    
    # Campos específicos para tarjetas de crédito
    credit_limit = factory.LazyAttribute(
        lambda obj: fuzzy.FuzzyDecimal(10000, 50000, 2).fuzz() if obj.type == 'credit' else None
    )
    closing_date = factory.LazyAttribute(
        lambda obj: fuzzy.FuzzyInteger(1, 28).fuzz() if obj.type == 'credit' else None
    )
    payment_date = factory.LazyAttribute(
        lambda obj: (obj.closing_date + 20) % 30 if obj.type == 'credit' and obj.closing_date else None
    )


class TransactionFactory(DjangoModelFactory):
    """Factory para el modelo Transaction."""
    class Meta:
        model = Transaction
    
    user = factory.SubFactory(UserFactory)
    account = factory.SubFactory(AccountFactory, user=factory.SelfAttribute('..user'))
    category = factory.SubFactory(
        CategoryFactory,
        user=factory.SelfAttribute('..user'),
        type=factory.SelfAttribute('..transaction_type')
    )
    transaction_type = fuzzy.FuzzyChoice(['income', 'expense'])
    amount = fuzzy.FuzzyDecimal(10, 5000, 2)
    description = factory.Faker('sentence', nb_words=6, locale='es_MX')
    date = fuzzy.FuzzyDate(
        datetime.now().date() - timedelta(days=30),
        datetime.now().date()
    )
    is_recurring = False


class TransferFactory(DjangoModelFactory):
    """Factory para el modelo Transfer."""
    class Meta:
        model = Transfer
    
    user = factory.SubFactory(UserFactory)
    from_account = factory.SubFactory(AccountFactory, user=factory.SelfAttribute('..user'))
    to_account = factory.SubFactory(AccountFactory, user=factory.SelfAttribute('..user'))
    amount = fuzzy.FuzzyDecimal(100, 5000, 2)
    description = factory.Faker('sentence', nb_words=4, locale='es_MX')
    date = fuzzy.FuzzyDate(
        datetime.now().date() - timedelta(days=30),
        datetime.now().date()
    )


class BudgetFactory(DjangoModelFactory):
    """Factory para el modelo Budget."""
    class Meta:
        model = Budget
    
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('catch_phrase', locale='es_MX')
    period_type = fuzzy.FuzzyChoice(['monthly', 'weekly', 'custom'])
    start_date = factory.LazyFunction(datetime.now().date)
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date + timedelta(days=30) if obj.period_type == 'custom' else None
    )
    currency = 'MXN'
    status = 'active'


class BudgetLineFactory(DjangoModelFactory):
    """Factory para el modelo BudgetLine."""
    class Meta:
        model = BudgetLine
    
    budget = factory.SubFactory(BudgetFactory)
    category = factory.SubFactory(
        CategoryFactory,
        user=factory.SelfAttribute('..budget.user'),
        type='expense'
    )
    amount = fuzzy.FuzzyDecimal(1000, 10000, 2)
    notes = factory.Faker('sentence', nb_words=4, locale='es_MX')


class SavingsGoalFactory(DjangoModelFactory):
    """Factory para el modelo SavingsGoal."""
    class Meta:
        model = SavingsGoal
    
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('catch_phrase', locale='es_MX')
    target_amount = fuzzy.FuzzyDecimal(5000, 50000, 2)
    target_date = factory.LazyAttribute(
        lambda o: datetime.now().date() + timedelta(days=random.randint(90, 365))
    )
    currency = 'MXN'
    linked_account = factory.SubFactory(
        AccountFactory,
        user=factory.SelfAttribute('..user'),
        type='bank'
    )
    contribution_frequency = fuzzy.FuzzyChoice(['weekly', 'monthly', 'flex'])
    is_active = True


class TagFactory(DjangoModelFactory):
    """Factory para el modelo Tag."""
    class Meta:
        model = Tag
        django_get_or_create = ('user', 'name')
    
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('word', locale='es_MX')
    color = factory.Faker('hex_color')


class RecurringTransactionFactory(DjangoModelFactory):
    """Factory para el modelo RecurringTransaction."""
    class Meta:
        model = RecurringTransaction
    
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('catch_phrase', locale='es_MX')
    description = factory.Faker('sentence', locale='es_MX')
    amount = fuzzy.FuzzyDecimal(100, 5000, 2)
    transaction_type = fuzzy.FuzzyChoice(['income', 'expense'])
    category = factory.SubFactory(
        CategoryFactory,
        user=factory.SelfAttribute('..user'),
        type=factory.SelfAttribute('..transaction_type')
    )
    account = factory.SubFactory(AccountFactory, user=factory.SelfAttribute('..user'))
    frequency = fuzzy.FuzzyChoice(['daily', 'weekly', 'biweekly', 'monthly', 'quarterly', 'yearly'])
    start_date = factory.LazyFunction(datetime.now().date)
    next_date = factory.LazyAttribute(lambda o: o.start_date)
    is_active = True
    auto_create = False
    notify_before_days = 1


class AlertFactory(DjangoModelFactory):
    """Factory para el modelo Alert."""
    class Meta:
        model = Alert
    
    user = factory.SubFactory(UserFactory)
    alert_type = fuzzy.FuzzyChoice([
        'budget_exceeded', 'budget_warning', 'low_balance',
        'payment_due', 'goal_milestone', 'recurring_due'
    ])
    is_active = True
    
    # Configuración específica según el tipo
    threshold_amount = factory.LazyAttribute(
        lambda obj: fuzzy.FuzzyDecimal(1000, 5000, 2).fuzz() if obj.alert_type == 'low_balance' else None
    )
    threshold_percentage = factory.LazyAttribute(
        lambda obj: fuzzy.FuzzyInteger(70, 90).fuzz() if obj.alert_type == 'budget_warning' else None
    )
    days_before = factory.LazyAttribute(
        lambda obj: fuzzy.FuzzyInteger(1, 5).fuzz() if obj.alert_type == 'payment_due' else None
    )


# Registrar las factories con pytest-factoryboy
pytest_plugins = []

try:
    import pytest_factoryboy
    from pytest_factoryboy import register
    
    register(UserFactory)
    register(CategoryFactory)
    register(AccountFactory)
    register(TransactionFactory)
    register(TransferFactory)
    register(BudgetFactory)
    register(BudgetLineFactory)
    register(SavingsGoalFactory)
    register(TagFactory)
    register(RecurringTransactionFactory)
    register(AlertFactory)
    
except ImportError:
    # Si pytest-factoryboy no está instalado, las factories siguen siendo útiles
    pass