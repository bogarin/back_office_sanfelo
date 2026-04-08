"""Django Admin global configuration.

Configures the admin interface for the backoffice with:
- Custom site headers and titles
- Dashboard modifications
- Admin actions and permissions
- Async audit trail using background tasks
"""

import logging
from datetime import date
from typing import Optional

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.tasks import task

logger = logging.getLogger(__name__)

# Admin Site Configuration
admin.site.site_header = 'Backoffice San Felipe'
admin.site.site_title = 'Backoffice San Felipe'
admin.site.index_title = 'Panel de Administración'


# =============================================================================
# Custom ModelAdmin Base Classes
# =============================================================================


class BaseModelAdmin(admin.ModelAdmin):
    """Base ModelAdmin with common configuration for all models."""

    # Pagination
    list_per_page = 25
    list_max_show_all = 100

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # Enable save_on_top for better UX
        self.save_on_top = True

    # class Media:
    #     css = {
    #         'all': ('admin/css/custom.css',),
    #     }


class ReadOnlyModelAdmin(BaseModelAdmin):
    """ModelAdmin for read-only models."""

    list_editable = ()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ActionableReadOnlyMixin:
    """Enables Django admin actions on a ReadOnlyModelAdmin.

    ReadOnlyModelAdmin blocks all write operations by design.
    This mixin selectively re-enables the action infrastructure
    (action dropdown, checkbox selection) WITHOUT enabling
    the change form or inline editing.

    Django uses ``has_change_permission(request, obj=None)`` in two contexts:

    1. **obj=None** (changelist): decides whether to show the action dropdown.
    2. **obj=instance** (change form): decides whether to allow editing.

    This mixin allows context 1 (actions work) and blocks context 2 (readonly).

    Usage::

        class MyAdmin(ActionableReadOnlyMixin, ReadOnlyModelAdmin):
            actions = ('my_action',)

            @admin.action(description='Do something')
            def my_action(self, request, queryset):
                ...

    Important:
        MRO order matters. ``ActionableReadOnlyMixin`` must come BEFORE
        ``ReadOnlyModelAdmin`` so that its ``has_change_permission`` takes
        precedence.
    """

    def has_change_permission(self, request, obj=None):
        """Allow actions on changelist, block the change form.

        Returns True when obj is None (changelist context) so Django
        renders the action dropdown.  Returns False when obj is an
        instance to keep the change form truly read-only.
        """
        return obj is None


# =============================================================================
# Custom Admin Actions
# =============================================================================


def mark_as_active(modeladmin, request, queryset):
    """Admin action to mark selected items as active."""
    rows_updated = queryset.update(activo=True)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "registro") or "registros"} marcados como activos.',
    )


mark_as_active.short_description = 'Marcar como activos'


def mark_as_inactive(modeladmin, request, queryset):
    """Admin action to mark selected items as inactive."""
    rows_updated = queryset.update(activo=False)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "registro") or "registros"} marcados como inactivos.',
    )


mark_as_inactive.short_description = 'Marcar como inactivos'


def mark_urgent(modeladmin, request, queryset):
    """Admin action to mark tramites as urgent."""
    rows_updated = queryset.update(urgente=True)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "trámite") or "trámites"} marcados como urgentes.',
    )


mark_urgent.short_description = 'Marcar como urgentes'


def mark_not_urgent(modeladmin, request, queryset):
    """Admin action to mark tramites as not urgent."""
    rows_updated = queryset.update(urgente=False)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "trámite") or "trámites"} marcados como no urgentes.',
    )


mark_not_urgent.short_description = 'Marcar como no urgentes'


def mark_as_paid(modeladmin, request, queryset):
    """Admin action to mark tramites as paid."""

    rows_updated = queryset.update(pagado=True)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "trámite") or "trámites"} marcados como pagados.',
    )


mark_as_paid.short_description = 'Marcar como pagados'


def mark_as_unpaid(modeladmin, request, queryset):
    """Admin action to mark tramites as unpaid."""
    rows_updated = queryset.update(pagado=False)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "trámite") or "trámites"} marcados como no pagados.',
    )


mark_as_unpaid.short_description = 'Marcar como no pagados'


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
        return request.user.groups.filter(name=settings.ADMINISTRADOR_GROUP_NAME).exists()


# =============================================================================
# Permission Mixins for Role-Based Access Control
# =============================================================================


