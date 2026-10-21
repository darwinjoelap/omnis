"""
Plantillas de historia: el médico compone su historia eligiendo secciones del catálogo (ADR-007).
- profesional vacío = plantilla de la clínica (la ven todos los profesionales de esa especialidad).
- ajustes por sección: {"ocultos": [...], "etiquetas": {...}, "por_defecto": {...}, "requeridos": [...]}
"""
from django.db import models

from apps.core.tenancy import Auditable, TenantModel


class PlantillaHistoria(TenantModel, Auditable):
    nombre = models.CharField('Nombre', max_length=100)
    descripcion = models.CharField('Descripción', max_length=250, blank=True)
    especialidad = models.ForeignKey('plataforma.Especialidad', on_delete=models.PROTECT, related_name='+',
                                     verbose_name='Especialidad')
    profesional = models.ForeignKey('equipo.PerfilProfesional', on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='plantillas', verbose_name='Profesional',
                                    help_text='Vacío = plantilla de la clínica.')
    es_predeterminada = models.BooleanField('Predeterminada', default=False)
    activa = models.BooleanField('Activa', default=True)
    origen = models.CharField('Origen', max_length=120, blank=True, editable=False,
                              help_text='Plantilla inicial del módulo de la que se copió.')

    class Meta:
        verbose_name = 'Plantilla de historia'
        verbose_name_plural = 'Plantillas de historia'
        ordering = ['especialidad__nombre', '-es_predeterminada', 'nombre']

    def __str__(self):
        return self.nombre

    @property
    def es_de_clinica(self):
        return self.profesional_id is None


class PlantillaSeccion(TenantModel):
    plantilla = models.ForeignKey(PlantillaHistoria, on_delete=models.CASCADE, related_name='items')
    seccion = models.ForeignKey('clinica.SeccionClinica', on_delete=models.PROTECT, related_name='+')
    orden = models.PositiveSmallIntegerField('Orden', default=0)
    obligatoria = models.BooleanField('Obligatoria', default=False)
    colapsada = models.BooleanField('Colapsada al abrir', default=False)
    ajustes = models.JSONField('Ajustes', default=dict, blank=True)

    class Meta:
        verbose_name = 'Sección de plantilla'
        verbose_name_plural = 'Secciones de plantilla'
        ordering = ['plantilla', 'orden', 'id']
        constraints = [models.UniqueConstraint(fields=['plantilla', 'seccion'], name='plantilla_seccion_unica')]

    def __str__(self):
        return f'{self.plantilla} · {self.seccion}'
