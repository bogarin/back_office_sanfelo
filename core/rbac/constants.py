"""
Role-Based Access Control (RBAC) constants and permission definitions.

This module is the central, authoritative source for defining what permissions
each role has in the system. It should be the first place to look when
understanding or modifying the RBAC system.

Roles:
------
- Administrador: Full access to all apps (auth + business apps)
- Operador: View-only access to business apps (no auth, no tramites)

Apps:
-----
- auth: User/group management via Django admin
- catalogos: Catalogs (CatTramite, CatEstatus, etc.)
- costos: Costs (Costo, Uma)
- bitacora: Audit log (read-only)
- tramites: Procedures (full access for admin only)
"""

from django.conf import settings


# =============================================================================
# ROLE DEFINITIONS
# =============================================================================


class Role:
    """Role constants matching settings."""

    ADMINISTRADOR = settings.ADMINISTRADOR_GROUP_NAME  # 'Administrador'
    OPERADOR = settings.OPERADOR_GROUP_NAME  # 'Operador'


# =============================================================================
# APP PERMISSIONS BY ROLE
# =============================================================================

# Apps where Administrador has full access (all permissions: add, change, delete, view)
ADMINISTRADOR_APPS = [
    'auth',  # User/group management
    'catalogos',  # All catalog models
    'costos',  # Cost management
    'bitacora',  # Audit log
    'tramites',  # Procedures
]

# Apps where Operador has view-only access
# Note: tramites is excluded - operators cannot view procedures
OPERADOR_APPS = [
    'catalogos',
    'costos',
    'bitacora',
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
