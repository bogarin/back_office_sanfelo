"""
Tests for tramites admin configuration.

NOTE: Generic admin tests are in tests/core/test_admin_generic.py
This file contains only tests specific to tramites.
"""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from tests.factories import TramiteFactory
from tramites.admin import TramiteAdmin
from tramites.models import TramiteLegacy


class TestTramiteAdmin(TestCase):
    """Test suite for TramiteAdmin specific tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = TramiteAdmin(TramiteLegacy, self.site)
        self.tramite = TramiteFactory()

    def test_admin_registered(self):
        """Test that TramiteLegacy is registered with admin."""
        self.assertIsNotNone(self.admin)
