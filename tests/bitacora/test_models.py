"""
Tests for bitacora models.

This module contains tests for:
- Bitacora model
- Audit trail functionality
- Model string representations
"""

from django.test import TestCase

from tests.factories import BitacoraFactory


class TestBitacora(TestCase):
    """Test suite for Bitacora model."""

    def setUp(self):
        """Set up test fixtures."""
        self.bitacora = BitacoraFactory()

    def test_str_representation(self):
        """Test string representation of Bitacora."""
        expected = f'{self.bitacora.usuario_sis} - {self.bitacora.tipo_mov} ({self.bitacora.fecha})'
        self.assertEqual(str(self.bitacora), expected)

    def test_model_fields(self):
        """Test Bitacora model fields."""
        self.assertIsNotNone(self.bitacora.usuario_sis)
        self.assertIsNotNone(self.bitacora.tipo_mov)
        self.assertIsNotNone(self.bitacora.usuario_pc)
        self.assertIsNotNone(self.bitacora.fecha)
        self.assertIsNotNone(self.bitacora.maquina)
        self.assertIsNotNone(self.bitacora.val_anterior)
        self.assertIsNotNone(self.bitacora.val_nuevo)
        self.assertIsNotNone(self.bitacora.observaciones)

    def test_tipo_mov_values(self):
        """Test that tipo_mov accepts valid values."""
        valid_types = ['CREATE', 'UPDATE', 'DELETE', 'VIEW']
        for tipo in valid_types:
            bitacora = BitacoraFactory(tipo_mov=tipo)
            self.assertEqual(bitacora.tipo_mov, tipo)
