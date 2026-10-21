"""
Piezas comunes de los PDF (adaptado de Ordo). TODOS los documentos usan encabezado_tenant() y pie_tenant()
para que la Configuración del consultorio y el perfil del profesional se reflejen en récipes e informes.
"""
import re
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import HRFlowable, Image, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.platypus import Paragraph as _Paragraph

# Un «&» o «<» sueltos en datos escritos por el usuario rompen el marcado de ReportLab: se escapan aquí.
_AMP_SUELTO = re.compile(r'&(?!(?:[A-Za-z][A-Za-z0-9]*|#[0-9]+|#x[0-9A-Fa-f]+);)')
_MENOR_SUELTO = re.compile(r'<(?!/?(?:b|i|u|br|font|super|sub|strike|a|para|span|nobr)\b[^<>]*>)')


def texto_seguro(texto):
    return _MENOR_SUELTO.sub('&lt;', _AMP_SUELTO.sub('&amp;', str(texto)))


class Paragraph(_Paragraph):
    """Paragraph que tolera «&» y «<» en los datos. TODOS los PDF importan este."""

    def __init__(self, text, *args, **kwargs):
        super().__init__(texto_seguro(text), *args, **kwargs)


ESTILOS = getSampleStyleSheet()
ESTILO_NOMBRE = ParagraphStyle('nombre', parent=ESTILOS['Heading2'], spaceAfter=2, leading=17)
ESTILO_DATO = ParagraphStyle('dato', parent=ESTILOS['Normal'], fontSize=8.5, leading=11,
                             textColor=colors.HexColor('#4B5563'))
ESTILO_CELDA = ParagraphStyle('celda', parent=ESTILOS['Normal'], fontSize=9, leading=11.5)
ESTILO_DATO_DER = ParagraphStyle('dato_der', parent=ESTILO_DATO, alignment=TA_RIGHT)
ESTILO_CENTRO = ParagraphStyle('centro', parent=ESTILO_DATO, alignment=TA_CENTER)


def imagen_ajustada(archivo, ancho_max, alto_max):
    """Image de ReportLab a escala, o None si no hay archivo o está dañado (nunca impide el PDF)."""
    if not archivo:
        return None
    try:
        archivo.open('rb')
        datos = BytesIO(archivo.read())
        archivo.close()
        ancho, alto = ImageReader(datos).getSize()
        escala = min(ancho_max / ancho, alto_max / alto)
        datos.seek(0)
        return Image(datos, width=ancho * escala, height=alto * escala)
    except Exception:  # noqa: BLE001
        return None


def _color(config):
    return colors.HexColor(getattr(config, 'color_primario', '') or '#2F625B')


def encabezado_tenant(tenant, titulo='', subtitulo='', profesional=None):
    """
    Flowables del encabezado. Si el profesional usa membrete propio, o el consultorio cargó un membrete
    (imagen de banner), se usa esa imagen; si no, logo + datos del consultorio (+ datos del profesional).
    """
    config = tenant.configuracion
    color = _color(config)
    membrete = None
    if profesional is not None and profesional.usar_membrete_propio and profesional.membrete:
        membrete = profesional.membrete
    elif config.membrete:
        membrete = config.membrete
    banner = imagen_ajustada(membrete, 186 * mm, 32 * mm) if membrete else None

    derecha = []
    if titulo:
        derecha.append(Paragraph(f'<b>{titulo}</b>', ParagraphStyle('t', parent=ESTILOS['Heading3'],
                                                                    alignment=TA_RIGHT, textColor=color)))
    if subtitulo:
        derecha.append(Paragraph(subtitulo, ESTILO_DATO_DER))

    if banner:
        elementos = [banner, Spacer(1, 2 * mm)]
        if derecha:
            elementos.append(Table([[derecha]], colWidths=[186 * mm]))
        return elementos + [HRFlowable(width='100%', thickness=1.2, color=color), Spacer(1, 4 * mm)]

    estilo_nombre = ParagraphStyle('n', parent=ESTILO_NOMBRE, textColor=color)
    datos = [Paragraph(config.nombre_display, estilo_nombre)]
    if profesional is not None:
        datos.append(Paragraph(f'<b>{profesional.nombre_con_titulo}</b>', ESTILO_DATO))
        linea = ' · '.join(x for x in [profesional.especialidad_texto, profesional.registros_texto] if x)
        if linea:
            datos.append(Paragraph(linea, ESTILO_DATO))
    if config.rif:
        datos.append(Paragraph(f'RIF: {config.rif}', ESTILO_DATO))
    if config.direccion:
        datos.append(Paragraph(config.direccion.replace('\n', '<br/>'), ESTILO_DATO))
    contacto = ' · '.join(x for x in [config.telefono, config.email] if x)
    if contacto:
        datos.append(Paragraph(contacto, ESTILO_DATO))

    logo = imagen_ajustada(config.logo_pdf or config.logo, 46 * mm, 22 * mm)
    celdas = [logo, datos, derecha] if logo else [datos, derecha]
    if logo:
        ancho_logo = logo.drawWidth + 5 * mm
        anchos = [ancho_logo, 130 * mm - ancho_logo, 56 * mm]
    else:
        anchos = [120 * mm, 66 * mm]
    tabla = Table([celdas], colWidths=anchos)
    tabla.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    return [tabla, Spacer(1, 3 * mm), HRFlowable(width='100%', thickness=1.4, color=color), Spacer(1, 5 * mm)]


