"""San Felipe Backoffice Application Configuration."""

from django.apps import AppConfig


class SanfelipeConfig(AppConfig):
    """Configuration for the San Felipe project."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sanfelipe'

    def ready(self):
        """Called when Django starts."""
        # Import admin inside ready() to avoid circular imports
        # and ensure all apps are registered before admin is imported
        from django.contrib import admin

        # Configure admin site branding
        admin.site.site_header = 'San Felipe Backoffice'
        admin.site.site_title = 'San Felipe Backoffice'
        admin.site.index_title = 'Panel de Control'
