"""
Role-Based Access Control (RBAC) module.

This module provides core functionality for managing roles and permissions
in San Felipe backoffice system.

Usage:
    from core.rbac import setup_all_roles

    # Setup all roles (Administrador, Coordinador, Analista)
    admin_group, coordinador_group, analista_group = setup_all_roles()

For permission definitions, see: core.rbac.constants
"""

import logging
from typing import List, Optional

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .constants import (
    ADMINISTRADOR_APPS,
    BackOfficeRole,
    PermissionType,
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
    Get all ContentType objects for given app labels.

    Args:
        app_labels: List of Django app labels (e.g., ['tramites'])

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
    Setup Administrador group with full permissions.

    The Administrador group receives:
    - All auth permissions (user/group management)
    - All permissions for business apps (tramites, core)

    Returns:
        The configured Administrador group

    Raises:
        RuntimeError: If group creation or permission assignment fails
    """
    group_name = BackOfficeRole.ADMINISTRADOR

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


def setup_coordinador() -> Group:
    """
    Setup Coordinador group.

    The Coordinador group receives:
    - No explicit permissions (access controlled by code in RoleBasedAccessMixin)

    Returns:
        The configured Coordinador group

    Raises:
        RuntimeError: If group creation fails
    """
    group_name = BackOfficeRole.COORDINADOR

    try:
        coordinador_group, _ = get_or_create_group(group_name)

        # Coordinador has no explicit permissions - access is controlled by code
        # RoleBasedAccessMixin and TramiteAdmin enforce permissions dynamically

        logger.info(f'Configured {group_name} group (permissions controlled by code)')

        return coordinador_group

    except Exception as e:
        logger.error(f'Failed to configure {group_name} group: {e}', exc_info=True)
        raise RuntimeError(f'Failed to configure {group_name} group: {e}') from e


def setup_analista() -> Group:
    """
    Setup Analista group.

    The Analista group receives:
    - No explicit permissions (access controlled by code in RoleBasedAccessMixin)

    Returns:
        The configured Analista group

    Raises:
        RuntimeError: If group creation fails
    """
    group_name = BackOfficeRole.ANALISTA

    try:
        analista_group, _ = get_or_create_group(group_name)

        # Analista has no explicit permissions - access is controlled by code
        # RoleBasedAccessMixin and TramiteAdmin enforce permissions dynamically

        logger.info(f'Configured {group_name} group (permissions controlled by code)')

        return analista_group

    except Exception as e:
        logger.error(f'Failed to configure {group_name} group: {e}', exc_info=True)
        raise RuntimeError(f'Failed to configure {group_name} group: {e}') from e


def setup_all_roles() -> tuple[Group, Group, Group]:
    """
    Setup all RBAC roles (Administrador, Coordinador, Analista).

    Returns:
        Tuple of (Administrador, Coordinador, Analista) groups
    """
    admin_group = setup_administrador()
    coordinador_group = setup_coordinador()
    analista_group = setup_analista()

    logger.info(
        f'Configured all roles: {admin_group.name}, {coordinador_group.name}, {analista_group.name}'
    )

    return admin_group, coordinador_group, analista_group
