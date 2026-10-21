from django.db.models import Q

from .models import Paciente, normalizar_documento, normalizar_texto

# ── Alcance: qué pacientes ve cada quien ──────────────────────────────────────
# - Titular, administrador y asistente: todos (son quienes organizan el consultorio).
# - Médico: «mis pacientes» por defecto; «todos» solo si la configuración lo autoriza.
#   Sus pacientes = los que atendió, los que tiene citados y los que registró. Además puede abrir (y buscar)
#   un paciente nuevo, sin ninguna consulta: así atiende a quien la asistente registró sin cita. Un paciente
#   con historia de otro médico le llega cuando se lo citan (interconsulta) o si la configuración lo autoriza.

def puede_ver_todos(membresia):
    from apps.core.permisos import Rol
    if membresia is None:
        return False
    if membresia.rol in (Rol.TITULAR, Rol.ADMIN, Rol.ASISTENTE) or membresia.perfil_activo is None:
        return True
    return membresia.tenant.configuracion.medicos_ven_todos_pacientes


def _ids_propios(membresia):
    from apps.agenda.models import Cita
    from apps.clinica.models import Consulta
    perfil = membresia.perfil_activo
    return (Q(pk__in=Consulta.objects.filter(profesional=perfil).values('paciente_id'))
            | Q(pk__in=Cita.objects.filter(profesional=perfil).values('paciente_id'))
            | Q(creado_por=membresia.usuario_id))


def filtrar_propios(qs, membresia):
    return qs.filter(_ids_propios(membresia))


def puede_ver_paciente(membresia, paciente):
    if puede_ver_todos(membresia):
        return True
    if membresia is None or membresia.perfil_activo is None:
        return False
    return (filtrar_propios(Paciente.objects.filter(pk=paciente.pk), membresia).exists()
            or not paciente.consultas.exists())


def alcance_inicial(membresia, pedido=None):
    """'mios' o 'todos' para la lista: el profesional arranca en «mis pacientes»."""
    if not puede_ver_todos(membresia):
        return 'mios'
    if pedido in ('mios', 'todos'):
        return pedido if membresia.perfil_activo is not None else 'todos'
    return 'mios' if membresia is not None and membresia.perfil_activo is not None else 'todos'


def buscar(texto='', solo_activos=True, membresia=None, alcance='todos'):
    """Busca por nombre o documento, sin importar acentos ni mayúsculas, en cualquier orden de palabras."""
    qs = Paciente.objects.all()
    if solo_activos:
        qs = qs.filter(activo=True)
    texto = (texto or '').strip()
    doc = normalizar_documento(texto) if texto else ''
    if texto:
        filtro = Q()
        for palabra in normalizar_texto(texto).split():
            filtro &= Q(busqueda__contains=palabra)
        if doc and doc.isdigit():
            filtro |= Q(documento_normalizado__endswith=doc)
        qs = qs.filter(filtro)
    if alcance == 'mios' and membresia is not None and membresia.perfil_activo is not None:
        from apps.clinica.models import Consulta
        sin_historia = ~Q(pk__in=Consulta.objects.values('paciente_id'))
        qs = qs.filter(_ids_propios(membresia) | sin_historia)
    return qs.order_by('apellidos', 'nombres')


def total_pacientes(membresia=None, alcance='todos'):
    return buscar(membresia=membresia, alcance=alcance).count()


def pacientes_recientes(limite=6, membresia=None, alcance='todos'):
    qs = Paciente.objects.all()
    if alcance == 'mios' and membresia is not None and membresia.perfil_activo is not None:
        qs = filtrar_propios(qs, membresia)
    return qs.order_by('-creado_en')[:limite]


def ficha(pk):
    return (Paciente.objects.select_related('antecedentes', 'creado_por')
            .prefetch_related('representantes').get(pk=pk))
