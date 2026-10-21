"""
Reglas de la agenda (Fase 08). Los cambios de estado de una cita pasan SOLO por aquí.
"""
import re
import urllib.parse
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.excepciones import ErrorDeNegocio
from apps.core.fechas import hora12
from apps.core.tenancy import tenant_actual

from .models import Bloqueo, Cita, HorarioAtencion

TRANSICIONES = {
    'TENTATIVA': {'PROGRAMADA', 'CONFIRMADA', 'CANCELADA'},
    'PROGRAMADA': {'CONFIRMADA', 'EN_SALA', 'ATENDIDA', 'CANCELADA', 'NO_ASISTIO', 'TENTATIVA'},
    'CONFIRMADA': {'EN_SALA', 'ATENDIDA', 'CANCELADA', 'NO_ASISTIO', 'PROGRAMADA'},
    'EN_SALA': {'ATENDIDA', 'CONFIRMADA', 'NO_ASISTIO'},
    'ATENDIDA': set(),
    'CANCELADA': {'PROGRAMADA'},
    'NO_ASISTIO': {'PROGRAMADA'},
}


def _dt(fecha, hora):
    return timezone.make_aware(datetime.combine(fecha, hora))


def calcular_fin(fecha, hora_inicio, duracion_min):
    if hora_inicio is None:
        return None
    fin = datetime.combine(fecha, hora_inicio) + timedelta(minutes=duracion_min or 30)
    return fin.time() if fin.date() == fecha else time(23, 59)


def solapadas(*, profesional, fecha, hora_inicio, hora_fin, excluir_pk=None):
    if hora_inicio is None:
        return Cita.objects.none()
    qs = Cita.objects.filter(profesional=profesional, fecha=fecha, estado__in=Cita.ACTIVAS,
                             hora_inicio__isnull=False, hora_inicio__lt=hora_fin, hora_fin__gt=hora_inicio)
    return qs.exclude(pk=excluir_pk) if excluir_pk else qs


def bloqueo_en(*, profesional, fecha, hora_inicio, hora_fin):
    inicio = _dt(fecha, hora_inicio or time(0, 0))
    fin = _dt(fecha, hora_fin or time(23, 59))
    return (Bloqueo.objects.filter(desde__lt=fin, hasta__gt=inicio)
            .filter(Q(profesional=profesional) | Q(profesional__isnull=True)).first())


def fuera_de_horario(*, profesional, fecha, hora_inicio, hora_fin):
    """True si el profesional tiene horario cargado para ese día y la cita cae fuera (solo aviso)."""
    if hora_inicio is None:
        return False
    horarios = HorarioAtencion.objects.filter(profesional=profesional, dia_semana=fecha.weekday(), activo=True)
    if not horarios.exists():
        return False
    return not horarios.filter(hora_inicio__lte=hora_inicio, hora_fin__gte=hora_fin).exists()


@transaction.atomic
def guardar_cita(cita, *, sobrecupo=False):
    """
    Crea o actualiza una cita (instancia ya llenada desde el formulario). Reglas:
    - el profesional debe estar activo; la especialidad es la suya;
    - no se pisa con otra cita activa del mismo profesional, salvo sobrecupo explícito;
    - no cae en un bloqueo; sin hora = tentativa.
    Devuelve (cita, avisos).
    """
    from apps.equipo.models import PerfilProfesional
    perfil = PerfilProfesional.objects.select_for_update().get(pk=cita.profesional_id)   # serializa por profesional
    if not perfil.activo or not perfil.membresia.activa:
        raise ErrorDeNegocio('Ese profesional no está activo.')
    cita.especialidad = perfil.especialidad
    avisos = []
    if cita.hora_inicio is None:
        cita.hora_fin = None
        if cita.estado in ('PROGRAMADA', 'CONFIRMADA'):
            cita.estado = Cita.Estado.TENTATIVA
    else:
        tenant = cita.tenant if cita.tenant_id else tenant_actual()
        duracion = cita.tipo.duracion_min if cita.tipo_id else tenant.configuracion.duracion_cita_min
        if not cita.hora_fin or cita.hora_fin <= cita.hora_inicio:
            cita.hora_fin = calcular_fin(cita.fecha, cita.hora_inicio, duracion)
        if cita.estado == Cita.Estado.TENTATIVA:
            cita.estado = Cita.Estado.PROGRAMADA
        choques = solapadas(profesional=perfil, fecha=cita.fecha, hora_inicio=cita.hora_inicio,
                            hora_fin=cita.hora_fin, excluir_pk=cita.pk)
        if choques.exists():
            if not sobrecupo:
                otra = choques.select_related('paciente').first()
                raise ErrorDeNegocio(f'{perfil} ya tiene cita a esa hora ({otra.paciente}, '
                                     f'{hora12(otra.hora_inicio)}). Marca «sobrecupo» si es a propósito.')
            cita.sobrecupo = True
        bloqueo = bloqueo_en(profesional=perfil, fecha=cita.fecha, hora_inicio=cita.hora_inicio,
                             hora_fin=cita.hora_fin)
        if bloqueo:
            raise ErrorDeNegocio(f'La agenda está bloqueada en ese horario: {bloqueo.motivo}.')
        if fuera_de_horario(profesional=perfil, fecha=cita.fecha, hora_inicio=cita.hora_inicio,
                            hora_fin=cita.hora_fin):
            avisos.append('La cita queda fuera del horario de atención cargado para ese día.')
    if cita.fecha < timezone.localdate() and cita.pk is None:
        avisos.append('La cita quedó en una fecha pasada.')
    cita.save()
    return cita, avisos


