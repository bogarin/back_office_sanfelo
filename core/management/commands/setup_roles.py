"""
Django management command to create Operator and Administrator groups.

This command is a thin wrapper around core.rbac functions. The permission
definitions are centralized in core/rbac/constants.py for visibility
and maintainability.

Usage:
    python manage.py setup_roles

For permission definitions, see: core.rbac.constants
"""

from django.core.management.base import BaseCommand

from core.rbac import setup_administrador, setup_operador
from core.rbac.constants import ADMINISTRADOR_APPS, OPERADOR_APPS


class Command(BaseCommand):
    """Create Operator and Administrator groups with appropriate permissions."""

    help = (
        'Create Operator and Administrator groups with appropriate permissions. '
        'See core/rbac/constants.py for permission definitions.'
    )

    def handle(self, *args, **options) -> None:
        """Execute the role setup command."""
        self.stdout.write(self.style.SUCCESS('Starting role setup...'))

        # Setup Administrador group
        admin_group = setup_administrador()
        admin_perms = admin_group.permissions.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Configured {admin_group.name} group with {admin_perms} permissions '
                f'(apps: {", ".join(ADMINISTRADOR_APPS)})'
            )
        )

        # Setup Operador group
        operator_group = setup_operador()
        operator_perms = operator_group.permissions.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Configured {operator_group.name} group with {operator_perms} view permissions '
                f'(apps: {", ".join(OPERADOR_APPS)})'
            )
        )

        self.stdout.write(self.style.SUCCESS('Role setup completed successfully'))
