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
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'transfers', views.TransferViewSet, basename='transfer')

# 3. Las URLs generadas por el router se incluyen en urlpatterns.
urlpatterns = [
    path('', include(router.urls)),
]
