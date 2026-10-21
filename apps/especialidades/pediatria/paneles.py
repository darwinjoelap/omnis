"""Paneles de pediatría en la ficha del paciente: crecimiento (curvas OMS) y vacunas/pesquisas."""
from apps.core.permisos import tiene_permiso

from . import curvas, vacunas
from .documentos import datos_nacimiento
from .models import MedicionCrecimiento


def crecimiento(request, paciente):
    if paciente.fecha_nacimiento is None or (paciente.edad_anios or 0) >= 19:
        return None
    mediciones = list(MedicionCrecimiento.objects.filter(paciente=paciente).order_by('fecha'))
    nacimiento = datos_nacimiento(paciente)
    graficos = []
    indicadores = ['peso', 'talla', 'pc', 'imc'] if (paciente.edad_anios or 0) < 5 else ['peso', 'talla', 'imc']
    if paciente.sexo:
        for ind in indicadores:
            puntos = curvas.puntos_del_paciente(paciente, ind, mediciones, nacimiento)
            g = curvas.geometria(ind, paciente.sexo, puntos)
            if g is not None:
                graficos.append({'codigo': ind, 'titulo': g['titulo'], 'svg': curvas.svg(g), 'n': len(g['puntos'])})
    return {'graficos': graficos, 'mediciones': list(reversed(mediciones))[:8], 'ultima': mediciones[-1] if
            mediciones else None, 'sin_sexo': not paciente.sexo}


def vacunas_pesquisas(request, paciente):
    if (paciente.edad_anios or 0) >= 19:
        return None
    return {'resumen': vacunas.resumen(paciente), 'pesquisas': vacunas.pesquisas(paciente),
            'puede_registrar': tiene_permiso(request, 'consultas.crear')}
