"""
Tests for MultiDatabaseRouter.

This module contains tests for:
- Database routing logic
- App-specific routing
- Cross-database relation blocking
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from core.db_router import MultiDatabaseRouter


class TestDatabaseRouter(TestCase):
    """Test suite for MultiDatabaseRouter."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.router = MultiDatabaseRouter()

    def test_auth_apps_routing(self) -> None:
        """Test that auth apps route to SQLite (default)."""
        # Test User model
        self.assertEqual(self.router.db_for_read(Permission), 'default')
        self.assertEqual(self.router.db_for_write(Permission), 'default')

        # Test Group model
        self.assertEqual(self.router.db_for_read(Group), 'default')
        self.assertEqual(self.router.db_for_write(Group), 'default')

        # Test Permission model
        self.assertEqual(self.router.db_for_read(Permission), 'default')
        self.assertEqual(self.router.db_for_write(Permission), 'default')

        # Test ContentType model
        self.assertEqual(self.router.db_for_read(ContentType), 'default')
        self.assertEqual(self.router.db_for_write(ContentType), 'default')

    def test_business_apps_routing(self) -> None:
        """Test that business apps route to PostgreSQL (backend)."""
        try:
            from tramites.models import Actividad, Tramite
        except ImportError:
            self.skipTest('Business models not available')

        # Test business models route to backend DB
        self.assertEqual(self.router.db_for_read(Tramite), 'backend')
        self.assertEqual(self.router.db_for_write(Tramite), 'backend')

        self.assertEqual(self.router.db_for_read(Actividad), 'backend')
        self.assertEqual(self.router.db_for_write(Actividad), 'backend')

    def test_cross_db_relations_blocked(self) -> None:
        """Test that cross-database relations are blocked."""
        # Test relations within auth apps (SQLite) - should be allowed
        self.assertTrue(self.router.allow_relation(Group, Permission))

        # Test relations within backend apps (PostgreSQL) - should be allowed
        try:
            from tramites.models import Actividad, Tramite

            self.assertTrue(self.router.allow_relation(Tramite, Actividad))
        except ImportError:
            self.skipTest('Business models not available')

        # Test cross-database relations - should be blocked
        try:
            from tramites.models import Tramite

            self.assertFalse(self.router.allow_relation(Group, Tramite))
        except ImportError:
            self.skipTest('Business models not available')

    def test_migration_routing(self) -> None:
        """Test that migrations are routed to the correct database."""
        # Test auth apps -> only migrate on SQLite (default)
        self.assertTrue(self.router.allow_migrate('default', 'auth'))
        self.assertFalse(self.router.allow_migrate('backend', 'auth'))

        self.assertTrue(self.router.allow_migrate('default', 'contenttypes'))
        self.assertTrue(self.router.allow_migrate('default', 'admin'))

        # Test business apps -> never migrate (managed=False)
        self.assertFalse(self.router.allow_migrate('default', 'tramites'))
        self.assertFalse(self.router.allow_migrate('backend', 'tramites'))

        self.assertFalse(self.router.allow_migrate('default', 'core'))
        self.assertFalse(self.router.allow_migrate('backend', 'core'))

    def test_router_attributes(self) -> None:
        """Test that router attributes are correctly defined."""
        # Check auth apps
        self.assertIn('auth', self.router.AUTH_APPS)
        self.assertIn('contenttypes', self.router.AUTH_APPS)
        self.assertIn('admin', self.router.AUTH_APPS)
        self.assertIn('sessions', self.router.AUTH_APPS)

        # Check business apps
        self.assertIn('tramites', self.router.BUSINESS_APPS)
        self.assertIn('core', self.router.BUSINESS_APPS)

        # Check database aliases
        self.assertEqual(self.router.AUTH_DB, 'default')
        self.assertEqual(self.router.BUSINESS_DB, 'backend')