def bloque_firma(profesional, incluir_firma=True):
    """Firma y sello del profesional sobre la línea, con nombre, especialidad y registros debajo."""
    if profesional is None:
        return []
    firma = imagen_ajustada(profesional.firma, 50 * mm, 22 * mm) if incluir_firma else None
    sello = imagen_ajustada(profesional.sello, 32 * mm, 28 * mm) if incluir_firma else None
    imagenes = [x for x in (firma, sello) if x]
    filas = []
    if imagenes:
        filas.append([Table([imagenes], colWidths=[(x.drawWidth + 4 * mm) for x in imagenes])])
    else:
        filas.append([Spacer(1, 16 * mm)])
    filas.append([HRFlowable(width=70 * mm, thickness=0.8, color=colors.HexColor('#374151'))])
    filas.append([Paragraph(f'<b>{profesional.nombre_con_titulo}</b>', ESTILO_CENTRO)])
    for linea in (profesional.especialidad_texto, profesional.registros_texto):
        if linea:
            filas.append([Paragraph(linea, ESTILO_CENTRO)])
    tabla = Table(filas, colWidths=[80 * mm], hAlign='CENTER')
    tabla.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 1),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 1)]))
    return [Spacer(1, 10 * mm), tabla]


def pie_tenant(tenant):
    """Función para onPage: pie con el texto del consultorio y la marca del producto, discreta."""
    config = tenant.configuracion

    def dibujar(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(colors.HexColor('#6B7280'))
        if config.pie_documentos:
            canvas.drawString(doc.leftMargin, 12 * mm, config.pie_documentos[:150])
        canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 12 * mm,
                               f'Página {doc.page} · Omnis')
        canvas.restoreState()
    return dibujar


def documento(buffer, titulo_pdf='Documento', horizontal=False, media_carta=False):
    from reportlab.lib.pagesizes import landscape
    tamano = (letter[0], letter[1] / 2) if media_carta else letter
    if horizontal:
        tamano = landscape(tamano)
    return SimpleDocTemplate(buffer, pagesize=tamano, title=titulo_pdf,
                             leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm, bottomMargin=20 * mm)


def nombre_archivo(*partes, extension='pdf'):
    """Une las partes con «_»: REC-2026-00012_Maria-Perez_2026-10-20.pdf"""
    import unicodedata
    from datetime import date, datetime
    limpias = []
    for x in partes:
        if isinstance(x, (date, datetime)):
            x = x.strftime('%Y-%m-%d')
        x = unicodedata.normalize('NFKD', str(x or '')).encode('ascii', 'ignore').decode().replace(' ', '-')
        x = ''.join(c for c in x if c.isalnum() or c in '-.').strip('-.')
        if x:
            limpias.append(x)
    return '_'.join(limpias) + f'.{extension}'


def respuesta_pdf(contenido, *partes):
    """PDF en línea, nunca en caché (cada vez que se abre sale la versión actual)."""
    from django.http import HttpResponse
    r = HttpResponse(contenido, content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{nombre_archivo(*partes)}"'
    r['Cache-Control'] = 'no-store, max-age=0'
    return r
