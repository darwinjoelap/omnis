"""
Registro de documentos PDF (Fase 10). El núcleo registra los comunes (comunes.py); cada módulo de
especialidad registra los suyos en su apps.ready() o en EspecialidadDef.documentos.

    registrar(DocumentoDef('reposo', 'Reposo médico', prefijo='REP', generar=..., formulario=ReposoForm))

- generar(doc: DocumentoEmitido, con_firma: bool) -> bytes
- formulario: Form con los datos que pide el documento (None = se emite directo, sin preguntar).
- inicial(paciente, consulta) -> dict con valores sugeridos para el formulario.
- requiere_consulta: el documento solo tiene sentido desde una consulta (récipe, informe).
- especialidad: '' = común; si no, solo aparece a profesionales de esa especialidad.
"""
from dataclasses import dataclass, field


@dataclass
class DocumentoDef:
    codigo: str
    nombre: str
    prefijo: str
    generar: object
    formulario: object = None
    inicial: object = None
    requiere_consulta: bool = False
    especialidad: str = ''
    icono: str = 'bi-file-earmark-text'
    orden: int = 100
    descripcion: str = ''
    extra: dict = field(default_factory=dict)


_documentos: dict[str, DocumentoDef] = {}


def registrar(d: DocumentoDef):
    if d.codigo in _documentos and _documentos[d.codigo] is not d:
        raise ValueError(f'Documento duplicado: {d.codigo}')
    _documentos[d.codigo] = d
    return d


def documento(codigo):
    if codigo not in _documentos:
        _cargar_de_especialidades()
    return _documentos.get(codigo)


def _cargar_de_especialidades():
    from apps.clinica import registro as clinica
    for esp in clinica.especialidades().values():
        for d in esp.documentos:
            if isinstance(d, DocumentoDef) and d.codigo not in _documentos:
                d.especialidad = d.especialidad or esp.codigo
                _documentos[d.codigo] = d


def disponibles(*, especialidad=None, con_consulta=False):
    """Documentos que puede emitir un profesional de `especialidad` (código), ordenados."""
    _cargar_de_especialidades()
    return sorted((d for d in _documentos.values()
                   if (not d.especialidad or d.especialidad == especialidad)
                   and (con_consulta or not d.requiere_consulta)),
                  key=lambda d: (d.orden, d.nombre))
