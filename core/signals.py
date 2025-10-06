from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Transaction, Transfer


@receiver(post_save, sender=Transaction)
def update_account_balance_on_transaction_save(sender, instance, created, **kwargs):
    """
    Actualiza el balance de la cuenta cuando se crea o actualiza una transacción
    
    LÓGICA PARA TARJETAS DE CRÉDITO:
    - Balance representa la DEUDA acumulada
    - Gastos AUMENTAN el balance (más deuda)
    - Pagos REDUCEN el balance (menos deuda)
    - Balance 0 = sin deuda
    - Balance positivo = deuda pendiente
    """
    if created:
        account = instance.account
        
        if account.type == 'credit':
            # TARJETAS DE CRÉDITO: Balance = Deuda acumulada
            if instance.transaction_type == 'expense':
                # Los gastos AUMENTAN la deuda
                account.balance += instance.amount
            elif instance.transaction_type == 'income':
                # Los pagos REDUCEN la deuda
                account.balance -= instance.amount
        else:
            # CUENTAS NORMALES: Balance = Dinero disponible
            if instance.transaction_type == 'expense':
                # Los gastos reducen el dinero disponible
                account.balance -= instance.amount
            elif instance.transaction_type == 'income':
                # Los ingresos aumentan el dinero disponible
                account.balance += instance.amount
        
        account.save()
        print(f"Balance actualizado para {account.name} ({account.type}): {account.balance}")


@receiver(post_delete, sender=Transaction)
def update_account_balance_on_transaction_delete(sender, instance, **kwargs):
    """
    Actualiza el balance de la cuenta cuando se elimina una transacción
    """
    account = instance.account
    
    if account.type == 'credit':
        # TARJETAS DE CRÉDITO: Revertir cambios en la deuda
        if instance.transaction_type == 'expense':
            # Revertir gasto: REDUCIR la deuda
            account.balance -= instance.amount
        elif instance.transaction_type == 'income':
            # Revertir pago: AUMENTAR la deuda
            account.balance += instance.amount
    else:
        # CUENTAS NORMALES: Revertir cambios en el dinero disponible
        if instance.transaction_type == 'expense':
            # Revertir gasto: aumentar el dinero disponible
            account.balance += instance.amount
        elif instance.transaction_type == 'income':
            # Revertir ingreso: reducir el dinero disponible
            account.balance -= instance.amount
    
    account.save()
    print(f"Balance revertido para {account.name} ({account.type}): {account.balance}")


@receiver(post_delete, sender=Transfer)
def revert_balances_on_transfer_delete(sender, instance, **kwargs):
    """
    Revierte los balances cuando se elimina una transferencia
    """
    # Devolver el dinero a la cuenta origen
    from_account = instance.from_account
    from_account.balance += instance.amount
    from_account.save()
    
    # Quitar el dinero de la cuenta destino
    to_account = instance.to_account
    to_account.balance -= instance.amount
    to_account.save()
    
    print(f"Transferencia revertida: {instance.amount} de {to_account.name} a {from_account.name}")
