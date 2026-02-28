from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # Import signals to register them
        import core.signals  # noqa: F401