class RoleBasedAccessMixin:
    """Mixin for role-based access control.

    Provides role-based access control for users in admin interface:
    - Superusers: Acceso completo (SELECT + UPDATE a todo)
    - Administrador group: Acceso completo (SELECT + UPDATE a todo)
    - Coordinador group: Ve todos los trámites (SELECT), puede UPDATE cualquier trámite, asignar/reasignar
    - Analista group: Ve sus trámites + libres (SELECT restringido), UPDATE solo sus trámites, auto-asignar
    - Other users: Sin acceso

    For Tramite model specifically, the access rules are:
    SELECT permissions (data visibility):
    - Superuser: Ve TODO
    - Administrador: Ve TODO
    - Coordinador: Ve TODO (para poder reasignar)
    - Analista: Ve SUS trámites + trámites libres

    UPDATE permissions (modify data):
    - Superuser: UPDATE a TODO
    - Administrador: UPDATE a TODO
    - Coordinador: UPDATE a TODO
    - Analista: UPDATE solo a SUS trámites
    """

    def _is_administrador(self, user: User) -> bool:
        """Check if user belongs to Administrador group.

        Args:
            user: Django User instance

        Returns:
            True if user is in Administrador group, False otherwise
        """
        return user.groups.filter(name=settings.ADMINISTRADOR_GROUP_NAME).exists()

    def _is_coordinador(self, user: User) -> bool:
        """Check if user belongs to Coordinador group.

        Coordinadores pueden:
        - Ver todos los trámites (SELECT)
        - Asignar y reasignar trámites
        - Modificar cualquier trámite (UPDATE)

        Args:
            user: Django User instance

        Returns:
            True if user is in Coordinador group, False otherwise
        """
        return user.groups.filter(name=settings.COORDINADOR_GROUP_NAME).exists()

    def _is_analista(self, user: User) -> bool:
        """Check if user belongs to Analista group.

        Analistas pueden:
        - Ver sus trámites asignados + trámites libres (SELECT restringido)
        - Auto-asignarse trámites libres
        - Modificar solo sus trámites asignados (UPDATE)

        Args:
            user: Django User instance

        Returns:
            True if user is in Analista group, False otherwise
        """
        return user.groups.filter(name=settings.ANALISTA_GROUP_NAME).exists()

    def get_queryset(self, request: HttpRequest) -> QuerySet[Model]:
        """Return the queryset with proper data filtering based on user permissions.

        This method controls data visibility in admin interface:
        - Superusers see all data (no filtering)
        - Administrador group users see all data (no filtering)
        - Other users have no access

        The method follows Django's pattern for queryset overrides and maintains
        proper chaining with other overrides. Permissions methods (has_view_permission,
        has_change_permission, etc.) control what actions users can perform on
        the data they see.

        Args:
            request: The HTTP request object containing user information.

        Returns:
            QuerySet: The queryset filtered according to user permissions.
                      For superusers and Administrador groups,
                      returns the full queryset without additional filtering.
        """
        # Get the base queryset from parent classes
        queryset = super().get_queryset(request)

        # Superusers see all data
        if request.user.is_superuser:
            return queryset

        # Administrador group users see all data
        if self._is_administrador(request.user):
            return queryset

        # Other users get the default queryset (empty due to permission checks)
        return queryset

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        """Check if user has view permission for this model.

        Args:
            request: HttpRequest instance
            obj: Optional model instance

        Returns:
            True if user can view the model, False otherwise
        """
        if request.user.is_superuser:
            return True

        return bool(self._is_administrador(request.user))

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Check if user has add permission for this model.

        Args:
            request: HttpRequest instance

        Returns:
            True if user can add instances, False otherwise
        """
        if request.user.is_superuser:
            return True

        return bool(self._is_administrador(request.user))

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        """Check if user has change permission for this model.

        Args:
            request: HttpRequest instance
            obj: Optional model instance

        Returns:
            True if user can change instances, False otherwise
        """
        if request.user.is_superuser:
            return True

        return bool(self._is_administrador(request.user))

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        """Check if user has delete permission for this model.

        Args:
            request: HttpRequest instance
            obj: Optional model instance

        Returns:
            True if user can delete instances, False otherwise
        """
        if request.user.is_superuser:
            return True

        return bool(self._is_administrador(request.user))
