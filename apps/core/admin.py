from django.contrib import admin

from .models import Auditoria, Secuencia


class TenantModelAdmin(admin.ModelAdmin):
    """Admin de plataforma: ve todos los tenants (manager `todos`)."""
    list_filter = ['tenant']

    def get_queryset(self, request):
        return self.model.todos.select_related('tenant')

    def has_add_permission(self, request):
        return False      # los datos de negocio se crean desde la app, dentro de su tenant

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        from .tenancy import TenantModel
        if issubclass(db_field.related_model, TenantModel):
            kwargs['queryset'] = db_field.related_model.todos.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Auditoria)
class AuditoriaAdmin(TenantModelAdmin):
    list_display = ['creado_en', 'tenant', 'usuario', 'accion', 'objeto_tipo', 'objeto_id', 'paciente_id', 'ip']
    list_filter = ['tenant', 'accion']
    readonly_fields = [f.name for f in Auditoria._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Secuencia)
class SecuenciaAdmin(TenantModelAdmin):
    list_display = ['tenant', 'tipo', 'anio', 'ultimo']
