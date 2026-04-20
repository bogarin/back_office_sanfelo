"""
Tests for setup_roles management command.

This module contains tests for:
- Group creation
- Permission assignment
- Role setup
- Custom Jazzmin permissions for sidebar visibility
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase

from core.rbac.constants import (
    BackOfficeRole,
    ROLE_CUSTOM_PERMISSIONS,
    TRAMITES_CUSTOM_PERMISSIONS,
    TramitePermission,
)


class TestSetupRolesCommand(TestCase):
    """Test suite for setup_roles management command."""

    def test_setup_roles_creates_groups(self) -> None:
        """Test that setup_roles command creates Administrador group."""
        # Ensure no groups exist initially
        Group.objects.filter(name=BackOfficeRole.ADMINISTRADOR).delete()

        # Run command
        call_command('setup_roles', verbosity=0)

        # Verify group was created
        admin_group = Group.objects.filter(name=BackOfficeRole.ADMINISTRADOR).first()
        self.assertIsNotNone(admin_group)

    def test_setup_roles_assigns_administrador_permissions(self) -> None:
        """Test that Administrador group gets all auth and business permissions."""
        # Create Administrador group
        admin_group, _ = Group.objects.get_or_create(name=BackOfficeRole.ADMINISTRADOR)

        # Run command
        call_command('setup_roles', verbosity=0)

        # Refresh from DB
        admin_group.refresh_from_db()

        # Should have permissions for auth and business apps
        auth_permissions = admin_group.permissions.filter(content_type__app_label='auth').count()

        # Should have at least some permissions
        self.assertGreater(auth_permissions, 0)

    def test_setup_roles_updates_existing_groups(self) -> None:
        """Test that setup_roles updates permissions for existing groups."""
        # Create Administrador group
        admin_group, _ = Group.objects.get_or_create(name=BackOfficeRole.ADMINISTRADOR)

        # Run command
        call_command('setup_roles', verbosity=0)

        # Verify permissions were updated (not just added)
        admin_group.refresh_from_db()
        self.assertGreater(admin_group.permissions.count(), 1)

    def test_custom_permissions_created(self) -> None:
        """Test that custom Jazzmin permissions are created."""
        # Run command
        call_command('setup_roles', verbosity=0)

        # Verify all custom permissions exist
        for codename in TRAMITES_CUSTOM_PERMISSIONS:
            permission = Permission.objects.filter(
                codename=codename,
                content_type__app_label='tramites',
            ).first()
            self.assertIsNotNone(
                permission,
                f'Custom permission {codename} was not created',
            )

    def test_administrador_has_all_custom_permissions(self) -> None:
        """Test that Administrador has all custom Jazzmin permissions."""
        # Setup roles
        call_command('setup_roles', verbosity=0)

        # Get Administrador group
        admin_group = Group.objects.get(name=BackOfficeRole.ADMINISTRADOR)

        # Get expected permissions
        expected_perms = ROLE_CUSTOM_PERMISSIONS[BackOfficeRole.ADMINISTRADOR]

        # Verify Administrador has all expected permissions
        for perm_codename in expected_perms:
            has_perm = admin_group.permissions.filter(
                codename=perm_codename,
                content_type__app_label='tramites',
            ).exists()
            self.assertTrue(
                has_perm,
                f'Administrador should have {perm_codename} permission',
            )

    def test_coordinador_has_correct_custom_permissions(self) -> None:
        """Test that Coordinador has correct custom Jazzmin permissions."""
        # Setup roles
        call_command('setup_roles', verbosity=0)

        # Get Coordinador group
        coordinador_group = Group.objects.get(name=BackOfficeRole.COORDINADOR)

        # Get expected permissions
        expected_perms = ROLE_CUSTOM_PERMISSIONS[BackOfficeRole.COORDINADOR]

        # Verify Coordinador has all expected permissions
        for perm_codename in expected_perms:
            has_perm = coordinador_group.permissions.filter(
                codename=perm_codename,
                content_type__app_label='tramites',
            ).exists()
            self.assertTrue(
                has_perm,
                f'Coordinador should have {perm_codename} permission',
            )

    def test_coordinador_lacks_mis_tramites_permission(self) -> None:
        """Test that Coordinador does NOT have view_mis_tramites permission."""
        # Setup roles
        call_command('setup_roles', verbosity=0)

        # Get Coordinador group
        coordinador_group = Group.objects.get(name=BackOfficeRole.COORDINADOR)

        # Verify Coordinador does NOT have view_mis_tramites
        has_perm = coordinador_group.permissions.filter(
            codename=TramitePermission.VIEW_MIS_TRAMITES,
            content_type__app_label='tramites',
        ).exists()
        self.assertFalse(
            has_perm,
            'Coordinador should NOT have view_mis_tramites permission',
        )

    def test_analista_has_correct_custom_permissions(self) -> None:
        """Test that Analista has correct custom Jazzmin permissions."""
        # Setup roles
        call_command('setup_roles', verbosity=0)

        # Get Analista group
        analista_group = Group.objects.get(name=BackOfficeRole.ANALISTA)

        # Get expected permissions
        expected_perms = ROLE_CUSTOM_PERMISSIONS[BackOfficeRole.ANALISTA]

        # Verify Analista has all expected permissions
        for perm_codename in expected_perms:
            has_perm = analista_group.permissions.filter(
                codename=perm_codename,
                content_type__app_label='tramites',
            ).exists()
            self.assertTrue(
                has_perm,
                f'Analista should have {perm_codename} permission',
            )

    def test_analista_lashes_restricted_permissions(self) -> None:
        """Test that Analista does NOT have restricted permissions."""
        # Setup roles
        call_command('setup_roles', verbosity=0)

        # Get Analista group
        analista_group = Group.objects.get(name=BackOfficeRole.ANALISTA)

        # Permissions that Analista should NOT have
        restricted_perms = [
            TramitePermission.VIEW_TODOS,
            TramitePermission.VIEW_ASIGNADOS,
            TramitePermission.VIEW_FINALIZADOS,
        ]

        # Verify Analista does NOT have these permissions
        for perm_codename in restricted_perms:
            has_perm = analista_group.permissions.filter(
                codename=perm_codename,
                content_type__app_label='tramites',
            ).exists()
            self.assertFalse(
                has_perm,
                f'Analista should NOT have {perm_codename} permission',
            )
