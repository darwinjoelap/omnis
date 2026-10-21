"""
Multi-tenant: tenant activo por request y modelo base con aislamiento (patrón de Ordo, ADR-003).

Regla de oro: todo modelo de un tenant hereda de TenantModel.
  - `Modelo.objects` solo ve filas del tenant activo.
  - Sin tenant activo, `Modelo.objects` no devuelve NADA (falla cerrado).
  - `Modelo.todos` ve todo: solo para comandos internos, admin y migraciones.

También guarda el usuario del request para llenar `creado_por` sin pasarlo a mano.
"""
from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

_tenant_actual = ContextVar('tenant_actual', default=None)
_usuario_actual = ContextVar('usuario_actual', default=None)


def tenant_actual():
    """Tenant activo del request/contexto en curso (o None)."""
    return _tenant_actual.get()


def fijar_tenant(tenant):
    """Fija el tenant activo y devuelve el token para restaurarlo."""
    return _tenant_actual.set(tenant)


def restaurar_tenant(token):
    _tenant_actual.reset(token)


def usuario_actual():
    return _usuario_actual.get()


def fijar_usuario(usuario):
    return _usuario_actual.set(usuario)


def restaurar_usuario(token):
    _usuario_actual.reset(token)


@contextmanager
def usando_tenant(tenant, usuario=None):
    """Para comandos y tests: `with usando_tenant(t): Paciente.objects...`"""
    token = fijar_tenant(tenant)
    token_u = fijar_usuario(usuario) if usuario is not None else None
    try:
        yield tenant
    finally:
        if token_u is not None:
            restaurar_usuario(token_u)
        restaurar_tenant(token)


class TenantQuerySet(models.QuerySet):
    pass


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = tenant_actual()
        if tenant is None:
            return qs.none()
        return qs.filter(tenant=tenant)


class TenantModel(models.Model):
    tenant = models.ForeignKey(
        'plataforma.Tenant', on_delete=models.PROTECT, editable=False,
        related_name='+', verbose_name='Tenant',
    )

    objects = TenantManager()
    todos = models.Manager()

    class Meta:
        abstract = True
        base_manager_name = 'todos'

    def save(self, *args, **kwargs):
        if self.tenant_id is None:
            tenant = tenant_actual()
            if tenant is None:
                raise ImproperlyConfigured(
                    f'{type(self).__name__} necesita tenant: guarda dentro de un request '
                    'con tenant activo o usa `usando_tenant(...)`.'
                )
            self.tenant = tenant
        super().save(*args, **kwargs)


class Auditable(models.Model):
    """Fechas y autor. `creado_por` se llena solo con el usuario del request (o de `usando_tenant`)."""
    creado_en = models.DateTimeField('Creado', auto_now_add=True)
    actualizado_en = models.DateTimeField('Actualizado', auto_now=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   editable=False, related_name='+', verbose_name='Creado por')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk is None and self.creado_por_id is None:
            usuario = usuario_actual()
            if usuario is not None and getattr(usuario, 'is_authenticated', False):
                self.creado_por = usuario
        super().save(*args, **kwargs)
