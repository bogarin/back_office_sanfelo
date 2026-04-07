"""
Tests for catalog admin configuration (now in tramites app).

NOTE: Generic admin tests are in tests/core/test_admin_generic.py
This file contains only tests specific to catalog admins not covered by generics.
"""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from tests.factories import ActividadesFactory, PeritoFactory
from tramites.admin import ActividadesAdmin, PeritoAdmin
from tramites.models import Actividades, Perito


class TestPeritoAdmin(TestCase):
    """Test suite for PeritoAdmin specific tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = PeritoAdmin(Perito, self.site)
        self.perito = PeritoFactory()

    def test_admin_registered(self):
        """Test that Perito admin is configured."""
        self.assertIsNotNone(self.admin)


class TestActividadesAdmin(TestCase):
    """Test suite for ActividadesAdmin specific tests."""

    def setUp(self):
        """Set up test fixtures."""
        self.site = AdminSite()
        self.admin = ActividadesAdmin(Actividades, self.site)
        self.actividades = ActividadesFactory()

    def test_admin_registered(self):
        """Test that Actividades admin is configured."""
        self.assertIsNotNone(self.admin)
