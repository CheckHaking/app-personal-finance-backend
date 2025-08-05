from django.db import models
from django.conf import settings


class Category(models.Model):
    CATEGORY_TYPES = (
        ('income', 'Ingreso'),
        ('expense', 'Gasto'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default='expense')
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default="#000000")
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

class Account(models.Model):
    ACCOUNT_TYPES = (
        ('cash', 'Efectivo'),
        ('bank', 'Cuenta Bancaria'),
        ('credit', 'Tarjeta de Credito'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="MXN")
    
    # Campos específicos para tarjetas de crédito
    credit_limit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Límite de crédito total (solo para tarjetas de crédito)"
    )
    closing_date = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Día del mes en que corta la tarjeta (1-31)"
    )
    payment_date = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Día del mes límite para pagar (1-31)"
    )

    def __str__(self):
        return f"{self.name} - {self.get_type_display()}"
    
    @property
    def current_debt(self):
        """Calcula la deuda actual para tarjetas de crédito"""
        if self.type == 'credit':
            # Con la nueva lógica: balance positivo = deuda
            return self.balance if self.balance > 0 else 0
        return 0
    
    @property
    def available_credit(self):
        """Calcula el crédito disponible para tarjetas de crédito"""
        if self.type == 'credit' and self.credit_limit:
            # Con la nueva lógica: crédito disponible = límite - deuda actual
            return self.credit_limit - self.current_debt
        return 0
    
    @property
    def credit_utilization(self):
        """Calcula el porcentaje de utilización del crédito"""
        if self.type == 'credit' and self.credit_limit and self.credit_limit > 0:
            # Con la nueva lógica: utilización = (deuda actual / límite) * 100
            return (self.current_debt / self.credit_limit) * 100
        return 0
    
    def get_next_closing_date(self):
        """Calcula la próxima fecha de corte"""
        if self.type == 'credit' and self.closing_date:
            from datetime import date
            from calendar import monthrange
            
            today = date.today()
            current_month = today.month
            current_year = today.year
            
            # Si ya pasó la fecha de corte de este mes, usar el siguiente mes
            if today.day > self.closing_date:
                if current_month == 12:
                    current_month = 1
                    current_year += 1
                else:
                    current_month += 1
            
            # Ajustar si el día de corte no existe en el mes (ej. 31 en febrero)
            max_day = monthrange(current_year, current_month)[1]
            closing_day = min(self.closing_date, max_day)
            
            return date(current_year, current_month, closing_day)
        return None
    
    def get_next_payment_date(self):
        """Calcula la próxima fecha límite de pago"""
        if self.type == 'credit' and self.payment_date:
            from datetime import date
            from calendar import monthrange
            
            today = date.today()
            current_month = today.month
            current_year = today.year
            
            # Calcular la fecha de pago para el mes actual
            # Si ya pasó la fecha de pago de este mes, usar el siguiente mes
            if today.day > self.payment_date:
                if current_month == 12:
                    current_month = 1
                    current_year += 1
                else:
                    current_month += 1
            
            # Ajustar si el día de pago no existe en el mes
            max_day = monthrange(current_year, current_month)[1]
            payment_day = min(self.payment_date, max_day)
            
            return date(current_year, current_month, payment_day)
        return None
        
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Ingreso'),
        ('expense', 'Gasto'),
        ('transfer', 'Transferencia'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField()
    
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.transaction_type} de {self.amount} en {self.account.name} el {self.date}"

class Transfer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    from_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transfers_made')
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transfers_received')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Transferencia de {self.amount} de {self.from_account.name} a {self.to_account.name} el {self.date}"