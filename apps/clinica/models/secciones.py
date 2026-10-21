"""
Catálogo de secciones clínicas (ADR-007).

- NUCLEO y MODULO: del sistema (tenant vacío). Las crea `sincronizar_catalogo()` desde el registro.
- PERSONALIZADA: del tenant; las arma el médico/administrador desde la app.
Cada cambio de esquema sube `version` y guarda el esquema anterior en SeccionClinicaVersion, para poder leer
e imprimir registros viejos con su estructura original.
"""
from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.tenancy import tenant_actual


class SeccionQuerySet(models.QuerySet):
    def visibles(self, tenant=None):
        """Del sistema + personalizadas del tenant activo (nunca las de otro tenant)."""
        tenant = tenant or tenant_actual()
        filtro = Q(tenant__isnull=True)
        if tenant is not None:
            filtro |= Q(tenant=tenant)
        return self.filter(filtro)


class SeccionClinica(models.Model):
    class Tipo(models.TextChoices):
        NUCLEO = 'NUCLEO', 'Núcleo'
        MODULO = 'MODULO', 'De especialidad'
        PERSONALIZADA = 'PERSONALIZADA', 'Personalizada'

    class Ambito(models.TextChoices):
        CONSULTA = 'CONSULTA', 'En cada consulta'
        PACIENTE = 'PACIENTE', 'Del paciente (se conserva entre consultas)'

    tenant = models.ForeignKey('plataforma.Tenant', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='+', editable=False)
    codigo = models.CharField('Código', max_length=60)
    nombre = models.CharField('Nombre', max_length=120)
    descripcion = models.CharField('Descripción', max_length=250, blank=True)
    tipo = models.CharField('Tipo', max_length=14, choices=Tipo.choices)
    ambito = models.CharField('Ámbito', max_length=10, choices=Ambito.choices, default=Ambito.CONSULTA)
    especialidad = models.ForeignKey('plataforma.Especialidad', on_delete=models.PROTECT, null=True, blank=True,
                                     related_name='secciones', verbose_name='Especialidad')
    version = models.PositiveIntegerField('Versión', default=1)
    esquema = models.JSONField('Esquema', default=dict)
    activa = models.BooleanField('Activa', default=True)
    orden = models.PositiveSmallIntegerField('Orden', default=100)
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='+', editable=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    objects = SeccionQuerySet.as_manager()

    class Meta:
        verbose_name = 'Sección clínica'
        verbose_name_plural = 'Secciones clínicas'
        ordering = ['orden', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'codigo'], name='seccion_codigo_por_tenant'),
            models.UniqueConstraint(fields=['codigo'], condition=Q(tenant__isnull=True),
                                    name='seccion_codigo_sistema'),
        ]

    def __str__(self):
        return self.nombre

    @property
    def es_del_sistema(self):
        return self.tenant_id is None

    @property
    def campos(self):
        return self.esquema.get('campos', [])

    def esquema_version(self, version):
        """Esquema con el que se guardó un registro (el actual si es la misma versión)."""
        if version is None or version == self.version:
            return self.esquema
        anterior = self.versiones.filter(version=version).first()
        return anterior.esquema if anterior else self.esquema


class SeccionClinicaVersion(models.Model):
    seccion = models.ForeignKey(SeccionClinica, on_delete=models.CASCADE, related_name='versiones')
    version = models.PositiveIntegerField('Versión')
    esquema = models.JSONField('Esquema')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Versión de sección'
        verbose_name_plural = 'Versiones de secciones'
        ordering = ['seccion', '-version']
        constraints = [models.UniqueConstraint(fields=['seccion', 'version'], name='seccion_version_unica')]

    def __str__(self):
        return f'{self.seccion} v{self.version}'
