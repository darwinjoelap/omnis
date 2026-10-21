from django.contrib import admin

from apps.core.admin import TenantModelAdmin

from .models import Bloqueo, Cita, HorarioAtencion, TipoCita


@admin.register(Cita)
class CitaAdmin(TenantModelAdmin):
    list_display = ['fecha', 'hora_inicio', 'paciente', 'profesional', 'estado', 'tenant']
    list_filter = ['tenant', 'estado']


for modelo in (HorarioAtencion, Bloqueo, TipoCita):
    admin.site.register(modelo, TenantModelAdmin)
