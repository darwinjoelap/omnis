from django import forms
from django.contrib.auth.validators import UnicodeUsernameValidator

from apps.core.forms import FormBase
from apps.core.imagenes import validar_imagen
from apps.plataforma.models import Especialidad

from .models import PerfilProfesional


class AgregarForm(FormBase, forms.Form):
    username = forms.CharField(label='Usuario', max_length=60, help_text='Para entrar. Ej.: maria, jperez.',
                               validators=[UnicodeUsernameValidator()])
    nombre = forms.CharField(label='Nombre', max_length=150)
    apellido = forms.CharField(label='Apellido', max_length=150)
    email = forms.EmailField(label='Correo (opcional)', required=False)
    rol = forms.ChoiceField(label='Rol')
    es_profesional = forms.BooleanField(label='Atiende pacientes (es profesional)', required=False)
    especialidad = forms.ModelChoiceField(label='Especialidad', queryset=Especialidad.objects.none(), required=False)
    titulo = forms.ChoiceField(label='Título', choices=PerfilProfesional.Titulo.choices, required=False)

    def __init__(self, *args, roles=(), tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol'].choices = roles
        if tenant is not None:
            self.fields['especialidad'].queryset = tenant.especialidades.filter(activa=True)

    def clean(self):
        datos = super().clean()
        if datos.get('rol') == 'MEDICO':
            datos['es_profesional'] = True
        if datos.get('es_profesional') and not datos.get('especialidad'):
            self.add_error('especialidad', 'Indica la especialidad del profesional.')
        if not datos.get('es_profesional'):
            datos['especialidad'] = None
        return datos


class PerfilProfesionalForm(FormBase, forms.ModelForm):
    quitar_firma = forms.BooleanField(label='Quitar firma', required=False)
    quitar_sello = forms.BooleanField(label='Quitar sello', required=False)
    quitar_membrete = forms.BooleanField(label='Quitar membrete', required=False)

    class Meta:
        model = PerfilProfesional
        fields = ['especialidad', 'subespecialidad', 'titulo', 'credenciales', 'numero_mpps', 'numero_colegio',
                  'telefono_consulta', 'firma', 'sello', 'membrete', 'usar_membrete_propio', 'color_agenda']
        widgets = {
            'firma': forms.FileInput(attrs={'accept': 'image/png,image/jpeg'}),
            'sello': forms.FileInput(attrs={'accept': 'image/png,image/jpeg'}),
            'membrete': forms.FileInput(attrs={'accept': 'image/png,image/jpeg'}),
            'color_agenda': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }

    def __init__(self, *args, tenant=None, puede_cambiar_especialidad=True, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields['especialidad'].queryset = tenant.especialidades.filter(activa=True)
        if not puede_cambiar_especialidad:
            self.fields['especialidad'].disabled = True
            self.fields['especialidad'].help_text = 'La cambia el administrador del consultorio.'

    def _imagen(self, campo, etiqueta):
        archivo = self.cleaned_data.get(campo)
        if archivo and hasattr(archivo, 'content_type'):
            validar_imagen(archivo, etiqueta)
        return archivo

    def clean_firma(self):
        return self._imagen('firma', 'La firma')

    def clean_sello(self):
        return self._imagen('sello', 'El sello')

    def clean_membrete(self):
        return self._imagen('membrete', 'El membrete')

    def save(self, commit=True):
        perfil = super().save(commit=False)
        for campo in ('firma', 'sello', 'membrete'):
            if self.cleaned_data.get(f'quitar_{campo}') and not self.files.get(campo):
                archivo = getattr(perfil, campo)
                if archivo:
                    archivo.delete(save=False)
        if commit:
            perfil.save()
        return perfil
