from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render

from . import selectors


@login_required
def inicio(request):
    """Tablero del día. Lo que se ve depende del rol y de si es profesional."""
    contexto = {'titulo': 'Inicio'}
    if request.tenant is not None:
        contexto.update(selectors.resumen_inicio(request))
    return render(request, 'core/inicio.html', contexto)


def salud(request):
    """Healthcheck para Railway: 200 si la app y la BD están vivas."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'estado': 'ok'})
    except Exception:  # pragma: no cover - solo falla con la BD caída
        return JsonResponse({'estado': 'error'}, status=503)


def prohibido(request, exception=None):
    return render(request, '403.html', {'titulo': 'Sin permiso'}, status=403)
