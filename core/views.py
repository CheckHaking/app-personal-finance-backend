from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Category, Account, Transaction, Transfer
from .serializers import (
    CategorySerializer,
    AccountSerializer,
    TransactionSerializer,
    TransferSerializer,
)


# ViewSet base para asegurar que los usuarios solo puedan ver y editar su propio objetos
class BaseViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        #Esta funcion sobreescribe el queryset base para que solo devuelva los objetos que pertenecen al usuario autenticado
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        #Esta funcion sobreescribe el metodo perform_create para que el usuario autenticado sea el dueño del objeto
        serializer.save(user=self.request.user)

# ----- ViewSets para cada modelo -----
# Heredan la logica de BaseViewSet y solo especifican el queryset y serializer

class CategoryViewSet(BaseViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class AccountViewSet(BaseViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class TransactionViewSet(BaseViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransferViewSet(BaseViewSet):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    