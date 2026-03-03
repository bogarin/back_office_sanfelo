"""
Tests for tramites models.

This module contains tests for:
- Tramite model
- Model properties
- Business logic
- Relationships
"""

from django.test import TestCase

from tests.factories import (
    TramiteFactory,
)


class TestTramite(TestCase):
    """Test suite for Tramite model."""

    def setUp(self):
        """Set up test fixtures."""
        self.tramite = TramiteFactory()

    def test_str_representation(self):
        """Test string representation of Tramite."""
        self.assertEqual(str(self.tramite), self.tramite.folio)

    def test_estatus_display_property(self):
        """Test estatus_display property."""
        estatus_display = self.tramite.estatus_display
        self.assertIsNotNone(estatus_display)
        # Should return the estatus name from CatEstatus

    def test_tramite_display_property(self):
        """Test tramite_display property."""
        tramite_display = self.tramite.tramite_display
        self.assertIsNotNone(tramite_display)
        # Should return the tramite name from CatTramite

    def test_model_fields(self):
        """Test Tramite model fields."""
        self.assertIsNotNone(self.tramite.folio)
        self.assertIsNotNone(self.tramite.id_cat_tramite)
        self.assertIsNotNone(self.tramite.id_cat_estatus)
        self.assertIsNotNone(self.tramite.clave_catastral)
        self.assertIsNotNone(self.tramite.es_propietario)
        self.assertIsNotNone(self.tramite.nom_sol)
        self.assertIsNotNone(self.tramite.pagado)
        self.assertIsNotNone(self.tramite.urgente)

    def test_folio_unique(self):
        """Test that folio is unique."""
        # Try to create another tramite with same folio
        with self.assertRaises(Exception):  # IntegrityError or similar
            TramiteFactory(folio=self.tramite.folio)
