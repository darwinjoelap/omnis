"""
Carga o actualiza el catálogo CIE-10 desde un CSV «codigo;descripcion» (UTF-8, con encabezado).
Sin archivo, carga la lista de diagnósticos frecuentes incluida en apps/clinica/datos/cie10_frecuentes.csv.

    python manage.py importar_cie10 [archivo.csv]
"""
import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.clinica.models import Cie10

POR_DEFECTO = Path(__file__).resolve().parents[2] / 'datos' / 'cie10_frecuentes.csv'


def importar(ruta):
    nuevos = actualizados = 0
    with open(ruta, encoding='utf-8-sig', newline='') as f:
        muestra = f.read(2048)
        f.seek(0)
        lector = csv.DictReader(f, delimiter=';' if ';' in muestra else ',')
        for fila in lector:
            codigo = (fila.get('codigo') or '').strip().upper()
            descripcion = (fila.get('descripcion') or '').strip()
            if not codigo or not descripcion:
                continue
            obj = Cie10.objects.filter(codigo=codigo).first()
            if obj is None:
                Cie10(codigo=codigo, descripcion=descripcion[:300]).save()
                nuevos += 1
            elif obj.descripcion != descripcion[:300]:
                obj.descripcion = descripcion[:300]
                obj.save()
                actualizados += 1
    return nuevos, actualizados


class Command(BaseCommand):
    help = 'Importa el catálogo CIE-10 desde un CSV (codigo;descripcion).'

    def add_arguments(self, parser):
        parser.add_argument('archivo', nargs='?', default=str(POR_DEFECTO))

    def handle(self, archivo, **opciones):
        if not Path(archivo).exists():
            raise CommandError(f'No existe {archivo}')
        nuevos, actualizados = importar(archivo)
        self.stdout.write(self.style.SUCCESS(f'CIE-10: {nuevos} nuevos, {actualizados} actualizados.'))
