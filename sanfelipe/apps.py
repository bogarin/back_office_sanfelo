"""San Felipe Backoffice Application Configuration."""

from django.apps import AppConfig
from django.contrib import admin


class SanfelipeConfig(AppConfig):
    """Configuration for the San Felipe project."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sanfelipe'

    def ready(self):
        """Called when Django starts."""
        # Configure admin site branding
        admin.site.site_header = 'San Felipe Backoffice'
        admin.site.site_title = 'San Felipe Backoffice'
        admin.site.index_title = 'Panel de Control'
