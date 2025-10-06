from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from .models import (
    Category, Account, Transaction, Transfer, Budget, BudgetLine, SavingsGoal,
    Tag, RecurringTransaction, TransactionReceipt, SharedExpense,
    SharedExpenseParticipant, Alert, UserOnboarding
)
from .serializers import (
    CategorySerializer,
    AccountSerializer,
    TransactionSerializer,
    TransferSerializer,
    BudgetSerializer,
    BudgetLineSerializer,
    SavingsGoalSerializer,
    TagSerializer,
    RecurringTransactionSerializer,
    TransactionReceiptSerializer,
    SharedExpenseSerializer,
    SharedExpenseParticipantSerializer,
    AlertSerializer,
    EnhancedTransactionSerializer,
    UserOnboardingSerializer,
    OnboardingStepSerializer
)


# ViewSet base para asegurar que los usuarios solo puedan ver y editar su propio objetos
class BaseViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        #Esta funcion sobreescribe el queryset base para que solo devuelva los objetos que pertenecen al usuario autenticado
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        #Esta funcion sobreescribe el metodo perform_create para que el usuario autenticado sea el dueño del objeto
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        #Esta funcion sobreescribe el metodo perform_update para evitar que se actualice el campo user
        serializer.save()

# ----- ViewSets para cada modelo -----
# Heredan la logica de BaseViewSet y solo especifican el queryset y serializer

