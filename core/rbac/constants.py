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


# =============================================================================
# CUSTOM PERMISSIONS FOR TRAMITES
# =============================================================================


class TramitePermission:
    """Custom permissions for tramites-specific functionality in Jazzmin sidebar.

    These permissions control visibility of custom links in the admin sidebar,
    allowing role-based filtering of tramite views.
    """

    # Link: Tramites/Mis Tramites (Analista only)
    VIEW_MIS_TRAMITES = 'view_mis_tramites'

    # Link: Tramites/Todos (Administrador, Coordinador)
    VIEW_TODOS = 'view_todos'

    # Link: Tramites/Disponibles/Sin asignar (All roles)
    VIEW_DISPONIBLES = 'view_disponibles'

    # Link: Tramites/Asignados (Administrador, Coordinador)
    VIEW_ASIGNADOS = 'view_asignados'

    # Link: Tramites/Finalizados (Administrador, Coordinador)
    VIEW_FINALIZADOS = 'view_finalizados'


# Full list of custom tramites permissions (for creating them in DB)
TRAMITES_CUSTOM_PERMISSIONS = [
    TramitePermission.VIEW_MIS_TRAMITES,
    TramitePermission.VIEW_TODOS,
    TramitePermission.VIEW_DISPONIBLES,
    TramitePermission.VIEW_ASIGNADOS,
    TramitePermission.VIEW_FINALIZADOS,
]


# =============================================================================
# PERMISSION MAPPING BY ROLE
# =============================================================================


# Custom permissions for each role
ROLE_CUSTOM_PERMISSIONS = {
    BackOfficeRole.ADMINISTRADOR: [
        TramitePermission.VIEW_MIS_TRAMITES,
        TramitePermission.VIEW_TODOS,
        TramitePermission.VIEW_DISPONIBLES,
        TramitePermission.VIEW_ASIGNADOS,
        TramitePermission.VIEW_FINALIZADOS,
    ],
    BackOfficeRole.COORDINADOR: [
        TramitePermission.VIEW_TODOS,
        TramitePermission.VIEW_DISPONIBLES,
        TramitePermission.VIEW_ASIGNADOS,
        TramitePermission.VIEW_FINALIZADOS,
    ],
    BackOfficeRole.ANALISTA: [
        TramitePermission.VIEW_MIS_TRAMITES,
        TramitePermission.VIEW_DISPONIBLES,
    ],
}
