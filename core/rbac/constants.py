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
    'auth',  # Group/Permission management
    'core',  # Custom User model (AUTH_USER_MODEL = 'core.User')
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


# =============================================================================
# CUSTOM PERMISSIONS FOR TRAMITES
# =============================================================================


class TramitePermission:
    """Custom permissions for tramites-specific functionality in Jazzmin sidebar.

    These permissions control visibility of custom links in the admin sidebar.
    Each permission grants access to a group of sidebar links tied to a role:

    - ACCESO_ANALISTA: Mis trámites + Disponibles (Analista + Administrador)
    - ACCESO_COORDINADOR: Trámites en curso + Finalizados (Coordinador + Administrador)
    """

    # Sidebar: Mis trámites, Disponibles (Analista + Administrador)
    ACCESO_ANALISTA = 'acceso_analista'

    # Sidebar: Trámites en curso, Finalizados (Coordinador + Administrador)
    ACCESO_COORDINADOR = 'acceso_coordinador'


# Full list of custom tramites permissions (for creating them in DB)
TRAMITES_CUSTOM_PERMISSIONS = [
    TramitePermission.ACCESO_ANALISTA,
    TramitePermission.ACCESO_COORDINADOR,
]


# =============================================================================
# PERMISSION MAPPING BY ROLE
# =============================================================================


# Custom permissions for each role
ROLE_CUSTOM_PERMISSIONS = {
    BackOfficeRole.ADMINISTRADOR: [
        TramitePermission.ACCESO_ANALISTA,
        TramitePermission.ACCESO_COORDINADOR,
    ],
    BackOfficeRole.COORDINADOR: [
        TramitePermission.ACCESO_COORDINADOR,
    ],
    BackOfficeRole.ANALISTA: [
        TramitePermission.ACCESO_ANALISTA,
    ],
}
