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
# Background Task for Audit Logging
# =============================================================================


@task
def log_audit_entry_async(
    usuario_sis: str,
    tipo_mov: str,
    usuario_pc: str,
    fecha: date,
    maquina: str,
    observaciones: str,
    val_anterior: Optional[str] = None,
    val_nuevo: Optional[str] = None,
) -> Optional[int]:
    """Background task to create a Bitacora audit entry asynchronously.

    This task is enqueued by the AuditTrailMixin to avoid blocking HTTP
    responses while writing to the audit log. It creates a new Bitacora
    record with all the provided information.

    Args:
        usuario_sis: System username who performed the action
        tipo_mov: Type of movement (e.g., 'UPDATE', 'DELETE', 'CREATE')
        usuario_pc: IP address of the user's computer
        fecha: Date when the action occurred
        maquina: Hostname of the user's machine (optional)
        observaciones: Description of the action performed
        val_anterior: Previous value for field changes (optional)
        val_nuevo: New value for field changes (optional)

    Returns:
        The ID of the created Bitacora entry, or None if creation failed.

    Raises:
        Exception: Any database exception during Bitacora creation is logged
                   but not re-raised to avoid task retry loops.
    """
    try:
        from bitacora.models import Bitacora

        bitacora_entry = Bitacora.objects.create(
            usuario_sis=usuario_sis,
            tipo_mov=tipo_mov,
            usuario_pc=usuario_pc,
            fecha=fecha,
            maquina=maquina,
            val_anterior=val_anterior,
            val_nuevo=val_nuevo,
            observaciones=observaciones,
        )

        logger.info(
            f'Successfully created audit log entry #{bitacora_entry.id} '
            f"for user '{usuario_sis}' action '{tipo_mov}'"
        )

        return bitacora_entry.id

    except Exception as exc:
        # Log the error but don't raise to prevent task retry loops
        logger.exception(
            f"Failed to create audit log entry for user '{usuario_sis}' action '{tipo_mov}': {exc}"
        )
        return None


# =============================================================================
# Custom ModelAdmin Base Classes
# =============================================================================


class BaseModelAdmin(admin.ModelAdmin):
    """Base ModelAdmin with common configuration for all models."""

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # Enable save_on_top for better UX
        self.save_on_top = True

    class Media:
        css = {
            'all': ('admin/css/custom.css',),
        }


