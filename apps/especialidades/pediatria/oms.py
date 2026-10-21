"""
Percentiles y puntaje z de crecimiento con las tablas LMS oficiales de la OMS (ADR-034).

- Edad en meses con decimales (días / 30,4375) e interpolación lineal de L, M y S entre meses (la OMS publica
  tablas por día en 0–5 años; la diferencia con la interpolación mensual es < 0,02 z).
- Peso/edad e IMC/edad usan el puntaje z «restringido» de la OMS más allá de ±3 (la cola se extrapola con la
  distancia entre 2 y 3 DE), igual que los programas Anthro y AnthroPlus.
- Talla/edad y perímetro cefálico/edad: fórmula LMS directa (L = 1).

Reemplaza el cálculo de Pediae (`consultas/oms.py`), que usaba una tabla reducida con L constante para el peso y
S desactualizado para la talla > 24 meses (desvíos de hasta varios percentiles en los extremos).
"""
import math
from datetime import date
from statistics import NormalDist

from .datos_oms import TABLAS

_NORMAL = NormalDist()
DIAS_POR_MES = 30.4375
PERCENTILES_CURVA = (3, 15, 50, 85, 97)
Z_DE_PERCENTIL = {p: _NORMAL.inv_cdf(p / 100) for p in PERCENTILES_CURVA}
RESTRINGIDOS = {'peso', 'imc'}          # z restringido más allá de ±3 (OMS)
NOMBRES = {'peso': 'Peso/edad', 'talla': 'Talla/edad', 'pc': 'Perímetro cefálico/edad', 'imc': 'IMC/edad'}
UNIDADES = {'peso': 'kg', 'talla': 'cm', 'pc': 'cm', 'imc': 'kg/m²'}


def edad_en_meses(nacimiento: date, fecha: date) -> float | None:
    if not nacimiento or not fecha or fecha < nacimiento:
        return None
    return (fecha - nacimiento).days / DIAS_POR_MES


def rango(indicador, sexo):
    """(primer mes, último mes) con datos para ese indicador y sexo."""
    filas = TABLAS[indicador][_sexo(sexo)]
    return filas[0][0], filas[-1][0]


def _sexo(sexo):
    s = (sexo or '').upper()[:1]
    if s not in ('M', 'F'):
        raise ValueError('Sexo desconocido: hace falta para los percentiles.')
    return s


def lms(indicador, sexo, meses):
    """(L, M, S) interpolados para la edad en meses; None fuera del rango de la tabla."""
    filas = TABLAS[indicador][_sexo(sexo)]
    primero, ultimo = filas[0][0], filas[-1][0]
    if meses is None or meses < primero or meses > ultimo:
        return None
    i = min(int(meses) - primero, len(filas) - 2)
    m0, l0, mu0, s0 = filas[i]
    _, l1, mu1, s1 = filas[i + 1]
    t = meses - m0
    return l0 + t * (l1 - l0), mu0 + t * (mu1 - mu0), s0 + t * (s1 - s0)


def valor_para_z(L, M, S, z):
    """Medida que corresponde a un puntaje z (inversa de LMS)."""
    if abs(L) < 1e-9:
        return M * math.exp(S * z)
    base = 1 + L * S * z
    return M * base ** (1 / L) if base > 0 else float('nan')


def _z_lms(L, M, S, x):
    if abs(L) < 1e-9:
        return math.log(x / M) / S
    return ((x / M) ** L - 1) / (L * S)


def zscore(indicador, sexo, meses, valor):
    """Puntaje z OMS (con la regla restringida para peso e IMC). None si no aplica a esa edad o falta el valor."""
    if valor is None or valor <= 0:
        return None
    params = lms(indicador, sexo, meses)
    if params is None:
        return None
    L, M, S = params
    z = _z_lms(L, M, S, valor)
    if indicador in RESTRINGIDOS and abs(z) > 3:
        if z > 3:
            sd3, sd2 = valor_para_z(L, M, S, 3), valor_para_z(L, M, S, 2)
            z = 3 + (valor - sd3) / (sd3 - sd2)
        else:
            sd3, sd2 = valor_para_z(L, M, S, -3), valor_para_z(L, M, S, -2)
            z = -3 + (valor - sd3) / (sd2 - sd3)
    return z


