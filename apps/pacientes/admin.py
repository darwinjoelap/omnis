from django.contrib import admin

from apps.core.admin import TenantModelAdmin

from .models import AntecedenteBase, Paciente, Representante


@admin.register(Paciente)
class PacienteAdmin(TenantModelAdmin):
    list_display = ['nombre_completo', 'documento', 'tenant', 'fecha_nacimiento', 'activo']
    search_fields = ['nombres', 'apellidos', 'numero_documento']


@admin.register(Representante)
class RepresentanteAdmin(TenantModelAdmin):
    list_display = ['nombre', 'paciente', 'parentesco', 'tenant']


@admin.register(AntecedenteBase)
class AntecedenteBaseAdmin(TenantModelAdmin):
    list_display = ['paciente', 'tenant']
