from rest_framework import serializers
from django.db import models
from .models import (
    Category, Account, Transaction, Transfer, Budget, BudgetLine, SavingsGoal,
    Tag, RecurringTransaction, TransactionReceipt, SharedExpense, 
    SharedExpenseParticipant, Alert, UserOnboarding
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta: 
        model = Category
        #Aqui le decimos que el campo user no se pide en la creacion de una categoria, ya que se obtiene del usuario autenticado
        #y que el campo id sirve para referenciar la categoria
        fields = ['id', 'name', 'type', 'description', 'color']
        read_only_fields = ['user']

class AccountSerializer(serializers.ModelSerializer):
    # Campos calculados para tarjetas de crédito
    current_debt = serializers.ReadOnlyField()
    available_credit = serializers.ReadOnlyField()
    credit_utilization = serializers.ReadOnlyField()
    next_closing_date = serializers.SerializerMethodField()
    next_payment_date = serializers.SerializerMethodField()
    # Campos calculados para cuentas de inversión
    total_return = serializers.ReadOnlyField()
    return_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Account
        fields = [
            'id', 'name', 'type', 'balance', 'currency', 'is_virtual',
            # Campos para tarjetas de crédito
            'credit_limit', 'closing_date', 'payment_date',
            'current_debt', 'available_credit', 'credit_utilization',
            'next_closing_date', 'next_payment_date',
            # Campos para cuentas de inversión
            'investment_platform', 'return_rate', 'initial_investment',
            'total_return', 'return_percentage'
        ]
        read_only_fields = ['user']
    
    def get_next_closing_date(self, obj):
        """Obtiene la próxima fecha de corte en formato ISO"""
        date = obj.get_next_closing_date()
        return date.isoformat() if date else None
    
    def get_next_payment_date(self, obj):
        """Obtiene la próxima fecha de pago en formato ISO"""
        date = obj.get_next_payment_date()
        return date.isoformat() if date else None

class TransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'account_name', 'category', 'category_name', 
            'transaction_type', 'amount', 'description', 'date'
        ]
        read_only_fields = ['user', 'account_name', 'category_name']

class TransferSerializer(serializers.ModelSerializer):
    from_account_name = serializers.CharField(source='from_account.name', read_only=True)
    to_account_name = serializers.CharField(source='to_account.name', read_only=True)
    
    class Meta:
        model = Transfer
        fields = ['id', 'from_account', 'from_account_name', 'to_account', 
                 'to_account_name', 'amount', 'description', 'date']
        read_only_fields = ['user', 'from_account_name', 'to_account_name']
    
    def validate(self, data):
        """Validaciones personalizadas para transferencias"""
        from_account = data.get('from_account')
        to_account = data.get('to_account')
        amount = data.get('amount')
        
        # Validar que las cuentas pertenezcan al usuario
        user = self.context['request'].user
        if from_account and from_account.user != user:
            raise serializers.ValidationError("La cuenta origen no te pertenece")
        if to_account and to_account.user != user:
            raise serializers.ValidationError("La cuenta destino no te pertenece")
        
        # Validar que no sean la misma cuenta
        if from_account == to_account:
            raise serializers.ValidationError("No puedes transferir a la misma cuenta")
        
        # Validar balance suficiente
        if from_account and amount:
            if from_account.balance < amount:
                raise serializers.ValidationError(
                    f"Balance insuficiente. Balance disponible: {from_account.balance}"
                )
        
        return data
    
    def create(self, validated_data):
        """Crear transferencia y actualizar balances"""
        transfer = super().create(validated_data)
        
        # Actualizar balances
        from_account = transfer.from_account
        to_account = transfer.to_account
        amount = transfer.amount
        
        from_account.balance -= amount
        from_account.save()
        
        to_account.balance += amount
        to_account.save()
        
        return transfer


class BudgetLineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    # Aseguramos que la categoría no pueda ser nula en la creación/actualización.
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        allow_null=False
    )

    class Meta:
        model = BudgetLine
        fields = ['id', 'category', 'category_name', 'amount', 'notes']


class BudgetSerializer(serializers.ModelSerializer):
    lines = BudgetLineSerializer(many=True, read_only=True, source='lines.all')
    total_budget = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    total_remaining = serializers.SerializerMethodField()
    current_period = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'period_type', 'start_date', 'end_date',
            'week_start', 'align_credit_cycle', 'credit_account',
            'rollover', 'currency', 'status', 'lines',
            'total_budget', 'total_spent', 'total_remaining', 'current_period',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_total_budget(self, obj):
        return obj.get_budget_limit()
    
    def get_total_spent(self, obj):
        return obj.get_spent_amount()
    
    def get_total_remaining(self, obj):
        return obj.get_budget_limit() - obj.get_spent_amount()
    
    def get_current_period(self, obj):
        start, end = obj.get_current_period_window()
        return {
            'start': start.isoformat() if start else None,
            'end': end.isoformat() if end else None
        }


