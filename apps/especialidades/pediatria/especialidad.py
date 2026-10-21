"""
Pediatría (Fase 13, ADR-034): reemplaza a la especialidad «básica» del mismo código.
Ver docs/roadmap/13_pediatria.md.
"""
from apps.clinica import registro
from apps.clinica.registro import EspecialidadDef, PlantillaDef

from .calculos import CALCULOS
from .secciones import CONSULTA, FICHA

# En pediatría peso y talla van en «Antropometría» (con percentiles): se ocultan de los signos vitales del núcleo.
SIGNOS_PEDIATRICOS = ('nucleo.signos_vitales', {'ajustes': {'ocultos': [
    'peso_kg', 'talla_cm', 'imc', 'superficie_corporal', 'glicemia', 'perimetro_abdominal']}})
FICHA_COLAPSADA = [(s.codigo, {'colapsada': True}) for s in FICHA]

PRIMERA = ['nucleo.motivo', 'nucleo.antecedentes', *FICHA_COLAPSADA, SIGNOS_PEDIATRICOS, 'ped.antropometria',
           'ped.habitos', 'ped.desarrollo', 'nucleo.examen_fisico', 'nucleo.paraclinicos',
           ('nucleo.diagnosticos', {'obligatoria': True}), 'nucleo.plan', 'nucleo.prescripcion', 'nucleo.ordenes']
CONTROL_SANO = ['nucleo.motivo', SIGNOS_PEDIATRICOS, 'ped.antropometria', 'ped.habitos', 'ped.desarrollo',
                'nucleo.examen_fisico', ('nucleo.diagnosticos', {'obligatoria': True}), 'nucleo.plan',
                'nucleo.prescripcion']
ENFERMEDAD = ['nucleo.motivo', SIGNOS_PEDIATRICOS, 'ped.antropometria', 'nucleo.examen_fisico',
              'nucleo.paraclinicos', ('nucleo.diagnosticos', {'obligatoria': True}), 'nucleo.plan',
              'nucleo.prescripcion', 'nucleo.ordenes']
SEGUIMIENTO = ['nucleo.motivo', SIGNOS_PEDIATRICOS, ('ped.antropometria', {'colapsada': True}),
               'nucleo.examen_fisico', ('nucleo.diagnosticos', {'obligatoria': True}), 'nucleo.plan',
               'nucleo.prescripcion']

PLANTILLAS = [
    PlantillaDef('Primera consulta pediátrica', PRIMERA, predeterminada=True,
                 descripcion='Ficha pediátrica completa, antropometría con percentiles OMS, hábitos y desarrollo.'),
    PlantillaDef('Control de niño sano', CONTROL_SANO, descripcion='Crecimiento, hábitos y desarrollo.'),
    PlantillaDef('Consulta por enfermedad', ENFERMEDAD),
    PlantillaDef('Seguimiento', SEGUIMIENTO),
]

registro.registrar(EspecialidadDef(
    codigo='pediatria', nombre='Pediatría', modulo='apps.especialidades.pediatria', icono='bi-balloon-heart',
    color='#2AACA8', orden=21, secciones=[*FICHA, *CONSULTA], calculos=CALCULOS, plantillas=PLANTILLAS,
))


def _sincronizar_medicion(consulta, datos):
    from .servicios import sincronizar_medicion
    sincronizar_medicion(consulta, datos)


registro.registrar_al_guardar('ped.antropometria', _sincronizar_medicion)
