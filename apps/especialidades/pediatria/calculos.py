"""Cálculos de las secciones de pediatría (campos «calculado»). Nunca fallan: sin datos devuelven None."""
from . import oms


def _evaluacion(datos, contexto):
    paciente = contexto.get('paciente')
    if paciente is None:
        return {}
    ev = oms.evaluar(sexo=contexto.get('sexo') or getattr(paciente, 'sexo', ''),
                     nacimiento=paciente.fecha_nacimiento, fecha=contexto.get('fecha'),
                     peso=_f(datos.get('peso_kg')), talla=_f(datos.get('talla_cm')), pc=_f(datos.get('pc_cm')))
    return ev if 'error' not in ev else {}


def _f(valor):
    try:
        return float(valor) if valor not in (None, '') else None
    except (TypeError, ValueError):
        return None


def _percentil(indicador):
    def calcular(datos, contexto):
        ev = _evaluacion(datos, contexto).get(indicador)
        return ev['percentil'] if ev else None
    return calcular


def imc(datos, contexto):
    valor = oms.imc(_f(datos.get('peso_kg')), _f(datos.get('talla_cm')))
    return round(valor, 1) if valor else None


def _texto(clave):
    def calcular(datos, contexto):
        return _evaluacion(datos, contexto).get(clave) or None
    return calcular


CALCULOS = {
    'ped.imc': imc,
    'ped.p_peso': _percentil('peso'),
    'ped.p_talla': _percentil('talla'),
    'ped.p_pc': _percentil('pc'),
    'ped.p_imc': _percentil('imc'),
    'ped.estado_nutricional': _texto('clasificacion_peso_edad'),
    'ped.clasificacion_imc': _texto('clasificacion_imc'),
    'ped.clasificacion_talla': _texto('clasificacion_talla'),
}
