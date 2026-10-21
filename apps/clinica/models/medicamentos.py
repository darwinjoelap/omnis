"""Glosario de medicamentos del médico con calculadora de dosis (de Pediae, para todas las especialidades)."""
from django.db import models

from apps.core.tenancy import Auditable, TenantModel


class Medicamento(TenantModel, Auditable):
    class Modo(models.TextChoices):
        PESO = 'PESO', 'Por peso (por kg)'
        FIJA = 'FIJA', 'Dosis fija'
        EDAD = 'EDAD', 'Por rango de edad'

    UNIDADES_KG = [('mg', 'mg/kg'), ('mcg', 'mcg/kg'), ('UI', 'UI/kg'), ('mL', 'mL/kg'), ('gotas', 'gotas/kg'),
                   ('tableta', 'tabletas/kg'), ('sobre', 'sobres/kg'), ('puff', 'puffs/kg')]
    UNIDADES_RESULTADO = [('mL', 'mL'), ('tableta', 'tableta(s)'), ('gotas', 'gotas'), ('mg', 'mg'), ('UI', 'UI'),
                          ('sobre', 'sobre(s)'), ('puff', 'puff(s)'), ('aplicacion', 'aplicación(es)')]
    DIRECTAS = {'mL', 'gotas', 'tableta', 'sobre', 'puff'}      # unidad/kg que ya es la cantidad final

    profesional = models.ForeignKey('equipo.PerfilProfesional', on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='medicamentos', help_text='Vacío = del consultorio (todos lo usan).')
    nombre = models.CharField('Nombre', max_length=150)
    presentacion = models.CharField('Presentación', max_length=120, blank=True,
                                    help_text='Ej.: susp. 250 mg/5 mL · tab. 500 mg · gotas 100 mg/mL')
    modo = models.CharField('Cálculo', max_length=4, choices=Modo.choices, default=Modo.PESO)
    # Por peso
    unidad_kg = models.CharField('Unidad por kg', max_length=8, choices=UNIDADES_KG, default='mg')
    dosis_kg_min = models.DecimalField('Dosis por kg (mínima o única)', max_digits=8, decimal_places=3, null=True,
                                       blank=True)
    dosis_kg_max = models.DecimalField('Dosis por kg (máxima)', max_digits=8, decimal_places=3, null=True,
                                       blank=True, help_text='Solo si hay rango (leve / severo).')
    concentracion_mg = models.DecimalField('Concentración (mg, mcg o UI)', max_digits=9, decimal_places=3, null=True,
                                           blank=True, help_text='Cantidad de principio activo en el volumen base.')
    volumen_ml = models.DecimalField('Volumen base (mL)', max_digits=7, decimal_places=2, null=True, blank=True,
                                     help_text='Ej.: 5 para «250 mg/5 mL». Vacío para tabletas.')
    unidad_resultado = models.CharField('Se administra en', max_length=10, choices=UNIDADES_RESULTADO, blank=True)
    dosis_max = models.DecimalField('Tope por dosis (mg)', max_digits=9, decimal_places=2, null=True, blank=True,
                                    help_text='Dosis de adulto: la calculada nunca la supera.')
    # Fija
    dosis_fija = models.CharField('Dosis fija', max_length=60, blank=True, help_text='Ej.: 2 puffs, 1 sobre.')
    # Por edad: [{"min": meses, "max": meses, "dosis": "texto"}]
    rangos_edad = models.JSONField('Dosis por edad', default=list, blank=True)
    frecuencia_horas = models.PositiveSmallIntegerField('Cada (horas)', null=True, blank=True)
    duracion_dias = models.PositiveSmallIntegerField('Durante (días)', null=True, blank=True)
    indicaciones = models.TextField(
        'Plantilla de indicaciones', blank=True,
        help_text='Variables: {{DOSIS}} {{DOSIS_MG}} {{FRECUENCIA}} {{DURACION}} {{PRESENTACION}} {{NOMBRE}} {{PESO}}')
    # Alertas
    edad_min_meses = models.PositiveSmallIntegerField('Edad mínima (meses)', null=True, blank=True)
    edad_max_meses = models.PositiveSmallIntegerField('Edad máxima (meses)', null=True, blank=True)
    peso_min_kg = models.DecimalField('Peso mínimo (kg)', max_digits=6, decimal_places=2, null=True, blank=True)
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Medicamento del glosario'
        verbose_name_plural = 'Glosario de medicamentos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} {self.presentacion}'.strip()