class ReadOnlyModelAdmin(BaseModelAdmin):
    """ModelAdmin for read-only models (like bitacora)."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Catalog base classes for catalog tables
class CatalogBaseAdmin(BaseModelAdmin):
    """Base ModelAdmin for catalog tables with common features."""

    list_per_page = 50
    search_fields = ('nombre', 'descripcion')
    save_as = True


# =============================================================================
# Audit Trail Mixin with Background Tasks
# =============================================================================


class AuditTrailMixin:
    """Mixin to add audit trail functionality to ModelAdmin using async tasks.

    Automatically logs changes to the bitacora when model instances are modified.
    Uses Django 6.0's background tasks framework to avoid blocking HTTP responses.

    This mixin provides:
    - Asynchronous audit logging for save operations (UPDATE)
    - Asynchronous audit logging for delete operations (DELETE)
    - Proper error handling and logging
    - Backward compatibility with existing code

    Usage:
        class MyModelAdmin(AuditTrailMixin, admin.ModelAdmin):
            # Your custom admin configuration here
            pass
    """

    def _extract_user_info(self, request: HttpRequest) -> tuple[str, str, str]:
        """Extract user information from the HTTP request.

        Args:
            request: The HTTP request object.

        Returns:
            A tuple of (username, remote_addr, remote_host).
        """
        username = request.user.username if hasattr(request, 'user') and request.user else 'admin'
        remote_addr = request.META.get('REMOTE_ADDR', 'localhost')
        remote_host = request.META.get('REMOTE_HOST', '')
        return username, remote_addr, remote_host

    def _enqueue_audit_log(
        self,
        request: HttpRequest,
        action_type: str,
        observaciones: str,
        val_anterior: Optional[str] = None,
        val_nuevo: Optional[str] = None,
    ) -> None:
        """Enqueue an audit log entry as a background task.

        This method creates a task that will asynchronously write to the Bitacora
        table, allowing the HTTP request to complete without waiting for the
        database write.

        Args:
            request: The HTTP request object.
            action_type: Type of action being logged (e.g., 'UPDATE', 'DELETE').
            observaciones: Description of the action performed.
            val_anterior: Previous value for field changes (optional).
            val_nuevo: New value for field changes (optional).
        """
        username, remote_addr, remote_host = self._extract_user_info(request)

        try:
            # Enqueue the background task
            log_audit_entry_async.enqueue(
                usuario_sis=username,
                tipo_mov=action_type,
                usuario_pc=remote_addr,
                fecha=date.today(),
                maquina=remote_host,
                observaciones=observaciones,
                val_anterior=val_anterior,
                val_nuevo=val_nuevo,
            )

            logger.debug(
                f"Enqueued audit log task for user '{username}' action '{action_type}' "
                f'on {self.model._meta.verbose_name}'
            )

        except Exception as exc:
            # Log the error but don't fail the request
            logger.exception(
                f"Failed to enqueue audit log task for user '{username}' "
                f"action '{action_type}': {exc}"
            )

    def save_model(self, request: HttpRequest, obj: Model, form: object, change: bool) -> None:
        """Save model and log changes to bitacora asynchronously.

        If this is a change (not a new object), enqueues a background task to
        log the update to the bitacora. The logging happens asynchronously,
        so the HTTP response is not blocked waiting for the database write.

        Args:
            request: The HTTP request object.
            obj: The model instance being saved.
            form: The ModelForm instance.
            change: True if this is an update, False for a new object.
        """
        # Call parent to save the model
        super().save_model(request, obj, form, change)

        # Only log updates, not creates
        if change:
            observaciones = f'Actualizado {self.model._meta.verbose_name}: {obj}'
            self._enqueue_audit_log(
                request=request,
                action_type='UPDATE',
                observaciones=observaciones,
            )

    def delete_model(self, request: HttpRequest, obj: Model) -> None:
        """Delete model and log to bitacora asynchronously.

        Enqueues a background task to log the deletion to the bitacora before
        actually deleting the object. The logging happens asynchronously,
        so the HTTP response is not blocked waiting for the database write.

        Args:
            request: The HTTP request object.
            obj: The model instance being deleted.
        """
        # Prepare the observaciones before deletion (while obj still exists)
        observaciones = f'Eliminado {self.model._meta.verbose_name}: {obj}'

        # Enqueue the background task to log the deletion
        self._enqueue_audit_log(
            request=request,
            action_type='DELETE',
            observaciones=observaciones,
        )

        # Now actually delete the model
        super().delete_model(request, obj)


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

        # Reorder apps: tramites first, then catalogs, then others
        order = {'tramites': 0, 'catalogos': 1, 'costos': 2, 'bitacora': 3}
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
        - Operador: can only see business modules (catalogos, costos, bitacora, tramites)
        - Auth/admin modules (auth, contenttypes, sessions): only visible to Administrador

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
        if request.user.groups.filter(name=settings.ADMINISTRADOR_GROUP_NAME).exists():
            return True

        # Operador group sees only business modules
        if request.user.groups.filter(name=settings.OPERADOR_GROUP_NAME).exists():
            business_modules = {'catalogos', 'costos', 'bitacora', 'tramites'}
            return app_label in business_modules

        # Default: deny access
        return False


# =============================================================================
# Permission Mixins for Role-Based Access Control
# =============================================================================


class RoleBasedAccessMixin:
    """Mixin for role-based access control.

    Provides role-based access control for users in the admin interface:
    - Superusers have full access
    - Administrador group users have full access
    - Operador group users have read-only access to catalogos, costos, and bitacora apps
    - Other users have no access
    """

    # Set of apps where operador users have view access
    OPERADOR_VIEW_APPS: set[str] = {'catalogos', 'costos', 'bitacora'}

    def _is_operador(self, user: User) -> bool:
        """Check if user belongs to Operador group.

        Args:
            user: Django User instance

        Returns:
            True if user is in Operador group, False otherwise
        """
        return user.groups.filter(name=settings.OPERADOR_GROUP_NAME).exists()

    def _is_administrador(self, user: User) -> bool:
        """Check if user belongs to Administrador group.

        Args:
            user: Django User instance

        Returns:
            True if user is in Administrador group, False otherwise
        """
        return user.groups.filter(name=settings.ADMINISTRADOR_GROUP_NAME).exists()

    def _is_allowed_app_for_operador(self, app_label: str) -> bool:
        """Check if app allows read-only access for Operador users.

        Args:
            app_label: Django app label (e.g., 'catalogos', 'costos')

        Returns:
            True if app allows operador access, False otherwise
        """
        return app_label in self.OPERADOR_VIEW_APPS

    def get_queryset(self, request: HttpRequest) -> QuerySet[Model]:
        """Return the queryset with proper data filtering based on user permissions.

        This method controls data visibility in admin interface:
        - Superusers see all data (no filtering)
        - Administrador group users see all data (no filtering)
        - Operador group users see all data (permissions control actions, not visibility)

        The method follows Django's pattern for queryset overrides and maintains
        proper chaining with other overrides. Permissions methods (has_view_permission,
        has_change_permission, etc.) control what actions users can perform on
        the data they see.

        Args:
            request: The HTTP request object containing user information.

        Returns:
            QuerySet: The queryset filtered according to user permissions.
                      For superusers, Administrador, and Operador groups,
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

        # Operador group users see all data
        # (permissions will control what actions they can perform)
        if self._is_operador(request.user):
            return queryset

        # Other users (if any) get the default queryset
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

        if self._is_administrador(request.user):
            return True

        if self._is_operador(request.user):
            app_label = self.model._meta.app_label
            return self._is_allowed_app_for_operador(app_label)

        return False

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Check if user has add permission for this model.

        Args:
            request: HttpRequest instance

        Returns:
            True if user can add instances, False otherwise
        """
        if request.user.is_superuser:
            return True

        if self._is_administrador(request.user):
            return True

        if self._is_operador(request.user):
            return False

        return False

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

        if self._is_administrador(request.user):
            return True

        if self._is_operador(request.user):
            return False

        return False

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

        if self._is_administrador(request.user):
            return True

        if self._is_operador(request.user):
            return False

        return False


class ReadOnlyModelAdmin(RoleBasedAccessMixin, admin.ModelAdmin):
    """Admin con solo permisos de lectura."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
