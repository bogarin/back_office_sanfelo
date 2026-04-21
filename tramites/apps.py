from django.apps import AppConfig


class TramitesConfig(AppConfig):
    name = 'tramites'

    def ready(self):
        """
        Called when Django starts.
        """
        pass
