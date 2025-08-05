from django.contrib import admin
from .models import Category, Account, Transaction, Transfer

# Registramos los modelos para que aparezcan en el panel de administración de Django.
# Esto nos permite ver, crear, editar y eliminar registros directamente desde la interfaz de admin.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color')
    search_fields = ('name', 'user__username')

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'type', 'balance', 'currency', 'credit_limit', 'current_debt_display')
    search_fields = ('name', 'user__username')
    list_filter = ('type', 'currency')
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'type', 'balance', 'currency')
        }),
        ('Configuración de Tarjeta de Crédito', {
            'fields': ('credit_limit', 'closing_date', 'payment_date'),
            'classes': ('collapse',),
            'description': 'Solo aplicable para tarjetas de crédito'
        }),
    )
    
    def current_debt_display(self, obj):
        """Muestra la deuda actual para tarjetas de crédito"""
        if obj.type == 'credit':
            return f"${obj.current_debt:,.2f}"
        return "-"
    current_debt_display.short_description = 'Deuda Actual'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'account', 'category', 'transaction_type', 'amount')
    search_fields = ('description', 'account__name', 'category__name')
    list_filter = ('date', 'transaction_type')

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'from_account', 'to_account', 'amount')
    search_fields = ('description', 'from_account__name', 'to_account__name')
    list_filter = ('date',)
