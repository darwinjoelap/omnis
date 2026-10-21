"""Valida los esquemas de todas las secciones registradas y de las personalizadas guardadas."""
from django.core.management.base import BaseCommand, CommandError

from apps.clinica import registro
from apps.clinica.esquemas import validar_esquema
from apps.clinica.models import SeccionClinica


class Command(BaseCommand):
    help = 'Valida los esquemas de las secciones clínicas.'

    def handle(self, *args, **opciones):
        malos = 0
        for codigo, s in registro.secciones().items():
            for e in validar_esquema(s.esquema):
                malos += 1
                self.stderr.write(f'{codigo}: {e}')
        for s in SeccionClinica.objects.filter(tipo=SeccionClinica.Tipo.PERSONALIZADA):
            for e in validar_esquema(s.esquema, permitir_calculado=False):
                malos += 1
                self.stderr.write(f'{s.tenant} · {s.codigo}: {e}')
        if malos:
            raise CommandError(f'{malos} problema(s) en los esquemas.')
        self.stdout.write(self.style.SUCCESS('Todos los esquemas son válidos.'))
