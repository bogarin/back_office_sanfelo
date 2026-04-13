"""
Role-Based Access Control (RBAC) constants and permission definitions.

This module is central, authoritative source for defining what permissions
each role has in system. It should be first place to look when
understanding or modifying RBAC system.

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

from django.conf import settings


# =============================================================================
# ROLE DEFINITIONS
# =============================================================================


class Role:
    """Role constants matching settings."""

    ADMINISTRADOR = settings.ADMINISTRADOR_GROUP_NAME  # 'Administrador'


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
