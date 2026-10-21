from django.apps import AppConfig


class ConfiguracionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.configuracion'
    verbose_name = 'Configuración del consultorio'

    def ready(self):
        from . import signals  # noqa: F401
