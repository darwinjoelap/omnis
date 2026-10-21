from django.db import transaction
from django.utils import timezone

from .models import Secuencia
from .tenancy import tenant_actual


@transaction.atomic
def siguiente_numero(tipo, prefijo=''):
    """
    Próximo número de un documento, p. ej. 'REC-2026-00001'. Dos usuarios a la vez nunca reciben el mismo.
    """
    anio = timezone.localdate().year
    Secuencia.objects.get_or_create(tenant=tenant_actual(), tipo=tipo, anio=anio)
    sec = Secuencia.objects.select_for_update().get(tipo=tipo, anio=anio)
    sec.ultimo += 1
    sec.save(update_fields=['ultimo'])
    return f'{prefijo}{tipo}-{anio}-{sec.ultimo:05d}'
