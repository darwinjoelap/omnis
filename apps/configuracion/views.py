from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.platypus import Spacer

from apps.core.imagenes import copia_para_pdf
from apps.core.pdf import ESTILOS, Paragraph, bloque_firma, documento, encabezado_tenant, pie_tenant, respuesta_pdf
from apps.core.permisos import requiere

from .forms import ConfiguracionForm, LugarForm
from .models import Lugar


@login_required
@requiere('tenant.configurar')
def editar(request):
    config = request.tenant.configuracion
    logo_anterior = config.logo.name if config.logo else ''
    form = ConfiguracionForm(request.POST or None, request.FILES or None, instance=config)
    if request.method == 'POST':
        if form.is_valid():
            config = form.save()
            if (config.logo.name if config.logo else '') != logo_anterior:
                copia_para_pdf(config.logo, config.logo_pdf)
                config.save(update_fields=['logo_pdf'])
            messages.success(request, 'Configuración guardada.')
            return redirect(f"{request.path}?tab={request.POST.get('tab', 'identidad')}")
        messages.error(request, 'Revisa los campos marcados.')
    return render(request, 'configuracion/editar.html', {
        'titulo': 'Configuración del consultorio', 'form': form, 'tab': request.GET.get('tab', 'identidad')})


@login_required
@requiere('tenant.configurar')
def pdf_prueba(request):
    """PDF de ejemplo para ver encabezado, firma y pie antes de emitir documentos reales."""
    perfil = request.membresia.perfil_activo if request.membresia else None
    buffer = BytesIO()
    doc = documento(buffer, titulo_pdf='Documento de prueba')
    elementos = encabezado_tenant(request.tenant, titulo='DOCUMENTO DE PRUEBA',
                                  subtitulo=f'Fecha: {timezone.localdate():%d/%m/%Y}', profesional=perfil)
    elementos += [Paragraph('Así se verá el encabezado en récipes, informes, constancias y reportes.',
                            ESTILOS['Normal']), Spacer(1, 8)]
    elementos += bloque_firma(perfil)
    pie = pie_tenant(request.tenant)
    doc.build(elementos, onFirstPage=pie, onLaterPages=pie)
    return respuesta_pdf(buffer.getvalue(), 'prueba-encabezado')


@login_required
@requiere('tenant.configurar')
def lugares(request):
    form = LugarForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lugar agregado.')
        return redirect('configuracion:lugares')
    return render(request, 'configuracion/lugares.html', {
        'titulo': 'Lugares de consulta', 'lugares': Lugar.objects.all(), 'form': form})


@login_required
@requiere('tenant.configurar')
def lugar_editar(request, pk):
    lugar = get_object_or_404(Lugar.objects.all(), pk=pk)
    form = LugarForm(request.POST or None, instance=lugar)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lugar actualizado.')
        return redirect('configuracion:lugares')
    return render(request, 'configuracion/lugar_form.html', {'titulo': f'Lugar · {lugar}', 'form': form})
