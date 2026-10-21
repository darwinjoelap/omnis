"""Fase 13.3: percentiles OMS (tablas oficiales). Referencia: −2 DE, mediana y +2 DE publicados por la OMS."""
from datetime import date

from django.test import SimpleTestCase

from apps.especialidades.pediatria import oms

# (indicador, sexo, mes, −2 DE, mediana, +2 DE) — WHO Child Growth Standards 2006, redondeados a 0,1
REFERENCIA = [
    ('peso', 'M', 0, 2.5, 3.3, 4.4),
    ('peso', 'M', 6, 6.4, 7.9, 9.8),
    ('peso', 'M', 12, 7.7, 9.6, 12.0),
    ('peso', 'M', 24, 9.7, 12.2, 15.3),
    ('peso', 'M', 36, 11.3, 14.3, 18.3),
    ('peso', 'M', 60, 14.1, 18.3, 24.2),
    ('peso', 'F', 0, 2.4, 3.2, 4.2),
    ('peso', 'F', 6, 5.7, 7.3, 9.3),
    ('peso', 'F', 12, 7.0, 8.9, 11.5),
    ('peso', 'F', 24, 9.0, 11.5, 14.8),
    ('peso', 'F', 36, 10.8, 13.9, 18.1),
    ('peso', 'F', 60, 13.7, 18.2, 24.9),
    ('talla', 'M', 0, 46.1, 49.9, 53.7),
    ('talla', 'M', 9, 67.5, 72.0, 76.5),
    ('talla', 'M', 18, 76.9, 82.3, 87.7),
    ('talla', 'F', 0, 45.4, 49.1, 52.9),
    ('talla', 'F', 9, 65.3, 70.1, 75.0),
    ('talla', 'F', 18, 74.9, 80.7, 86.5),
    ('talla', 'M', 30, 85.1, 91.9, 98.7),
    ('talla', 'M', 48, 94.9, 103.3, 111.7),
    ('talla', 'M', 60, 100.7, 110.0, 119.2),
    ('talla', 'F', 30, 83.6, 90.7, 97.7),
    ('talla', 'F', 48, 94.1, 102.7, 111.3),
    ('talla', 'F', 60, 99.9, 109.4, 118.9),
    ('pc', 'M', 0, 31.9, 34.5, 37.0),
    ('pc', 'M', 6, 40.9, 43.3, 45.8),
    ('pc', 'M', 12, 43.5, 46.1, 48.6),
    ('pc', 'M', 24, 45.5, 48.3, 51.0),
    ('pc', 'F', 0, 31.5, 33.9, 36.2),
    ('pc', 'F', 6, 39.6, 42.2, 44.8),
    ('pc', 'F', 12, 42.2, 44.9, 47.6),
    ('pc', 'F', 24, 44.4, 47.2, 50.0),
    ('imc', 'M', 36, 13.4, 15.6, 18.4),
    ('imc', 'M', 60, 12.9, 15.2, 18.3),
    ('imc', 'F', 36, 13.1, 15.4, 18.4),
    ('imc', 'F', 60, 12.7, 15.3, 18.8),
]


