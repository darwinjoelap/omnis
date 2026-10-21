import logging
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.core.numeros import numero
from apps.core.permisos import requiere

from . import servicios
from .models import TasaCambio, TasaTenant


@login_required
@requiere('tasa.cargar')
def tasa(request):
    """Tasa del día: ver la vigente, cargar una propia si el BCV no actualizó, o volver a la del BCV."""
    hoy = timezone.localdate()
    tenant = request.tenant
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'borrar':
            try:
                fecha = date.fromisoformat(request.POST.get('fecha', ''))
            except ValueError:
                fecha = None
            if fecha:
                servicios.borrar_del_tenant(tenant, fecha)
                messages.success(request, 'Tasa propia eliminada: se usa la del BCV.')
        elif accion == 'bcv':
            try:
                t = servicios.actualizar_desde_bcv()
                messages.success(request, f'BCV consultado: Bs {t.bs_por_usd} ({t.fecha:%d/%m/%Y}).')
            except Exception as e:  # noqa: BLE001 - el sitio del BCV falla seguido
                logging.getLogger('apps.tasas').warning('Consulta al BCV desde %s falló: %s', tenant, e)
                messages.error(request, 'El BCV no respondió. Puedes cargar la tasa del día a mano.')
        else:
            valor = numero(request.POST.get('valor', ''))
            if valor is None or valor <= 0:
                messages.error(request, 'Indica una tasa mayor que cero (ej.: 36,5021).')
            else:
                servicios.registrar_del_tenant(tenant, valor.quantize(Decimal('0.0001')), request.user, hoy)
                messages.success(request, f'Tasa de hoy guardada: Bs {valor}.')
        return redirect('tasas:tasa')
    return render(request, 'tasas/tasa.html', {
        'titulo': 'Tasa del día', 'hoy': hoy, 'vigente': servicios.tasa_vigente(tenant),
        'bcv': servicios.tasa_global(), 'propias': TasaTenant.objects.select_related('registrada_por')[:30],
        'historial_bcv': TasaCambio.objects.all()[:15]})
