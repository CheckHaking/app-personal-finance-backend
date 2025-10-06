from django.db import models
from django.conf import settings
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone


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
        ('investment', 'Cuenta de Inversión'),
        ('virtual', 'Cuenta Virtual'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="MXN")
    is_virtual = models.BooleanField(
        default=False,
        help_text="Marca esta cuenta como virtual (no representa dinero real)"
    )
    
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
    
    # Campos específicos para cuentas de inversión
    investment_platform = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Plataforma de inversión (ej: Fintual, GBM+, Kuspit)"
    )
    return_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tasa de retorno anual estimada (%)"
    )
    initial_investment = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Inversión inicial"
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
    
    @property
    def total_return(self):
        """Calcula el retorno total para cuentas de inversión"""
        if self.type == 'investment' and self.initial_investment:
            return self.balance - self.initial_investment
        return 0
    
    @property
    def return_percentage(self):
        """Calcula el porcentaje de retorno para cuentas de inversión"""
        if self.type == 'investment' and self.initial_investment and self.initial_investment > 0:
            return ((self.balance - self.initial_investment) / self.initial_investment) * 100
        return 0
        
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
    
    # Campos para funcionalidades nuevas
    tags = models.ManyToManyField('Tag', blank=True, related_name='transactions')
    is_recurring = models.BooleanField(default=False)
    recurring_transaction = models.ForeignKey('RecurringTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_transactions')
    
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