class CategoryViewSet(BaseViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class AccountViewSet(BaseViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class TransactionViewSet(BaseViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransferViewSet(BaseViewSet):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer


class AccountViewSetExtended(AccountViewSet):
    """ViewSet extendido para cuentas con endpoints adicionales"""
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Obtiene estadísticas para el dashboard"""
        user = request.user
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Balance total por tipo de cuenta
        accounts = Account.objects.filter(user=user)
        
        # Patrimonio neto (activos - deudas)
        cash_accounts = accounts.filter(type='cash').aggregate(total=Sum('balance'))['total'] or 0
        bank_accounts = accounts.filter(type='bank').aggregate(total=Sum('balance'))['total'] or 0
        credit_debt = accounts.filter(type='credit').aggregate(total=Sum('balance'))['total'] or 0
        
        net_worth = cash_accounts + bank_accounts - credit_debt
        
        # Transacciones del mes actual
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_income = Transaction.objects.filter(
            user=user,
            transaction_type='income',
            date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_expenses = Transaction.objects.filter(
            user=user,
            transaction_type='expense',
            date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Gastos por categoría (últimos 30 días)
        expenses_by_category = Transaction.objects.filter(
            user=user,
            transaction_type='expense',
            date__gte=thirty_days_ago
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')[:5]
        
        # Tarjetas de crédito
        credit_cards = accounts.filter(type='credit')
        total_credit_limit = credit_cards.aggregate(total=Sum('credit_limit'))['total'] or 0
        total_credit_used = credit_cards.aggregate(total=Sum('balance'))['total'] or 0
        total_credit_available = total_credit_limit - total_credit_used if total_credit_limit > 0 else 0
        credit_utilization = (total_credit_used / total_credit_limit * 100) if total_credit_limit > 0 else 0
        
        # Transacciones recientes
        recent_transactions = Transaction.objects.filter(
            user=user
        ).select_related('account', 'category').order_by('-date')[:5]
        
        recent_transactions_data = [{
            'id': t.id,
            'date': t.date,
            'description': t.description,
            'amount': t.amount,
            'type': t.transaction_type,
            'account': t.account.name,
            'category': t.category.name if t.category else None
        } for t in recent_transactions]
        
        return Response({
            'net_worth': net_worth,
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'monthly_balance': monthly_income - monthly_expenses,
            'accounts_summary': {
                'cash': cash_accounts,
                'bank': bank_accounts,
                'credit_debt': credit_debt,
                'total_accounts': accounts.count()
            },
            'credit_cards_summary': {
                'total_limit': total_credit_limit,
                'total_used': total_credit_used,
                'total_available': total_credit_available,
                'utilization_percentage': round(credit_utilization, 2)
            },
            'expenses_by_category': list(expenses_by_category),
            'recent_transactions': recent_transactions_data
        })
    
    @action(detail=False, methods=['get'])
    def monthly_trends(self, request):
        """Obtiene tendencias mensuales para gráficos"""
        user = request.user
        
        # Obtener últimos 6 meses
        end_date = timezone.now()
        start_date = end_date - timedelta(days=180)
        
        # Agrupar por mes
        monthly_data = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            next_month = (current_date + timedelta(days=32)).replace(day=1)
            
            income = Transaction.objects.filter(
                user=user,
                transaction_type='income',
                date__gte=current_date,
                date__lt=next_month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            expenses = Transaction.objects.filter(
                user=user,
                transaction_type='expense',
                date__gte=current_date,
                date__lt=next_month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_data.append({
                'month': current_date.strftime('%B %Y'),
                'income': income,
                'expenses': expenses,
                'balance': income - expenses
            })
            
            current_date = next_month
        
        return Response({
            'monthly_trends': monthly_data
        })


class BudgetViewSet(BaseViewSet):
    """ViewSet para presupuestos"""
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    
    def get_queryset(self):
        # Filtrar por usuario y estado activo por defecto
        queryset = super().get_queryset()
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        else:
            queryset = queryset.filter(status='active')
        return queryset.prefetch_related('lines', 'lines__category')
    
    @action(detail=True, methods=['post'])
    def add_line(self, request, pk=None):
        """Agrega una línea de presupuesto.

        Si ya existe una línea para la misma categoría, la actualiza.
        Si no, crea una nueva.
        """
        budget = self.get_object()
        category_id = request.data.get('category')

        # --- DEBUG: Imprimir datos recibidos ---
        print(f"[DEBUG] add_line request data: {request.data}")
        # ----------------------------------------


        # El serializador ahora requiere 'category', por lo que no es necesario
        # verificar si category_id es nulo aquí. Si lo es, el serializador fallará.

        try:
            instance = budget.lines.get(category_id=category_id)
            serializer = BudgetLineSerializer(instance, data=request.data, partial=True)
        except BudgetLine.DoesNotExist:
            serializer = BudgetLineSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            line = serializer.save(budget=budget)
            # Re-serializar para obtener campos de solo lectura como category_name
            response_serializer = BudgetLineSerializer(line)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Obtiene el resumen del presupuesto actual"""
        budget = self.get_object()
        start, end = budget.get_current_period_window()
        
        lines_summary = []
        for line in budget.lines.all():
            spent = line.get_spent_amount(start, end)
            lines_summary.append({
                'category': line.category.name if line.category else 'General',
                'budgeted': line.amount,
                'spent': spent,
                'remaining': line.amount - spent,
                'percentage': (spent / line.amount * 100) if line.amount > 0 else 0
            })
        
        total_budget = budget.get_budget_limit()
        total_spent = budget.get_spent_amount(start, end)
        
        return Response({
            'budget_name': budget.name,
            'period': {
                'type': budget.get_period_type_display(),
                'start': start.isoformat(),
                'end': end.isoformat()
            },
            'lines': lines_summary,
            'totals': {
                'budget': total_budget,
                'spent': total_spent,
                'remaining': total_budget - total_spent,
                'percentage': (total_spent / total_budget * 100) if total_budget > 0 else 0
            }
        })
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archiva un presupuesto"""
        budget = self.get_object()
        budget.status = 'archived'
        budget.save()
        return Response({'status': 'Budget archived'})

    @action(detail=True, methods=['post'], url_path='lines/(?P<line_pk>[^/.]+)/delete')
    def delete_line(self, request, pk=None, line_pk=None):
        """Elimina una línea de presupuesto"""
        budget = self.get_object()
        try:
            line = budget.lines.get(pk=line_pk)
            line.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BudgetLine.DoesNotExist:
            return Response({'error': 'Línea de presupuesto no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SavingsGoalViewSet(BaseViewSet):
    """ViewSet para metas de ahorro"""
    queryset = SavingsGoal.objects.all()
    serializer_class = SavingsGoalSerializer
    
    def get_queryset(self):
        # Filtrar por usuario y estado activo por defecto
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        else:
            queryset = queryset.filter(is_active=True)
        return queryset.select_related('linked_account')
    
    @action(detail=True, methods=['post'])
    def contribute(self, request, pk=None):
        """Registra una contribución hacia la meta de ahorro"""
        goal = self.get_object()
        
        # Debug: Ver qué datos está enviando el frontend
        print(f"DEBUG - Request data: {request.data}")
        print(f"DEBUG - Request keys: {list(request.data.keys())}")
        
        # Validar y convertir amount
        try:
            amount = Decimal(str(request.data.get('amount', 0)))
            if amount <= 0:
                return Response({'error': 'Amount must be greater than 0'}, status=400)
        except (ValueError, TypeError, InvalidOperation):
            return Response({'error': 'Invalid amount format'}, status=400)
            
        description = request.data.get('description', f'Contribución a {goal.name}')
        account_id = request.data.get('account_id')
        
        # También verificar si viene como accountId (camelCase)
        if not account_id:
            account_id = request.data.get('accountId')
        
        if not account_id:
            # Si no se proporciona account_id, intentar usar la primera cuenta del usuario
            # que no sea de crédito y tenga saldo suficiente
            user_accounts = Account.objects.filter(
                user=request.user
            ).exclude(type='credit').order_by('-balance')
            
            if user_accounts.exists() and amount > 0:
                # Buscar una cuenta con saldo suficiente
                for acc in user_accounts:
                    if acc.balance >= amount:
                        account_id = acc.id
                        print(f"DEBUG - Auto-selected account: {acc.name} (ID: {acc.id})")
                        break
                
                if not account_id:
                    return Response({
                        'error': 'No account with sufficient balance found',
                        'received_data': dict(request.data),
                        'note': 'Please select an account or ensure you have sufficient balance'
                    }, status=400)
            else:
                return Response({
                    'error': 'account_id is required or no accounts available',
                    'received_data': dict(request.data),
                    'expected_format': {
                        'amount': 'number (required)',
                        'account_id': 'number (required)',
                        'description': 'string (optional)'
                    }
                }, status=400)
        
        try:
            # Si hay cuenta vinculada, crear transferencia
            if goal.linked_account:
                from_account = Account.objects.get(id=account_id, user=request.user)
                transfer = Transfer.objects.create(
                    user=request.user,
                    from_account=from_account,
                    to_account=goal.linked_account,
                    amount=amount,
                    description=description,
                    date=timezone.now().date()
                )
                from_account.balance -= amount
                from_account.save()
                goal.linked_account.balance += amount
                goal.linked_account.save()
            else:
                # Si no hay cuenta vinculada, crear transacción de ahorro
                account = Account.objects.get(id=account_id, user=request.user)
                savings_category, created = Category.objects.get_or_create(
                    user=request.user,
                    name='Ahorro',
                    defaults={'type': 'expense', 'color': '#00ff00'}
                )
                transaction = Transaction.objects.create(
                    user=request.user,
                    account=account,
                    category=savings_category,
                    transaction_type='expense',
                    amount=amount,
                    description=f'{goal.name}: {description}',
                    date=timezone.now().date()
                )
                account.balance -= amount
                account.save()
                
            return Response({
                'message': 'Contribution registered successfully',
                'new_saved_amount': goal.get_saved_amount(),
                'progress_percentage': goal.get_progress_percentage()
            })
            
        except Account.DoesNotExist:
            return Response({'error': 'Account not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Obtiene un resumen de todas las metas de ahorro activas"""
        goals = self.get_queryset()
        
        total_target = goals.aggregate(total=Sum('target_amount'))['total'] or 0
        total_saved = sum(goal.get_saved_amount() for goal in goals)
        
        goals_summary = []
        for goal in goals:
            goals_summary.append({
                'id': goal.id,
                'name': goal.name,
                'target_amount': goal.target_amount,
                'saved_amount': goal.get_saved_amount(),
                'progress_percentage': goal.get_progress_percentage(),
                'is_on_track': goal.is_on_track(),
                'target_date': goal.target_date.isoformat(),
                'days_remaining': (goal.target_date - timezone.now().date()).days
            })
        
        return Response({
            'total_goals': goals.count(),
            'total_target_amount': total_target,
            'total_saved_amount': total_saved,
            'overall_progress_percentage': (total_saved / total_target * 100) if total_target > 0 else 0,
            'goals': goals_summary
        })


# NUEVAS VISTAS PARA FUNCIONALIDADES AGREGADAS

class TagViewSet(BaseViewSet):
    """ViewSet para etiquetas"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Obtiene las etiquetas más usadas"""
        tags = self.get_queryset().annotate(
            usage_count=Count('transactions')
        ).order_by('-usage_count')[:10]
        
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)


class RecurringTransactionViewSet(BaseViewSet):
    """ViewSet para transacciones recurrentes"""
    queryset = RecurringTransaction.objects.all()
    serializer_class = RecurringTransactionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrar solo activas por defecto
        if self.request.query_params.get('all') != 'true':
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('next_date')
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Ejecuta manualmente una transacción recurrente"""
        recurring = self.get_object()
        
        try:
            transaction = recurring.create_transaction()
            serializer = TransactionSerializer(transaction)
            return Response({
                'message': 'Transaction created successfully',
                'transaction': serializer.data,
                'next_date': recurring.next_date.isoformat()
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pausa una transacción recurrente"""
        recurring = self.get_object()
        recurring.is_active = False
        recurring.save()
        return Response({'message': 'Recurring transaction paused'})
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Reanuda una transacción recurrente"""
        recurring = self.get_object()
        recurring.is_active = True
        recurring.save()
        return Response({'message': 'Recurring transaction resumed'})
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Obtiene las transacciones recurrentes próximas"""
        days = int(request.query_params.get('days', 7))
        cutoff_date = timezone.now().date() + timedelta(days=days)
        
        upcoming = self.get_queryset().filter(
            next_date__lte=cutoff_date,
            is_active=True
        )
        
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


class TransactionReceiptViewSet(viewsets.ModelViewSet):
    """ViewSet para recibos de transacciones"""
    queryset = TransactionReceipt.objects.all()
    serializer_class = TransactionReceiptSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtrar solo recibos de transacciones del usuario
        queryset = self.queryset.filter(transaction__user=self.request.user)
        
        # Filtro opcional por transacción
        transaction_id = self.request.query_params.get('transaction')
        if transaction_id:
            queryset = queryset.filter(transaction_id=transaction_id)
            
        return queryset.order_by('-uploaded_at')
    
    def create(self, request):
        """Sube uno o múltiples recibos para una transacción"""
        transaction_id = request.data.get('transaction')
        
        try:
            transaction = Transaction.objects.get(
                id=transaction_id,
                user=request.user
            )
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=404)
        
        files = request.FILES.getlist('files')
        if not files:
            # Intentar con un solo archivo
            file = request.FILES.get('file')
            if file:
                files = [file]
            else:
                return Response({'error': 'No files provided'}, status=400)
        
        # Validar tipos de archivo permitidos
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'application/pdf']
        receipts = []
        
        for file in files:
            if file.content_type not in allowed_types:
                return Response({
                    'error': f'Invalid file type: {file.content_type}. Allowed types: {", ".join(allowed_types)}'
                }, status=400)
            
            # Validar tamaño (max 5MB)
            if file.size > 5 * 1024 * 1024:
                return Response({'error': f'File {file.name} is too large. Max size is 5MB'}, status=400)
        
        # Crear recibos
        for file in files:
            receipt = TransactionReceipt.objects.create(
                transaction=transaction,
                file=file,
                file_name=file.name,
                file_type=file.content_type
            )
            receipts.append(receipt)
        
        serializer = self.get_serializer(receipts, many=True)
        return Response({
            'message': f'Successfully uploaded {len(receipts)} receipt(s)',
            'receipts': serializer.data
        }, status=201)
    
    @action(detail=False, methods=['get'])
    def by_transaction(self, request):
        """Obtiene todos los recibos de una transacción específica"""
        transaction_id = request.query_params.get('transaction_id')
        if not transaction_id:
            return Response({'error': 'transaction_id parameter is required'}, status=400)
        
        receipts = self.get_queryset().filter(transaction_id=transaction_id)
        serializer = self.get_serializer(receipts, many=True)
        return Response(serializer.data)


