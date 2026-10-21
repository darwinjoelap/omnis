"""Validación y copias livianas de imágenes para PDF (logo, firma, sello, membrete). De Ordo."""
from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

MAX_BYTES = 2 * 1024 * 1024        # 2 MB
FORMATOS = {'PNG', 'JPEG'}
ANCHO_PDF = 600                     # px de la copia para PDF


def validar_imagen(archivo, etiqueta='La imagen'):
    """PNG o JPG de hasta 2 MB. SVG/GIF/WebP no: ReportLab no los dibuja bien."""
    if archivo.size > MAX_BYTES:
        raise ValidationError(f'{etiqueta} pesa {archivo.size / 1024 / 1024:.1f} MB; el máximo es 2 MB.')
    try:
        archivo.seek(0)
        with Image.open(archivo) as img:
            formato = img.format
            img.verify()
    except (UnidentifiedImageError, OSError):
        raise ValidationError(f'{etiqueta} no es una imagen válida.')
    finally:
        archivo.seek(0)
    if formato not in FORMATOS:
        raise ValidationError(f'{etiqueta} debe ser PNG o JPG (recibido: {formato or "desconocido"}).')


def copia_para_pdf(campo_origen, campo_destino):
    """Genera en `campo_destino` un PNG de máx. 600 px desde `campo_origen` (o lo borra si no hay origen)."""
    if not campo_origen:
        if campo_destino:
            campo_destino.delete(save=False)
        return
    campo_origen.open('rb')
    try:
        contenido = campo_origen.read()
    finally:
        campo_origen.close()
    with Image.open(BytesIO(contenido)) as img:
        img.load()
        img = img.convert('RGBA')
        if img.width > ANCHO_PDF:
            img = img.resize((ANCHO_PDF, round(img.height * ANCHO_PDF / img.width)), Image.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
    nombre = f'{Path(campo_origen.name).stem}-pdf.png'
    if campo_destino:
        campo_destino.delete(save=False)
    campo_destino.save(nombre, ContentFile(buffer.getvalue()), save=False)
