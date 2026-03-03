"""
Tests for RoleBasedAccessMixin.

This module contains tests for:
- Permission-based access control
- Role-based operations (view, add, change, delete)
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.test import TestCase

from core.admin import RoleBasedAccessMixin

User = get_user_model()


class TestRoleBasedAccessMixin(TestCase):
    """Test suite for RoleBasedAccessMixin."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        try:
            from catalogos.models import CatTramite

            # Create a ModelAdmin with RoleBasedAccessMixin
            class TestModelAdmin(RoleBasedAccessMixin, admin.ModelAdmin):
                pass

            self.model_admin = TestModelAdmin(CatTramite, admin.site)  # type: ignore
        except ImportError:
            self.skipTest('Business models not available')

    def test_superuser_has_full_access(self) -> None:
        """Test that superusers have full access to all operations."""
        # Create a superuser
        superuser = User.objects.create_superuser(
            username='test_superuser',
            email='superuser@example.com',
            password='testpass123',
        )

        # Create a mock request with superuser
        request = HttpRequest()
        request.user = superuser

        # Test all permissions
        self.assertTrue(self.model_admin.has_view_permission(request))
        self.assertTrue(self.model_admin.has_add_permission(request))
        self.assertTrue(self.model_admin.has_change_permission(request))
        self.assertTrue(self.model_admin.has_delete_permission(request))

    def test_administrador_has_full_access(self) -> None:
        """Test that Administrador users have full access to all operations."""
        # Get or create Administrador group
        admin_group, _ = Group.objects.get_or_create(name=settings.ADMINISTRADOR_GROUP_NAME)

        # Create an Administrador user
        admin_user = User.objects.create_user(
            username='test_admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
        )
        admin_user.groups.add(admin_group)

        # Create a mock request with Administrador user
        request = HttpRequest()
        request.user = admin_user

        # Test all permissions
        self.assertTrue(self.model_admin.has_view_permission(request))
        self.assertTrue(self.model_admin.has_add_permission(request))
        self.assertTrue(self.model_admin.has_change_permission(request))
        self.assertTrue(self.model_admin.has_delete_permission(request))

    def test_operador_has_read_only_access(self) -> None:
        """Test that Operador users have read-only access to allowed apps."""
        # Get or create Operador group
        operador_group, _ = Group.objects.get_or_create(name=settings.OPERADOR_GROUP_NAME)

        # Create an Operador user
        operador_user = User.objects.create_user(
            username='test_operator',
            email='operator@example.com',
            password='testpass123',
            is_staff=True,
        )
        operador_user.groups.add(operador_group)

        # Create a mock request with Operador user
        request = HttpRequest()
        request.user = operador_user

        # Can view
        self.assertTrue(self.model_admin.has_view_permission(request))

        # Cannot modify
        self.assertFalse(self.model_admin.has_add_permission(request))
        self.assertFalse(self.model_admin.has_change_permission(request))
        self.assertFalse(self.model_admin.has_delete_permission(request))

    def test_operator_helper_methods(self) -> None:
        """Test helper methods for role checking."""
        mixin = RoleBasedAccessMixin()

        # Test _is_allowed_app_for_operador
        self.assertTrue(mixin._is_allowed_app_for_operador('catalogos'))
        self.assertTrue(mixin._is_allowed_app_for_operador('costos'))
        self.assertTrue(mixin._is_allowed_app_for_operador('bitacora'))
        self.assertFalse(mixin._is_allowed_app_for_operador('tramites'))
        self.assertFalse(mixin._is_allowed_app_for_operador('auth'))
