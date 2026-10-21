from django.contrib import admin

from apps.core.admin import TenantModelAdmin

from .models import ConfiguracionTenant, Lugar


@admin.register(ConfiguracionTenant)
class ConfiguracionTenantAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'nombre_mostrar', 'visibilidad_historia', 'dictado_activo', 'actualizado_en']
    readonly_fields = ['logo_pdf', 'dictado_activo']


@admin.register(Lugar)
class LugarAdmin(TenantModelAdmin):
    list_display = ['nombre', 'tenant', 'ciudad', 'activo']
