"""
Django management command to create RBAC roles and repair inconsistencies.

This command is a thin wrapper around core.rbac functions. The permission
definitions are centralized in core/rbac/constants.py for visibility
and maintainability.

Creates three roles:
- Administrador: Full permissions on auth and tramites apps + custom Jazzmin permissions
- Coordinador: Custom Jazzmin permissions for sidebar visibility
- Analista: Custom Jazzmin permissions for sidebar visibility

Custom permissions control visibility of custom links in Jazzmin sidebar:
- acceso_analista: Mis trámites + Disponibles (Analista + Administrador)
- acceso_coordinador: Trámites en curso + Finalizados (Coordinador + Administrador)

Also repairs is_staff inconsistencies: any user belonging to an RBAC group
with is_staff=False is automatically corrected.

Usage:
    python manage.py setup_roles

For permission definitions, see: core.rbac.constants
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.rbac import setup_all_roles
from core.rbac.constants import ADMINISTRADOR_APPS, BackOfficeRole


class Command(BaseCommand):
    """Create all RBAC roles with appropriate permissions and repair is_staff."""

    help = (
        'Create all RBAC roles (Administrador, Coordinador, Analista) '
        'and repair is_staff inconsistencies. '
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
                '(acceso_coordinador)'
            )
        )

        # Display Analista details
        analista_perms = analista_group.permissions.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'  - {analista_group.name}: {analista_perms} custom Jazzmin permissions '
                '(acceso_analista)'
            )
        )

        # Repair is_staff inconsistencies
        self._repair_is_staff()

        self.stdout.write(self.style.SUCCESS('Role setup completed successfully'))

    def _repair_is_staff(self) -> None:
        """Fix users in RBAC groups that have is_staff=False."""
        User = get_user_model()

        role_group_names = list(BackOfficeRole)
        users_in_role_groups = User.objects.filter(
            groups__name__in=role_group_names,
            is_staff=False,
        ).distinct()

        fixed_count = 0
        for user in users_in_role_groups:
            user.is_staff = True
            user.save(update_fields=['is_staff'])
            fixed_count += 1
            self.stdout.write(
                self.style.WARNING(f'  - Repaired is_staff for user: {user.username}')
            )

        if fixed_count:
            self.stdout.write(
                self.style.SUCCESS(f'  Repaired {fixed_count} user(s) with is_staff inconsistency.')
            )
        else:
            self.stdout.write(self.style.SUCCESS('  No is_staff inconsistencies found.'))
