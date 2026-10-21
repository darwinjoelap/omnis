from django.contrib import admin

from apps.core.admin import TenantModelAdmin

from .models import DocumentoEmitido


@admin.register(DocumentoEmitido)
class DocumentoEmitidoAdmin(TenantModelAdmin):
    list_display = ('numero', 'tipo', 'paciente', 'profesional', 'fecha', 'anulado')
    list_filter = ('tipo', 'anulado')
    search_fields = ('numero',)
