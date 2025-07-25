from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    #Crea un perfil automaticamente cuando se crea un usuario
    if created: 
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    #Guarda el perfil cuando se guarda el usuario
    instance.profile.save()