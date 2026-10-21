from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.plataforma.models import Tenant

from .models import ConfiguracionTenant


@receiver(post_save, sender=Tenant)
def crear_configuracion(sender, instance, created, **kwargs):
    """Todo tenant nace con su configuración."""
    if created:
        ConfiguracionTenant.objects.get_or_create(tenant=instance, defaults={'nombre_mostrar': instance.nombre})
