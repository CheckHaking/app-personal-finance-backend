from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Configuración del panel de administración para el modelo de usuario personalizado."""
    # Puedes personalizar los campos que se muestran aquí en el futuro.
    # Por ejemplo:
    # list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    pass

