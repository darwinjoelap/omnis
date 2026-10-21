from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _sincronizar(sender, **kwargs):
    from .servicios import actualizar_plantillas_de_modulos, sincronizar_catalogo
    sincronizar_catalogo(verbosidad=kwargs.get('verbosity', 1))
    actualizar_plantillas_de_modulos()


class ClinicaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clinica'
    verbose_name = 'Clínica (historia)'

    def ready(self):
        from . import consultas, nucleo  # noqa: F401  (consultas registra la copia a tablas del núcleo)
        nucleo.registrar()
        # Tras cada `migrate` el catálogo de especialidades y secciones queda al día (también en Railway)
        post_migrate.connect(_sincronizar, sender=self, dispatch_uid='clinica_sincronizar_catalogo')
