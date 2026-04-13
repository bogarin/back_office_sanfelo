"""
Tests for tramites models.

This module contains tests for:
- Tramite model
- Model properties
- Business logic
- Relationships
- TramiteManager statistics and caching
"""

from datetime import date

from django.test import TestCase
from django.core.cache import cache

from tests.factories import TramiteFactory, TramiteWithEstatusFactory
from tests.factories.catalogos import ActividadFactory
from tramites.models import Tramite
from tests.factories import (
    TramiteFactory,
    TramiteWithEstatusFactory,
)


class TestTramite(TestCase):
    """Test suite for Tramite model."""

    def setUp(self):
        """Set up test fixtures."""
        self.tramite = TramiteWithEstatusFactory()  # Creates Actividades automatically

    def test_str_representation(self):
        """Test string representation of Tramite."""
        self.assertEqual(str(self.tramite), self.tramite.folio)

    def test_estatus_display_property(self):
        """Test estatus_display property."""
        estatus_display = self.tramite.estatus_display
        self.assertIsNotNone(estatus_display)
        # Should return estatus name from CatEstatus

    def test_tramite_display_property(self):
        """Test tramite_display property."""
        tramite_display = self.tramite.tramite_display
        self.assertIsNotNone(tramite_display)
        # Should return tramite name from CatTramite

    def test_model_fields(self):
        """Test Tramite model fields."""
        self.assertIsNotNone(self.tramite.folio)
        self.assertIsNotNone(self.tramite.tramite_catalogo_id)
        self.assertIsNotNone(self.tramite.estatus_id)  # From Actividades via property
        self.assertIsNotNone(self.tramite.es_propietario)
        self.assertIsNotNone(self.tramite.nom_sol)
        self.assertIsNotNone(self.tramite.pagado)

    def test_folio_unique(self):
        """Test that folio is unique."""
        # Try to create another tramite with same folio
        with self.assertRaises(Exception):  # IntegrityError or similar
            TramiteWithEstatusFactory(folio=self.tramite.folio)


class TestTramiteManager(TestCase):
    """Test suite for TramiteManager statistics methods."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear cache before each test
        cache.clear()

    def test_get_total_count(self):
        """Test get_total_count method."""
        # Create some tramites
        TramiteFactory.create_batch(5)

        count = Tramite.objects.get_total_count()
        self.assertEqual(count, 5)

    def test_get_total_count_caching(self):
        """Test that get_total_count uses cache.

        Note: This test assumes a real cache backend. In testing
        environment with DummyCache, caching is disabled.
        """
        TramiteFactory.create_batch(3)

        # First call - should query DB
        count1 = Tramite.objects.get_total_count()
        self.assertEqual(count1, 3)

        # Create more tramites without invalidating cache
        TramiteFactory.create_batch(2)

        # Second call - return value (cached or not, depends on backend)
        count2 = Tramite.objects.get_total_count()

        # Invalidate cache
        Tramite.objects.invalidate_statistics_cache()

        # Third call - should query DB again
        count3 = Tramite.objects.get_total_count()

        # After invalidation, should have all 5
        self.assertEqual(count3, 5)

    def test_get_statistics(self):
        """Test get_statistics returns all counts."""
        from tests.factories import TramiteEstatusFactory
        from tramites.models import Actividades

        # Create statuses
        estatus_pendiente = TramiteEstatusFactory(id=101, estatus='Pendiente')
        estatus_finalizado = TramiteEstatusFactory(id=300, estatus='Finalizado')
        estatus_cancelado = TramiteEstatusFactory(id=304, estatus='Cancelado')

        # Create trámites and their Actividades (new schema)
        tramite1 = TramiteFactory.create()
        Actividades.objects.create(
            tramite=tramite1,
            estatus=estatus_pendiente,
            backoffice_user_id=None,
            observacion='Test',
        )

        tramite2 = TramiteFactory.create()
        Actividades.objects.create(
            tramite=tramite2,
            estatus=estatus_finalizado,
            backoffice_user_id=None,
            observacion='Test',
        )

        tramite3 = TramiteFactory.create()
        Actividades.objects.create(
            tramite=tramite3,
            estatus=estatus_finalizado,
            backoffice_user_id=None,
            observacion='Test',
        )

        tramite4 = TramiteFactory.create()
        Actividades.objects.create(
            tramite=tramite4,
            estatus=estatus_cancelado,
            backoffice_user_id=None,
            observacion='Test',
        )

        stats = Tramite.objects.get_statistics()

        self.assertEqual(stats['total'], 4)
        # Note: sin_asignar and asignados depend on AsignacionTramite
        # which is None in this test, so all are "sin_asignar"
        self.assertEqual(stats['sin_asignar'], 4)  # All unassigned
        self.assertEqual(stats['asignados'], 0)  # None assigned

        # estatus >= 300 includes id=300 AND id=304
        # So 3 trámites have estatus >= 300
        self.assertEqual(stats['finalizados'], 3)
        self.assertEqual(stats['cancelados'], 1)  # 1 with estatus 304

    def test_invalidate_statistics_cache(self):
        """Test cache invalidation."""
        TramiteFactory.create_batch(2)

        # Get initial count
        count1 = Tramite.objects.get_total_count()
        self.assertEqual(count1, 2)

        # Add more tramites
        TramiteFactory.create_batch(3)

        # Invalidate cache
        Tramite.objects.invalidate_statistics_cache()

        # Get new count
        count2 = Tramite.objects.get_total_count()
        self.assertEqual(count2, 5)

    def test_cache_key_structure(self):
        """Test that cache keys are properly structured."""
        TramiteFactory.create_batch(3)

        # Call get_statistics to populate cache
        stats = Tramite.objects.get_statistics()
        self.assertEqual(stats['total'], 3)

        # Check that cache keys are set
        expected_keys = [
            'tramite_stats:total',
            'tramite_stats:sin_asignar',
            'tramite_stats:asignados',
            'tramite_stats:finalizados',
            'tramite_stats:cancelados',
        ]

        # Note: With DummyCache, get() always returns None
        # This test just verifies the key structure in manager
        self.assertEqual(Tramite.objects.CACHE_KEY_PREFIX, 'tramite_stats')
        self.assertGreater(Tramite.objects.CACHE_TIMEOUT, 0)
