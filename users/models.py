from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager para el modelo de usuario personalizado"""
    def create_user(self, email, password=None, **extra_fields):
        """Crear y guardar un usuario con el email y contraseña proporcionados"""
        if not email:
            raise ValueError(_('El email es obligatorio'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crear y guardar un superusuario con el email y contraseña proporcionados"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Modelo de usuario personalizado que utiliza email como identificador único"""
    # Nulificamos el campo username ya que usaremos email como principal
    username = None
    email = models.EmailField(_('dirección de email'), unique=True)
    
    # Campos adicionales para información financiera
    currency = models.CharField(_('moneda predeterminada'), max_length=3, default='USD')
    monthly_budget = models.DecimalField(_('presupuesto mensual'), max_digits=10, decimal_places=2, default=0)
    profile_photo = models.ImageField(_('foto de perfil'), upload_to='profile_photos/', null=True, blank=True)
    
    # Configurar email como campo de username para autenticación
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
