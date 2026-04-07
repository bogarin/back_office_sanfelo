from django.apps import AppConfig


class TramitesConfig(AppConfig):
    name = 'tramites'

    def ready(self):
        """
        Called when Django starts.

        This is the correct place to register signals.
        Signals are imported here to ensure Django apps are ready.
        """
        # Import signals to register them with Django's signal dispatcher
        import tramites.signals  # noqa: F401
