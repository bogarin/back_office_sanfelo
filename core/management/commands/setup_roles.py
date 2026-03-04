"""
Django management command to create Administrator groups.

This command is a thin wrapper around core.rbac functions. The permission
definitions are centralized in core/rbac/constants.py for visibility
and maintainability.

Usage:
    python manage.py setup_roles

For permission definitions, see: core.rbac.constants
"""

from django.core.management.base import BaseCommand

from core.rbac import setup_all_roles
from core.rbac.constants import ADMINISTRADOR_APPS


class Command(BaseCommand):
    """Create Administrator group with appropriate permissions."""

    help = (
        'Create Administrator group with appropriate permissions. '
        'See core/rbac/constants.py for permission definitions.'
    )

    def handle(self, *args, **options) -> None:
        """Execute the role setup command."""
        self.stdout.write(self.style.SUCCESS('Starting role setup...'))

        # Setup Administrador group
        admin_group = setup_all_roles()
        admin_perms = admin_group.permissions.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Configured {admin_group.name} group with {admin_perms} permissions '
                f'(apps: {", ".join(ADMINISTRADOR_APPS)})'
            )
        )

        self.stdout.write(self.style.SUCCESS('Role setup completed successfully'))
