from django.apps import AppConfig


class DocumentosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documentos'
    verbose_name = 'Documentos'

    def ready(self):
        from . import comunes  # noqa: F401  registra récipe, informe, referencia, reposo, constancia