class PercentilesOMSTest(SimpleTestCase):
    def test_valores_publicados(self):
        for ind, sexo, mes, menos2, mediana, mas2 in REFERENCIA:
            with self.subTest(ind=ind, sexo=sexo, mes=mes):
                self.assertAlmostEqual(oms.zscore(ind, sexo, mes, mediana), 0, delta=0.12)
                self.assertAlmostEqual(oms.zscore(ind, sexo, mes, menos2), -2, delta=0.12)
                self.assertAlmostEqual(oms.zscore(ind, sexo, mes, mas2), 2, delta=0.12)

    def test_caso_que_pediae_clasificaba_mal(self):
        # niño de 24 meses y 10,0 kg: Pediae daba P1,6 (desnutrición severa); OMS da ≈P4,4 (desnutrición)
        p = oms.percentil(oms.zscore('peso', 'M', 24, 10.0))
        self.assertAlmostEqual(p, 4.4, delta=0.2)
        self.assertEqual(oms.clasificar_peso_edad(p), 'Desnutrición (p3–p10)')

    def test_z_restringido_mas_alla_de_3(self):
        L, M, S = oms.lms('peso', 'M', 12)
        sd3, sd2 = oms.valor_para_z(L, M, S, 3), oms.valor_para_z(L, M, S, 2)
        self.assertAlmostEqual(oms.zscore('peso', 'M', 12, sd3 + (sd3 - sd2)), 4, places=6)
        self.assertAlmostEqual(oms.zscore('talla', 'M', 12, oms.valor_para_z(*oms.lms('talla', 'M', 12), 4)), 4,
                               places=6)

    def test_continuidad_entre_2006_y_2007(self):
        for ind in ('talla', 'imc'):
            for sexo in 'MF':
                m60, m61 = oms.lms(ind, sexo, 60)[1], oms.lms(ind, sexo, 61)[1]
                self.assertLess(abs(m61 - m60) / m60, 0.01, (ind, sexo))

    def test_rangos_por_indicador(self):
        self.assertEqual(oms.rango('pc', 'F'), (0, 60))
        self.assertEqual(oms.rango('peso', 'F'), (0, 120))
        self.assertEqual(oms.rango('imc', 'M'), (0, 228))
        self.assertIsNone(oms.zscore('pc', 'M', 72, 50))       # PC solo hasta 5 años
        self.assertIsNone(oms.zscore('peso', 'M', 150, 40))    # peso/edad solo hasta 10 años

    def test_interpolacion_entre_meses(self):
        L0, M0, _ = oms.lms('talla', 'F', 10)
        L1, M1, _ = oms.lms('talla', 'F', 11)
        self.assertAlmostEqual(oms.lms('talla', 'F', 10.5)[1], (M0 + M1) / 2)

    def test_evaluar_y_clasificaciones(self):
        ev = oms.evaluar(sexo='F', nacimiento=date(2023, 1, 10), fecha=date(2026, 1, 10), peso=14.0, talla=95.0,
                         pc=48.5)
        self.assertAlmostEqual(ev['edad_meses'], 36, delta=0.1)
        self.assertGreater(ev['peso']['percentil'], 40)
        self.assertEqual(ev['clasificacion_peso_edad'], 'Eutrófico (p15–p85)')
        self.assertEqual(ev['clasificacion_imc'], 'Normal')
        self.assertEqual(ev['clasificacion_talla'], 'Talla adecuada')
        self.assertIn('error', oms.evaluar(sexo='', nacimiento=date(2023, 1, 1), fecha=date(2026, 1, 1), peso=12))
        self.assertIn('error', oms.evaluar(sexo='M', nacimiento=None, fecha=date(2026, 1, 1), peso=12))

    def test_clasificacion_imc_cortes(self):
        self.assertEqual(oms.clasificar_imc(2.5, 30), 'Sobrepeso')
        self.assertEqual(oms.clasificar_imc(2.5, 100), 'Obesidad')
        self.assertEqual(oms.clasificar_imc(-2.5, 30), 'Emaciación')
        self.assertEqual(oms.clasificar_imc(-2.5, 100), 'Delgadez')
        self.assertEqual(oms.clasificar_peso_edad(3), 'Desnutrición (p3–p10)')
        self.assertEqual(oms.clasificar_peso_edad(85), 'Eutrófico (p15–p85)')
        self.assertEqual(oms.clasificar_peso_edad(97.1), 'Obesidad (>p97)')

    def test_curvas(self):
        c = oms.curvas('peso', 'M', 24)
        self.assertEqual(len(c[50]), 25)
        self.assertAlmostEqual(c[50][12][1], 9.65, delta=0.01)
        self.assertLess(c[3][12][1], c[97][12][1])
