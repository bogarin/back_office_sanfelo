"""
Tests for costos admin configuration.

NOTE: Generic admin tests are in tests/core/test_admin_generic.py
This file contains only tests specific to costos.
"""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from costos.admin import CostoAdmin, UmaAdmin
from costos.models import Costo, Uma
from tests.factories import CostoFactory, UmaFactory


class TestCostoAdmin(TestCase):
    """Test suite for CostoAdmin specific tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = CostoAdmin(Costo, self.site)
        self.costo = CostoFactory()

    def test_admin_registered(self):
        """Test that Costo is registered with admin."""
        self.assertIsNotNone(self.admin)


class TestUmaAdmin(TestCase):
    """Test suite for UmaAdmin specific tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = UmaAdmin(Uma, self.site)
        self.uma = UmaFactory()

    def test_admin_registered(self):
        """Test that Uma is registered with admin."""
        self.assertIsNotNone(self.admin)
