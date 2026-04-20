"""
Django management command to create RBAC roles.

This command is a thin wrapper around core.rbac functions. The permission
definitions are centralized in core/rbac/constants.py for visibility
and maintainability.

Creates three roles:
- Administrador: Full permissions on auth and tramites apps + custom Jazzmin permissions
- Coordinador: Custom Jazzmin permissions for sidebar visibility
- Analista: Custom Jazzmin permissions for sidebar visibility

Custom permissions control visibility of custom links in Jazzmin sidebar:
- view_mis_tramites: Trámites/Mis Trámites (Analista only)
- view_todos: Trámites/Todos (Administrador, Coordinador)
- view_disponibles: Trámites/Disponibles (All roles)
- view_asignados: Trámites/Asignados (Administrador, Coordinador)
- view_finalizados: Trámites/Finalizados (Administrador, Coordinador)

Usage:
    python manage.py setup_roles

For permission definitions, see: core.rbac.constants
"""

from django.core.management.base import BaseCommand

from core.rbac import setup_all_roles
from core.rbac.constants import ADMINISTRADOR_APPS


class Command(BaseCommand):
    """Create all RBAC roles with appropriate permissions."""

    help = (
        'Create all RBAC roles (Administrador, Coordinador, Analista). '
        'See core/rbac/constants.py for permission definitions.'
    )

    def handle(self, *args, **options) -> None:
        """Execute the role setup command."""
        self.stdout.write(self.style.SUCCESS('Starting role setup...'))

        # Setup all roles (Administrador, Coordinador, Analista)
        admin_group, coordinador_group, analista_group = setup_all_roles()

        # Display Administrador details
        admin_perms = admin_group.permissions.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'  - {admin_group.name}: {admin_perms} permissions '
                f'(apps: {", ".join(ADMINISTRADOR_APPS)} + custom Jazzmin permissions)'
            )
        )

        # Display Coordinador details
        coordinador_perms = coordinador_group.permissions.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'  - {coordinador_group.name}: {coordinador_perms} custom Jazzmin permissions '
                '(view_todos, view_disponibles, view_asignados, view_finalizados)'
            )
        )

        # Display Analista details
        analista_perms = analista_group.permissions.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'  - {analista_group.name}: {analista_perms} custom Jazzmin permissions '
                '(view_mis_tramites, view_disponibles)'
            )
        )

        self.stdout.write(self.style.SUCCESS('Role setup completed successfully'))
