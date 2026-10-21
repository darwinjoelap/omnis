from django import forms
from django.forms import formset_factory

from apps.core.forms import FormBase
from apps.plataforma.models import Especialidad

from .esquemas import TIPOS, TIPOS_PERSONALIZABLES
from .models import PlantillaHistoria, SeccionClinica

ANCHOS = [(12, 'Toda la fila'), (6, 'Media fila'), (4, 'Un tercio'), (3, 'Un cuarto')]


class NuevaPlantillaForm(FormBase, forms.Form):
    nombre = forms.CharField(label='Nombre', max_length=100, help_text='Ej.: Primera consulta, Control, Niño sano.')
    especialidad = forms.ModelChoiceField(label='Especialidad', queryset=Especialidad.objects.none())
    de_clinica = forms.BooleanField(label='Compartida con los profesionales de la especialidad', required=False)
    copiar_de = forms.ModelChoiceField(label='Partir de', queryset=PlantillaHistoria.objects.none(), required=False,
                                       empty_label='Plantilla vacía')

    def __init__(self, *args, tenant=None, plantillas=None, puede_clinica=False, es_profesional=False, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields['especialidad'].queryset = tenant.especialidades.filter(activa=True)
        if plantillas is not None:
            self.fields['copiar_de'].queryset = plantillas
        if not puede_clinica:
            del self.fields['de_clinica']
        elif not es_profesional:
            self.fields['de_clinica'].initial = True
            self.fields['de_clinica'].disabled = True


class SeccionPersonalizadaForm(FormBase, forms.Form):
    nombre = forms.CharField(label='Nombre de la sección', max_length=120)
    descripcion = forms.CharField(label='Descripción (opcional)', max_length=250, required=False)
    ambito = forms.ChoiceField(label='¿Cuándo se llena?', choices=SeccionClinica.Ambito.choices,
                               initial=SeccionClinica.Ambito.CONSULTA)
    especialidad = forms.ModelChoiceField(label='Especialidad (opcional)', queryset=Especialidad.objects.none(),
                                          required=False, empty_label='Cualquier especialidad')

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields['especialidad'].queryset = tenant.especialidades.all()


class CampoForm(FormBase, forms.Form):
    clave = forms.CharField(widget=forms.HiddenInput, required=False)
    etiqueta = forms.CharField(label='Etiqueta', max_length=120)
    tipo = forms.ChoiceField(label='Tipo', choices=[(t, TIPOS[t]) for t in TIPOS_PERSONALIZABLES])
    opciones = forms.CharField(label='Opciones / columnas', required=False,
                               widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Una por línea'}))
    unidad = forms.CharField(label='Unidad', max_length=20, required=False)
    minimo = forms.DecimalField(label='Mínimo', required=False)
    maximo = forms.DecimalField(label='Máximo', required=False)
    decimales = forms.IntegerField(label='Decimales', required=False, min_value=0, max_value=4)
    ancho = forms.TypedChoiceField(label='Ancho', choices=ANCHOS, coerce=int, initial=6)
    requerido = forms.BooleanField(label='Obligatorio', required=False)
    ayuda = forms.CharField(label='Ayuda', max_length=200, required=False)
    orden = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def clean(self):
        datos = super().clean()
        tipo = datos.get('tipo')
        lineas = [x for x in (datos.get('opciones') or '').splitlines() if x.strip()]
        if tipo in ('opcion', 'opciones') and not lineas:
            self.add_error('opciones', 'Escribe las opciones, una por línea.')
        if tipo == 'tabla' and not lineas:
            self.add_error('opciones', 'Escribe las columnas de la tabla, una por línea.')
        if tipo == 'escala' and datos.get('minimo') is not None and datos.get('maximo') is not None \
                and datos['minimo'] >= datos['maximo']:
            self.add_error('maximo', 'Debe ser mayor que el mínimo.')
        return datos


CamposFormSet = formset_factory(CampoForm, extra=0, can_delete=True, min_num=1, validate_min=True)
