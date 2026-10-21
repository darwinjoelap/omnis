"""Glosario de medicamentos con calculadora de dosis (núcleo, de Pediae)."""
import re

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.forms import FormBase
from apps.core.permisos import requiere

from .dosis import calcular
from .models import Medicamento

RANGO = re.compile(r'^\s*(\d+)?\s*(?:-|a|–)\s*(\d+)?\s*(?:m(?:eses)?)?\s*:\s*(.+)$', re.I)


def visibles(request):
    perfil = request.membresia.perfil_activo
    return Medicamento.objects.filter(Q(profesional__isnull=True) | Q(profesional=perfil))


class MedicamentoForm(FormBase, forms.ModelForm):
    rangos = forms.CharField(label='Dosis por edad', required=False, widget=forms.Textarea(attrs={'rows': 3}),
                             help_text='Una línea por rango, en meses: «6-23: ½ sobre» · «24-: 1 sobre».')
    solo_mio = forms.BooleanField(label='Solo para mí (no lo ven los demás médicos)', required=False)

    class Meta:
        model = Medicamento
        fields = ['nombre', 'presentacion', 'modo', 'unidad_kg', 'dosis_kg_min', 'dosis_kg_max', 'concentracion_mg',
                  'volumen_ml', 'unidad_resultado', 'dosis_max', 'dosis_fija', 'frecuencia_horas', 'duracion_dias',
                  'indicaciones', 'edad_min_meses', 'edad_max_meses', 'peso_min_kg', 'activo']
        widgets = {'indicaciones': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['rangos'] = '\n'.join(
                f"{r.get('min') if r.get('min') is not None else ''}-{r.get('max') if r.get('max') is not None else ''}"
                f": {r.get('dosis', '')}" for r in self.instance.rangos_edad or [])
            self.initial['solo_mio'] = self.instance.profesional_id is not None

    def clean_rangos(self):
        salida = []
        for linea in (self.cleaned_data.get('rangos') or '').splitlines():
            if not linea.strip():
                continue
            m = RANGO.match(linea)
            if not m:
                raise forms.ValidationError(f'No entiendo «{linea.strip()}». Usa «6-23: ½ sobre».')
            salida.append({'min': int(m[1]) if m[1] else None, 'max': int(m[2]) if m[2] else None,
                           'dosis': m[3].strip()})
        return salida

    def clean(self):
        d = super().clean()
        if d.get('modo') == 'PESO' and not d.get('dosis_kg_min'):
            self.add_error('dosis_kg_min', 'Indica la dosis por kg.')
        if d.get('modo') == 'FIJA' and not d.get('dosis_fija'):
            self.add_error('dosis_fija', 'Indica la dosis fija.')
        if d.get('modo') == 'EDAD' and not d.get('rangos'):
            self.add_error('rangos', 'Indica al menos un rango de edad.')
        if d.get('dosis_kg_min') and d.get('dosis_kg_max') and d['dosis_kg_max'] < d['dosis_kg_min']:
            self.add_error('dosis_kg_max', 'Debe ser mayor que la mínima.')
        return d


@login_required
@requiere('consultas.crear')
def lista(request):
    meds = visibles(request).order_by('-activo', 'nombre')
    return render(request, 'clinica/medicamentos.html', {'titulo': 'Glosario de medicamentos', 'medicamentos': meds})


@login_required
@requiere('consultas.crear')
def editar(request, pk=None):
    med = get_object_or_404(visibles(request), pk=pk) if pk else Medicamento()
    form = MedicamentoForm(request.POST or None, instance=med)
    if request.method == 'POST' and form.is_valid():
        med = form.save(commit=False)
        med.rangos_edad = form.cleaned_data['rangos']
        med.profesional = request.membresia.perfil_activo if form.cleaned_data['solo_mio'] else None
        med.save()
        messages.success(request, f'«{med}» guardado.')
        return redirect('clinica:medicamentos')
    prueba = None
    if med.pk:
        prueba = [(p, calcular(med, peso_kg=p, edad_meses=e)) for p, e in ((5, 3), (10, 15), (20, 72))]
    return render(request, 'clinica/medicamento_form.html', {
        'titulo': str(med) if med.pk else 'Nuevo medicamento', 'form': form, 'med': med, 'prueba': prueba})


@login_required
@requiere('consultas.crear')
@require_POST
def activar(request, pk):
    med = get_object_or_404(visibles(request), pk=pk)
    med.activo = not med.activo
    med.save(update_fields=['activo', 'actualizado_en'])
    return redirect('clinica:medicamentos')


@login_required
@requiere('consultas.crear')
def calcular_json(request, pk):
    """GET ?peso=12&edad_meses=30&nivel=estandar → dosis calculada para llenar la fila del récipe."""
    med = get_object_or_404(visibles(request).filter(activo=True), pk=pk)

    def num(nombre, tipo=float):
        try:
            return tipo(str(request.GET.get(nombre, '')).replace(',', '.'))
        except ValueError:
            return None
    return JsonResponse(calcular(med, peso_kg=num('peso'), edad_meses=num('edad_meses', lambda v: int(float(v))),
                                 nivel=request.GET.get('nivel', 'estandar')))
