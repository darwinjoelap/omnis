"""
Panel de plataforma (solo superusuarios): alta y control de tenants (consultorios y clínicas).
El enlace de cada tenant es su slug: https://<dominio>/<slug>/
"""
import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.fechas import sumar_meses
from apps.core.permisos import Rol

from .models import Suscripcion, Tenant

# Primeros segmentos de URL que usa Omnis: no pueden ser enlaces de un tenant
RESERVADOS = {
    'admin', 'api', 'cuenta', 'equipo', 'configuracion', 'tasa', 'servicios', 'cobros', 'pacientes', 'agenda',
    'consultas', 'clinica', 'historia', 'plantillas', 'secciones', 'documentos', 'reportes', 'plataforma',
    'salud', 'offline', 'instalar', 'visor', 'static', 'media', 'favicon.ico', 'manifest.webmanifest', 'sw.js',
    '__debug__', 'omnis', 'www', 'app', 'soporte', 'ayuda', 'login', 'entrar', 'dictado', 'cie10', 'adjuntos', 'citas',
}
PATRON = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


def validar_enlace(slug, excluir_pk=None):
    slug = (slug or '').strip().lower()
    if not 3 <= len(slug) <= 40 or not PATRON.match(slug):
        raise ValidationError('Usa de 3 a 40 letras minúsculas, números o guiones (ej. dra-perez).')
    if slug in RESERVADOS:
        raise ValidationError(f'"{slug}" está reservado por Omnis. Elige otro.')
    if Tenant.objects.filter(slug=slug).exclude(pk=excluir_pk).exists():
        raise ValidationError('Ese enlace ya lo usa otro consultorio.')
    return slug


def habilitar_especialidades(tenant, especialidades):
    """Habilita especialidades y copia al tenant las plantillas iniciales de cada módulo."""
    from apps.clinica.servicios import asegurar_plantillas_especialidad
    from apps.core.tenancy import usando_tenant
    tenant.especialidades.add(*especialidades)
    with usando_tenant(tenant):
        for especialidad in especialidades:
            asegurar_plantillas_especialidad(especialidad)


@transaction.atomic
def crear_tenant(datos):
    """
    datos: nombre, slug, plan, activo_hasta, notas, especialidades (lista),
           usuario_titular, nombre_titular, apellido_titular, email_titular,
           titular_es_profesional (bool), especialidad_titular, titulo_titular.
    Devuelve (tenant, titular, clave_temporal). El Titular es un usuario propio del tenant.
    """
    from apps.equipo.models import Membresia
    from apps.equipo.servicios import clave_temporal, crear_perfil

    tenant = Tenant.objects.create(
        nombre=datos['nombre'], slug=datos['slug'], plan=datos.get('plan'),
        activo_hasta=datos.get('activo_hasta'), notas=datos.get('notas', ''))
    especialidades = list(datos.get('especialidades') or [])
    if datos.get('titular_es_profesional') and datos.get('especialidad_titular') \
            and datos['especialidad_titular'] not in especialidades:
        especialidades.append(datos['especialidad_titular'])
    habilitar_especialidades(tenant, especialidades)

    U = get_user_model()
    clave = clave_temporal()
    titular = U.objects.create_user(datos['usuario_titular'], clave, tenant_cuenta=tenant,
                                    email=datos.get('email_titular') or '',
                                    first_name=(datos.get('nombre_titular') or '').strip(),
                                    last_name=(datos.get('apellido_titular') or '').strip(), debe_cambiar_clave=True)
    m = Membresia.objects.create(usuario=titular, tenant=tenant, rol=Rol.TITULAR)
    if datos.get('titular_es_profesional') and datos.get('especialidad_titular'):
        crear_perfil(m, datos['especialidad_titular'], titulo=datos.get('titulo_titular') or 'Dr.')
    return tenant, titular, clave


@transaction.atomic
def actualizar_tenant(tenant, datos):
    for campo in ('nombre', 'slug', 'plan', 'estado', 'activo_hasta', 'limite_usuarios', 'limite_profesionales',
                  'notas'):
        if campo in datos:
            setattr(tenant, campo, datos[campo])
    tenant.save()
    if 'especialidades' in datos:
        nuevas = [e for e in datos['especialidades'] if not tenant.especialidades.filter(pk=e.pk).exists()]
        tenant.especialidades.set(datos['especialidades'])
        habilitar_especialidades(tenant, nuevas)
    if 'dictado_activo' in datos:
        config = tenant.configuracion
        config.dictado_activo = datos['dictado_activo']
        config.save(update_fields=['dictado_activo', 'actualizado_en'])
    return tenant


@transaction.atomic
def renovar(tenant, *, meses, monto_usd=0, referencia='', notas='', plan=None):
    """Registra una renovación: extiende `activo_hasta` desde el vencimiento (o desde hoy si ya venció)."""
    hoy = timezone.localdate()
    desde = tenant.activo_hasta + timedelta(days=1) if tenant.activo_hasta and tenant.activo_hasta >= hoy else hoy
    hasta = sumar_meses(desde, meses) - timedelta(days=1)
    plan = plan or tenant.plan
    Suscripcion.objects.create(tenant=tenant, plan=plan, desde=desde, hasta=hasta, monto_usd=monto_usd,
                               referencia=referencia, notas=notas)
    tenant.activo_hasta = hasta
    tenant.plan = plan
    if tenant.estado != Tenant.Estado.ACTIVO:
        tenant.estado = Tenant.Estado.ACTIVO
    tenant.save(update_fields=['activo_hasta', 'plan', 'estado'])
    return tenant
