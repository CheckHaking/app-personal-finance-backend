from django.db import models
from django.conf import settings


class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#000000")
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        unique_together = ('user', 'name')

    def __str__(self):
        return self.name

class Account(models.Model):
    ACOOUNT_TYPES = (
        ('cash', 'Efectivo'),
        ('bank', 'Cuenta Bancaria'),
        ('credit', 'Tarjeta de Credito'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=ACOOUNT_TYPES)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="MXN")

    def __str__(self):
        return f"{self.name} - {self.get_account_type_display()}"
        
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