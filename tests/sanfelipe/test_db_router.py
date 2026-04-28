"""
Tests for ModelBasedRouter.

This module contains tests for:
- Database routing logic based on model configuration
- Model-specific routing (identity and label-based)
- Cross-database relation blocking
- Migration routing with label-based fallback for migration stubs
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from core.db_router import ModelBasedRouter
from core.model_config import AccessPattern, get_model_config


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

    def test_user_model_routing(self) -> None:
        """Test that the custom User model routes to default database."""
        from core.models import User

        self.assertEqual(self.router.db_for_read(User), 'default')
        self.assertEqual(self.router.db_for_write(User), 'default')

        config = get_model_config(User)
        self.assertIsNotNone(config)
        self.assertEqual(config.db_alias, 'default')
        self.assertEqual(config.access_pattern, AccessPattern.FULL_ACCESS)
        self.assertTrue(config.allow_migrations)

    def test_business_models_routing(self) -> None:
        """Test that business models route to correct database based on @register_model configuration."""
        try:
            from tramites.models import Actividad, Tramite
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

        from core.models import User

        # Cross-DB: Tramite (default) ↔ Actividades (backend) → blocked
        self.assertFalse(self.router.allow_relation(Tramite, Actividad))

        # Both unregistered: Group ↔ Permission → allowed
        self.assertTrue(self.router.allow_relation(Group, Permission))

        # Same-DB, both registered: Tramite (default) ↔ User (default) → allowed
        self.assertTrue(self.router.allow_relation(Tramite, User))

        # One registered (default), one unregistered: Tramite ↔ Group → allowed
        # Unregistered models default to 'default' (same DB as Tramite).
        self.assertTrue(self.router.allow_relation(Tramite, Group))

        # One registered (backend), one unregistered: Actividad ↔ Group → blocked
        # Actividad is on 'backend', Group defaults to 'default' — different DBs.
        self.assertFalse(self.router.allow_relation(Actividad, Group))

    def test_migration_routing(self) -> None:
        """Test that migrations are routed correctly based on model configuration."""
        try:
            from tramites.models import Actividad, Tramite
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

    def test_allow_migrate_label_lookup(self) -> None:
        """Test allow_migrate with label-based lookup (migration stub scenario).

        During migrations Django creates stub classes via type() that are
        distinct objects from the real model classes.  Identity-based lookup
        fails for these stubs, but (app_label, model_name) are stable strings.
        """
        # Backend models: allow_migrations=False → blocked on ANY database
        self.assertFalse(
            self.router.allow_migrate('default', 'tramites', 'tramitecatalogo')
        )
        self.assertFalse(
            self.router.allow_migrate('backend', 'tramites', 'tramitecatalogo')
        )

        # Tramite (default, READ_ONLY, allow_migrations=False) → blocked
        self.assertFalse(
            self.router.allow_migrate('default', 'tramites', 'tramite')
        )

        # Actividades (backend, APPEND_ONLY, allow_migrations=False) → blocked
        self.assertFalse(
            self.router.allow_migrate('backend', 'tramites', 'actividades')
        )

        # Core User: allow_migrations=True, db='default'
        self.assertTrue(
            self.router.allow_migrate('default', 'core', 'user')
        )
        self.assertFalse(
            self.router.allow_migrate('backend', 'core', 'user')
        )

        # Unregistered models: default behavior → True (allow)
        self.assertTrue(
            self.router.allow_migrate('default', 'auth', 'group')
        )
        self.assertTrue(
            self.router.allow_migrate('default', 'contenttypes', 'contenttype')
        )

    def test_unregistered_models_routing(self) -> None:
        """Test that unregistered models route to default database."""
        # Auth models are not registered with @register_model
        # They should route to default database
        self.assertEqual(self.router.db_for_read(Group), 'default')
        self.assertEqual(self.router.db_for_write(Permission), 'default')
        self.assertEqual(self.router.db_for_read(ContentType), 'default')

    def test_label_registry_populated(self) -> None:
        """Test that the label-based registry is populated during model registration."""
        from core.model_config import get_model_config_by_label

        # Registered models should be findable by label
        config = get_model_config_by_label('tramites', 'tramite')
        self.assertIsNotNone(config)
        self.assertEqual(config.db_alias, 'default')

        config = get_model_config_by_label('tramites', 'tramitecatalogo')
        self.assertIsNotNone(config)
        self.assertEqual(config.db_alias, 'backend')

        config = get_model_config_by_label('core', 'user')
        self.assertIsNotNone(config)
        self.assertEqual(config.db_alias, 'default')
        self.assertTrue(config.allow_migrations)

        # Unregistered models should return None
        self.assertIsNone(get_model_config_by_label('auth', 'group'))