def percentil(z):
    return None if z is None else _NORMAL.cdf(z) * 100


def curvas(indicador, sexo, hasta_meses, desde_meses=0, paso=1):
    """{percentil: [(mes, valor), …]} para dibujar las curvas P3–P97."""
    primero, ultimo = rango(indicador, sexo)
    desde, hasta = max(primero, desde_meses), min(ultimo, hasta_meses)
    salida = {p: [] for p in PERCENTILES_CURVA}
    mes = desde
    while mes <= hasta:
        L, M, S = lms(indicador, sexo, mes)
        for p, z in Z_DE_PERCENTIL.items():
            salida[p].append((mes, round(valor_para_z(L, M, S, z), 2)))
        mes += paso
    return salida


# ── Clasificaciones ──────────────────────────────────────────────────────────

def clasificar_peso_edad(p):
    """Criterio que usaban las pediatras en Pediae (percentil de peso/edad)."""
    if p is None:
        return ''
    if p < 3:
        return 'Desnutrición severa (<p3)'
    if p < 10:
        return 'Desnutrición (p3–p10)'
    if p < 15:
        return 'Riesgo de desnutrición (p10–p15)'
    if p <= 85:
        return 'Eutrófico (p15–p85)'
    if p <= 97:
        return 'Sobrepeso (p85–p97)'
    return 'Obesidad (>p97)'


def clasificar_imc(z, meses):
    """Criterio OMS por IMC/edad (menores de 5 años y de 5 a 19 años tienen puntos de corte distintos)."""
    if z is None:
        return ''
    if meses is not None and meses < 61:
        if z > 3:
            return 'Obesidad'
        if z > 2:
            return 'Sobrepeso'
        if z > 1:
            return 'Riesgo de sobrepeso'
        if z < -3:
            return 'Emaciación severa'
        if z < -2:
            return 'Emaciación'
        return 'Normal'
    if z > 2:
        return 'Obesidad'
    if z > 1:
        return 'Sobrepeso'
    if z < -3:
        return 'Delgadez severa'
    if z < -2:
        return 'Delgadez'
    return 'Normal'


def clasificar_talla(z):
    if z is None:
        return ''
    if z < -3:
        return 'Talla baja severa'
    if z < -2:
        return 'Talla baja'
    if z > 3:
        return 'Talla muy alta'
    return 'Talla adecuada'


def clasificar_pc(z):
    if z is None:
        return ''
    if z < -2:
        return 'Microcefalia (< −2 DE)'
    if z > 2:
        return 'Macrocefalia (> +2 DE)'
    return 'Normal'


def imc(peso_kg, talla_cm):
    if not peso_kg or not talla_cm:
        return None
    return peso_kg / (talla_cm / 100) ** 2


def evaluar(*, sexo, nacimiento, fecha, peso=None, talla=None, pc=None):
    """
    Evaluación antropométrica completa de una consulta. Devuelve dict con `edad_meses`, y por indicador
    (`peso`, `talla`, `pc`, `imc`) {valor, z, percentil} (o None si no aplica) y las clasificaciones.
    Sin sexo o sin fecha de nacimiento devuelve `error`.
    """
    meses = edad_en_meses(nacimiento, fecha)
    if meses is None:
        return {'error': 'Falta la fecha de nacimiento.'}
    try:
        _sexo(sexo)
    except ValueError as e:
        return {'error': str(e), 'edad_meses': meses}
    valores = {'peso': peso, 'talla': talla, 'pc': pc, 'imc': imc(peso, talla)}
    salida = {'edad_meses': meses}
    for ind, v in valores.items():
        z = zscore(ind, sexo, meses, v) if v else None
        salida[ind] = None if z is None else {'valor': v, 'z': round(z, 2), 'percentil': round(percentil(z), 1)}
    p_peso = salida['peso']['percentil'] if salida['peso'] else None
    salida['clasificacion_peso_edad'] = clasificar_peso_edad(p_peso)
    salida['clasificacion_imc'] = clasificar_imc(salida['imc']['z'] if salida['imc'] else None, meses)
    salida['clasificacion_talla'] = clasificar_talla(salida['talla']['z'] if salida['talla'] else None)
    salida['clasificacion_pc'] = clasificar_pc(salida['pc']['z'] if salida['pc'] else None)
    return salida
