"""
Tests for bitacora admin configuration.

NOTE: Generic admin tests are in tests/core/test_admin_generic.py
This file contains only tests specific to bitacora (read-only behavior).
"""

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase

from bitacora.admin import BitacoraAdmin
from bitacora.models import Bitacora
from tests.factories import BitacoraFactory


class TestBitacoraAdmin(TestCase):
    """Test suite for BitacoraAdmin specific tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = BitacoraAdmin(Bitacora, self.site)
        self.bitacora = BitacoraFactory()

    def test_admin_registered(self):
        """Test that Bitacora is registered with admin."""
        self.assertIsNotNone(self.admin)

    def test_readonly_permissions(self):
        """Test that Bitacora is read-only (no add/change/delete)."""
        User = get_user_model()
        request = HttpRequest()
        request.user = User.objects.create_superuser(
            username='test',
            email='test@example.com',
            password='test123',
        )

        self.assertFalse(self.admin.has_add_permission(request))
        self.assertFalse(self.admin.has_change_permission(request))
        self.assertFalse(self.admin.has_delete_permission(request))
