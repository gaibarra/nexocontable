from django.apps import AppConfig


class PanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'panel'
    verbose_name = 'Torre de Control'

    def ready(self):
        from . import signals  # noqa: F401
