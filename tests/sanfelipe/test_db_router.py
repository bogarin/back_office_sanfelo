"""
Tests for ModelBasedRouter.

This module contains tests for:
- Database routing logic based on model configuration
- Model-specific routing
- Cross-database relation blocking
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from core.db_router import ModelBasedRouter


class TestDatabaseRouter(TestCase):
    """Test suite for ModelBasedRouter."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.router = ModelBasedRouter()

    def test_auth_apps_routing(self) -> None:
        """Test that auth apps route to default database."""
        # Test Permission model (not registered, should use default)
        self.assertEqual(self.router.db_for_read(Permission), 'default')
        self.assertEqual(self.router.db_for_write(Permission), 'default')

        # Test Group model (not registered, should use default)
        self.assertEqual(self.router.db_for_read(Group), 'default')
        self.assertEqual(self.router.db_for_write(Group), 'default')

        # Test ContentType model (not registered, should use default)
        self.assertEqual(self.router.db_for_read(ContentType), 'default')
        self.assertEqual(self.router.db_for_write(ContentType), 'default')

    def test_business_models_routing(self) -> None:
        """Test that business models route to correct database based on @register_model configuration."""
        try:
            from tramites.models import Actividad, Tramite
            from core.model_config import get_model_config
        except ImportError:
            self.skipTest('Business models not available')

        # Test Tramite routes to default (READ_ONLY)
        self.assertEqual(self.router.db_for_read(Tramite), 'default')
        self.assertEqual(self.router.db_for_write(Tramite), 'default')

        # Test Actividad routes to backend (READ_ONLY)
        self.assertEqual(self.router.db_for_read(Actividad), 'backend')
        self.assertEqual(self.router.db_for_write(Actividad), 'backend')

        # Verify model configurations
        tramite_config = get_model_config(Tramite)
        self.assertIsNotNone(tramite_config)
        self.assertEqual(tramite_config.db_alias, 'default')

        actividad_config = get_model_config(Actividad)
        self.assertIsNotNone(actividad_config)
        self.assertEqual(actividad_config.db_alias, 'backend')

    def test_cross_db_relations_blocked(self) -> None:
        """Test that cross-database relations are blocked."""
        try:
            from tramites.models import Actividad, Tramite
        except ImportError:
            self.skipTest('Business models not available')

        # Test relations within backend apps (PostgreSQL) - should be blocked
        # Note: Tramite is now in default (backoffice), not backend
        # Actividad is in backend - cross-DB relation should be blocked
        self.assertFalse(self.router.allow_relation(Tramite, Actividad))

        # Test relations within default apps - should be allowed
        self.assertTrue(self.router.allow_relation(Group, Permission))

        # Test same-database relations - should be allowed
        # Tramite (default) with Group (default) - same DB, should be allowed
        self.assertTrue(self.router.allow_relation(Tramite, Group))

    def test_migration_routing(self) -> None:
        """Test that migrations are routed correctly based on model configuration."""
        try:
            from tramites.models import Actividad, Tramite
            from core.model_config import get_model_config
            from core.model_config import AccessPattern
        except ImportError:
            self.skipTest('Business models not available')

        # Test READ_ONLY models - should not allow migrations
        tramite_config = get_model_config(Tramite)
        self.assertIsNotNone(tramite_config)
        self.assertEqual(tramite_config.access_pattern, AccessPattern.READ_ONLY)
        self.assertFalse(tramite_config.allow_migrations)

        actividad_config = get_model_config(Actividad)
        self.assertIsNotNone(actividad_config)
        self.assertEqual(actividad_config.access_pattern, AccessPattern.READ_ONLY)
        self.assertFalse(actividad_config.allow_migrations)

    def test_unregistered_models_routing(self) -> None:
        """Test that unregistered models route to default database."""
        # Auth models are not registered with @register_model
        # They should route to default database
        self.assertEqual(self.router.db_for_read(Group), 'default')
        self.assertEqual(self.router.db_for_write(Permission), 'default')
        self.assertEqual(self.router.db_for_read(ContentType), 'default')
