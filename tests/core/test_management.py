"""Tests for setup_roles management command.

Verifies:
- Group creation for all three RBAC roles
- Permission assignment per role
- Custom Jazzmin permissions (acceso_analista, acceso_coordinador)
- is_staff auto-repair for users in RBAC groups
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command

from core.rbac.constants import (
    ROLE_CUSTOM_PERMISSIONS,
    TRAMITES_CUSTOM_PERMISSIONS,
    BackOfficeRole,
    TramitePermission,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Group creation
# ---------------------------------------------------------------------------


def test_setup_roles_creates_groups(db):
    """setup_roles creates all three RBAC groups."""
    Group.objects.filter(name__in=list(BackOfficeRole)).delete()

    call_command('setup_roles', verbosity=0)

    for role in BackOfficeRole:
        assert Group.objects.filter(name=role).exists(), f'Group {role} was not created'


def test_setup_roles_updates_existing_groups(db):
    """setup_roles updates permissions for existing groups."""
    Group.objects.get_or_create(name=BackOfficeRole.ADMINISTRADOR)

    call_command('setup_roles', verbosity=0)

    admin_group = Group.objects.get(name=BackOfficeRole.ADMINISTRADOR)
    assert admin_group.permissions.count() > 1


# ---------------------------------------------------------------------------
# Administrador permissions
# ---------------------------------------------------------------------------


def test_administrador_has_auth_permissions(db):
    """Administrador group gets auth permissions."""
    Group.objects.get_or_create(name=BackOfficeRole.ADMINISTRADOR)

    call_command('setup_roles', verbosity=0)

    admin_group = Group.objects.get(name=BackOfficeRole.ADMINISTRADOR)
    auth_permissions = admin_group.permissions.filter(content_type__app_label='auth').count()
    assert auth_permissions > 0


def test_administrador_has_all_custom_permissions(db):
    """Administrador has both acceso_analista and acceso_coordinador."""
    call_command('setup_roles', verbosity=0)

    admin_group = Group.objects.get(name=BackOfficeRole.ADMINISTRADOR)
    expected_perms = ROLE_CUSTOM_PERMISSIONS[BackOfficeRole.ADMINISTRADOR]

    for perm_codename in expected_perms:
        has_perm = admin_group.permissions.filter(
            codename=perm_codename,
            content_type__app_label='tramites',
        ).exists()
        assert has_perm, f'Administrador should have {perm_codename} permission'


# ---------------------------------------------------------------------------
# Custom permissions creation
# ---------------------------------------------------------------------------


def test_custom_permissions_created(db):
    """All custom permissions are created in the database."""
    call_command('setup_roles', verbosity=0)

    for codename in TRAMITES_CUSTOM_PERMISSIONS:
        permission = Permission.objects.filter(
            codename=codename,
            content_type__app_label='tramites',
        ).first()
        assert permission is not None, f'Custom permission {codename} was not created'


# ---------------------------------------------------------------------------
# Coordinador permissions
# ---------------------------------------------------------------------------


def test_coordinador_has_correct_custom_permissions(db):
    """Coordinador has acceso_coordinador permission."""
    call_command('setup_roles', verbosity=0)

    coordinador_group = Group.objects.get(name=BackOfficeRole.COORDINADOR)
    expected_perms = ROLE_CUSTOM_PERMISSIONS[BackOfficeRole.COORDINADOR]

    for perm_codename in expected_perms:
        has_perm = coordinador_group.permissions.filter(
            codename=perm_codename,
            content_type__app_label='tramites',
        ).exists()
        assert has_perm, f'Coordinador should have {perm_codename} permission'


def test_coordinador_lacks_analista_permission(db):
    """Coordinador does NOT have acceso_analista permission."""
    call_command('setup_roles', verbosity=0)

    coordinador_group = Group.objects.get(name=BackOfficeRole.COORDINADOR)
    has_perm = coordinador_group.permissions.filter(
        codename=TramitePermission.ACCESO_ANALISTA,
        content_type__app_label='tramites',
    ).exists()
    assert not has_perm, 'Coordinador should NOT have acceso_analista permission'


# ---------------------------------------------------------------------------
# Analista permissions
# ---------------------------------------------------------------------------


def test_analista_has_correct_custom_permissions(db):
    """Analista has acceso_analista permission."""
    call_command('setup_roles', verbosity=0)

    analista_group = Group.objects.get(name=BackOfficeRole.ANALISTA)
    expected_perms = ROLE_CUSTOM_PERMISSIONS[BackOfficeRole.ANALISTA]

    for perm_codename in expected_perms:
        has_perm = analista_group.permissions.filter(
            codename=perm_codename,
            content_type__app_label='tramites',
        ).exists()
        assert has_perm, f'Analista should have {perm_codename} permission'


def test_analista_lacks_coordinador_permission(db):
    """Analista does NOT have acceso_coordinador permission."""
    call_command('setup_roles', verbosity=0)

    analista_group = Group.objects.get(name=BackOfficeRole.ANALISTA)
    has_perm = analista_group.permissions.filter(
        codename=TramitePermission.ACCESO_COORDINADOR,
        content_type__app_label='tramites',
    ).exists()
    assert not has_perm, 'Analista should NOT have acceso_coordinador permission'


# ---------------------------------------------------------------------------
# is_staff auto-repair
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'role',
    list(BackOfficeRole),
    ids=[r.name for r in BackOfficeRole],
)
def test_setup_roles_repairs_is_staff(db, role):
    """setup_roles fixes is_staff for users in RBAC groups with is_staff=False."""
    call_command('setup_roles', verbosity=0)

    group = Group.objects.get(name=role)
    user = User.objects.create_user(
        username=f'broken_{role.name.lower()}',
        password='pass',
        is_staff=False,
    )
    user.groups.add(group)

    # Re-run setup_roles to trigger repair
    call_command('setup_roles', verbosity=0)

    user.refresh_from_db()
    assert user.is_staff is True, f'is_staff not repaired for {role.name}'


def test_setup_roles_does_not_touch_users_without_roles(db):
    """setup_roles does not modify users outside RBAC groups."""
    call_command('setup_roles', verbosity=0)

    user = User.objects.create_user(
        username='no_role_user',
        password='pass',
        is_staff=False,
    )

    call_command('setup_roles', verbosity=0)

    user.refresh_from_db()
    assert user.is_staff is False
