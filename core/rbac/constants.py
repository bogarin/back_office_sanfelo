"""
Role-Based Access Control (RBAC) constants and permission definitions.

This module is the central, authoritative source for defining roles and
permissions in the system.  It should be the first place to look when
understanding or modifying the RBAC system.

Roles:
------
- Administrador: Full access to all apps (auth + business apps)
- Coordinador: Full access to tramites app, can assign/reassign
- Analista: Limited access to own trámites + free trámites

Apps:
-----
- auth: User/group management via Django admin
- tramites: Procedures and all catalog models (TramiteCatalogo, TramiteEstatus, etc.)
"""

from enum import StrEnum


# =============================================================================
# ROLE DEFINITIONS
# =============================================================================


class BackOfficeRole(StrEnum):
    """Authoritative role names for the backoffice system.

    Members are plain strings — they work directly in Django ORM queries,
    form choices, template rendering, and set membership checks without
    needing ``.value`` or ``.name`` indirection.

    Usage::

        BackOfficeRole.COORDINADOR == 'Coordinador'          # True
        BackOfficeRole.COORDINADOR in user.roles             # True (set[str])
        Group.objects.filter(name=BackOfficeRole.COORDINADOR) # works
        list(BackOfficeRole)                                  # ['Administrador', ...]
    """

    ADMINISTRADOR = 'Administrador'
    COORDINADOR = 'Coordinador'
    ANALISTA = 'Analista'


# =============================================================================
# APP PERMISSIONS BY ROLE
# =============================================================================

# Apps where Administrador has full access (all permissions: add, change, delete, view)
ADMINISTRADOR_APPS = [
    'auth',  # User/group management
    'tramites',  # Procedures and catalog models
]


# =============================================================================
# PERMISSION TYPES
# =============================================================================


class PermissionType:
    """Standard Django permission types."""

    ADD = 'add'
    CHANGE = 'change'
    DELETE = 'delete'
    VIEW = 'view'


# All permission types (for full access roles)
ALL_PERMISSION_TYPES = [
    PermissionType.ADD,
    PermissionType.CHANGE,
    PermissionType.DELETE,
    PermissionType.VIEW,
]

# Only view permission (for restricted roles)
VIEW_ONLY_PERMISSION_TYPES = [PermissionType.VIEW]