class SavingsGoalSerializer(serializers.ModelSerializer):
    saved_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    is_on_track = serializers.SerializerMethodField()
    account_name = serializers.CharField(source='linked_account.name', read_only=True)
    
    class Meta:
        model = SavingsGoal
        fields = [
            'id', 'name', 'target_amount', 'target_date', 'currency',
            'linked_account', 'account_name', 'contribution_frequency',
            'auto_rollover', 'is_active', 'saved_amount', 'remaining_amount',
            'progress_percentage', 'is_on_track', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_saved_amount(self, obj):
        return obj.get_saved_amount()
    
    def get_remaining_amount(self, obj):
        return obj.get_remaining_amount()
    
    def get_progress_percentage(self, obj):
        return round(obj.get_progress_percentage(), 2)
    
    def get_is_on_track(self, obj):
        return obj.is_on_track()


# NUEVOS SERIALIZADORES

class TagSerializer(serializers.ModelSerializer):
    transaction_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'transaction_count', 'created_at']
        read_only_fields = ['user', 'created_at']
    
    def get_transaction_count(self, obj):
        return obj.transactions.count()
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RecurringTransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    next_occurrence = serializers.DateField(source='next_date', read_only=True)
    
    class Meta:
        model = RecurringTransaction
        fields = [
            'id', 'name', 'description', 'amount', 'transaction_type',
            'category', 'category_name', 'account', 'account_name',
            'frequency', 'start_date', 'end_date', 'next_date',
            'next_occurrence', 'is_active', 'auto_create',
            'notify_before_days', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'next_date']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        if 'next_date' not in validated_data:
            validated_data['next_date'] = validated_data['start_date']
        return super().create(validated_data)


class TransactionReceiptSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TransactionReceipt
        fields = [
            'id', 'transaction', 'file', 'file_url', 'file_name',
            'file_type', 'uploaded_at', 'ocr_text', 'ocr_amount',
            'ocr_date', 'ocr_processed'
        ]
        read_only_fields = ['uploaded_at', 'file_name', 'file_type']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class SharedExpenseParticipantSerializer(serializers.ModelSerializer):
    amount_pending = serializers.SerializerMethodField()
    
    class Meta:
        model = SharedExpenseParticipant
        fields = [
            'id', 'email', 'name', 'amount_owed', 'amount_paid',
            'amount_pending', 'is_paid', 'paid_date'
        ]
    
    def get_amount_pending(self, obj):
        return obj.amount_owed - obj.amount_paid


class SharedExpenseSerializer(serializers.ModelSerializer):
    participants = SharedExpenseParticipantSerializer(many=True, read_only=True)
    transaction_details = TransactionSerializer(source='transaction', read_only=True)
    total_paid = serializers.SerializerMethodField()
    total_pending = serializers.SerializerMethodField()
    
    class Meta:
        model = SharedExpense
        fields = [
            'id', 'transaction', 'transaction_details', 'created_by',
            'description', 'total_amount', 'status', 'participants',
            'total_paid', 'total_pending', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_total_paid(self, obj):
        return obj.participants.aggregate(
            total=models.Sum('amount_paid')
        )['total'] or 0
    
    def get_total_pending(self, obj):
        return obj.total_amount - self.get_total_paid(obj)


class AlertSerializer(serializers.ModelSerializer):
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    budget_name = serializers.CharField(source='budget.name', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'alert_type', 'alert_type_display', 'is_active',
            'threshold_amount', 'threshold_percentage', 'days_before',
            'category', 'category_name', 'account', 'account_name',
            'budget', 'budget_name', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# Actualizar TransactionSerializer para incluir tags
class EnhancedTransactionSerializer(TransactionSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Tag.objects.all(),
        write_only=True,
        source='tags'
    )
    receipts = TransactionReceiptSerializer(many=True, read_only=True)
    is_shared = serializers.SerializerMethodField()
    shared_expense_details = SharedExpenseSerializer(source='shared_expense', read_only=True)
    
    class Meta(TransactionSerializer.Meta):
        fields = TransactionSerializer.Meta.fields + [
            'tags', 'tag_ids', 'is_recurring', 'recurring_transaction',
            'receipts', 'is_shared', 'shared_expense_details'
        ]
    
    def get_is_shared(self, obj):
        return hasattr(obj, 'shared_expense')
    
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        transaction = super().create(validated_data)
        transaction.tags.set(tags)
        return transaction
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        transaction = super().update(instance, validated_data)
        if tags is not None:
            transaction.tags.set(tags)
        return transaction


class UserOnboardingSerializer(serializers.ModelSerializer):
    """Serializer para el tutorial de onboarding"""
    current_step_display = serializers.CharField(source='get_current_step_display', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    should_show_tutorial = serializers.ReadOnlyField()
    
    class Meta:
        model = UserOnboarding
        fields = [
            'id', 'current_step', 'current_step_display', 'completed', 'skipped',
            'tutorial_data', 'started_at', 'completed_at', 'last_interaction',
            'total_time_spent', 'step_times', 'progress_percentage', 'should_show_tutorial'
        ]
        read_only_fields = [
            'user', 'started_at', 'completed_at', 'last_interaction', 
            'total_time_spent', 'step_times'
        ]
    
    def create(self, validated_data):
        """Crear onboarding asociado al usuario autenticado"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OnboardingStepSerializer(serializers.Serializer):
    """Serializer para actualizar pasos del tutorial"""
    step = serializers.IntegerField(min_value=0, max_value=6)
    step_data = serializers.JSONField(required=False, default=dict)
    time_spent = serializers.IntegerField(required=False, min_value=0)