class Budget(models.Model):
    """Modelo para presupuestos flexibles por periodo"""
    PERIOD_TYPES = (
        ('monthly', 'Mensual'),
        ('weekly', 'Semanal'),
        ('custom', 'Personalizado'),
        ('card_cycle', 'Ciclo de Tarjeta'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Activo'),
        ('archived', 'Archivado'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=100)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Null para periodos recurrentes
    week_start = models.CharField(max_length=10, default='monday')  # Por defecto lunes
    align_credit_cycle = models.BooleanField(default=False)
    credit_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, 
                                     limit_choices_to={'type': 'credit'}, 
                                     related_name='aligned_budgets')
    rollover = models.BooleanField(default=False)
    currency = models.CharField(max_length=3, default='MXN')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_period_type_display()})"
    
    def get_current_period_window(self):
        """Calcula la ventana del periodo actual según el tipo"""
        today = timezone.now().date()
        
        if self.period_type == 'weekly':
            # Semana empieza en lunes
            days_since_monday = today.weekday()
            start = today - timedelta(days=days_since_monday)
            end = start + timedelta(days=6)
            return start, end
            
        elif self.period_type == 'monthly':
            # Mes calendario completo
            start = today.replace(day=1)
            next_month = start + relativedelta(months=1)
            end = next_month - timedelta(days=1)
            return start, end
            
        elif self.period_type == 'card_cycle' and self.credit_account:
            # Alineado al ciclo de tarjeta
            closing_date = self.credit_account.get_next_closing_date()
            if closing_date:
                # El ciclo actual terminará en la próxima fecha de corte
                end = closing_date
                # El ciclo empezó el día después del corte anterior
                prev_closing = closing_date - relativedelta(months=1)
                start = prev_closing + timedelta(days=1)
                
                # Si hoy es después del corte, usar el siguiente ciclo
                if today > closing_date:
                    start = closing_date + timedelta(days=1)
                    end = self.credit_account.get_next_closing_date()
                    
                return start, end
                
        elif self.period_type == 'custom':
            # Periodo personalizado fijo
            return self.start_date, self.end_date
            
        # Fallback
        return self.start_date, self.end_date
    
    def get_spent_amount(self, start_date=None, end_date=None):
        """Calcula el monto gastado en el periodo especificado"""
        if not start_date or not end_date:
            start_date, end_date = self.get_current_period_window()
            
        # Obtener todas las categorías de las líneas del presupuesto
        category_ids = self.lines.values_list('category_id', flat=True)
        
        # Sumar transacciones de tipo 'expense' en las categorías del presupuesto
        spent = Transaction.objects.filter(
            user=self.user,
            transaction_type='expense',
            category_id__in=category_ids,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return spent
    
    def get_budget_limit(self):
        """Obtiene el límite total del presupuesto sumando todas las líneas"""
        return self.lines.aggregate(total=models.Sum('amount'))['total'] or 0
    
    def clean(self):
        """Validaciones del modelo"""
        if self.period_type == 'custom' and not self.end_date:
            raise ValidationError("Los presupuestos personalizados requieren fecha de fin")
            
        if self.align_credit_cycle and not self.credit_account:
            raise ValidationError("Debes seleccionar una tarjeta de crédito para alinear el ciclo")
            
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError("La fecha de fin debe ser posterior a la fecha de inicio")


class BudgetLine(models.Model):
    """Línea de presupuesto para una categoría específica"""
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='lines')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.CharField(max_length=200, blank=True)
    
    class Meta:
        unique_together = ['budget', 'category']
        ordering = ['category__name']
    
    def __str__(self):
        category_name = self.category.name if self.category else "General"
        return f"{category_name}: {self.amount}"
    
    def get_spent_amount(self, start_date=None, end_date=None):
        """Calcula el monto gastado para esta línea específica"""
        if not self.category:
            return 0
            
        if not start_date or not end_date:
            start_date, end_date = self.budget.get_current_period_window()
            
        spent = Transaction.objects.filter(
            user=self.budget.user,
            transaction_type='expense',
            category=self.category,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return spent
    
    def clean(self):
        """Validaciones del modelo"""
        if self.category and self.category.user != self.budget.user:
            raise ValidationError("La categoría debe pertenecer al mismo usuario del presupuesto")
            
        if self.amount <= 0:
            raise ValidationError("El monto debe ser mayor a cero")


class SavingsGoal(models.Model):
    """Modelo para metas de ahorro"""
    CONTRIBUTION_FREQUENCY = (
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('flex', 'Flexible'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    target_date = models.DateField()
    currency = models.CharField(max_length=3, default='MXN')
    linked_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='savings_goals')
    contribution_frequency = models.CharField(max_length=10, choices=CONTRIBUTION_FREQUENCY, default='monthly')
    auto_rollover = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.target_amount} {self.currency}"
    
    def get_saved_amount(self):
        """Calcula el monto ahorrado hacia esta meta"""
        saved = 0
        
        # Si hay cuenta vinculada, sumar transferencias hacia ella
        if self.linked_account:
            saved += Transfer.objects.filter(
                user=self.user,
                to_account=self.linked_account,
                date__gte=self.created_at.date()
            ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        # También buscar transacciones categorizadas como "Ahorro" con esta meta en la descripción
        savings_category = Category.objects.filter(
            user=self.user,
            name__icontains='ahorro',
            type='expense'  # Los ahorros se registran como "gastos" en categoría ahorro
        ).first()
        
        if savings_category:
            saved += Transaction.objects.filter(
                user=self.user,
                category=savings_category,
                description__icontains=self.name,
                date__gte=self.created_at.date()
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        return saved
    
    def get_remaining_amount(self):
        """Calcula cuánto falta para alcanzar la meta"""
        return max(Decimal('0'), self.target_amount - self.get_saved_amount())
    
    def get_progress_percentage(self):
        """Calcula el porcentaje de progreso"""
        if self.target_amount > 0:
            progress = (self.get_saved_amount() / self.target_amount) * Decimal('100')
            # Devolver como float para UI
            return float(min(Decimal('100'), progress))
        return 0
    
    def is_on_track(self):
        """Determina si la meta va por buen camino según la fecha objetivo"""
        today = timezone.now().date()
        if today >= self.target_date:
            return self.get_saved_amount() >= self.target_amount
            
        days_total = (self.target_date - self.created_at.date()).days
        days_elapsed = (today - self.created_at.date()).days
        
        if days_total <= 0:
            return True
            
        expected_progress = (Decimal(days_elapsed) / Decimal(days_total)) * self.target_amount
        actual_progress = self.get_saved_amount()
        
        # Consideramos "on track" si el progreso real está al menos al 80% del esperado
        return actual_progress >= (expected_progress * Decimal('0.8'))
    
    def clean(self):
        """Validaciones del modelo"""
        if self.target_amount <= 0:
            raise ValidationError("El monto objetivo debe ser mayor a cero")
            
        if self.target_date <= timezone.now().date():
            raise ValidationError("La fecha objetivo debe ser futura")
            
        if self.linked_account and self.linked_account.user != self.user:
            raise ValidationError("La cuenta vinculada debe pertenecer al mismo usuario")


# NUEVOS MODELOS AGREGADOS

class Tag(models.Model):
    """Etiquetas para categorizar transacciones de forma más flexible"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#000000")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'name')
        ordering = ['name']
    
    def __str__(self):
        return f"#{self.name}"


class RecurringTransaction(models.Model):
    """Plantilla para transacciones recurrentes"""
    FREQUENCY_CHOICES = (
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=Transaction.TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_date = models.DateField()
    
    is_active = models.BooleanField(default=True)
    auto_create = models.BooleanField(default=False, help_text="Crear transacciones automáticamente")
    notify_before_days = models.IntegerField(default=1, help_text="Días antes para notificar")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_date', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"
    
    def calculate_next_date(self, from_date=None):
        """Calcula la próxima fecha de ocurrencia"""
        if not from_date:
            from_date = self.next_date or self.start_date
            
        if self.frequency == 'daily':
            return from_date + timedelta(days=1)
        elif self.frequency == 'weekly':
            return from_date + timedelta(weeks=1)
        elif self.frequency == 'biweekly':
            return from_date + timedelta(weeks=2)
        elif self.frequency == 'monthly':
            return from_date + relativedelta(months=1)
        elif self.frequency == 'quarterly':
            return from_date + relativedelta(months=3)
        elif self.frequency == 'yearly':
            return from_date + relativedelta(years=1)
            
        return from_date
    
    def create_transaction(self):
        """Crea una transacción basada en esta plantilla"""
        transaction = Transaction.objects.create(
            user=self.user,
            amount=self.amount,
            transaction_type=self.transaction_type,
            category=self.category,
            account=self.account,
            description=f"{self.description} (Recurrente: {self.name})",
            date=self.next_date,
            is_recurring=True,
            recurring_transaction=self
        )
        
        # Actualizar próxima fecha
        self.next_date = self.calculate_next_date()
        self.save()
        
        return transaction


class TransactionReceipt(models.Model):
    """Recibos/comprobantes adjuntos a transacciones"""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='receipts')
    file = models.FileField(upload_to='receipts/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Campos para OCR (opcional)
    ocr_text = models.TextField(blank=True, null=True)
    ocr_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ocr_date = models.DateField(null=True, blank=True)
    ocr_processed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Recibo para {self.transaction} - {self.file_name}"


class SharedExpense(models.Model):
    """Gastos compartidos entre múltiples personas"""
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('partially_paid', 'Parcialmente pagado'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado'),
    )
    
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='shared_expense')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_shared_expenses')
    description = models.CharField(max_length=200)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Gasto compartido: {self.description}"


class SharedExpenseParticipant(models.Model):
    """Participantes en un gasto compartido"""
    shared_expense = models.ForeignKey(SharedExpense, on_delete=models.CASCADE, related_name='participants')
    email = models.EmailField()
    name = models.CharField(max_length=100)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('shared_expense', 'email')
    
    def __str__(self):
        return f"{self.name} debe {self.amount_owed - self.amount_paid}"


class Alert(models.Model):
    """Sistema de alertas configurables"""
    ALERT_TYPES = (
        ('budget_exceeded', 'Presupuesto excedido'),
        ('budget_warning', 'Advertencia de presupuesto'),
        ('low_balance', 'Saldo bajo'),
        ('payment_due', 'Pago próximo'),
        ('goal_milestone', 'Hito de meta alcanzado'),
        ('recurring_due', 'Transacción recurrente próxima'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    is_active = models.BooleanField(default=True)
    
    # Configuración específica por tipo
    threshold_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    threshold_percentage = models.IntegerField(null=True, blank=True)
    days_before = models.IntegerField(null=True, blank=True)
    
    # Referencias opcionales
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['alert_type', 'created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.user.username}"


class UserOnboarding(models.Model):
    """Modelo para trackear el progreso del tutorial de onboarding"""
    TUTORIAL_STEPS = (
        (0, 'No iniciado'),
        (1, 'Bienvenida'),
        (2, 'Configuración de perfil'),
        (3, 'Primera cuenta'),
        (4, 'Categorías'),
        (5, 'Primera transacción'),
        (6, 'Tutorial completado'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='onboarding')
    current_step = models.IntegerField(choices=TUTORIAL_STEPS, default=0)
    completed = models.BooleanField(default=False)
    skipped = models.BooleanField(default=False)
    
    # Datos recopilados durante el tutorial
    tutorial_data = models.JSONField(default=dict, help_text="Datos recopilados durante el tutorial")
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_interaction = models.DateTimeField(auto_now=True)
    
    # Métricas para Tokio School
    total_time_spent = models.IntegerField(default=0, help_text="Tiempo total en segundos")
    step_times = models.JSONField(default=dict, help_text="Tiempo por paso en segundos")
    
    class Meta:
        verbose_name = "User Onboarding"
        verbose_name_plural = "User Onboardings"
    
    def __str__(self):
        return f"{self.user.username} - Paso {self.current_step} ({'Completado' if self.completed else 'En progreso'})"
    
    def start_tutorial(self):
        """Iniciar el tutorial"""
        if not self.started_at:
            self.started_at = timezone.now()
            self.current_step = 1
            self.save()
    
    def advance_step(self, step_data=None):
        """Avanzar al siguiente paso"""
        if self.current_step < 6:
            self.current_step += 1
            if step_data:
                self.tutorial_data.update(step_data)
            self.save()
    
    def complete_tutorial(self):
        """Marcar tutorial como completado"""
        self.completed = True
        self.completed_at = timezone.now()
        self.current_step = 6
        
        # Calcular tiempo total
        if self.started_at:
            total_seconds = (self.completed_at - self.started_at).total_seconds()
            self.total_time_spent = int(total_seconds)
        
        self.save()
    
    def skip_tutorial(self):
        """Saltar el tutorial"""
        self.skipped = True
        self.completed = True
        self.completed_at = timezone.now()
        self.save()
    
    @property
    def progress_percentage(self):
        """Calcular porcentaje de progreso"""
        if self.completed:
            return 100
        return (self.current_step / 6) * 100
    
    @property
    def should_show_tutorial(self):
        """Determinar si debe mostrar el tutorial"""
        return not self.completed and not self.skipped
