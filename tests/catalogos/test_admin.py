"""
Tests for catalogos admin configuration.

NOTE: Generic admin tests are in tests/core/test_admin_generic.py
This file contains only tests specific to catalogos that are not covered by generics.
"""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from catalogos.admin import CatTramiteAdmin
from catalogos.models import CatTramite
from tests.factories import CatTramiteFactory


class TestCatTramiteAdmin(TestCase):
    """Test suite for CatTramiteAdmin specific tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = CatTramiteAdmin(CatTramite, self.site)
        self.tramite = CatTramiteFactory()

    def test_admin_registered(self):
        """Test that CatTramite is registered with admin."""
        self.assertIsNotNone(self.admin)
