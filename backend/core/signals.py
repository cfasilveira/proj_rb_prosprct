"""Signals do core: criação automática de Perfil."""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Perfil

User = get_user_model()


@receiver(post_save, sender=User)
def cria_perfil(sender, instance, created, **kwargs):
    if created and not Perfil.objects.filter(user=instance).exists():
        Perfil.objects.create(
            user=instance,
            nome_completo=instance.get_full_name() or instance.email,
        )
