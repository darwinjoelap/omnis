from django.contrib import admin

from .models import Especialidad, Plan, Suscripcion, Tenant


class SuscripcionInline(admin.TabularInline):
    model = Suscripcion
    extra = 0


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug', 'estado', 'plan', 'activo_hasta', 'creado_en']
    list_filter = ['estado', 'plan']
    search_fields = ['nombre', 'slug']
    filter_horizontal = ['especialidades']
    inlines = [SuscripcionInline]


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio_usd', 'precio_anual_usd', 'max_profesionales', 'max_usuarios',
                    'incluye_dictado', 'activo']


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'modulo', 'activa', 'orden']
    readonly_fields = ['codigo', 'modulo']
