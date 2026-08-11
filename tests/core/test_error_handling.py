"""Error handling tests for setup_roles command.

Verifies that setup_roles is robust against edge cases:
- Running without pre-existing groups or permissions
- Re-running multiple times (idempotency)
"""

from django.contrib.auth.models import Group, Permission
from django.core.management import call_command

from core.rbac.constants import (
    ROLE_CUSTOM_PERMISSIONS,
    TRAMITES_CUSTOM_PERMISSIONS,
    BackOfficeRole,
)


def test_setup_roles_creates_groups_without_preconditions(db):  # noqa: ARG001
    """setup_roles succeeds even when no groups or permissions exist beforehand."""
    # Delete all groups to simulate fresh state
    Group.objects.filter(name__in=list(BackOfficeRole)).delete()

    # Should not raise any exception
    call_command('setup_roles', verbosity=0)

    # All groups should be created
    for role in BackOfficeRole:
        assert Group.objects.filter(name=role).exists(), f'{role} group was not created'


def test_setup_roles_idempotent(db):  # noqa: ARG001
    """setup_roles produces the same result when run multiple times."""
    call_command('setup_roles', verbosity=0)
    call_command('setup_roles', verbosity=0)  # Second run

    # All groups still exist with correct permissions
    for role in BackOfficeRole:
        group = Group.objects.get(name=role)
        expected_perms = set(ROLE_CUSTOM_PERMISSIONS[role])
        actual_perms = set(
            group.permissions.filter(
                content_type__app_label='tramites',
                codename__in=TRAMITES_CUSTOM_PERMISSIONS,
            ).values_list('codename', flat=True)
        )
        assert actual_perms == expected_perms, (
            f'{role.name}: expected {expected_perms}, got {actual_perms}'
        )


def test_setup_roles_preserves_all_custom_permissions(db):  # noqa: ARG001
    """setup_roles ensures all custom permissions exist after any number of runs."""
    call_command('setup_roles', verbosity=0)

    for codename in TRAMITES_CUSTOM_PERMISSIONS:
        exists = Permission.objects.filter(
            codename=codename,
            content_type__app_label='tramites',
        ).exists()
        assert exists, f'Permission {codename} was not created'
