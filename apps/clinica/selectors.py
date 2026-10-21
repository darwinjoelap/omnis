from django.db.models import Count, Q

from . import esquemas
from .models import PlantillaHistoria, SeccionClinica


def plantillas_visibles(membresia, especialidad=None):
    """Plantillas de la clínica + las propias del profesional (si lo es)."""
    perfil = membresia.perfil_activo if membresia else None
    filtro = Q(profesional__isnull=True)
    if perfil is not None:
        filtro |= Q(profesional=perfil)
    qs = (PlantillaHistoria.objects.filter(filtro).select_related('especialidad', 'profesional__membresia__usuario')
          .annotate(n_secciones=Count('items')))
    if especialidad is not None:
        qs = qs.filter(especialidad=especialidad)
    return qs.order_by('especialidad__nombre', 'profesional', '-es_predeterminada', 'nombre')


def plantilla_completa(pk):
    return PlantillaHistoria.objects.select_related('especialidad', 'profesional__membresia__usuario').get(pk=pk)


def items_de(plantilla):
    items = list(plantilla.items.select_related('seccion', 'seccion__especialidad').order_by('orden', 'id'))
    for item in items:
        item.campos = esquemas.campos_efectivos(item.seccion.esquema, item.ajustes)
    return items


def secciones_para(plantilla, tenant):
    """Secciones que se pueden agregar, agrupadas: [(titulo, [secciones])]."""
    ya = set(plantilla.items.values_list('seccion_id', flat=True))
    habilitadas = set(tenant.especialidades.values_list('pk', flat=True))
    qs = (SeccionClinica.objects.visibles(tenant).filter(activa=True).exclude(pk__in=ya)
          .select_related('especialidad').order_by('orden', 'nombre'))
    grupos = {'nucleo': [], 'propia': [], 'otras': [], 'personalizadas': []}
    for s in qs:
        if s.tipo == SeccionClinica.Tipo.NUCLEO or (s.tipo == SeccionClinica.Tipo.MODULO and not s.especialidad_id):
            grupos['nucleo'].append(s)
        elif s.tipo == SeccionClinica.Tipo.PERSONALIZADA:
            grupos['personalizadas'].append(s)
        elif s.especialidad_id == plantilla.especialidad_id:
            grupos['propia'].append(s)
        elif s.especialidad_id in habilitadas:
            grupos['otras'].append(s)
    return [(t, grupos[k]) for k, t in (('propia', f'De {plantilla.especialidad}'), ('nucleo', 'Generales'),
                                         ('otras', 'De otras especialidades del consultorio'),
                                         ('personalizadas', 'Personalizadas del consultorio')) if grupos[k]]


def secciones_personalizadas(tenant):
    return SeccionClinica.objects.filter(tenant=tenant).select_related('especialidad').order_by('-activa', 'nombre')


def catalogo(tenant):
    """Todas las secciones visibles (para consultar el catálogo)."""
    return SeccionClinica.objects.visibles(tenant).filter(activa=True).select_related('especialidad') \
        .order_by('tipo', 'especialidad__nombre', 'orden', 'nombre')


def consultas_visibles(request, paciente):
    """Consultas del paciente que el profesional puede ver según la visibilidad del consultorio (ADR-008)."""
    from .consultas import puede_ver
    from .models import Consulta
    qs = (Consulta.objects.filter(paciente=paciente).select_related('profesional__membresia__usuario',
                                                                    'especialidad', 'tenant__configuracion')
          .order_by('-fecha_hora'))
    return [c for c in qs if puede_ver(request.membresia, c)]


def resumen_paciente(request, paciente):
    """Datos clínicos para la ficha del paciente (solo profesionales)."""
    from apps.configuracion.models import Lugar

    from .consultas import plantilla_para
    from .models import Consulta, SignosVitales
    perfil = request.membresia.perfil_activo
    consultas = consultas_visibles(request, paciente)
    ids = [c.pk for c in consultas]
    signos = list(SignosVitales.objects.filter(consulta_id__in=ids).order_by('-fecha')[:12])
    en_curso = next((c for c in consultas if c.estado == Consulta.Estado.BORRADOR and perfil
                     and c.profesional_id == perfil.pk), None)
    return {
        'consultas': consultas,
        'signos': signos,
        'ultimo_signo': signos[0] if signos else None,
        'consulta_en_curso': en_curso,
        'plantillas_consulta': (plantillas_visibles(request.membresia, perfil.especialidad).filter(activa=True)
                                if perfil else []),
        'lugares': Lugar.objects.filter(activo=True),
        'tipos_consulta': Consulta.Tipo.choices,
        'ocultas': Consulta.objects.filter(paciente=paciente).count() - len(consultas),
        'plantilla_sugerida': plantilla_para(perfil) if perfil else None,
        **fichas_y_paneles(request, paciente),
    }


def fichas_y_paneles(request, paciente):
    """
    Lo que aportan los perfiles de especialidad a la ficha del paciente: la ficha de cada especialidad del
    consultorio (la del profesional que mira, o las que ya tienen datos) y los paneles de los módulos
    (curvas de crecimiento, vacunas…).
    """
    from . import registro
    from .consultas import items_ficha, lectura_ficha
    perfil = request.membresia.perfil_activo
    propia = perfil.especialidad.codigo if perfil and perfil.especialidad_id else None
    codigos = list(request.tenant.especialidades.order_by('orden').values_list('codigo', 'nombre'))
    fichas = []
    for codigo, nombre in codigos:
        if not items_ficha(codigo):
            continue
        lectura = lectura_ficha(paciente, codigo)
        if lectura or codigo == propia:
            fichas.append({'codigo': codigo, 'nombre': nombre, 'lectura': lectura})
    paneles = []
    for panel in registro.paneles({c for c, _ in codigos}):
        contexto = panel.contexto(request, paciente) if panel.contexto else {}
        if contexto is not None:
            paneles.append({'def': panel, 'ctx': contexto})
    return {'fichas_especialidad': fichas, 'paneles_especialidad': paneles}


def consultas_en_curso(perfil, limite=10):
    from .models import Consulta
    return (Consulta.objects.filter(profesional=perfil, estado=Consulta.Estado.BORRADOR)
            .select_related('paciente').order_by('-fecha_hora')[:limite])
