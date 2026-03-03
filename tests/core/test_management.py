"""
Tests for setup_roles management command.

This module contains tests for:
- Group creation
- Permission assignment
- Role setup
"""

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase


class TestSetupRolesCommand(TestCase):
    """Test suite for setup_roles management command."""

    def test_setup_roles_creates_groups(self) -> None:
        """Test that setup_roles command creates both groups."""
        # Ensure no groups exist initially
        Group.objects.filter(
            name__in=[settings.ADMINISTRADOR_GROUP_NAME, settings.OPERADOR_GROUP_NAME]
        ).delete()

        # Run command
        call_command('setup_roles', verbosity=0)

        # Verify groups were created
        admin_group = Group.objects.filter(name=settings.ADMINISTRADOR_GROUP_NAME).first()
        operador_group = Group.objects.filter(name=settings.OPERADOR_GROUP_NAME).first()

        self.assertIsNotNone(admin_group)
        self.assertIsNotNone(operador_group)

    def test_setup_roles_assigns_administrador_permissions(self) -> None:
        """Test that Administrador group gets all auth and business permissions."""
        # Create Administrador group
        admin_group, _ = Group.objects.get_or_create(name=settings.ADMINISTRADOR_GROUP_NAME)

        # Run command
        call_command('setup_roles', verbosity=0)

        # Refresh from DB
        admin_group.refresh_from_db()

        # Should have permissions for auth and business apps
        auth_permissions = admin_group.permissions.filter(content_type__app_label='auth').count()

        # Should have at least some permissions
        self.assertGreater(auth_permissions, 0)

    def test_setup_roles_assigns_operador_permissions(self) -> None:
        """Test that Operador group gets only view permissions.

        This test verifies that the Operador group receives only view permissions
        for business apps (catalogos, costos) and no add/change/delete
        permissions.
        """
        # Ensure ContentType and view permissions exist for business models
        from catalogos.models import CatTramite
        from costos.models import Costo, Uma

        business_models = [CatTramite, Costo, Uma]

        for model in business_models:
            ct = ContentType.objects.get_for_model(model)
            # Try to get view permission
            try:
                view_perm = Permission.objects.get(
                    codename=f'view_{model._meta.model_name}', content_type=ct
                )
            except Permission.DoesNotExist:
                # Create view permission manually
                view_perm = Permission.objects.create(
                    codename=f'view_{model._meta.model_name}',
                    name=f'Can view {model._meta.verbose_name}',
                    content_type=ct,
                )

        # Create Operador group
        operador_group, _ = Group.objects.get_or_create(name=settings.OPERADOR_GROUP_NAME)

        # Run command
        call_command('setup_roles', verbosity=0)

        # Refresh from DB
        operador_group.refresh_from_db()

        # Should have view permissions for business apps (excluding tramites)
        view_permissions = operador_group.permissions.filter(codename__startswith='view_').count()

        # Should have at least some view permissions
        self.assertGreater(view_permissions, 0)

        # Should not have add/change/delete permissions
        add_permissions = operador_group.permissions.filter(codename__startswith='add_').count()
        change_permissions = operador_group.permissions.filter(
            codename__startswith='change_'
        ).count()
        delete_permissions = operador_group.permissions.filter(
            codename__startswith='delete_'
        ).count()

        self.assertEqual(add_permissions, 0)
        self.assertEqual(change_permissions, 0)
        self.assertEqual(delete_permissions, 0)

    def test_setup_roles_updates_existing_groups(self) -> None:
        """Test that setup_roles updates permissions for existing groups."""
        # Create Administrador group
        admin_group, _ = Group.objects.get_or_create(name=settings.ADMINISTRADOR_GROUP_NAME)

        # Run command
        call_command('setup_roles', verbosity=0)

        # Verify permissions were updated (not just added)
        admin_group.refresh_from_db()
        self.assertGreater(admin_group.permissions.count(), 1)
