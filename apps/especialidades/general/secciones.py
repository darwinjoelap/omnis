"""Secciones de medicina general (reutilizables por cualquier especialidad del consultorio)."""
from apps.clinica.registro import SeccionDef

T = 'texto_largo'

HABITOS = SeccionDef('gen.habitos', 'Hábitos y estilo de vida', ambito='PACIENTE', orden=25, universal=True,
                     esquema={'campos': [
    {'clave': 'tabaco', 'tipo': 'opcion', 'etiqueta': 'Tabaco', 'ancho': 6,
     'opciones': [['NUNCA', 'Nunca'], ['EX', 'Exfumador'], ['ACTUAL', 'Fuma']]},
    {'clave': 'cigarrillos_dia', 'tipo': 'numero', 'etiqueta': 'Cigarrillos al día', 'decimales': 0, 'min': 0,
     'max': 200, 'ancho': 3, 'visible_si': {'campo': 'tabaco', 'en': ['ACTUAL', 'EX']}},
    {'clave': 'anios_fumando', 'tipo': 'numero', 'etiqueta': 'Años fumando', 'decimales': 0, 'min': 0, 'max': 90,
     'ancho': 3, 'visible_si': {'campo': 'tabaco', 'en': ['ACTUAL', 'EX']}},
    {'clave': 'alcohol', 'tipo': 'opcion', 'etiqueta': 'Alcohol', 'ancho': 6,
     'opciones': [['NO', 'No'], ['OCASIONAL', 'Ocasional'], ['FRECUENTE', 'Frecuente']]},
    {'clave': 'actividad_fisica', 'tipo': 'opcion', 'etiqueta': 'Actividad física', 'ancho': 6,
     'opciones': [['SEDENTARIO', 'Sedentario'], ['LEVE', '1–2 veces/semana'], ['REGULAR', '3 o más/semana']]},
    {'clave': 'cafe', 'tipo': 'si_no', 'etiqueta': 'Consume café', 'ancho': 3},
    {'clave': 'horas_sueno', 'tipo': 'numero', 'etiqueta': 'Horas de sueño', 'decimales': 0, 'min': 0, 'max': 24,
     'ancho': 3},
    {'clave': 'alimentacion', 'tipo': T, 'etiqueta': 'Alimentación', 'filas': 1},
    {'clave': 'otras_sustancias', 'tipo': 'texto', 'etiqueta': 'Otras sustancias', 'ancho': 12},
]})

REVISION_SISTEMAS = SeccionDef('gen.revision_sistemas', 'Revisión por sistemas', orden=35, universal=True,
                               esquema={'campos': [
    {'clave': 'sin_alteraciones', 'tipo': 'opciones', 'etiqueta': 'Niega síntomas en',
     'opciones': [['GENERAL', 'General'], ['CV', 'Cardiovascular'], ['RESP', 'Respiratorio'],
                  ['DIG', 'Digestivo'], ['GU', 'Genitourinario'], ['ME', 'Musculoesquelético'],
                  ['NEURO', 'Neurológico'], ['PIEL', 'Piel']]},
    {'clave': 'general', 'tipo': T, 'etiqueta': 'General (fiebre, peso, astenia)', 'filas': 1, 'ancho': 6},
    {'clave': 'cardiovascular', 'tipo': T, 'etiqueta': 'Cardiovascular', 'filas': 1, 'ancho': 6},
    {'clave': 'respiratorio', 'tipo': T, 'etiqueta': 'Respiratorio', 'filas': 1, 'ancho': 6},
    {'clave': 'digestivo', 'tipo': T, 'etiqueta': 'Digestivo', 'filas': 1, 'ancho': 6},
    {'clave': 'genitourinario', 'tipo': T, 'etiqueta': 'Genitourinario', 'filas': 1, 'ancho': 6},
    {'clave': 'musculoesqueletico', 'tipo': T, 'etiqueta': 'Musculoesquelético', 'filas': 1, 'ancho': 6},
    {'clave': 'neurologico', 'tipo': T, 'etiqueta': 'Neurológico', 'filas': 1, 'ancho': 6},
    {'clave': 'psiquico', 'tipo': T, 'etiqueta': 'Psíquico / sueño', 'filas': 1, 'ancho': 6},
]})
