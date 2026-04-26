"""Custom User model for the backoffice application.

Extends Django's AbstractUser with convenience properties that map group
membership to role checks.  This avoids scattering ``BackOfficeRole in
user.roles`` comparisons throughout the codebase.

The role properties delegate to ``request.user.roles`` (populated by
``CacheUserRolesMiddleware``) when available, falling back to a database
query otherwise.
"""

from django.contrib.auth.models import AbstractUser

from core.rbac.constants import BackOfficeRole


class User(AbstractUser):
    """Backoffice user with role convenience properties.

    Roles are stored as Django Group memberships.  The properties below
    provide a clean API for checking the user's role without requiring
    knowledge of the underlying group system.

    Usage::

        if user.is_coordinador:
            ...

        # Equivalent to:
        if BackOfficeRole.COORDINADOR in user.roles:
            ...
    """

    class Meta:
        app_label = 'core'

    # ------------------------------------------------------------------
    # Role convenience properties
    # ------------------------------------------------------------------

    @property
    def is_administrador(self) -> bool:
        """Whether this user belongs to the Administrador group."""
        return BackOfficeRole.ADMINISTRADOR in self._get_roles()

    @property
    def is_coordinador(self) -> bool:
        """Whether this user belongs to the Coordinador group."""
        return BackOfficeRole.COORDINADOR in self._get_roles()

    @property
    def is_analista(self) -> bool:
        """Whether this user belongs to the Analista group."""
        return BackOfficeRole.ANALISTA in self._get_roles()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_roles(self) -> set[str]:
        """Return cached roles when available, otherwise query the database."""
        roles = getattr(self, 'roles', None)
        if roles is not None:
            return roles
        return set(self.groups.values_list('name', flat=True))
