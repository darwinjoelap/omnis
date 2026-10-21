"""Fechas para la práctica médica: edad exacta y hora en formato 12 h."""
from datetime import date, datetime, time

from django.utils import timezone


def edad_partes(nacimiento, referencia=None):
    """(años, meses, días) cumplidos a la fecha de referencia (hoy por defecto)."""
    if not nacimiento:
        return None
    ref = referencia or timezone.localdate()
    if isinstance(ref, datetime):
        ref = timezone.localtime(ref).date() if timezone.is_aware(ref) else ref.date()
    if ref < nacimiento:
        return (0, 0, 0)
    anios = ref.year - nacimiento.year
    meses = ref.month - nacimiento.month
    dias = ref.day - nacimiento.day
    if dias < 0:
        meses -= 1
        mes_anterior = (ref.month - 2) % 12 + 1
        anio_mes_anterior = ref.year if ref.month > 1 else ref.year - 1
        dias += _dias_del_mes(anio_mes_anterior, mes_anterior)
    if meses < 0:
        anios -= 1
        meses += 12
    return (anios, meses, dias)


def _dias_del_mes(anio, mes):
    siguiente = date(anio + (mes // 12), mes % 12 + 1, 1)
    return (siguiente - date(anio, mes, 1)).days


def edad_anios(nacimiento, referencia=None):
    partes = edad_partes(nacimiento, referencia)
    return partes[0] if partes else None


def edad_meses(nacimiento, referencia=None):
    partes = edad_partes(nacimiento, referencia)
    return partes[0] * 12 + partes[1] if partes else None


def edad_texto(nacimiento, referencia=None):
    """'34 años' · '3 años 2 meses' (menores de 6) · '5 meses 3 días' · '12 días'."""
    partes = edad_partes(nacimiento, referencia)
    if partes is None:
        return ''
    a, m, d = partes

    def p(n, uno, varios):
        return f'{n} {uno if n == 1 else varios}'
    if a >= 6:
        return p(a, 'año', 'años')
    if a >= 1:
        return p(a, 'año', 'años') + (f' {p(m, "mes", "meses")}' if m else '')
    if m >= 1:
        return p(m, 'mes', 'meses') + (f' {p(d, "día", "días")}' if d else '')
    return p(d, 'día', 'días')


def hora12(valor):
    """time/datetime → '1:05 p. m.' (formato venezolano de 12 horas)."""
    if valor is None or valor == '':
        return ''
    if isinstance(valor, datetime):
        if timezone.is_aware(valor):
            valor = timezone.localtime(valor)
        valor = valor.time()
    if not isinstance(valor, time):
        return str(valor)
    h = valor.hour % 12 or 12
    sufijo = 'a. m.' if valor.hour < 12 else 'p. m.'
    return f'{h}:{valor.minute:02d} {sufijo}'


def sumar_meses(fecha, meses):
    """Misma fecha N meses después; si el día no existe (31 → febrero), el último día del mes."""
    total = fecha.month - 1 + meses
    anio, mes = fecha.year + total // 12, total % 12 + 1
    return date(anio, mes, min(fecha.day, _dias_del_mes(anio, mes)))
