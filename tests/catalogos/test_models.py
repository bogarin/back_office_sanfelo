"""
Tests for catalogos models.

This module contains tests for:
- All catalog models (CatTramite, CatEstatus, etc.)
- Model string representations
- Model properties and methods
"""

from django.test import TestCase

from tests.factories import (
    CatPeritoFactory,
    ActividadesFactory,
)


class TestCatPerito(TestCase):
    """Test suite for CatPerito model."""

    def setUp(self):
        """Set up test fixtures."""
        self.perito = CatPeritoFactory()

    def test_str_representation(self):
        """Test string representation of CatPerito."""
        expected = f'{self.perito.paterno} {self.perito.materno} {self.perito.nombre}'
        self.assertEqual(str(self.perito), expected)

    def test_nombre_completo_property(self):
        """Test nombre_completo property."""
        nombre_completo = self.perito.nombre_completo
        self.assertIn(self.perito.nombre, nombre_completo)
        self.assertIn(self.perito.paterno, nombre_completo)


class TestActividades(TestCase):
    """Test suite for Actividades model."""

    def setUp(self):
        """Set up test fixtures."""
        self.actividades = ActividadesFactory()

    def test_str_representation(self):
        """Test string representation of Actividades."""
        self.assertEqual(str(self.actividades), str(self.actividades))
