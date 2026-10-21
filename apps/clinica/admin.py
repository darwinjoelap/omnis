from django.contrib import admin

from apps.core.admin import TenantModelAdmin

from .models import PlantillaHistoria, PlantillaSeccion, SeccionClinica, SeccionClinicaVersion


@admin.register(SeccionClinica)
class SeccionClinicaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'tipo', 'ambito', 'especialidad', 'tenant', 'version', 'activa']
    list_filter = ['tipo', 'ambito', 'especialidad', 'activa']
    search_fields = ['nombre', 'codigo']
    readonly_fields = ['tenant', 'codigo', 'tipo', 'version']


@admin.register(SeccionClinicaVersion)
class SeccionClinicaVersionAdmin(admin.ModelAdmin):
    list_display = ['seccion', 'version', 'creado_en']


class PlantillaSeccionInline(admin.TabularInline):
    model = PlantillaSeccion
    extra = 0
    fields = ['seccion', 'orden', 'obligatoria', 'colapsada']

    def get_queryset(self, request):
        return PlantillaSeccion.todos.all()


@admin.register(PlantillaHistoria)
class PlantillaHistoriaAdmin(TenantModelAdmin):
    list_display = ['nombre', 'tenant', 'especialidad', 'profesional', 'es_predeterminada', 'activa']
    inlines = [PlantillaSeccionInline]
