from django import forms

from apps.core.forms import FormBase

FECHA = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')
HORA = forms.TimeInput(attrs={'type': 'time'}, format='%H:%M')


def _area(filas=3):
    return forms.Textarea(attrs={'rows': filas})


class DocumentoForm(FormBase, forms.Form):
    """Base: todo documento puede llevar ciudad (para «Ciudad, fecha»)."""
    ciudad = forms.CharField(label='Ciudad', max_length=80, required=False)

    def datos(self):
        salida = {}
        for k, v in self.cleaned_data.items():
            if v in (None, ''):
                continue
            salida[k] = v.isoformat() if hasattr(v, 'isoformat') else v
        return salida


class InformeForm(DocumentoForm):
    dirigido_a = forms.CharField(label='Dirigido a (opcional)', max_length=150, required=False)
    introduccion = forms.CharField(label='Introducción (opcional)', required=False, widget=_area(2))
    conclusion = forms.CharField(label='Conclusión (opcional)', required=False, widget=_area(3))


class ReferenciaForm(DocumentoForm):
    dirigido_a = forms.CharField(label='Referido a (especialidad, médico o institución)', max_length=150)
    prioridad = forms.ChoiceField(label='Prioridad', required=False,
                                  choices=[('', '—'), ('Electiva', 'Electiva'), ('Prioritaria', 'Prioritaria'),
                                           ('Urgente', 'Urgente')])
    motivo = forms.CharField(label='Motivo de la referencia', widget=_area(3))
    resumen = forms.CharField(label='Resumen clínico', required=False, widget=_area(4))
    diagnosticos = forms.CharField(label='Impresión diagnóstica', required=False, widget=_area(2))
    tratamiento = forms.CharField(label='Tratamiento actual', required=False, widget=_area(2))


class ReposoForm(DocumentoForm):
    dias = forms.IntegerField(label='Días de reposo', min_value=1, max_value=365)
    desde = forms.DateField(label='Desde', widget=FECHA)
    diagnostico = forms.CharField(label='Diagnóstico', required=False, widget=_area(2))
    indicaciones = forms.CharField(label='Indicaciones (opcional)', required=False, widget=_area(2))


class ConstanciaForm(DocumentoForm):
    fecha_asistencia = forms.DateField(label='Fecha de la consulta', widget=FECHA)
    hora_desde = forms.TimeField(label='Desde', required=False, widget=HORA)
    hora_hasta = forms.TimeField(label='Hasta', required=False, widget=HORA)
    acompanante = forms.CharField(label='Acompañante (opcional)', max_length=150, required=False)
    observaciones = forms.CharField(label='Observaciones (opcional)', required=False, widget=_area(2))

    def clean(self):
        d = super().clean()
        if d.get('hora_desde') and d.get('hora_hasta') and d['hora_hasta'] <= d['hora_desde']:
            self.add_error('hora_hasta', 'Debe ser posterior a la hora de inicio.')
        return d


class AnularForm(forms.Form):
    motivo = forms.CharField(label='Motivo', max_length=200, min_length=3)
