"""
Role-Based Access Control (RBAC) module.

This module provides the core functionality for managing roles and permissions
in the San Felipe backoffice system.

Usage:
    from core.rbac import setup_administrador, setup_operador

    # Setup roles
    admin_group = setup_administrador()
    operator_group = setup_operador()

For permission definitions, see: core.rbac.constants
"""

import logging
from typing import List, Optional

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .constants import (
    ADMINISTRADOR_APPS,
    OPERADOR_APPS,
    PermissionType,
    Role,
)

logger = logging.getLogger(__name__)


def get_or_create_group(group_name: str) -> tuple[Group, bool]:
    """
    Get or create a group by name.

    Args:
        group_name: Name of the group to create/get

    Returns:
        Tuple of (Group, created) - created is True if group was newly created
    """
    return Group.objects.get_or_create(name=group_name)


def get_content_types_for_apps(app_labels: List[str]) -> List[ContentType]:
    """
    Get all ContentType objects for the given app labels.

    Args:
        app_labels: List of Django app labels (e.g., ['catalogos', 'costos'])

    Returns:
        List of ContentType objects
    """
    return list(ContentType.objects.filter(app_label__in=app_labels))


def get_permissions_for_apps(
    app_labels: List[str], permission_types: Optional[List[str]] = None
) -> List[Permission]:
    """
    Get all permissions for the given apps and permission types.

    Args:
        app_labels: List of Django app labels
        permission_types: List of permission types (e.g., ['add', 'change', 'delete', 'view'])
                         If None, returns all permissions

    Returns:
        List of Permission objects
    """
    content_types = get_content_types_for_apps(app_labels)

    if permission_types is None:
        # All permissions
        return list(Permission.objects.filter(content_type__in=content_types))

    # Specific permission types
    codenames = [f'{pt}_{ct.model}' for ct in content_types for pt in permission_types]
    return list(Permission.objects.filter(codename__in=codenames))


def get_view_permissions_for_apps(app_labels: List[str]) -> List[Permission]:
    """
    Get only view permissions for the given apps.

    Args:
        app_labels: List of Django app labels

    Returns:
        List of view Permission objects
    """
    return get_permissions_for_apps(app_labels, [PermissionType.VIEW])


def setup_administrador() -> Group:
    """
    Setup the Administrador group with full permissions.

    The Administrador group receives:
    - All auth permissions (user/group management)
    - All permissions for business apps (catalogos, costos, bitacora, tramites)

    Returns:
        The configured Administrador group

    Raises:
        RuntimeError: If group creation or permission assignment fails
    """
    group_name = Role.ADMINISTRADOR

    try:
        admin_group, created = get_or_create_group(group_name)

        # Get all permissions for allowed apps
        permissions = get_permissions_for_apps(ADMINISTRADOR_APPS)

        # Clear existing and assign new permissions
        admin_group.permissions.clear()
        admin_group.permissions.set(permissions)

        logger.info(
            f'Configured {group_name} group with {len(permissions)} permissions '
            f'for apps: {", ".join(ADMINISTRADOR_APPS)}'
        )

        return admin_group

    except Exception as e:
        logger.error(f'Failed to configure {group_name} group: {e}', exc_info=True)
        raise RuntimeError(f'Failed to configure {group_name} group: {e}') from e


def setup_operador() -> Group:
    """
    Setup the Operador group with view-only permissions.

    The Operador group receives:
    - View-only permissions for business apps (catalogos, costos, bitacora)
    - No auth permissions (cannot manage users/groups)
    - No tramites permissions

    Returns:
        The configured Operador group

    Raises:
        RuntimeError: If group creation or permission assignment fails
    """
    group_name = Role.OPERADOR

    try:
        operator_group, created = get_or_create_group(group_name)

        # Get only view permissions for allowed apps
        permissions = get_view_permissions_for_apps(OPERADOR_APPS)

        # Clear existing and assign new permissions
        operator_group.permissions.clear()
        operator_group.permissions.set(permissions)

        logger.info(
            f'Configured {group_name} group with {len(permissions)} view permissions '
            f'for apps: {", ".join(OPERADOR_APPS)}'
        )

        return operator_group

    except Exception as e:
        logger.error(f'Failed to configure {group_name} group: {e}', exc_info=True)
        raise RuntimeError(f'Failed to configure {group_name} group: {e}') from e


def setup_all_roles() -> tuple[Group, Group]:
    """
    Setup all RBAC roles (Administrador and Operador).

    Returns:
        Tuple of (administrador_group, operador_group)
    """
    admin_group = setup_administrador()
    operator_group = setup_operador()
    return admin_group, operator_group
