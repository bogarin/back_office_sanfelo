"""
Tests for BackofficeAdminSite.

This module contains tests for:
- Admin site module visibility control
- Role-based admin access
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.test import TestCase

from core.admin import BackofficeAdminSite

User = get_user_model()


class TestBackofficeAdminSite(TestCase):
    """Test suite for BackofficeAdminSite module visibility control."""

    multi_db = True  # Allow access to both databases

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.admin_site = BackofficeAdminSite()

    def test_superuser_sees_all_modules(self) -> None:
        """Test that superusers can see all modules."""
        # Create a superuser
        superuser = User.objects.create_superuser(
            username='test_superuser',
            email='superuser@example.com',
            password='testpass123',
        )

        # Create a mock request with superuser
        request = HttpRequest()
        request.user = superuser

        # Should see all modules
        self.assertTrue(self.admin_site.has_module_permission(request, 'auth'))
        self.assertTrue(self.admin_site.has_module_permission(request, 'tramites'))
        self.assertTrue(self.admin_site.has_module_permission(request, 'buzon'))

    def test_administrador_sees_all_modules(self) -> None:
        """Test that Administrador users can see all modules."""
        # Create Administrador group
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

        # Should see all modules
        self.assertTrue(self.admin_site.has_module_permission(request, 'auth'))
        self.assertTrue(self.admin_site.has_module_permission(request, 'tramites'))
        self.assertTrue(self.admin_site.has_module_permission(request, 'buzon'))

    def test_has_permission_checks_staff_and_active(self) -> None:
        """Test that has_permission checks user is staff and active."""
        admin_site = BackofficeAdminSite()

        # Active staff user
        request = HttpRequest()
        request.user = type('User', (), {'is_staff': True, 'is_active': True})()
        self.assertTrue(admin_site.has_permission(request))

        # Inactive user
        request.user = type('User', (), {'is_staff': True, 'is_active': False})()
        self.assertFalse(admin_site.has_permission(request))

        # Non-staff user
        request.user = type('User', (), {'is_staff': False, 'is_active': True})()
        self.assertFalse(admin_site.has_permission(request))
