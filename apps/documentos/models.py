"""
Documentos emitidos (Fase 10). Cada PDF con número correlativo queda registrado: quién lo emitió, a quién,
desde qué consulta y con qué datos. El PDF se vuelve a generar a partir de `datos` (no se guardan archivos).
"""
from django.db import models

from apps.core.tenancy import Auditable, TenantModel


class DocumentoEmitido(TenantModel, Auditable):
    tipo = models.CharField('Tipo', max_length=40, db_index=True)        # código del registro: 'reposo', 'ped.lactancia'
    numero = models.CharField('Número', max_length=30)
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.PROTECT, related_name='documentos')
    consulta = models.ForeignKey('clinica.Consulta', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='documentos')
    profesional = models.ForeignKey('equipo.PerfilProfesional', on_delete=models.PROTECT, null=True, blank=True,
                                    related_name='documentos')
    fecha = models.DateField('Fecha')
    datos = models.JSONField('Datos', default=dict, blank=True)
    anulado = models.BooleanField('Anulado', default=False)
    motivo_anulacion = models.CharField('Motivo de anulación', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Documento emitido'
        verbose_name_plural = 'Documentos emitidos'
        ordering = ['-fecha', '-id']
        constraints = [models.UniqueConstraint(fields=['tenant', 'numero'], name='documento_numero_unico')]

    def __str__(self):
        return f'{self.numero} · {self.paciente}'

    @property
    def definicion(self):
        from .registro import documento
        return documento(self.tipo)
