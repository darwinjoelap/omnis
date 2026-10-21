"""
Alta rápida de un consultorio con su Titular.

    python manage.py crear_tenant "Consultorio Dra. Pérez" dperez --especialidad pediatria --password clave
"""
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.plataforma import servicios
from apps.plataforma.models import Especialidad


class Command(BaseCommand):
    help = 'Crea un tenant (consultorio o clínica) y su usuario Titular.'

    def add_arguments(self, parser):
        parser.add_argument('nombre')
        parser.add_argument('usuario_titular')
        parser.add_argument('--especialidad', help='Código de la especialidad del Titular (si atiende pacientes).')
        parser.add_argument('--titulo', default='Dr.', help='Dr., Dra., Lic. (por defecto Dr.)')
        parser.add_argument('--password', help='Clave del Titular (si no se indica, se genera una temporal).')
        parser.add_argument('--enlace', help='Enlace (/enlace/). Por defecto se genera del nombre.')

    def handle(self, nombre, usuario_titular, especialidad=None, titulo='Dr.', password=None, enlace=None, **op):
        try:
            slug = servicios.validar_enlace(enlace or slugify(nombre)[:40])
        except ValidationError as e:
            raise CommandError(e.messages[0])
        esp = None
        if especialidad:
            esp = Especialidad.objects.filter(codigo=especialidad).first()
            if esp is None:
                raise CommandError(f'No existe la especialidad "{especialidad}". '
                                   'Corre `python manage.py sincronizar_especialidades`.')
        tenant, titular, clave = servicios.crear_tenant({
            'nombre': nombre, 'slug': slug, 'usuario_titular': usuario_titular,
            'nombre_titular': usuario_titular.capitalize(), 'apellido_titular': '',
            'titular_es_profesional': esp is not None, 'especialidad_titular': esp, 'titulo_titular': titulo,
            'especialidades': [esp] if esp else []})
        if password:
            titular.set_password(password)
            titular.debe_cambiar_clave = False
            titular.save(update_fields=['password', 'debe_cambiar_clave'])
            self.stdout.write(f'Usuario creado: {titular.username}')
        else:
            self.stdout.write(f'Usuario creado: {titular.username} · clave temporal: {clave}')
        self.stdout.write(self.style.SUCCESS(f'Consultorio "{tenant}" creado. Enlace: /{tenant.slug}/'))
