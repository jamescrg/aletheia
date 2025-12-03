from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.documents"

    def ready(self):
        import apps.documents.search_config  # noqa: F401
        import apps.documents.signals  # noqa: F401
