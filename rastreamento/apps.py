from django.apps import AppConfig


class RastreamentoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rastreamento"
    verbose_name = "Rastreamento"

    def ready(self):
        from . import signals  # noqa: F401
