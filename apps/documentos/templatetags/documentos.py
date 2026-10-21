"""
Etiquetas para que otras pantallas muestren documentos sin importar la app (la ficha y la consulta no
dependen de `documentos`):
    {% load documentos %}  {% menu_documentos paciente consulta %}  {% documentos_emitidos paciente %}
"""
from django import template

from apps.clinica.consultas import puede_ver

from ..models import DocumentoEmitido
from ..views import menu_documentos as _menu

register = template.Library()


@register.inclusion_tag('documentos/_menu.html', takes_context=True)
def menu_documentos(context, paciente, consulta=None):
    request = context['request']
    return {'opciones': _menu(request, consulta), 'paciente': paciente, 'consulta': consulta}


@register.inclusion_tag('documentos/_emitidos.html', takes_context=True)
def documentos_emitidos(context, paciente=None, consulta=None, limite=10):
    request = context['request']
    qs = DocumentoEmitido.objects.exclude(tipo='recibo').select_related('consulta__tenant__configuracion',
                                                                        'profesional__membresia__usuario')
    qs = qs.filter(consulta=consulta) if consulta is not None else qs.filter(paciente=paciente)
    docs = [d for d in qs[:limite * 2] if d.consulta is None or puede_ver(request.membresia, d.consulta)][:limite]
    return {'documentos': docs}
