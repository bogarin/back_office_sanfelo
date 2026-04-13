"""Permission mixins for role-based access control.

Provides mixins for role-based access control in admin interface:
- RoleBasedAccessMixin: Granular permissions based on user groups
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Model, QuerySet
from django.http import HttpRequest


# =============================================================================
# Permission Mixins for Role-Based Access Control
# =============================================================================


class RoleBasedAccessMixin:
    """Mixin for role-based access control.

    Provides role-based access control for users in admin interface:
    - Superusers: Acceso completo (SELECT + UPDATE a todo)
    - Administrador group: Acceso completo (SELECT + UPDATE a todo)
    - Coordinador group: Ve todos los trámites (SELECT), puede UPDATE cualquier trámite, asignar/reasignar
    - Analista group: Ve sus trámites + sin asignar (SELECT restringido), UPDATE solo sus trámites, auto-asignar
    - Other users: Sin acceso

    For Tramite model specifically, access rules are:
    SELECT permissions (data visibility):
    - Superuser: Ve TODO
    - Administrador: Ve TODO
    - Coordinador: Ve TODO (para poder reasignar)
    - Analista: Ve SUS trámites + trámites sin asignar

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
        - Ver sus trámites asignados + trámites sin asignar (SELECT restringido)
        - Auto-asignarse trámites sin asignar
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

    def has_view_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
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

    def has_change_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
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

    def has_delete_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
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
