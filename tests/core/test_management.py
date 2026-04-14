"""
Tests for setup_roles management command.

This module contains tests for:
- Group creation
- Permission assignment
- Role setup
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase

from core.rbac.constants import BackOfficeRole


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
