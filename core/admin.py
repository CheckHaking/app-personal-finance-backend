from django.contrib import admin
from .models import (
    Category, Account, Transaction, Transfer, Budget, BudgetLine, SavingsGoal,
    Tag, RecurringTransaction, TransactionReceipt, SharedExpense, 
    SharedExpenseParticipant, Alert
)

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

# Reemplazado por EnhancedTransactionAdmin más abajo
# class TransactionAdmin(admin.ModelAdmin):
#     list_display = ('date', 'user', 'account', 'category', 'transaction_type', 'amount')
#     search_fields = ('description', 'account__name', 'category__name')
#     list_filter = ('date', 'transaction_type')

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'from_account', 'to_account', 'amount')
    search_fields = ('description', 'from_account__name', 'to_account__name')
    list_filter = ('date',)


class BudgetLineInline(admin.TabularInline):
    model = BudgetLine
    extra = 1
    fields = ('category', 'amount', 'notes')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'period_type', 'status', 'get_budget_limit', 'created_at')
    list_filter = ('period_type', 'status', 'currency')
    search_fields = ('name', 'user__username')
    inlines = [BudgetLineInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'user', 'period_type', 'status', 'currency')
        }),
        ('Configuración del Periodo', {
            'fields': ('start_date', 'end_date', 'week_start', 'rollover')
        }),
        ('Alineación con Tarjeta de Crédito', {
            'fields': ('align_credit_cycle', 'credit_account'),
            'classes': ('collapse',),
            'description': 'Solo aplicable si deseas alinear con el ciclo de una tarjeta'
        }),
    )
    
    def get_budget_limit(self, obj):
        """Muestra el límite total del presupuesto"""
        return f"${obj.get_budget_limit():,.2f}"
    get_budget_limit.short_description = 'Límite Total'


@admin.register(BudgetLine)
class BudgetLineAdmin(admin.ModelAdmin):
    list_display = ('budget', 'category', 'amount', 'get_spent_amount_display')
    list_filter = ('budget__period_type', 'category__type')
    search_fields = ('budget__name', 'category__name', 'notes')
    
    def get_spent_amount_display(self, obj):
        """Muestra el monto gastado"""
        return f"${obj.get_spent_amount():,.2f}"
    get_spent_amount_display.short_description = 'Gastado'


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'target_amount', 'get_saved_amount_display', 
                   'get_progress_display', 'target_date', 'is_active')
    list_filter = ('is_active', 'contribution_frequency', 'currency')
    search_fields = ('name', 'user__username')
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'user', 'target_amount', 'target_date', 'currency', 'is_active')
        }),
        ('Configuración de Contribución', {
            'fields': ('contribution_frequency', 'auto_rollover', 'linked_account')
        }),
    )
    
    def get_saved_amount_display(self, obj):
        """Muestra el monto ahorrado"""
        return f"${obj.get_saved_amount():,.2f}"
    get_saved_amount_display.short_description = 'Ahorrado'
    
    def get_progress_display(self, obj):
        """Muestra el progreso"""
        return f"{obj.get_progress_percentage():.1f}%"
    get_progress_display.short_description = 'Progreso'


# CONFIGURACIÓN ADMIN PARA NUEVOS MODELOS

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color', 'get_transaction_count', 'created_at')
    search_fields = ('name', 'user__username')
    list_filter = ('created_at',)
    
    def get_transaction_count(self, obj):
        """Muestra el número de transacciones con esta etiqueta"""
        return obj.transactions.count()
    get_transaction_count.short_description = 'Transacciones'


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'amount', 'frequency', 'next_date', 'is_active')
    list_filter = ('frequency', 'is_active', 'transaction_type')
    search_fields = ('name', 'description', 'user__username')
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'user', 'description', 'amount', 'transaction_type', 'category', 'account')
        }),
        ('Configuración de Recurrencia', {
            'fields': ('frequency', 'start_date', 'end_date', 'next_date', 'is_active', 'auto_create', 'notify_before_days')
        }),
    )
    
    actions = ['execute_now', 'pause_selected', 'resume_selected']
    
    def execute_now(self, request, queryset):
        """Ejecuta las transacciones recurrentes seleccionadas"""
        count = 0
        for recurring in queryset:
            try:
                recurring.create_transaction()
                count += 1
            except Exception as e:
                self.message_user(request, f"Error en {recurring.name}: {str(e)}", level='error')
        self.message_user(request, f"{count} transacciones creadas exitosamente")
    execute_now.short_description = "Ejecutar transacciones ahora"
    
    def pause_selected(self, request, queryset):
        """Pausa las transacciones recurrentes seleccionadas"""
        queryset.update(is_active=False)
    pause_selected.short_description = "Pausar seleccionadas"
    
    def resume_selected(self, request, queryset):
        """Reanuda las transacciones recurrentes seleccionadas"""
        queryset.update(is_active=True)
    resume_selected.short_description = "Reanudar seleccionadas"


class TransactionReceiptInline(admin.TabularInline):
    model = TransactionReceipt
    extra = 0
    fields = ('file', 'file_name', 'file_type', 'ocr_processed')
    readonly_fields = ('file_name', 'file_type', 'ocr_processed')


# Actualizar TransactionAdmin para incluir recibos y tags
@admin.register(Transaction)
class EnhancedTransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'account', 'category', 'transaction_type', 'amount', 'get_tags_display', 'has_receipts')
    search_fields = ('description', 'account__name', 'category__name', 'tags__name')
    list_filter = ('date', 'transaction_type', 'is_recurring', 'tags')
    filter_horizontal = ('tags',)
    inlines = [TransactionReceiptInline]
    
    def get_tags_display(self, obj):
        """Muestra las etiquetas de la transacción"""
        return ", ".join([f"#{tag.name}" for tag in obj.tags.all()[:3]])
    get_tags_display.short_description = 'Etiquetas'
    
    def has_receipts(self, obj):
        """Indica si la transacción tiene recibos adjuntos"""
        return obj.receipts.exists()
    has_receipts.boolean = True
    has_receipts.short_description = 'Recibos'


class SharedExpenseParticipantInline(admin.TabularInline):
    model = SharedExpenseParticipant
    extra = 1
    fields = ('email', 'name', 'amount_owed', 'amount_paid', 'is_paid')


@admin.register(SharedExpense)
class SharedExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'created_by', 'total_amount', 'status', 'get_participants_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('description', 'created_by__username')
    inlines = [SharedExpenseParticipantInline]
    readonly_fields = ('transaction', 'created_by', 'created_at', 'updated_at')
    
    def get_participants_count(self, obj):
        """Muestra el número de participantes"""
        return obj.participants.count()
    get_participants_count.short_description = 'Participantes'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert_type', 'is_active', 'get_config_display', 'created_at')
    list_filter = ('alert_type', 'is_active', 'created_at')
    search_fields = ('user__username',)
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'alert_type', 'is_active')
        }),
        ('Configuración de Umbral', {
            'fields': ('threshold_amount', 'threshold_percentage', 'days_before'),
            'description': 'Configura los valores según el tipo de alerta'
        }),
        ('Referencias', {
            'fields': ('category', 'account', 'budget'),
            'description': 'Asocia la alerta con elementos específicos'
        }),
    )
    
    def get_config_display(self, obj):
        """Muestra la configuración de la alerta"""
        if obj.threshold_amount:
            return f"${obj.threshold_amount}"
        elif obj.threshold_percentage:
            return f"{obj.threshold_percentage}%"
        elif obj.days_before:
            return f"{obj.days_before} días"
        return "-"
    get_config_display.short_description = 'Configuración'
