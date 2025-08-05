from rest_framework import serializers
from .models import Category, Account, Transaction, Transfer

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
    
    class Meta:
        model = Account
        fields = [
            'id', 'name', 'type', 'balance', 'currency',
            'credit_limit', 'closing_date', 'payment_date',
            'current_debt', 'available_credit', 'credit_utilization',
            'next_closing_date', 'next_payment_date'
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
    class Meta:
        model = Transfer
        fields = ['id', 'from_account', 'to_account', 'amount', 'description', 'date']
        read_only_fields = ['user']
        