from django.apps import AppConfig


class GeneralConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.especialidades.general'
    label = 'esp_general'
    verbose_name = 'Especialidad: Medicina general'

    def ready(self):
        from . import especialidad  # noqa: F401  (registra la especialidad y las básicas)
