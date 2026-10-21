from django.contrib import admin

from apps.core.admin import TenantModelAdmin

from .models import Membresia, PerfilProfesional


@admin.register(Membresia)
class MembresiaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tenant', 'rol', 'activa']
    list_filter = ['rol', 'activa', 'tenant']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name', 'tenant__nombre']
    autocomplete_fields = ['usuario', 'tenant']


@admin.register(PerfilProfesional)
class PerfilProfesionalAdmin(TenantModelAdmin):
    list_display = ['__str__', 'tenant', 'especialidad', 'numero_mpps', 'activo']
    list_filter = ['tenant', 'especialidad', 'activo']
