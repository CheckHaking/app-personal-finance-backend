from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 1. Se crea una instancia del router.
router = DefaultRouter()

# 2. Se registra cada ViewSet con el router.
# El router se encarga de generar las URLs para las acciones CRUD estándar:
# - /categories/ -> GET (list), POST (create)
# - /categories/{id}/ -> GET (retrieve), PUT (update), PATCH (partial_update), DELETE (destroy)
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'accounts', views.AccountViewSetExtended, basename='account')
router.register(r'transactions', views.EnhancedTransactionViewSet, basename='transaction')
router.register(r'transfers', views.TransferViewSet, basename='transfer')
router.register(r'budgets', views.BudgetViewSet, basename='budget')
router.register(r'savings-goals', views.SavingsGoalViewSet, basename='savingsgoal')

# Nuevas rutas para funcionalidades agregadas
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'recurring-transactions', views.RecurringTransactionViewSet, basename='recurring-transaction')
router.register(r'receipts', views.TransactionReceiptViewSet, basename='receipt')
router.register(r'shared-expenses', views.SharedExpenseViewSet, basename='shared-expense')
router.register(r'alerts', views.AlertViewSet, basename='alert')
router.register(r'onboarding', views.OnboardingViewSet, basename='onboarding')

# 3. Las URLs generadas por el router se incluyen en urlpatterns.
urlpatterns = [
    path('', include(router.urls)),
]
