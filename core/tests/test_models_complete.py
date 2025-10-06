"""
Tests completos para todos los modelos del proyecto Personal Finance.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import patch

from core.models import (
    Category, Account, Transaction, Transfer, Budget, BudgetLine,
    SavingsGoal, Tag, RecurringTransaction, Alert
)

pytestmark = pytest.mark.django_db


class TestCategoryModel:
    """Tests para el modelo Category."""
    
    def test_create_category(self, user):
        """Test crear una categoría básica."""
        category = Category.objects.create(
            user=user,
            name="Comida",
            type="expense",
            description="Gastos en alimentación",
            color="#FF5733"
        )
        assert category.name == "Comida"
        assert category.type == "expense"
        assert str(category) == "Comida"
    
    def test_unique_category_per_user(self, user, user_factory):
        """Test que las categorías sean únicas por usuario."""
        Category.objects.create(user=user, name="Comida", type="expense")
        
        # Mismo usuario, mismo nombre - debe fallar
        with pytest.raises(Exception):
            Category.objects.create(user=user, name="Comida", type="income")
        
        # Diferente usuario, mismo nombre - debe funcionar
        other_user = user_factory(username="other")
        category = Category.objects.create(user=other_user, name="Comida", type="expense")
        assert category.name == "Comida"


class TestAccountModel:
    """Tests para el modelo Account."""
    
    def test_create_basic_account(self, user):
        """Test crear una cuenta básica."""
        account = Account.objects.create(
            user=user,
            name="Cuenta Principal",
            type="bank",
            balance=Decimal("10000.00"),
            currency="MXN"
        )
        assert account.name == "Cuenta Principal"
        assert account.balance == Decimal("10000.00")
        assert str(account) == "Cuenta Principal - Cuenta Bancaria"
    
    def test_credit_card_properties(self, user):
        """Test propiedades específicas de tarjetas de crédito."""
        card = Account.objects.create(
            user=user,
            name="Tarjeta Platino",
            type="credit",
            balance=Decimal("5000.00"),  # Deuda actual
            credit_limit=Decimal("20000.00"),
            closing_date=15,
            payment_date=25,
            currency="MXN"
        )
        
        # Test propiedades calculadas
        assert card.current_debt == Decimal("5000.00")
        assert card.available_credit == Decimal("15000.00")
        assert card.credit_utilization == 25.0
    
    def test_next_closing_date(self, user):
        """Test cálculo de próxima fecha de corte."""
        card = Account.objects.create(
            user=user,
            name="Tarjeta",
            type="credit",
            balance=Decimal("1000.00"),
            credit_limit=Decimal("10000.00"),
            closing_date=15,
            payment_date=25
        )
        
        # Mock today as day 10 
        with patch('datetime.date.today', return_value=date(2024, 1, 10)):
            # Estamos en día 10, el próximo corte es el 15 de enero
            assert card.get_next_closing_date() == date(2024, 1, 15)
    
    def test_next_closing_date_after_current(self, user):
        """Test próxima fecha de corte cuando ya pasó este mes."""
        card = Account.objects.create(
            user=user,
            name="Tarjeta",
            type="credit",
            balance=Decimal("1000.00"),
            credit_limit=Decimal("10000.00"),
            closing_date=15,
            payment_date=25
        )
        
        # Mock today as day 20
        with patch('datetime.date.today', return_value=date(2024, 1, 20)):
            # Estamos en día 20, el próximo corte es el 15 de febrero
            assert card.get_next_closing_date() == date(2024, 2, 15)
    
    def test_investment_account_properties(self, user):
        """Test propiedades de cuenta de inversión."""
        investment = Account.objects.create(
            user=user,
            name="Portafolio",
            type="investment",
            balance=Decimal("55000.00"),
            initial_investment=Decimal("50000.00"),
            investment_platform="GBM+",
            return_rate=Decimal("12.5"),
            currency="MXN"
        )
        
        assert investment.total_return == Decimal("5000.00")
        assert investment.return_percentage == 10.0


class TestTransactionModel:
    """Tests para el modelo Transaction."""
    
    def test_create_transaction(self, user, account_factory, category_factory):
        """Test crear una transacción básica."""
        account = account_factory(user=user)
        category = category_factory(user=user, type="expense")
        
        transaction = Transaction.objects.create(
            user=user,
            account=account,
            category=category,
            transaction_type="expense",
            amount=Decimal("500.00"),
            description="Compra en supermercado",
            date=timezone.now().date()
        )
        
        assert transaction.amount == Decimal("500.00")
        assert transaction.transaction_type == "expense"
        assert str(transaction).startswith("expense de 500.00")
    
    def test_transaction_with_tags(self, user, account_factory, category_factory, tag_factory):
        """Test transacción con etiquetas."""
        account = account_factory(user=user)
        category = category_factory(user=user, type="expense")
        tag1 = tag_factory(user=user, name="urgente")
        tag2 = tag_factory(user=user, name="mensual")
        
        transaction = Transaction.objects.create(
            user=user,
            account=account,
            category=category,
            transaction_type="expense",
            amount=Decimal("1000.00"),
            date=timezone.now().date()
        )
        transaction.tags.add(tag1, tag2)
        
        assert transaction.tags.count() == 2
        assert tag1 in transaction.tags.all()
    
    def test_transaction_ordering(self, user, account_factory, category_factory):
        """Test que las transacciones se ordenen por fecha descendente."""
        account = account_factory(user=user)
        category = category_factory(user=user, type="expense")
        
        # Crear transacciones en diferente orden
        t1 = Transaction.objects.create(
            user=user, account=account, category=category,
            transaction_type="expense", amount=100,
            date=timezone.now().date() - timedelta(days=2)
        )
        t2 = Transaction.objects.create(
            user=user, account=account, category=category,
            transaction_type="expense", amount=200,
            date=timezone.now().date()
        )
        t3 = Transaction.objects.create(
            user=user, account=account, category=category,
            transaction_type="expense", amount=300,
            date=timezone.now().date() - timedelta(days=1)
        )
        
        transactions = Transaction.objects.all()
        assert transactions[0] == t2  # Más reciente primero
        assert transactions[1] == t3
        assert transactions[2] == t1


class TestBudgetModel:
    """Tests para el modelo Budget."""
    
    def test_create_monthly_budget(self, user):
        """Test crear presupuesto mensual."""
        budget = Budget.objects.create(
            user=user,
            name="Presupuesto Mensual",
            period_type="monthly",
            start_date=date(2024, 1, 1),
            currency="MXN"
        )
        
        assert budget.name == "Presupuesto Mensual"
        assert budget.period_type == "monthly"
        assert budget.status == "active"
    
    def test_monthly_period_window(self, user):
        """Test ventana de período para presupuesto mensual."""
        budget = Budget.objects.create(
            user=user,
            name="Mensual",
            period_type="monthly",
            start_date=date(2024, 1, 1)
        )
        
        with patch('datetime.date.today', return_value=date(2024, 1, 15)):
            start, end = budget.get_current_period_window()
            assert start == date(2024, 1, 1)
            assert end == date(2024, 1, 31)
    
    def test_weekly_period_window(self, user):
        """Test ventana de período para presupuesto semanal."""
        budget = Budget.objects.create(
            user=user,
            name="Semanal",
            period_type="weekly",
            start_date=date(2024, 1, 1)
        )
        
        # Mock date - miércoles 15 enero 2024
        with patch('datetime.date.today', return_value=date(2024, 1, 15)):
            start, end = budget.get_current_period_window()
            # La semana empieza el lunes 15-01-2024
            assert start == date(2024, 1, 15)
            assert end == date(2024, 1, 21)
    
    def test_custom_budget_validation(self, user):
        """Test validación de presupuesto personalizado."""
        with pytest.raises(ValidationError):
            budget = Budget(
                user=user,
                name="Custom",
                period_type="custom",
                start_date=date(2024, 1, 1),
                end_date=None  # Falta fecha fin
            )
            budget.full_clean()
    
    def test_budget_spent_calculation(self, user, category_factory, account_factory):
        """Test cálculo de gastos en presupuesto."""
        # Crear presupuesto y categoría
        budget = Budget.objects.create(
            user=user,
            name="Test Budget",
            period_type="monthly",
            start_date=date.today().replace(day=1)
        )
        
        category = category_factory(user=user, type="expense")
        account = account_factory(user=user)
        
        # Agregar línea de presupuesto
        BudgetLine.objects.create(
            budget=budget,
            category=category,
            amount=Decimal("5000.00")
        )
        
        # Crear transacciones
        Transaction.objects.create(
            user=user,
            account=account,
            category=category,
            transaction_type="expense",
            amount=Decimal("1000.00"),
            date=date.today()
        )
        Transaction.objects.create(
            user=user,
            account=account,
            category=category,
            transaction_type="expense",
            amount=Decimal("500.00"),
            date=date.today()
        )
        
        # Verificar cálculo
        assert budget.get_spent_amount() == Decimal("1500.00")
        assert budget.get_budget_limit() == Decimal("5000.00")


class TestSavingsGoalModel:
    """Tests para el modelo SavingsGoal."""
    
    def test_create_savings_goal(self, user, account_factory):
        """Test crear meta de ahorro."""
        account = account_factory(user=user, type="bank")
        goal = SavingsGoal.objects.create(
            user=user,
            name="Vacaciones 2024",
            target_amount=Decimal("30000.00"),
            target_date=date.today() + timedelta(days=180),
            linked_account=account,
            contribution_frequency="monthly"
        )
        
        assert goal.name == "Vacaciones 2024"
        assert goal.target_amount == Decimal("30000.00")
        assert goal.is_active is True
    
    def test_savings_goal_validation(self, user):
        """Test validaciones de meta de ahorro."""
        # Monto negativo
        with pytest.raises(ValidationError):
            goal = SavingsGoal(
                user=user,
                name="Meta Inválida",
                target_amount=Decimal("-1000.00"),
                target_date=date.today() + timedelta(days=30)
            )
            goal.full_clean()
        
        # Fecha pasada
        with pytest.raises(ValidationError):
            goal = SavingsGoal(
                user=user,
                name="Meta Pasada",
                target_amount=Decimal("1000.00"),
                target_date=date.today() - timedelta(days=1)
            )
            goal.full_clean()
    
    def test_savings_goal_progress(self, user, account_factory):
        """Test cálculo de progreso en meta de ahorro."""
        with patch('datetime.date.today', return_value=date(2024, 1, 1)):
            account = account_factory(user=user, type="bank")
            goal = SavingsGoal.objects.create(
                user=user,
                name="Fondo de Emergencia",
                target_amount=Decimal("50000.00"),
                target_date=date(2024, 12, 31),
                linked_account=account
            )
            
            # Simular transferencias hacia la cuenta de ahorro
            from_account = account_factory(user=user, type="bank", name="Cuenta Principal")
            Transfer.objects.create(
                user=user,
                from_account=from_account,
                to_account=account,
                amount=Decimal("10000.00"),
                date=date(2024, 1, 15)
            )
            Transfer.objects.create(
                user=user,
                from_account=from_account,
                to_account=account,
                amount=Decimal("5000.00"),
                date=date(2024, 2, 1)
            )
            
            # Verificar cálculos
            assert goal.get_saved_amount() == Decimal("15000.00")
            assert goal.get_remaining_amount() == Decimal("35000.00")
            assert goal.get_progress_percentage() == 30.0
    
    def test_savings_goal_on_track(self, user, account_factory):
        """Test verificación si la meta va por buen camino."""
        with patch('datetime.date.today', return_value=date(2024, 1, 1)):
            goal = SavingsGoal.objects.create(
                user=user,
                name="Meta Test",
                target_amount=Decimal("12000.00"),
                target_date=date(2024, 12, 31),
                linked_account=account_factory(user=user)
            )
        
        # Avanzar 6 meses (50% del tiempo)
        with patch('datetime.date.today', return_value=date(2024, 7, 1)):
            # Sin ahorro - no va por buen camino
            assert goal.is_on_track() is False
            
            # Simular ahorro del 40% (menos del esperado 50%)
            from_account = account_factory(user=user, type="bank")
            Transfer.objects.create(
                user=user,
                from_account=from_account,
                to_account=goal.linked_account,
                amount=Decimal("4800.00"),
                date=date(2024, 6, 1)
            )
            
            # Con 40% ahorrado en 50% del tiempo (80% del esperado) - va por buen camino
            assert goal.is_on_track() is True


class TestRecurringTransactionModel:
    """Tests para el modelo RecurringTransaction."""
    
    def test_create_recurring_transaction(self, user, account_factory, category_factory):
        """Test crear transacción recurrente."""
        account = account_factory(user=user)
        category = category_factory(user=user, type="expense")
        
        recurring = RecurringTransaction.objects.create(
            user=user,
            name="Renta Mensual",
            amount=Decimal("10000.00"),
            transaction_type="expense",
            category=category,
            account=account,
            frequency="monthly",
            start_date=date.today(),
            next_date=date.today(),
            notify_before_days=3
        )
        
        assert recurring.name == "Renta Mensual"
        assert recurring.frequency == "monthly"
        assert recurring.is_active is True
    
    def test_calculate_next_date_monthly(self, user, account_factory, category_factory):
        """Test cálculo de próxima fecha mensual."""
        account = account_factory(user=user)
        category = category_factory(user=user, type="expense")
        
        recurring = RecurringTransaction.objects.create(
            user=user,
            name="Test Monthly",
            amount=100,
            transaction_type="expense",
            category=category,
            account=account,
            frequency="monthly",
            start_date=date(2024, 1, 15),
            next_date=date(2024, 1, 15)
        )
        
        next_date = recurring.calculate_next_date()
        assert next_date == date(2024, 2, 15)
    
    def test_calculate_next_date_weekly(self, user, account_factory, category_factory):
        """Test cálculo de próxima fecha semanal."""
        account = account_factory(user=user)
        category = category_factory(user=user, type="expense")
        
        recurring = RecurringTransaction.objects.create(
            user=user,
            name="Test Weekly",
            amount=100,
            transaction_type="expense",
            category=category,
            account=account,
            frequency="weekly",
            start_date=date(2024, 1, 1),
            next_date=date(2024, 1, 1)
        )
        
        next_date = recurring.calculate_next_date()
        assert next_date == date(2024, 1, 8)
    
    def test_create_transaction_from_recurring(self, user, account_factory, category_factory):
        """Test crear transacción desde plantilla recurrente."""
        account = account_factory(user=user)
        category = category_factory(user=user, type="expense")
        
        recurring = RecurringTransaction.objects.create(
            user=user,
            name="Suscripción Netflix",
            description="Pago mensual",
            amount=Decimal("200.00"),
            transaction_type="expense",
            category=category,
            account=account,
            frequency="monthly",
            start_date=date.today(),
            next_date=date.today()
        )
        
        # Crear transacción
        transaction = recurring.create_transaction()
        
        # Verificar transacción creada
        assert transaction.amount == Decimal("200.00")
        assert transaction.is_recurring is True
        assert transaction.recurring_transaction == recurring
        assert "Recurrente: Suscripción Netflix" in transaction.description
        
        # Verificar que se actualizó la próxima fecha
        recurring.refresh_from_db()
        assert recurring.next_date > date.today()


class TestAlertModel:
    """Tests para el modelo Alert."""
    
    def test_create_budget_alert(self, user, budget_factory):
        """Test crear alerta de presupuesto."""
        budget = budget_factory(user=user)
        alert = Alert.objects.create(
            user=user,
            alert_type="budget_warning",
            threshold_percentage=80,
            budget=budget
        )
        
        assert alert.alert_type == "budget_warning"
        assert alert.threshold_percentage == 80
        assert alert.is_active is True
    
    def test_create_low_balance_alert(self, user, account_factory):
        """Test crear alerta de saldo bajo."""
        account = account_factory(user=user)
        alert = Alert.objects.create(
            user=user,
            alert_type="low_balance",
            threshold_amount=Decimal("1000.00"),
            account=account
        )
        
        assert alert.alert_type == "low_balance"
        assert alert.threshold_amount == Decimal("1000.00")
    
    def test_create_payment_due_alert(self, user, account_factory):
        """Test crear alerta de pago próximo."""
        card = account_factory(user=user, type="credit")
        alert = Alert.objects.create(
            user=user,
            alert_type="payment_due",
            days_before=5,
            account=card
        )
        
        assert alert.alert_type == "payment_due"
        assert alert.days_before == 5


class TestTransferModel:
    """Tests para el modelo Transfer."""
    
    def test_create_transfer(self, user, account_factory):
        """Test crear transferencia entre cuentas."""
        from_account = account_factory(user=user, name="Cuenta Origen", balance=5000)
        to_account = account_factory(user=user, name="Cuenta Destino", balance=1000)
        
        transfer = Transfer.objects.create(
            user=user,
            from_account=from_account,
            to_account=to_account,
            amount=Decimal("1500.00"),
            description="Transferencia de ahorro",
            date=date.today()
        )
        
        assert transfer.amount == Decimal("1500.00")
        assert str(transfer) == f"Transferencia de 1500.00 de Cuenta Origen a Cuenta Destino el {date.today()}"
    
    def test_transfer_ordering(self, user, account_factory):
        """Test que las transferencias se ordenen por fecha descendente."""
        account1 = account_factory(user=user)
        account2 = account_factory(user=user)
        
        t1 = Transfer.objects.create(
            user=user,
            from_account=account1,
            to_account=account2,
            amount=100,
            date=date.today() - timedelta(days=2)
        )
        t2 = Transfer.objects.create(
            user=user,
            from_account=account1,
            to_account=account2,
            amount=200,
            date=date.today()
        )
        
        transfers = Transfer.objects.all()
        assert transfers[0] == t2  # Más reciente primero
        assert transfers[1] == t1