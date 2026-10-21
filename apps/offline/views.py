from datetime import timedelta

from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from apps.core import auditoria

MAX_URLS = 80


@never_cache
def ping(request):
    """Respuesta mínima para medir la conexión y saber si la sesión sigue abierta."""
    user = getattr(request, 'user', None)
    return JsonResponse({'ok': True, 'auth': bool(user and user.is_authenticated and getattr(request, 'tenant', None))})


@never_cache
def precache(request):
    """
    Páginas que offline.js descarga por adelantado (con buena señal) para trabajar sin datos:
    inicio, agenda de hoy y mañana, lista de pacientes, ficha de cada paciente citado,
    la «Nueva consulta» de cada cita del médico y sus consultas en curso.
    """
    membresia = getattr(request, 'membresia', None)
    if not request.user.is_authenticated or getattr(request, 'tenant', None) is None or membresia is None \
            or getattr(membresia, 'soporte', False):
        return JsonResponse({'urls': []})
    from apps.agenda.models import Cita
    from apps.core.permisos import tiene_permiso

    hoy = timezone.localdate()
    manana = hoy + timedelta(days=1)
    perfil = membresia.perfil_activo
    agenda = reverse('agenda:dia')
    urls = [reverse('core:inicio'), agenda, f'{agenda}?fecha={manana.isoformat()}', reverse('pacientes:lista')]
    if tiene_permiso(request, 'agenda.ver'):
        citas = (Cita.objects.filter(fecha__range=(hoy, manana), estado__in=Cita.ACTIVAS)
                 .order_by('fecha', 'hora_inicio'))
        if perfil is not None:
            urls.append(f'{agenda}?fecha={manana.isoformat()}&p={perfil.pk}')
            urls.append(f'{agenda}?p={perfil.pk}')
            citas = citas.filter(profesional=perfil)
        vistos = set()
        for cita in citas[:40]:
            if cita.paciente_id not in vistos:
                vistos.add(cita.paciente_id)
                urls.append(reverse('pacientes:detalle', args=[cita.paciente_id]))
            if perfil is not None and tiene_permiso(request, 'consultas.crear'):
                urls.append(f"{reverse('clinica:consulta_nueva', args=[cita.paciente_id])}?cita={cita.pk}")
    if perfil is not None:
        from apps.clinica.selectors import consultas_en_curso
        for c in consultas_en_curso(perfil, limite=20):
            urls.append(reverse('clinica:consulta_editar', args=[c.pk]))
    urls = list(dict.fromkeys(urls))[:MAX_URLS]
    auditoria.registrar(request, 'VER', 'offline', detalle=f'Precarga sin conexión: {len(urls)} páginas')
    return JsonResponse({'urls': urls})
