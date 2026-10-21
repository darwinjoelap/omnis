"""Servicios de pediatría: mediciones de crecimiento (desde la consulta) y datos para las curvas."""
from decimal import Decimal

from django.utils import timezone

from . import oms
from .models import MedicionCrecimiento


def _d(valor, lugares):
    if valor in (None, ''):
        return None
    return Decimal(str(round(float(valor), lugares)))


def sincronizar_medicion(consulta, datos):
    """Gancho al guardar «Antropometría»: guarda la medición con su evaluación OMS (o la borra si se vació)."""
    peso, talla, pc = datos.get('peso_kg'), datos.get('talla_cm'), datos.get('pc_cm')
    if not any((peso, talla, pc)):
        MedicionCrecimiento.objects.filter(consulta=consulta).delete()
        return None
    paciente = consulta.paciente
    fecha = timezone.localtime(consulta.fecha_hora).date()
    ev = oms.evaluar(sexo=paciente.sexo, nacimiento=paciente.fecha_nacimiento, fecha=fecha,
                     peso=float(peso) if peso else None, talla=float(talla) if talla else None,
                     pc=float(pc) if pc else None)
    sin = 'error' in ev

    def z(ind):
        return None if sin or not ev.get(ind) else _d(ev[ind]['z'], 2)

    def p(ind):
        return None if sin or not ev.get(ind) else _d(ev[ind]['percentil'], 1)

    medicion, _ = MedicionCrecimiento.objects.update_or_create(consulta=consulta, defaults={
        'tenant': consulta.tenant, 'paciente': paciente, 'fecha': fecha,
        'edad_meses': None if ev.get('edad_meses') is None else _d(ev['edad_meses'], 2),
        'peso_kg': _d(peso, 3), 'talla_cm': _d(talla, 1), 'pc_cm': _d(pc, 1),
        'imc': _d(oms.imc(float(peso) if peso else None, float(talla) if talla else None), 2),
        'z_peso': z('peso'), 'p_peso': p('peso'), 'z_talla': z('talla'), 'p_talla': p('talla'),
        'z_pc': z('pc'), 'p_pc': p('pc'), 'z_imc': z('imc'), 'p_imc': p('imc'),
        'estado_nutricional': '' if sin else ev['clasificacion_peso_edad'],
        'clasificacion_imc': '' if sin else ev['clasificacion_imc'],
        'clasificacion_talla': '' if sin else ev['clasificacion_talla']})
    _copiar_a_signos(consulta, medicion)
    return medicion


def _copiar_a_signos(consulta, medicion):
    """Peso, talla e IMC también en «Signos vitales» del núcleo (los usan los reportes generales)."""
    from apps.clinica.models import SignosVitales
    SignosVitales.objects.update_or_create(consulta=consulta, defaults={
        'tenant': consulta.tenant, 'paciente': consulta.paciente, 'fecha': medicion.fecha,
        'peso_kg': medicion.peso_kg, 'talla_cm': medicion.talla_cm, 'imc': medicion.imc})
