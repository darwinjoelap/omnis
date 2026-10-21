from django.apps import AppConfig


class PediatriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.especialidades.pediatria'
    label = 'esp_pediatria'
    verbose_name = 'Especialidad: Pediatría'

    def ready(self):
        from . import especialidad  # noqa: F401  (registra la especialidad, sus secciones y ganchos)
