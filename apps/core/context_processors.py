from django.conf import settings
from django.utils import timezone

from .permisos import permisos_de


def omnis(request):
    """Datos globales para todas las plantillas."""
    membresia = getattr(request, 'membresia', None)
    tenant = getattr(request, 'tenant', None)
    tasa = None
    if tenant is not None:
        from apps.tasas.servicios import tasa_vigente
        tasa = tasa_vigente(tenant)
    aviso = None
    if tenant and membresia and membresia.rol in ('TITULAR', 'ADMIN'):
        dias = tenant.dias_para_vencer
        if dias is not None and 0 <= dias <= 7:
            aviso = dias
    return {
        'PRODUCTO': settings.PRODUCTO,
        'OMNIS_VERSION': settings.OMNIS_VERSION,
        'aviso_vencimiento': aviso,
        'tasa': tasa,
        'tasa_desactualizada': bool(tasa and tasa.fecha < timezone.localdate()),
        'tenant': tenant,
        'config': getattr(tenant, 'configuracion', None) if tenant else None,
        'membresia': membresia,
        'membresias': getattr(request, 'membresias', []),
        'profesional': getattr(membresia, 'perfil_activo', None) if membresia else None,
        'permisos': permisos_de(membresia),
    }
