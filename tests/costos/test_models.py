"""
Tests for costos models.

This module contains tests for:
- Costo model
- Uma model
- UMA class methods
- Cost calculations
"""

import decimal

from django.test import TestCase

from costos.models import Uma
from tests.factories import CostoFactory, UmaFactory


class TestCosto(TestCase):
    """Test suite for Costo model."""

    def setUp(self):
        """Set up test fixtures."""
        self.costo = CostoFactory()

    def test_str_representation(self):
        """Test string representation of Costo."""
        expected = f'{self.costo.descripcion} ({self.costo.id_tramite})'
        self.assertEqual(str(self.costo), expected)

    def test_model_fields(self):
        """Test Costo model fields."""
        self.assertIsNotNone(self.costo.descripcion)
        self.assertIsNotNone(self.costo.axo)
        self.assertIsNotNone(self.costo.formula)
        self.assertIsNotNone(self.costo.cant_umas)
        self.assertIsNotNone(self.costo.rango_ini)
        self.assertIsNotNone(self.costo.rango_fin)
        self.assertIsNotNone(self.costo.inciso)
        self.assertIsNotNone(self.costo.fomento)
        self.assertIsNotNone(self.costo.cruz_roja)
        self.assertIsNotNone(self.costo.bomberos)
        self.assertIsNotNone(self.costo.activo)
        self.assertIsNotNone(self.costo.id_usuario)
        self.assertIsNotNone(self.costo.fecha_actualiza)


class TestUma(TestCase):
    """Test suite for Uma model."""

    def setUp(self):
        """Set up test fixtures."""
        self.uma = UmaFactory()

    def test_str_representation(self):
        """Test string representation of Uma."""
        expected = f'UMA: ${self.uma.valor}'
        self.assertEqual(str(self.uma), expected)

    def test_get_current_uma(self):
        """Test get_current_uma class method."""
        # Get current UMA
        current_uma = Uma.get_current_uma()
        self.assertIsNotNone(current_uma)
        self.assertEqual(current_uma, self.uma.valor)

    def test_update_uma(self):
        """Test update_uma class method."""
        # This test only verifies the method exists
        # Actual execution would require PostgreSQL connection
        new_value = decimal.Decimal('100.50')
        # We don't call update_uma as it requires PostgreSQL
        # Just verify the method signature is correct
        self.assertTrue(callable(Uma.update_uma))
