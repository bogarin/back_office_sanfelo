"""Custom admin site configuration.

Provides a custom admin site for backoffice with:
- Custom site headers and titles
- App list ordering
- Role-based access control
"""

from django.contrib import admin
from django.http import HttpRequest

from core.rbac.constants import BackOfficeRole


# =============================================================================
# Custom Admin Site (optional for future customization)
# =============================================================================


class BackofficeAdminSite(admin.AdminSite):
    """Custom admin site for backoffice with specific configurations."""

    site_header = 'Backoffice San Felipe'
    site_title = 'Backoffice San Felipe'
    index_title = 'Panel de Administración'

    def get_app_list(self, request, app_label=None):
        """Customize app list ordering."""
        app_list = super().get_app_list(request, app_label)

        # Reorder apps: tramites first, then others
        order = {'tramites': 0, 'buzon': 1}
        app_list.sort(key=lambda x: order.get(x['app_label'], 999))

        return app_list

    def has_permission(self, request):
        """Check if user has permission to access the admin site."""
        return request.user.is_active and request.user.is_staff

    def has_module_permission(self, request: HttpRequest, app_label: str) -> bool:
        """Check if user has permission to view a module in admin index.

        Controls module visibility based on user role:
        - Superusers: can see all modules
        - Administrador: can see all modules
        - Other users have no access

        Args:
            request: The HTTP request object
            app_label: The Django app label for the module

        Returns:
            bool: True if user can view the module, False otherwise
        """
        # Superusers see all modules
        if request.user.is_superuser:
            return True

        # Administrador group sees all modules
        return BackOfficeRole.ADMINISTRADOR in getattr(request.user, 'roles', set())
