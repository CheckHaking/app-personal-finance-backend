from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

class User(AbstractUser):
    """Modelo de usuario personalizado que extiende el AbstractUser de Django."""
    #abstract user ya tiene username, email, password, first_name, last_name, is_active, is_staff, is_superuser, last_login, date_joined
    pass

class Profile(models.Model):
    CURRENCY_CHOICES = (
        ('USD', 'Dollar'),
        ('EUR', 'Euro'),
        ('MXN', 'Peso Mexicano'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    default_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='MXN')

    def __str__(self):
        return f'Profile of {self.user.username}'