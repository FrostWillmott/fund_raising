from django.apps import AppConfig


class CollectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "collects"

    def ready(self):
        import collects.signals  # noqa: F401