"""Copia al catálogo las especialidades y secciones de los módulos instalados (también corre tras `migrate`)."""
from django.core.management.base import BaseCommand

from apps.clinica import registro
from apps.clinica.servicios import sincronizar_catalogo


class Command(BaseCommand):
    help = 'Sincroniza especialidades y secciones clínicas desde los módulos instalados.'

    def handle(self, *args, **opciones):
        sincronizar_catalogo()
        self.stdout.write(self.style.SUCCESS(
            f'{len(registro.especialidades())} especialidades y {len(registro.secciones())} secciones sincronizadas.'))
