from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite ver, crear y editar usuarios.
    El método POST de este endpoint servirá para el registro de nuevos usuarios.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    # Por ahora, permitimos que cualquiera pueda registrarse.
    # Más adelante, ajustaremos los permisos para otras acciones (ver, editar).
    permission_classes = [permissions.AllowAny]

