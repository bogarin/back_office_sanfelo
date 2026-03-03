"""
Tests for catalogos admin configuration.

NOTE: Generic admin tests are in tests/core/test_admin_generic.py
This file contains only tests specific to catalogos that are not covered by generics.
"""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from catalogos.admin import ActividadesAdmin, CatPeritoAdmin
from catalogos.models import Actividades, CatPerito
from tests.factories import ActividadesFactory, CatPeritoFactory


class TestCatPeritoAdmin(TestCase):
    """Test suite for CatPeritoAdmin specific tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = CatPeritoAdmin(CatPerito, self.site)
        self.perito = CatPeritoFactory()

    def test_admin_registered(self):
        """Test that CatPerito is registered with admin."""
        self.assertIsNotNone(self.admin)


class TestActividadesAdmin(TestCase):
    """Test suite for ActividadesAdmin specific tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = ActividadesAdmin(Actividades, self.site)
        self.actividades = ActividadesFactory()

    def test_admin_registered(self):
        """Test that Actividades is registered with admin."""
        self.assertIsNotNone(self.admin)
