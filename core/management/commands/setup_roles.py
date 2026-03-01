"""Django management command to create Operator and Administrator groups with appropriate permissions.

This command implements role-based access control (RBAC) for the San Felipe backoffice system.
Permissions are assigned explicitly to avoid granting unnecessary access.

Permission Strategy:
- Administrador: Full access to auth (user/group management) and all business apps
- Operador: View-only access to business apps (catalogos, costos, bitacora)
"""

import logging
from typing import List

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Create Operator and Administrator groups with explicit, controlled permissions."""

    help = (
        'Create Operator and Administrator groups with appropriate permissions. '
        'Administrador gets full access to auth and business apps. '
        'Operador gets view-only access to business apps.'
    )

    def handle(self, *args, **options) -> None:
        """Execute the role setup command."""
        self.stdout.write(self.style.SUCCESS('Starting role setup...'))

        # Create and configure Administrador group
        admin_group = self._setup_administrador_group()

        # Create and configure Operador group
        operator_group = self._setup_operador_group()

        self.stdout.write(self.style.SUCCESS('Role setup completed successfully'))

    def _setup_administrador_group(self) -> Group:
        """Create and configure the Administrador group with appropriate permissions.

        The Administrador group receives:
        - All auth permissions (for user/group management via Django admin)
        - All permissions for business apps (catalogos, costos, bitacora, tramites)

        Returns:
            Group: The configured Administrador group

        Raises:
            RuntimeError: If group creation or permission assignment fails
        """
        group_name = settings.ADMINISTRADOR_GROUP_NAME

        try:
            admin_group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created {group_name} group'))
                logger.info(f'Created new group: {group_name}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'{group_name} group already exists, updating permissions')
                )

            # Define app labels for which to grant all permissions
            # auth: User/group management (Django admin access)
            # Business apps: catalogos, costos, bitacora, tramites
            admin_app_labels: List[str] = ['auth', 'catalogos', 'costos', 'bitacora', 'tramites']

            # Get content types for all specified apps
            content_types = ContentType.objects.filter(app_label__in=admin_app_labels)

            # Get all permissions for these content types
            permissions = Permission.objects.filter(content_type__in=content_types)

            # Clear existing permissions and assign new ones
            admin_group.permissions.clear()
            admin_group.permissions.set(permissions)

            # Log detailed permission assignment
            permission_count = permissions.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Added {permission_count} permissions to {group_name} group '
                    f'(apps: {", ".join(admin_app_labels)})'
                )
            )
            logger.info(
                f'Assigned {permission_count} permissions to {group_name} group '
                f'for apps: {", ".join(admin_app_labels)}'
            )

            return admin_group

        except Exception as e:
            error_msg = f'Failed to configure {group_name} group: {e}'
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    def _setup_operador_group(self) -> Group:
        """Create and configure the Operador group with view-only permissions.

        The Operador group receives:
        - View-only permissions for business apps (catalogos, costos, bitacora)
        - No auth permissions (cannot manage users/groups)

        Note: tramites app is excluded from Operador view permissions
        as per original implementation.

        Returns:
            Group: The configured Operador group

        Raises:
            RuntimeError: If group creation or permission assignment fails
        """
        group_name = settings.OPERADOR_GROUP_NAME

        try:
            operator_group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created {group_name} group'))
                logger.info(f'Created new group: {group_name}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'{group_name} group already exists, updating permissions')
                )

            # Define app labels for view-only access
            # Note: tramites app is excluded per original implementation
            operator_app_labels: List[str] = ['catalogos', 'costos', 'bitacora']

            # Get content types for specified apps
            content_types = ContentType.objects.filter(app_label__in=operator_app_labels)

            # Clear existing permissions
            operator_group.permissions.clear()

            # Assign view-only permissions for each content type
            permissions_added = 0
            for content_type in content_types:
                try:
                    # Get view permission for this model
                    view_permission = Permission.objects.get(
                        codename=f'view_{content_type.model}', content_type=content_type
                    )
                    operator_group.permissions.add(view_permission)
                    permissions_added += 1
                    logger.debug(
                        f'Added view_{content_type.model} permission to {group_name} group'
                    )
                except Permission.DoesNotExist:
                    # Log but don't fail if permission doesn't exist
                    # (some models might not have view permissions)
                    logger.warning(
                        f'View permission not found for model: {content_type.model} '
                        f'in app: {content_type.app_label}'
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Added {permissions_added} view permissions to {group_name} group '
                    f'(apps: {", ".join(operator_app_labels)})'
                )
            )
            logger.info(
                f'Assigned {permissions_added} view permissions to {group_name} group '
                f'for apps: {", ".join(operator_app_labels)}'
            )

            return operator_group

        except Exception as e:
            error_msg = f'Failed to configure {group_name} group: {e}'
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