class SharedExpenseViewSet(BaseViewSet):
    """ViewSet para gastos compartidos"""
    queryset = SharedExpense.objects.all()
    serializer_class = SharedExpenseSerializer
    
    def get_queryset(self):
        queryset = SharedExpense.objects.filter(
            Q(created_by=self.request.user) |
            Q(participants__email=self.request.user.email)
        ).distinct()
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-created_at')
    
    def create(self, request):
        """Crea un gasto compartido con participantes"""
        transaction_id = request.data.get('transaction_id')
        participants_data = request.data.get('participants', [])
        
        # Validar transacción
        try:
            transaction = Transaction.objects.get(id=transaction_id, user=request.user)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=404)
        
        # Crear gasto compartido
        shared_expense = SharedExpense.objects.create(
            transaction=transaction,
            created_by=request.user,
            description=request.data.get('description', transaction.description),
            total_amount=transaction.amount
        )
        
        # Agregar participantes
        total_participants = len(participants_data) + 1  # +1 por el creador
        default_amount = transaction.amount / total_participants
        
        # Agregar al creador como participante
        SharedExpenseParticipant.objects.create(
            shared_expense=shared_expense,
            email=request.user.email,
            name=request.user.username,
            amount_owed=default_amount,
            amount_paid=default_amount,  # El creador ya pagó su parte
            is_paid=True
        )
        
        # Agregar otros participantes
        for participant_data in participants_data:
            SharedExpenseParticipant.objects.create(
                shared_expense=shared_expense,
                email=participant_data['email'],
                name=participant_data.get('name', participant_data['email']),
                amount_owed=participant_data.get('amount_owed', default_amount)
            )
        
        serializer = self.get_serializer(shared_expense)
        return Response(serializer.data, status=201)
    
    @action(detail=True, methods=['post'])
    def add_participants(self, request, pk=None):
        """Agrega participantes a un gasto compartido"""
        shared_expense = self.get_object()
        participants = request.data.get('participants', [])
        
        if not participants:
            return Response({'error': 'No participants provided'}, status=400)
        
        created = []
        for p in participants:
            participant, was_created = SharedExpenseParticipant.objects.get_or_create(
                shared_expense=shared_expense,
                email=p['email'],
                defaults={
                    'name': p.get('name', p['email']),
                    'amount_owed': p.get('amount_owed', shared_expense.total_amount / (len(participants) + 1))
                }
            )
            if was_created:
                created.append(participant)
        
        serializer = SharedExpenseParticipantSerializer(created, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Marca un participante como pagado"""
        shared_expense = self.get_object()
        participant_email = request.data.get('email')
        amount = request.data.get('amount')
        
        try:
            participant = shared_expense.participants.get(email=participant_email)
            participant.amount_paid = amount or participant.amount_owed
            participant.is_paid = participant.amount_paid >= participant.amount_owed
            if participant.is_paid:
                participant.paid_date = timezone.now()
            participant.save()
            
            # Actualizar estado del gasto compartido
            total_paid = shared_expense.participants.aggregate(
                total=Sum('amount_paid')
            )['total'] or 0
            
            if total_paid >= shared_expense.total_amount:
                shared_expense.status = 'paid'
            elif total_paid > 0:
                shared_expense.status = 'partially_paid'
            
            shared_expense.save()
            
            return Response({
                'message': 'Payment recorded successfully',
                'participant': SharedExpenseParticipantSerializer(participant).data,
                'expense_status': shared_expense.status
            })
            
        except SharedExpenseParticipant.DoesNotExist:
            return Response({'error': 'Participant not found'}, status=404)
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Calcula el balance de quién debe a quién"""
        shared_expense = self.get_object()
        participants = shared_expense.participants.all()
        
        balances = []
        for participant in participants:
            balance = participant.amount_owed - participant.amount_paid
            balances.append({
                'email': participant.email,
                'name': participant.name,
                'amount_owed': participant.amount_owed,
                'amount_paid': participant.amount_paid,
                'balance': balance,
                'owes' if balance > 0 else 'is_owed': abs(balance),
                'is_paid': participant.is_paid
            })
        
        return Response({
            'shared_expense_id': shared_expense.id,
            'total_amount': shared_expense.total_amount,
            'status': shared_expense.status,
            'balances': balances
        })
    
    @action(detail=False, methods=['get'])
    def my_balance(self, request):
        """Obtiene el balance total del usuario en todos los gastos compartidos"""
        user_email = request.user.email
        
        # Gastos donde el usuario participa
        participant_entries = SharedExpenseParticipant.objects.filter(
            email=user_email,
            shared_expense__status__in=['pending', 'partially_paid']
        )
        
        total_owed = 0
        total_to_receive = 0
        details = []
        
        for entry in participant_entries:
            balance = entry.amount_owed - entry.amount_paid
            if balance > 0:
                total_owed += balance
                details.append({
                    'expense': entry.shared_expense.description,
                    'amount': balance,
                    'type': 'owe',
                    'to': entry.shared_expense.created_by.username
                })
        
        # Gastos creados por el usuario donde otros deben
        created_expenses = SharedExpense.objects.filter(
            created_by=request.user,
            status__in=['pending', 'partially_paid']
        )
        
        for expense in created_expenses:
            participants = expense.participants.exclude(email=user_email)
            for participant in participants:
                balance = participant.amount_owed - participant.amount_paid
                if balance > 0:
                    total_to_receive += balance
                    details.append({
                        'expense': expense.description,
                        'amount': balance,
                        'type': 'receive',
                        'from': participant.name
                    })
        
        return Response({
            'total_owed': total_owed,
            'total_to_receive': total_to_receive,
            'net_balance': total_to_receive - total_owed,
            'details': details
        })


class AlertViewSet(BaseViewSet):
    """ViewSet para alertas"""
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('active_only', 'true').lower() == 'true':
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('alert_type', '-created_at')
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Activa/desactiva una alerta"""
        alert = self.get_object()
        alert.is_active = not alert.is_active
        alert.save()
        return Response({
            'message': f'Alert {"activated" if alert.is_active else "deactivated"}',
            'is_active': alert.is_active
        })
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """Verifica y retorna alertas activas que necesitan ser disparadas"""
        triggered_alerts = []
        alerts = self.get_queryset().filter(is_active=True)
        
        for alert in alerts:
            if self._should_trigger(alert):
                triggered_alerts.append({
                    'alert': AlertSerializer(alert).data,
                    'message': self._get_alert_message(alert)
                })
        
        return Response(triggered_alerts)
    
    def _should_trigger(self, alert):
        """Determina si una alerta debe ser disparada"""
        today = timezone.now().date()
        
        if alert.alert_type == 'budget_exceeded':
            if alert.budget:
                spent = alert.budget.get_spent_amount()
                limit = alert.budget.get_budget_limit()
                return spent > limit
                
        elif alert.alert_type == 'budget_warning':
            if alert.budget and alert.threshold_percentage:
                spent = alert.budget.get_spent_amount()
                limit = alert.budget.get_budget_limit()
                if limit > 0:
                    percentage = (spent / limit) * 100
                    return percentage >= alert.threshold_percentage
                    
        elif alert.alert_type == 'low_balance':
            if alert.account and alert.threshold_amount:
                return alert.account.balance < alert.threshold_amount
                
        elif alert.alert_type == 'payment_due':
            if alert.account and alert.account.type == 'credit' and alert.days_before:
                payment_date = alert.account.get_next_payment_date()
                if payment_date:
                    days_until = (payment_date - today).days
                    return 0 <= days_until <= alert.days_before
                    
        elif alert.alert_type == 'goal_milestone':
            # Por implementar cuando se defina la lógica de hitos
            pass
            
        elif alert.alert_type == 'recurring_due':
            if alert.days_before:
                # Verificar transacciones recurrentes próximas
                upcoming = RecurringTransaction.objects.filter(
                    user=alert.user,
                    is_active=True,
                    next_date__lte=today + timedelta(days=alert.days_before),
                    next_date__gte=today
                ).exists()
                return upcoming
                
        return False
    
    def _get_alert_message(self, alert):
        """Genera un mensaje descriptivo para la alerta"""
        if alert.alert_type == 'budget_exceeded':
            return f"El presupuesto {alert.budget.name} ha sido excedido"
            
        elif alert.alert_type == 'budget_warning':
            return f"Has alcanzado el {alert.threshold_percentage}% del presupuesto {alert.budget.name}"
            
        elif alert.alert_type == 'low_balance':
            return f"La cuenta {alert.account.name} tiene un saldo bajo: {alert.account.balance}"
            
        elif alert.alert_type == 'payment_due':
            payment_date = alert.account.get_next_payment_date()
            return f"Pago de {alert.account.name} vence el {payment_date}"
            
        elif alert.alert_type == 'recurring_due':
            return f"Tienes transacciones recurrentes próximas en los siguientes {alert.days_before} días"
            


# Actualizar TransactionViewSet para usar EnhancedTransactionSerializer
class EnhancedTransactionViewSet(TransactionViewSet):
    """ViewSet mejorado para transacciones con soporte de tags y más"""
    serializer_class = EnhancedTransactionSerializer
    
    @action(detail=False, methods=['get'])
    def by_tag(self, request):
        """Filtra transacciones por etiqueta"""
        tag_name = request.query_params.get('tag')
        if not tag_name:
            return Response({'error': 'Tag parameter is required'}, status=400)
        
        transactions = self.get_queryset().filter(tags__name=tag_name)
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def split(self, request, pk=None):
        """Convierte una transacción en un gasto compartido"""
        transaction = self.get_object()
        
        # Verificar si ya es compartida
        if hasattr(transaction, 'shared_expense'):
            return Response({'error': 'Transaction is already shared'}, status=400)
        
        participants = request.data.get('participants', [])
        description = request.data.get('description', transaction.description)
        
        shared_expense = SharedExpense.objects.create(
            transaction=transaction,
            created_by=request.user,
            description=description,
            total_amount=transaction.amount
        )
        
        # Agregar participantes
        for p in participants:
            SharedExpenseParticipant.objects.create(
                shared_expense=shared_expense,
                email=p['email'],
                name=p.get('name', p['email']),
                amount_owed=p.get('amount_owed', transaction.amount / len(participants))
            )
        
        serializer = SharedExpenseSerializer(shared_expense)
        return Response(serializer.data)


class OnboardingViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar el tutorial de onboarding"""
    serializer_class = UserOnboardingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Solo el onboarding del usuario autenticado"""
        return UserOnboarding.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Obtener o crear el onboarding del usuario"""
        try:
            return UserOnboarding.objects.get(user=self.request.user)
        except UserOnboarding.DoesNotExist:
            return UserOnboarding.objects.create(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Obtener el estado actual del tutorial"""
        try:
            onboarding = UserOnboarding.objects.get(user=request.user)
            serializer = self.get_serializer(onboarding)
            return Response(serializer.data)
        except UserOnboarding.DoesNotExist:
            # Crear nuevo onboarding si no existe
            onboarding = UserOnboarding.objects.create(user=request.user)
            serializer = self.get_serializer(onboarding)
            return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """Iniciar el tutorial"""
        onboarding, created = UserOnboarding.objects.get_or_create(user=request.user)
        
        if not onboarding.completed and not onboarding.skipped:
            onboarding.start_tutorial()
            serializer = self.get_serializer(onboarding)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Tutorial already completed or skipped'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def advance_step(self, request):
        """Avanzar al siguiente paso del tutorial"""
        serializer = OnboardingStepSerializer(data=request.data)
        if serializer.is_valid():
            onboarding, _ = UserOnboarding.objects.get_or_create(user=request.user)
            
            step = serializer.validated_data['step']
            step_data = serializer.validated_data.get('step_data', {})
            time_spent = serializer.validated_data.get('time_spent', 0)
            
            # Validar que el paso sea el siguiente
            if step != onboarding.current_step + 1:
                return Response(
                    {'error': f'Expected step {onboarding.current_step + 1}, got {step}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Guardar tiempo del paso
            if time_spent > 0:
                if not onboarding.step_times:
                    onboarding.step_times = {}
                onboarding.step_times[str(step - 1)] = time_spent
                onboarding.save()
            
            # Avanzar paso
            onboarding.advance_step(step_data)
            
            # Crear datos iniciales según el paso
            self._create_step_data(request.user, step, step_data)
            
            response_serializer = self.get_serializer(onboarding)
            return Response(response_serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def complete(self, request):
        """Completar el tutorial"""
        onboarding, _ = UserOnboarding.objects.get_or_create(user=request.user)
        onboarding.complete_tutorial()
        
        # Crear configuración inicial completa si no se hizo en pasos previos
        self._ensure_initial_setup(request.user, onboarding.tutorial_data)
        
        serializer = self.get_serializer(onboarding)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def skip(self, request):
        """Saltar el tutorial"""
        onboarding, _ = UserOnboarding.objects.get_or_create(user=request.user)
        onboarding.skip_tutorial()
        
        # Crear configuración mínima
        self._create_minimal_setup(request.user)
        
        serializer = self.get_serializer(onboarding)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Métricas del tutorial para Tokio School"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        total_users = UserOnboarding.objects.count()
        completed = UserOnboarding.objects.filter(completed=True, skipped=False).count()
        skipped = UserOnboarding.objects.filter(skipped=True).count()
        in_progress = UserOnboarding.objects.filter(completed=False, skipped=False).count()
        
        # Calcular tiempos promedio
        completed_with_time = UserOnboarding.objects.filter(
            completed=True, 
            skipped=False,
            total_time_spent__gt=0
        )
        avg_time = completed_with_time.aggregate(
            avg_time=Sum('total_time_spent') / Count('id')
        )['avg_time'] or 0
        
        # Puntos de abandono
        abandonment_points = {}
        for step in range(1, 7):
            count = UserOnboarding.objects.filter(current_step=step, completed=False).count()
            abandonment_points[f'step_{step}'] = count
        
        analytics_data = {
            'total_users': total_users,
            'completion_rate': (completed / total_users * 100) if total_users > 0 else 0,
            'skip_rate': (skipped / total_users * 100) if total_users > 0 else 0,
            'in_progress': in_progress,
            'average_completion_time_seconds': int(avg_time),
            'abandonment_points': abandonment_points
        }
        
        return Response(analytics_data)
    
    def _create_step_data(self, user, step, step_data):
        """Crear datos específicos según el paso del tutorial"""
        if step == 3 and 'account_data' in step_data:
            # Paso 3: Crear primera cuenta
            account_data = step_data['account_data']
            Account.objects.get_or_create(
                user=user,
                name=account_data.get('name', 'Mi Cuenta Principal'),
                defaults={
                    'type': account_data.get('type', 'bank'),
                    'balance': Decimal(str(account_data.get('balance', '0.00'))),
                    'currency': account_data.get('currency', 'MXN')
                }
            )
        
        elif step == 5 and 'transaction_data' in step_data:
            # Paso 5: Crear primera transacción
            transaction_data = step_data['transaction_data']
            try:
                account = Account.objects.filter(user=user).first()
                category = Category.objects.filter(user=user).first()
                
                if account and category:
                    Transaction.objects.create(
                        user=user,
                        account=account,
                        category=category,
                        transaction_type=transaction_data.get('type', 'expense'),
                        amount=Decimal(str(transaction_data.get('amount', '100.00'))),
                        description=transaction_data.get('description', 'Mi primera transacción')
                    )
            except Exception:
                pass  # No forzar la creación si hay errores
    
    def _ensure_initial_setup(self, user, tutorial_data):
        """Asegurar que el usuario tenga configuración inicial mínima"""
        # Crear categorías predeterminadas si no existen
        self._create_default_categories(user)
        
        # Crear cuenta principal si no existe
        if not Account.objects.filter(user=user).exists():
            Account.objects.create(
                user=user,
                name="Mi Cuenta Principal",
                type='bank',
                balance=Decimal('0.00'),
                currency=tutorial_data.get('currency', 'MXN')
            )
    
    def _create_minimal_setup(self, user):
        """Crear configuración mínima cuando se salta el tutorial"""
        self._create_default_categories(user)
        
        if not Account.objects.filter(user=user).exists():
            Account.objects.create(
                user=user,
                name="Mi Cuenta",
                type='bank',
                balance=Decimal('0.00'),
                currency='MXN'
            )
    
    def _create_default_categories(self, user):
        """Crear categorías predeterminadas"""
        default_categories = [
            {'name': 'Alimentación', 'type': 'expense', 'color': '#FF6B6B'},
            {'name': 'Transporte', 'type': 'expense', 'color': '#4ECDC4'},
            {'name': 'Entretenimiento', 'type': 'expense', 'color': '#45B7D1'},
            {'name': 'Servicios', 'type': 'expense', 'color': '#F7DC6F'},
            {'name': 'Salud', 'type': 'expense', 'color': '#BB8FCE'},
            {'name': 'Salario', 'type': 'income', 'color': '#58D68D'},
            {'name': 'Freelance', 'type': 'income', 'color': '#52C41A'},
            {'name': 'Inversiones', 'type': 'income', 'color': '#1890FF'},
        ]
        
        for cat_data in default_categories:
            Category.objects.get_or_create(
                user=user,
                name=cat_data['name'],
                defaults={
                    'type': cat_data['type'],
                    'color': cat_data['color'],
                    'description': f"Categoría {cat_data['name'].lower()} creada automáticamente"
                }
            )