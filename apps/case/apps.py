from django.apps import AppConfig


class CaseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.case"

    def ready(self):
        import apps.case.search_config  # noqa: F401
        import apps.case.signals  # noqa: F401
