"""Catálogo inicial: esquema de vacunas que usa Pediae (migración 0017) y las 4 pesquisas estándar (0018)."""
from django.db import migrations

# (nombre, enfermedad, dosis, edad_meses, edad_max_meses, orden, grupo)
VACUNAS = [
    # ── Recién nacido (0-28 días) ──────────────────────────────────────────────
    ('BCG',         'Tuberculosis',  1, 0, 2,  10, 'Recién nacido (0-28 días)'),
    ('Hepatitis B', 'Hepatitis B',   1, 0, 1,  20, 'Recién nacido (0-28 días)'),

    # ── 2 meses ────────────────────────────────────────────────────────────────
    ('Pentavalente / Hexavalente', 'Difteria, Tétanos, Tos ferina, Hib, HepB',  1, 2, 4, 30, '2 meses'),
    ('Polio (VPI / bVPO)',         'Poliomielitis',                              1, 2, 4, 40, '2 meses'),
    ('Neumococo PCV13',            'Enfermedad neumocócica',                     1, 2, 4, 50, '2 meses'),
    ('Rotavirus',                  'Gastroenteritis por rotavirus',               1, 2, 3, 60, '2 meses'),

    # ── 4 meses ────────────────────────────────────────────────────────────────
    ('Pentavalente / Hexavalente', 'Difteria, Tétanos, Tos ferina, Hib, HepB',  2, 4, 6, 30, '4 meses'),
    ('Polio (VPI / bVPO)',         'Poliomielitis',                              2, 4, 6, 40, '4 meses'),
    ('Neumococo PCV13',            'Enfermedad neumocócica',                     2, 4, 6, 50, '4 meses'),
    ('Rotavirus',                  'Gastroenteritis por rotavirus',               2, 4, 6, 60, '4 meses'),

    # ── 6 meses ────────────────────────────────────────────────────────────────
    ('Pentavalente / Hexavalente', 'Difteria, Tétanos, Tos ferina, Hib, HepB',  3, 6, 9, 30, '6 meses'),
    ('Polio (VPI / bVPO)',         'Poliomielitis',                              3, 6, 9, 40, '6 meses'),
    ('Neumococo PCV13',            'Enfermedad neumocócica',                     3, 6, 9, 50, '6 meses'),
    ('Rotavirus',                  'Gastroenteritis por rotavirus',               3, 6, 8, 60, '6 meses'),
    ('Influenza',                  'Influenza estacional',                        1, 6, 8, 70, '6 meses'),

    # ── 7 meses ────────────────────────────────────────────────────────────────
    ('Influenza',                  'Influenza estacional',                        2, 7, 9, 70, '7 meses'),

    # ── 9 meses ────────────────────────────────────────────────────────────────
    ('Meningococo conjugada',      'Enfermedad meningocócica',                   1, 9, 12, 80, '9 meses'),

    # ── 12 meses ───────────────────────────────────────────────────────────────
    ('Triple Viral (SRP)',         'Sarampión, Rubéola, Parotiditis',             1, 12, 15,   90, '12 meses'),
    ('Fiebre Amarilla',            'Fiebre Amarilla',                             1, 12, None, 100, '12 meses'),
    ('Hepatitis A',                'Hepatitis A',                                 1, 12, 18,  110, '12 meses'),
    ('Varicela',                   'Varicela',                                    1, 12, 15,  120, '12 meses'),
    ('Meningococo conjugada',      'Enfermedad meningocócica',                    2, 12, 15,   80, '12 meses'),

    # ── 18 meses ───────────────────────────────────────────────────────────────
    ('Pentavalente / DPT',         'Difteria, Tétanos, Tos ferina, Hib (1.er refuerzo)', 4, 18, 24, 30, '18 meses'),
    ('Polio (VPI / bVPO)',         'Poliomielitis (1.er refuerzo)',               4, 18, 24,  40, '18 meses'),
    ('Triple Viral (SRP)',         'Sarampión, Rubéola, Parotiditis',             2, 18, 24,  90, '18 meses'),
    ('Hepatitis A',                'Hepatitis A (6 m después de la 1.ª dosis)',   2, 18, 30, 110, '18 meses'),
    ('Neumococo PCV13',            'Enfermedad neumocócica (refuerzo)',            4, 18, 24,   50, '18 meses'),

    # ── 4 a 6 años ─────────────────────────────────────────────────────────────
    ('DPT',                        'Difteria, Tétanos, Tos ferina (2.º refuerzo)', 5, 48, 72, 130, '4 a 6 años'),
    ('Polio (VPI / bVPO)',         'Poliomielitis (2.º refuerzo)',                5, 48, 72,  40, '4 a 6 años'),
    ('Triple Viral (SRP)',         'Sarampión, Rubéola, Parotiditis (refuerzo)',  3, 48, 72,  90, '4 a 6 años'),
    ('Varicela',                   'Varicela',                                    2, 48, 72, 120, '4 a 6 años'),

    # ── Adolescentes (9-18 años) ────────────────────────────────────────────────
    ('VPH',              'Virus del Papiloma Humano (esquema 2 dosis: 9-14 a.)',  1, 108, 216, 140, 'Adolescentes (9-18 años)'),
    ('Tdap',             'Difteria, Tétanos, Tos ferina acelular (refuerzo)',     1, 132, 216, 150, 'Adolescentes (9-18 años)'),
    ('Meningococo MCV4', 'Enfermedad meningocócica (MenACWY)',                    1, 132, 216, 160, 'Adolescentes (9-18 años)'),

    # ── Vacunación anual ────────────────────────────────────────────────────────
    ('Influenza (anual)', 'Influenza estacional (dosis anual desde los 6 m)',     1, 6, None,  75, 'Vacunación anual'),
]

PESQUISAS = [
    ('Eco de cadera', 'Ecografía de caderas (displasia del desarrollo)', 10),
    ('Eco renal / abdominal', 'Ecografía renal y abdominal', 20),
    ('Oftalmológica', 'Evaluación oftalmológica pediátrica', 30),
    ('Audiología', 'Evaluación audiológica / otoemisiones acústicas', 40),
]


def cargar(apps, schema_editor):
    Vacuna = apps.get_model('esp_pediatria', 'Vacuna')
    Pesquisa = apps.get_model('esp_pediatria', 'Pesquisa')
    for nombre, enfermedad, dosis, edad, edad_max, orden, grupo in VACUNAS:
        Vacuna.objects.get_or_create(tenant=None, nombre=nombre, dosis=dosis, edad_meses=edad, defaults={
            'enfermedad': enfermedad, 'edad_max_meses': edad_max, 'orden': orden, 'grupo': grupo,
            'anual': grupo == 'Vacunación anual'})
    for nombre, descripcion, orden in PESQUISAS:
        Pesquisa.objects.get_or_create(tenant=None, nombre=nombre, defaults={'descripcion': descripcion,
                                                                            'orden': orden})


class Migration(migrations.Migration):
    dependencies = [('esp_pediatria', '0002_vacunas_pesquisas')]
    operations = [migrations.RunPython(cargar, migrations.RunPython.noop)]
