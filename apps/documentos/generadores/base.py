"""
Piezas comunes de los documentos clínicos: datos del paciente, títulos, texto por líneas y armado final.
El encabezado, la firma y el pie salen de apps.core.pdf (configuración del consultorio + perfil profesional).
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, KeepTogether, Spacer, Table, TableStyle

from apps.core.pdf import (
    ESTILO_CELDA,
    ESTILO_DATO,
    ESTILOS,
    Paragraph,
    bloque_firma,
    documento,
    encabezado_tenant,
    pie_tenant,
)

GRIS = colors.HexColor('#6B7280')
LINEA = colors.HexColor('#D1D5DB')
FONDO = colors.HexColor('#F3F4F6')
ANCHO = 186 * mm

CUERPO = ParagraphStyle('cuerpo', parent=ESTILOS['Normal'], fontSize=10.5, leading=15, alignment=TA_JUSTIFY)
CUERPO_ITEM = ParagraphStyle('cuerpo_item', parent=CUERPO, leftIndent=5 * mm, alignment=0)
ETIQUETA = ParagraphStyle('etiqueta', parent=ESTILOS['Normal'], fontSize=8, leading=10, textColor=GRIS)
SUBTITULO = ParagraphStyle('subtitulo', parent=ESTILOS['Normal'], fontName='Helvetica-Bold', fontSize=9.5,
                           leading=12, textColor=colors.HexColor('#111827'), spaceBefore=2, spaceAfter=1)
TITULO = ParagraphStyle('titulo', parent=ESTILOS['Heading2'], alignment=1, spaceAfter=2)
LUGAR_FECHA = ParagraphStyle('lugar_fecha', parent=ESTILO_DATO, alignment=TA_RIGHT, fontSize=9.5)
NOTA = ParagraphStyle('nota', parent=ESTILO_DATO, fontSize=7.5, leading=9.5)

MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre',
         'noviembre', 'diciembre']


def fecha_larga(fecha):
    return f'{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}'


def color_tenant(tenant):
    return colors.HexColor(tenant.configuracion.color_primario or '#2F625B')


def lineas(texto, estilo=CUERPO):
    """Texto libre → párrafos; las líneas que empiezan con «-», «•» o «1.» se sangran como lista."""
    salida = []
    for linea in (texto or '').strip().split('\n'):
        linea = linea.strip()
        if not linea:
            salida.append(Spacer(1, 2 * mm))
            continue
        es_item = linea[0] in '-·•' or (len(linea) > 2 and linea[0].isdigit() and linea[1] in '.)')
        salida.append(Paragraph(linea, CUERPO_ITEM if es_item and estilo is CUERPO else estilo))
    return salida


def seccion(titulo, tenant):
    """Barra de título de sección (fondo gris, texto del color del consultorio)."""
    t = Table([[Paragraph(f'<b>{titulo.upper()}</b>', ParagraphStyle('s', parent=SUBTITULO,
                                                                     textColor=color_tenant(tenant)))]],
              colWidths=[ANCHO])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), FONDO), ('TOPPADDING', (0, 0), (-1, -1), 3),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 3), ('LEFTPADDING', (0, 0), (-1, -1), 5)]))
    return [Spacer(1, 2 * mm), t, Spacer(1, 1.5 * mm)]


def tabla_datos(pares, columnas=2):
    """[(etiqueta, valor)] en una grilla de `columnas` pares por fila."""
    pares = [(e, v) for e, v in pares if v not in (None, '')]
    if not pares:
        return []
    filas, fila = [], []
    for etiqueta, valor in pares:
        fila += [Paragraph(etiqueta, ETIQUETA), Paragraph(str(valor), ESTILO_CELDA)]
        if len(fila) == columnas * 2:
            filas.append(fila)
            fila = []
    if fila:
        filas.append(fila + [''] * (columnas * 2 - len(fila)))
    ancho_e = 26 * mm
    ancho_v = ANCHO / columnas - ancho_e
    t = Table(filas, colWidths=[ancho_e, ancho_v] * columnas)
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 2),
                           ('TOPPADDING', (0, 0), (-1, -1), 1.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5)]))
    return [t]


def datos_paciente(paciente, completo=True):
    pares = [('Paciente', f'<b>{paciente.nombre_completo}</b>'), ('Documento', paciente.documento)]
    if paciente.fecha_nacimiento:
        pares += [('Nacimiento', paciente.fecha_nacimiento.strftime('%d/%m/%Y')), ('Edad', paciente.edad_texto)]
    if completo:
        pares += [('Sexo', paciente.get_sexo_display() if paciente.sexo else ''), ('Teléfono', paciente.telefono)]
    if paciente.es_menor and paciente.representante_principal:
        r = paciente.representante_principal
        pares.append(('Representante', f'{r.nombre}' + (f' ({r.documento})' if r.numero_documento else '')))
    return tabla_datos(pares)


def lugar_y_fecha(fecha, ciudad=''):
    texto = f'{ciudad}, {fecha_larga(fecha)}' if ciudad else fecha_larga(fecha)
    return [Paragraph(texto, LUGAR_FECHA), Spacer(1, 3 * mm)]


def titulo(texto, tenant, numero=''):
    salida = [Paragraph(texto.upper(), ParagraphStyle('t', parent=TITULO, textColor=color_tenant(tenant)))]
    if numero:
        salida.append(Paragraph(f'N.º {numero}', ParagraphStyle('n', parent=ESTILO_DATO, alignment=1)))
    return salida + [Spacer(1, 4 * mm)]


def nota_confidencial():
    return [Spacer(1, 4 * mm), HRFlowable(width='100%', thickness=0.4, color=LINEA), Spacer(1, 1.5 * mm),
            Paragraph('Documento con información médica confidencial; su uso está restringido al destinatario.',
                      NOTA)]


def construir(doc, cuerpo, *, con_firma=True, titulo_pdf=''):
    """Arma el PDF vertical: encabezado del consultorio/profesional + cuerpo + firma + pie."""
    tenant, profesional = doc.tenant, doc.profesional
    buffer = BytesIO()
    plantilla = documento(buffer, titulo_pdf=titulo_pdf or doc.numero)
    historia = encabezado_tenant(tenant, profesional=profesional)
    historia += cuerpo
    historia.append(KeepTogether(bloque_firma(profesional, incluir_firma=con_firma)))
    pie = pie_tenant(tenant)
    plantilla.build(historia, onFirstPage=pie, onLaterPages=pie)
    return buffer.getvalue()


def ciudad_de(doc):
    """Ciudad para «lugar y fecha»: la indicada en el documento o la del lugar de la consulta."""
    if doc.datos.get('ciudad'):
        return doc.datos['ciudad']
    lugar = doc.consulta.lugar if doc.consulta_id and doc.consulta.lugar_id else None
    return lugar.ciudad if lugar else ''
