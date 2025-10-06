from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile
from core.models import UserOnboarding

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    #Crea un perfil automaticamente cuando se crea un usuario
    if created: 
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    #Guarda el perfil cuando se guarda el usuario
    instance.profile.save()

@receiver(post_save, sender=User)
def create_user_onboarding(sender, instance, created, **kwargs):
    """
    Crea un UserOnboarding automáticamente cuando se crea un nuevo usuario
    """
    if created:
        UserOnboarding.objects.create(user=instance)
        print(f"UserOnboarding creado para el usuario: {instance.username}")