@transaction.atomic
def cambiar_estado(cita, nuevo, motivo=''):
    cita = Cita.objects.select_for_update().get(pk=cita.pk)
    if nuevo == cita.estado:
        return cita
    if nuevo not in TRANSICIONES.get(cita.estado, set()):
        raise ErrorDeNegocio(f'Una cita «{cita.get_estado_display()}» no puede pasar a '
                             f'«{Cita.Estado(nuevo).label}».')
    if nuevo == Cita.Estado.CANCELADA:
        cita.motivo_cancelacion = (motivo or '')[:200]
    cita.estado = nuevo
    cita.save(update_fields=['estado', 'motivo_cancelacion', 'actualizado_en'])
    return cita


@transaction.atomic
def atender(cita, perfil):
    """Abre la consulta de la cita (o vuelve a la ya abierta) y la marca atendida."""
    from apps.clinica.consultas import abrir_consulta
    cita = Cita.objects.select_for_update().get(pk=cita.pk)
    if cita.consulta_id:
        return cita.consulta
    if cita.profesional_id != perfil.pk:
        raise ErrorDeNegocio(f'La cita es con {cita.profesional}; solo esa persona puede atenderla.')
    if not cita.activa:
        raise ErrorDeNegocio(f'La cita está «{cita.get_estado_display()}».')
    tipo = cita.tipo
    consulta = abrir_consulta(paciente=cita.paciente, profesional=perfil,
                              plantilla=tipo.plantilla if tipo and tipo.plantilla_id and tipo.plantilla.activa else None,
                              tipo=tipo.tipo_consulta if tipo else 'PRIMERA', lugar=cita.lugar)
    cita.consulta = consulta
    cita.estado = Cita.Estado.ATENDIDA
    cita.save(update_fields=['consulta', 'estado', 'actualizado_en'])
    if tipo and tipo.servicio_id and tipo.servicio.activo and not cita.cargos.exists():
        from apps.cobros.servicios import crear_cargo
        crear_cargo(paciente=cita.paciente, servicio=tipo.servicio, descripcion=tipo.servicio.nombre,
                    precio_usd=tipo.servicio.precio_usd, consulta=consulta, cita=cita, profesional=perfil)
    return consulta


def turnos_libres(profesional, fecha):
    """Horas de inicio libres del día según el horario cargado (para sugerir al agendar)."""
    citas = [(c.hora_inicio, c.hora_fin) for c in Cita.objects.filter(
        profesional=profesional, fecha=fecha, estado__in=Cita.ACTIVAS, hora_inicio__isnull=False)]
    libres = []
    for h in HorarioAtencion.objects.filter(profesional=profesional, dia_semana=fecha.weekday(), activo=True):
        actual = datetime.combine(fecha, h.hora_inicio)
        fin = datetime.combine(fecha, h.hora_fin)
        paso = timedelta(minutes=h.duracion_turno_min)
        while actual + paso <= fin:
            ini, ter = actual.time(), (actual + paso).time()
            if not any(a < ter and b > ini for a, b in citas):
                libres.append((ini, h.lugar))
            actual += paso
    if fecha == timezone.localdate():
        ahora = timezone.localtime().time()
        libres = [x for x in libres if x[0] > ahora]
    return libres


def semana_de(fecha):
    lunes = fecha - timedelta(days=fecha.weekday())
    return [lunes + timedelta(days=i) for i in range(7)]


def url_whatsapp(cita):
    """Recordatorio por WhatsApp (de Pediae): si es menor, al representante."""
    paciente = cita.paciente
    representante = paciente.representante_principal if paciente.es_menor else None
    telefono = (representante.telefono if representante and representante.telefono else '') or paciente.telefono
    numero = re.sub(r'[^\d+]', '', telefono or '')
    if not numero:
        return None
    if numero.startswith('0'):
        numero = '58' + numero[1:]
    numero = numero.lstrip('+')
    config = cita.tenant.configuracion
    saludo = (representante.nombre if representante else paciente.nombres).split()[0]
    cuando = f'el {cita.fecha:%d/%m/%Y}' + (f' a las {hora12(cita.hora_inicio)}' if cita.hora_inicio else '')
    lugar = f' en {cita.lugar.nombre}' + (f' ({cita.lugar.direccion})' if cita.lugar and cita.lugar.direccion else '') \
        if cita.lugar else ''
    de_quien = f'de {paciente.nombres} ' if representante else ''
    texto = (f'Hola {saludo}, le recordamos la cita {de_quien}con {cita.profesional.nombre_con_titulo} '
             f'({config.nombre_display}) {cuando}{lugar}.')
    texto += f'\n\n{config.mensaje_whatsapp}' if config.mensaje_whatsapp else ' Por favor confirme su asistencia. Gracias.'
    return f'https://wa.me/{numero}?text={urllib.parse.quote(texto)}'


def marcar_recordatorio(cita):
    cita.recordatorio_en = timezone.now()
    cita.save(update_fields=['recordatorio_en'])


def hoy():
    return timezone.localdate()


def fecha_de(texto, por_defecto=None):
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        return por_defecto or hoy()
