"""Modelos propios de pediatría: datos que se grafican y se cuentan (guía de especialidades §3)."""
from django.db import models

from apps.core.tenancy import TenantModel


class MedicionCrecimiento(TenantModel):
    """
    Una medición antropométrica con su evaluación OMS. Se escribe al guardar la sección «Antropometría» de una
    consulta (una por consulta) y alimenta las curvas y los reportes de estado nutricional.
    """
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.CASCADE, related_name='mediciones')
    consulta = models.OneToOneField('clinica.Consulta', on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='medicion_crecimiento')
    fecha = models.DateField('Fecha', db_index=True)
    edad_meses = models.DecimalField('Edad (meses)', max_digits=6, decimal_places=2, null=True, blank=True)
    peso_kg = models.DecimalField('Peso (kg)', max_digits=6, decimal_places=3, null=True, blank=True)
    talla_cm = models.DecimalField('Talla (cm)', max_digits=5, decimal_places=1, null=True, blank=True)
    pc_cm = models.DecimalField('Perímetro cefálico (cm)', max_digits=4, decimal_places=1, null=True, blank=True)
    imc = models.DecimalField('IMC', max_digits=5, decimal_places=2, null=True, blank=True)
    z_peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    p_peso = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    z_talla = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    p_talla = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    z_pc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    p_pc = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    z_imc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    p_imc = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    estado_nutricional = models.CharField('Estado nutricional (peso/edad)', max_length=40, blank=True, db_index=True)
    clasificacion_imc = models.CharField('Clasificación OMS (IMC/edad)', max_length=40, blank=True)
    clasificacion_talla = models.CharField('Talla para la edad', max_length=40, blank=True)

    class Meta:
        verbose_name = 'Medición de crecimiento'
        verbose_name_plural = 'Mediciones de crecimiento'
        ordering = ['paciente', 'fecha']
        indexes = [models.Index(fields=['tenant', 'paciente', 'fecha'], name='medicion_paciente_fecha')]

    def __str__(self):
        return f'{self.paciente} · {self.fecha:%d/%m/%Y}'
