import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.middleware import SESION_SOPORTE, SESION_TENANT
from apps.core.numeros import numero

from . import servicios
from .forms import EditarTenantForm, NuevoTenantForm, RenovarForm
from .models import Tenant

log = logging.getLogger('apps.plataforma')


def solo_plataforma(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return vista(request, *args, **kwargs)
    return login_required(envoltura)


def _enlace(request, tenant):
    return request.build_absolute_uri(f'/{tenant.slug}/')


@solo_plataforma
def lista(request):
    q = request.GET.get('q', '').strip()
    tenants = (Tenant.objects.select_related('plan', 'configuracion').prefetch_related('especialidades')
               .annotate(n_activos=Count('membresias', filter=Q(membresias__activa=True,
                                                               membresias__usuario__is_superuser=False)))
               .order_by('nombre'))
    if q:
        tenants = tenants.filter(Q(nombre__icontains=q) | Q(slug__icontains=q) | Q(configuracion__rif__icontains=q))
    tenants = list(tenants)
    for t in tenants:
        t.enlace = _enlace(request, t)
    return render(request, 'plataforma/lista.html', {'titulo': 'Consultorios y clínicas', 'tenants': tenants, 'q': q})


@solo_plataforma
def nuevo(request):
    form = NuevoTenantForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tenant, titular, clave = servicios.crear_tenant(form.cleaned_data)
        log.warning('Plataforma: %s creó el tenant %s (%s)', request.user.username, tenant.nombre, tenant.pk)
        return render(request, 'plataforma/creado.html', {
            'titulo': 'Consultorio creado', 'tenant': tenant, 'titular': titular, 'clave': clave,
            'enlace': _enlace(request, tenant)})
    return render(request, 'plataforma/form.html', {'titulo': 'Nuevo consultorio o clínica', 'form': form})


@solo_plataforma
def editar(request, pk):
    tenant = get_object_or_404(Tenant.objects.select_related('configuracion', 'plan'), pk=pk)
    inicial = {'nombre': tenant.nombre, 'slug': tenant.slug, 'plan': tenant.plan, 'estado': tenant.estado,
               'activo_hasta': tenant.activo_hasta, 'limite_usuarios': tenant.limite_usuarios,
               'limite_profesionales': tenant.limite_profesionales, 'notas': tenant.notas,
               'especialidades': list(tenant.especialidades.all()),
               'dictado_activo': tenant.configuracion.dictado_activo}
    form = EditarTenantForm(request.POST or None, initial=inicial, tenant=tenant)
    if request.method == 'POST' and form.is_valid():
        servicios.actualizar_tenant(tenant, form.cleaned_data)
        messages.success(request, f'{tenant.nombre}: cambios guardados.')
        return redirect('plataforma:editar', pk=pk)
    from apps.equipo.models import Membresia
    miembros = (Membresia.objects.filter(tenant=tenant, usuario__is_superuser=False)
                .select_related('usuario', 'perfil', 'perfil__especialidad').order_by('-activa', 'rol'))
    return render(request, 'plataforma/form.html', {
        'titulo': tenant.nombre, 'form': form, 'tenant_obj': tenant, 'miembros': miembros,
        'renovaciones': tenant.suscripciones.select_related('plan')[:12],
        'form_renovar': RenovarForm(initial={'plan': tenant.plan}), 'enlace': _enlace(request, tenant)})


@solo_plataforma
@require_POST
def renovar(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    form = RenovarForm(request.POST)
    if form.is_valid():
        d = form.cleaned_data
        servicios.renovar(tenant, meses=d['meses'], monto_usd=d['monto_usd'], referencia=d['referencia'],
                          notas=d['notas'], plan=d['plan'])
        messages.success(request, f'{tenant.nombre}: activo hasta el {tenant.activo_hasta:%d/%m/%Y}.')
    else:
        messages.error(request, 'Revisa los datos de la renovación.')
    return redirect('plataforma:editar', pk=pk)


@solo_plataforma
@require_POST
def entrar(request, pk):
    """El superusuario entra al tenant como Soporte (permisos de Titular, sin ver historias clínicas)."""
    tenant = get_object_or_404(Tenant, pk=pk)
    request.session[SESION_SOPORTE] = tenant.pk
    request.session.pop(SESION_TENANT, None)
    log.warning('Soporte: %s entró al tenant %s (%s)', request.user.username, tenant.nombre, tenant.pk)
    return redirect('core:inicio')


@solo_plataforma
@require_POST
def salir(request):
    request.session.pop(SESION_SOPORTE, None)
    request.session.pop(SESION_TENANT, None)
    return redirect('plataforma:lista')


@solo_plataforma
def tasas(request):
    """Tasa BCV (única para todos): historial, carga manual y consulta al BCV."""
    from apps.tasas import servicios as tasas_srv
    from apps.tasas.models import TasaCambio
    if request.method == 'POST':
        if request.POST.get('accion') == 'bcv':
            try:
                t = tasas_srv.actualizar_desde_bcv()
                messages.success(request, f'Tasa BCV registrada: Bs {t.bs_por_usd} ({t.fecha:%d/%m/%Y}).')
            except Exception as e:  # noqa: BLE001 - el BCV falla seguido: se informa y se carga a mano
                logging.getLogger('apps.tasas').warning('Consulta manual al BCV falló: %s', e)
                messages.error(request, f'No se pudo consultar el BCV ({e.__class__.__name__}). Cárgala a mano.')
        else:
            try:
                valor = numero(request.POST.get('valor', ''))
                fecha = date.fromisoformat(request.POST.get('fecha') or timezone.localdate().isoformat())
                if valor is None or valor <= 0 or fecha > timezone.localdate():
                    raise ValueError
            except (InvalidOperation, ValueError):
                messages.error(request, 'Indica una tasa mayor que cero y una fecha que no sea futura.')
            else:
                tasas_srv.registrar(valor.quantize(Decimal('0.0001')), TasaCambio.Fuente.MANUAL, request.user, fecha)
                messages.success(request, f'Tasa del {fecha:%d/%m/%Y} guardada: Bs {valor}.')
        return redirect('plataforma:tasas')
    return render(request, 'plataforma/tasas.html', {
        'titulo': 'Tasa BCV', 'tasas': TasaCambio.objects.select_related('registrada_por')[:60],
        'vigente': tasas_srv.tasa_global(), 'hoy': timezone.localdate()})
