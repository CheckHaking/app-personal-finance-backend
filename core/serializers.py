from rest_framework import serializers
from .models import Category, Account, Transaction, Transfer

class CategorySerializer(serializers.ModelSerializer):
    class Meta: 
        model = Category
        #Aqui le decimos que el campo user no se pide en la creacion de una categoria, ya que se obtiene del usuario autenticado
        #y que el campo id sirve para referenciar la categoria
        fields = ['id', 'name', 'color']
        read_only_fields = ['user']

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'type', 'balance', 'currency']
        read_only_fields = ['user']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'account', 'category', 'transaction_type', 'amount', 'description', 'date']
        read_only_fields = ['user']

class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = ['id', 'from_account', 'to_account', 'amount', 'description', 'date']
        read_only_fields = ['user']
        