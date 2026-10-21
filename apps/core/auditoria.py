"""Registro de auditoría: `registrar(request, 'VER', paciente, paciente_id=paciente.pk)`."""
from .models import Auditoria
from .tenancy import tenant_actual


def _ip(request):
    if request is None:
        return None
    reenviada = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (reenviada.split(',')[0].strip() or request.META.get('REMOTE_ADDR')) or None


def registrar(request, accion, objeto, *, paciente_id=None, detalle=''):
    """No falla nunca hacia el usuario: si no hay tenant activo, no registra."""
    if tenant_actual() is None:
        return None
    if accion == 'VER' and request is not None and request.META.get('HTTP_X_OFFLINE_PREFETCH'):
        return None      # la precarga sin conexión no es una lectura de la persona (se audita una vez en /offline/precache/)
    usuario = getattr(request, 'user', None) if request is not None else None
    return Auditoria.objects.create(
        usuario=usuario if usuario is not None and usuario.is_authenticated else None,
        accion=accion,
        objeto_tipo=objeto._meta.label if hasattr(objeto, '_meta') else str(objeto),
        objeto_id=str(getattr(objeto, 'pk', '') or ''),
        paciente_id=paciente_id,
        detalle=detalle[:300],
        ip=_ip(request),
    )
