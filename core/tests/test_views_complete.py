"""
Tests completos para todos los ViewSets del proyecto Personal Finance.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
import json

from core.models import (
    Category, Account, Transaction, Transfer, Budget, BudgetLine,
    SavingsGoal, RecurringTransaction, Alert
)

pytestmark = pytest.mark.django_db


class TestCategoryViewSet:
    """Tests para el CategoryViewSet."""
    
    def test_list_categories(self, auth_client, category_factory):
        """Test listar categorías del usuario autenticado."""
        # Crear categorías para el usuario
        category_factory(user=auth_client.user, name="Comida")
        category_factory(user=auth_client.user, name="Transporte")
        
        # Crear categoría de otro usuario (no debe aparecer)
        other_user = category_factory._meta.model.user.field.related_model.objects.create_user(
            username="other", password="pass"
        )
        category_factory(user=other_user, name="Otra")
        
        url = reverse('category-list')
        response = auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'results' in data  # Respuesta paginada
        assert len(data['results']) == 2
        assert all(cat['name'] in ['Comida', 'Transporte'] for cat in data['results'])
    
    def test_create_category(self, auth_client):
        """Test crear categoría."""
        url = reverse('category-list')
        data = {
            'name': 'Entretenimiento',
            'type': 'expense',
            'description': 'Gastos de ocio',
            'color': '#FF5733'
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Entretenimiento'
        assert Category.objects.filter(user=auth_client.user, name='Entretenimiento').exists()
    
    def test_update_category(self, auth_client, category_factory):
        """Test actualizar categoría."""
        category = category_factory(user=auth_client.user, name="Original")
        
        url = reverse('category-detail', kwargs={'pk': category.id})
        data = {'name': 'Actualizada'}
        
        response = auth_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Actualizada'
        category.refresh_from_db()
        assert category.name == 'Actualizada'
    
    def test_delete_category(self, auth_client, category_factory):
        """Test eliminar categoría."""
        category = category_factory(user=auth_client.user)
        
        url = reverse('category-detail', kwargs={'pk': category.id})
        response = auth_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Category.objects.filter(id=category.id).exists()
    
    def test_cannot_access_other_user_category(self, auth_client, category_factory, user_factory):
        """Test que no se puede acceder a categorías de otros usuarios."""
        other_user = user_factory(username="other")
        category = category_factory(user=other_user)
        
        url = reverse('category-detail', kwargs={'pk': category.id})
        response = auth_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAccountViewSetExtended:
    """Tests para el AccountViewSet con endpoints extendidos."""
    
    def test_list_accounts(self, auth_client, account_factory):
        """Test listar cuentas."""
        account_factory(user=auth_client.user, name="Cuenta 1", type="bank")
        account_factory(user=auth_client.user, name="Cuenta 2", type="credit")
        
        url = reverse('account-list')
        response = auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['results']) == 2
    
    def test_create_credit_card(self, auth_client):
        """Test crear tarjeta de crédito con campos especiales."""
        url = reverse('account-list')
        data = {
            'name': 'Tarjeta Oro',
            'type': 'credit',
            'balance': '2500.00',
            'credit_limit': '50000.00',
            'closing_date': 15,
            'payment_date': 25,
            'currency': 'MXN'
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['credit_limit'] == '50000.00'
        assert response.data['available_credit'] == 47500.0
        assert response.data['credit_utilization'] == 5.0
    
    def test_dashboard_summary(self, auth_client, account_factory, transaction_factory):
        """Test endpoint de resumen del dashboard."""
        # Crear cuentas y transacciones
        bank = account_factory(user=auth_client.user, type="bank", balance=10000)
        credit = account_factory(user=auth_client.user, type="credit", balance=2000, credit_limit=10000)
        
        transaction_factory(user=auth_client.user, account=bank, transaction_type="income", amount=5000)
        transaction_factory(user=auth_client.user, account=bank, transaction_type="expense", amount=1000)
        
        url = reverse('account-dashboard-summary')
        response = auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert 'total_balance' in data
        assert 'total_income' in data
        assert 'total_expenses' in data
        assert 'net_balance' in data
        assert 'accounts_summary' in data
        assert 'recent_transactions' in data
    
    def test_account_trends(self, auth_client, account_factory, transaction_factory):
        """Test endpoint de tendencias por cuenta."""
        account = account_factory(user=auth_client.user, type="bank")
        
        # Crear transacciones en diferentes fechas
        for i in range(5):
            transaction_factory(
                user=auth_client.user,
                account=account,
                transaction_type="income" if i % 2 == 0 else "expense",
                amount=1000 * (i + 1),
                date=date.today() - timedelta(days=i * 7)
            )
        
        url = reverse('account-trends', kwargs={'pk': account.id})
        response = auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert 'balance_history' in data
        assert 'income_trend' in data
        assert 'expense_trend' in data


class TestTransactionViewSet:
    """Tests para el TransactionViewSet."""
    
    def test_create_transaction(self, auth_client, account_factory, category_factory):
        """Test crear transacción."""
        account = account_factory(user=auth_client.user)
        category = category_factory(user=auth_client.user, type="expense")
        
        url = reverse('transaction-list')
        data = {
            'account': account.id,
            'category': category.id,
            'transaction_type': 'expense',
            'amount': '500.00',
            'description': 'Compra de prueba',
            'date': str(date.today())
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['amount'] == '500.00'
        assert Transaction.objects.filter(user=auth_client.user).count() == 1
    
    def test_filter_transactions_by_type(self, auth_client, account_factory, category_factory, transaction_factory):
        """Test filtrar transacciones por tipo."""
        account = account_factory(user=auth_client.user)
        cat_income = category_factory(user=auth_client.user, type="income")
        cat_expense = category_factory(user=auth_client.user, type="expense")
        
        transaction_factory(user=auth_client.user, account=account, category=cat_income, transaction_type="income")
        transaction_factory(user=auth_client.user, account=account, category=cat_expense, transaction_type="expense")
        transaction_factory(user=auth_client.user, account=account, category=cat_expense, transaction_type="expense")
        
        url = reverse('transaction-list')
        response = auth_client.get(url, {'transaction_type': 'expense'})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['results']) == 2
        assert all(t['transaction_type'] == 'expense' for t in data['results'])
    
    def test_filter_transactions_by_date_range(self, auth_client, account_factory, category_factory, transaction_factory):
        """Test filtrar transacciones por rango de fecha."""
        account = account_factory(user=auth_client.user)
        category = category_factory(user=auth_client.user)
        
        # Transacciones en diferentes fechas
        transaction_factory(
            user=auth_client.user, account=account, category=category,
            date=date.today() - timedelta(days=10)
        )
        transaction_factory(
            user=auth_client.user, account=account, category=category,
            date=date.today() - timedelta(days=5)
        )
        transaction_factory(
            user=auth_client.user, account=account, category=category,
            date=date.today()
        )
        
        # Filtrar últimos 7 días
        url = reverse('transaction-list')
        response = auth_client.get(url, {
            'date_after': str(date.today() - timedelta(days=7)),
            'date_before': str(date.today())
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data['results']) == 2


class TestBudgetViewSet:
    """Tests para el BudgetViewSet."""
    
    def test_create_budget_with_lines(self, auth_client, category_factory):
        """Test crear presupuesto con líneas."""
        cat1 = category_factory(user=auth_client.user, type="expense", name="Comida")
        cat2 = category_factory(user=auth_client.user, type="expense", name="Transporte")
        
        url = reverse('budget-list')
        data = {
            'name': 'Presupuesto Mensual',
            'period_type': 'monthly',
            'start_date': str(date.today()),
            'lines': [
                {'category': cat1.id, 'amount': '5000.00'},
                {'category': cat2.id, 'amount': '2000.00'}
            ]
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        budget = Budget.objects.get(id=response.data['id'])
        assert budget.lines.count() == 2
        assert budget.get_budget_limit() == Decimal('7000.00')
    
    def test_budget_summary(self, auth_client, budget_factory, budget_line_factory, 
                           transaction_factory, account_factory, category_factory):
        """Test resumen de presupuesto."""
        # Crear presupuesto con categoría
        budget = budget_factory(user=auth_client.user, period_type="monthly")
        category = category_factory(user=auth_client.user, type="expense")
        budget_line = budget_line_factory(budget=budget, category=category, amount=5000)
        
        # Crear gastos
        account = account_factory(user=auth_client.user)
        transaction_factory(
            user=auth_client.user,
            account=account,
            category=category,
            transaction_type="expense",
            amount=2000,
            date=date.today()
        )
        
        url = reverse('budget-summary', kwargs={'pk': budget.id})
        response = auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data['total_budget'] == 5000.0
        assert data['total_spent'] == 2000.0
        assert data['remaining'] == 3000.0
        assert data['percentage_used'] == 40.0


class TestSavingsGoalViewSet:
    """Tests para el SavingsGoalViewSet."""
    
    def test_create_savings_goal(self, auth_client, account_factory):
        """Test crear meta de ahorro."""
        account = account_factory(user=auth_client.user, type="bank")
        
        url = reverse('savingsgoal-list')
        data = {
            'name': 'Viaje a Europa',
            'target_amount': '50000.00',
            'target_date': str(date.today() + timedelta(days=365)),
            'linked_account': account.id,
            'contribution_frequency': 'monthly'
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Viaje a Europa'
        assert response.data['progress_percentage'] == 0.0
    
    def test_add_contribution(self, auth_client, savings_goal_factory, account_factory):
        """Test agregar contribución a meta de ahorro."""
        linked_account = account_factory(user=auth_client.user, type="bank", name="Ahorro")
        from_account = account_factory(user=auth_client.user, type="bank", name="Principal")
        
        goal = savings_goal_factory(
            user=auth_client.user,
            linked_account=linked_account,
            target_amount=10000
        )
        
        url = reverse('savingsgoal-add-contribution', kwargs={'pk': goal.id})
        data = {
            'amount': '2000.00',
            'from_account': from_account.id
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Contribution added successfully'
        
        # Verificar que se creó la transferencia
        assert Transfer.objects.filter(
            user=auth_client.user,
            from_account=from_account,
            to_account=linked_account
        ).exists()


class TestRecurringTransactionViewSet:
    """Tests para el RecurringTransactionViewSet."""
    
    def test_create_recurring_transaction(self, auth_client, account_factory, category_factory):
        """Test crear transacción recurrente."""
        account = account_factory(user=auth_client.user)
        category = category_factory(user=auth_client.user, type="expense")
        
        url = reverse('recurringtransaction-list')
        data = {
            'name': 'Renta Mensual',
            'amount': '15000.00',
            'transaction_type': 'expense',
            'account': account.id,
            'category': category.id,
            'frequency': 'monthly',
            'start_date': str(date.today()),
            'auto_create': True,
            'notify_before_days': 5
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Renta Mensual'
        assert response.data['is_active'] is True
    
    def test_execute_recurring_transaction(self, auth_client, recurring_transaction_factory):
        """Test ejecutar transacción recurrente manualmente."""
        recurring = recurring_transaction_factory(user=auth_client.user)
        
        url = reverse('recurringtransaction-execute', kwargs={'pk': recurring.id})
        response = auth_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'transaction' in response.data
        assert response.data['message'] == 'Transaction created successfully'
        
        # Verificar que se creó la transacción
        assert Transaction.objects.filter(
            user=auth_client.user,
            recurring_transaction=recurring
        ).exists()
    
    def test_pause_resume_recurring_transaction(self, auth_client, recurring_transaction_factory):
        """Test pausar y reanudar transacción recurrente."""
        recurring = recurring_transaction_factory(user=auth_client.user, is_active=True)
        
        # Pausar
        url = reverse('recurringtransaction-pause', kwargs={'pk': recurring.id})
        response = auth_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        recurring.refresh_from_db()
        assert recurring.is_active is False
        
        # Reanudar
        url = reverse('recurringtransaction-resume', kwargs={'pk': recurring.id})
        response = auth_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        recurring.refresh_from_db()
        assert recurring.is_active is True
    
    def test_upcoming_transactions(self, auth_client, recurring_transaction_factory):
        """Test obtener transacciones recurrentes próximas."""
        # Crear varias con diferentes fechas
        recurring_transaction_factory(
            user=auth_client.user,
            next_date=date.today() + timedelta(days=2),
            is_active=True
        )
        recurring_transaction_factory(
            user=auth_client.user,
            next_date=date.today() + timedelta(days=5),
            is_active=True
        )
        recurring_transaction_factory(
            user=auth_client.user,
            next_date=date.today() + timedelta(days=10),
            is_active=True
        )
        
        url = reverse('recurringtransaction-upcoming')
        response = auth_client.get(url, {'days': 7})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Solo las de los próximos 7 días


class TestAlertViewSet:
    """Tests para el AlertViewSet."""
    
    def test_create_budget_alert(self, auth_client, budget_factory):
        """Test crear alerta de presupuesto."""
        budget = budget_factory(user=auth_client.user)
        
        url = reverse('alert-list')
        data = {
            'alert_type': 'budget_warning',
            'threshold_percentage': 80,
            'budget': budget.id
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['alert_type'] == 'budget_warning'
    
    def test_check_alerts(self, auth_client, alert_factory, account_factory):
        """Test verificar alertas activas."""
        # Crear alerta de saldo bajo
        account = account_factory(user=auth_client.user, balance=500)
        alert_factory(
            user=auth_client.user,
            alert_type='low_balance',
            threshold_amount=1000,
            account=account
        )
        
        url = reverse('alert-check')
        response = auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0  # Debe detectar el saldo bajo
    
    def test_toggle_alert(self, auth_client, alert_factory):
        """Test activar/desactivar alerta."""
        alert = alert_factory(user=auth_client.user, is_active=True)
        
        url = reverse('alert-toggle', kwargs={'pk': alert.id})
        response = auth_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        alert.refresh_from_db()
        assert alert.is_active is False


class TestTransferViewSet:
    """Tests para el TransferViewSet."""
    
    def test_create_transfer(self, auth_client, account_factory):
        """Test crear transferencia."""
        from_account = account_factory(user=auth_client.user, name="Origen", balance=5000)
        to_account = account_factory(user=auth_client.user, name="Destino", balance=1000)
        
        url = reverse('transfer-list')
        data = {
            'from_account': from_account.id,
            'to_account': to_account.id,
            'amount': '1500.00',
            'description': 'Transferencia de prueba',
            'date': str(date.today())
        }
        
        response = auth_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['amount'] == '1500.00'
        
        # Verificar que se actualizaron los saldos (si hay lógica implementada)
        # Esto dependería de si hay signals o lógica en el serializer
    
    def test_cannot_transfer_between_different_users(self, auth_client, account_factory, user_factory):
        """Test que no se puede transferir a cuentas de otros usuarios."""
        from_account = account_factory(user=auth_client.user)
        other_user = user_factory(username="other")
        to_account = account_factory(user=other_user)
        
        url = reverse('transfer-list')
        data = {
            'from_account': from_account.id,
            'to_account': to_account.id,
            'amount': '1000.00',
            'date': str(date.today())
        }
        
        response = auth_client.post(url, data, format='json')
        
        # Debería fallar porque la cuenta destino es de otro usuario
        assert response.status_code == status.HTTP_400_BAD_REQUEST