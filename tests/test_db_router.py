#!/usr/bin/env python
"""
Test script to verify MultiDatabaseRouter functionality.

This script tests the database routing logic to ensure:
1. Auth apps route to SQLite (default)
2. Business apps route to PostgreSQL (business)
3. Relations are correctly allowed/blocked
4. Migrations are routed appropriately

Run this script from the Django project root:
    python -m pytest tests/test_db_router.py -v
Or directly:
    python tests/test_db_router.py
"""

import os
import sys
import django
from pathlib import Path

# Setup Django settings
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanfelipe.settings')

django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from sanfelipe.db_router import MultiDatabaseRouter


def test_db_router_read_routing():
    """Test that read queries are routed to the correct database."""
    router = MultiDatabaseRouter()

    print('\n=== Testing db_for_read Routing ===')

    # Test auth apps → SQLite (default)
    print('\nAuth Models → SQLite (default):')
    assert router.db_for_read(User) == 'default', 'User should route to SQLite'
    print("  ✓ User → 'default'")

    assert router.db_for_read(Group) == 'default', 'Group should route to SQLite'
    print("  ✓ Group → 'default'")

    assert router.db_for_read(Permission) == 'default', 'Permission should route to SQLite'
    print("  ✓ Permission → 'default'")

    assert router.db_for_read(ContentType) == 'default', 'ContentType should route to SQLite'
    print("  ✓ ContentType → 'default'")

    # Test business apps → PostgreSQL (business)
    print('\nBusiness Models → PostgreSQL (business):')
    try:
        from tramites.models import Tramite

        assert router.db_for_read(Tramite) == 'business', 'Tramite should route to PostgreSQL'
        print("  ✓ Tramite → 'business'")
    except ImportError:
        print('  ⊗ Tramite model not available (skipping)')

    try:
        from catalogos.models import CatActividad

        assert router.db_for_read(CatActividad) == 'business', (
            'CatActividad should route to PostgreSQL'
        )
        print("  ✓ CatActividad → 'business'")
    except ImportError:
        print('  ⊗ CatActividad model not available (skipping)')

    try:
        from costos.models import Costo

        assert router.db_for_read(Costo) == 'business', 'Costo should route to PostgreSQL'
        print("  ✓ Costo → 'business'")
    except ImportError:
        print('  ⊗ Costo model not available (skipping)')

    try:
        from bitacora.models import Bitacora

        assert router.db_for_read(Bitacora) == 'business', 'Bitacora should route to PostgreSQL'
        print("  ✓ Bitacora → 'business'")
    except ImportError:
        print('  ⊗ Bitacora model not available (skipping)')

    try:
        from core.models import (
            CatActividad,
            CatEstatus,
            CatPrioridad,
            CatTipoDocumento,
            CatUsuario,
        )

        assert router.db_for_read(CatActividad) == 'business', (
            'Core CatActividad should route to PostgreSQL'
        )
        print("  ✓ Core CatActividad → 'business'")
    except ImportError:
        print('  ⊗ Core models not available (skipping)')


def test_db_router_write_routing():
    """Test that write queries are routed to the correct database."""
    router = MultiDatabaseRouter()

    print('\n=== Testing db_for_write Routing ===')

    # Test auth apps → SQLite (default)
    print('\nAuth Models → SQLite (default):')
    assert router.db_for_write(User) == 'default', 'User should route to SQLite'
    print("  ✓ User → 'default'")

    assert router.db_for_write(Group) == 'default', 'Group should route to SQLite'
    print("  ✓ Group → 'default'")

    # Test business apps → PostgreSQL (business)
    print('\nBusiness Models → PostgreSQL (business):')
    try:
        from tramites.models import Tramite

        assert router.db_for_write(Tramite) == 'business', 'Tramite should route to PostgreSQL'
        print("  ✓ Tramite → 'business'")
    except ImportError:
        print('  ⊗ Tramite model not available (skipping)')

    try:
        from catalogos.models import CatActividad

        assert router.db_for_write(CatActividad) == 'business', (
            'CatActividad should route to PostgreSQL'
        )
        print("  ✓ CatActividad → 'business'")
    except ImportError:
        print('  ⊗ CatActividad model not available (skipping)')


def test_db_router_allow_relation():
    """Test that relations are correctly allowed/blocked."""
    router = MultiDatabaseRouter()

    print('\n=== Testing allow_relation ===')

    # Test relations within auth apps (SQLite) - should be allowed
    print('\nSame database relations (allowed):')
    assert router.allow_relation(User, Group) is True, 'User-Group relation should be allowed'
    print('  ✓ User ↔ Group (both SQLite) → True')

    assert router.allow_relation(User, Permission) is True, (
        'User-Permission relation should be allowed'
    )
    print('  ✓ User ↔ Permission (both SQLite) → True')

    # Test relations within business apps (PostgreSQL) - should be allowed
    print('\nSame database relations (allowed):')
    try:
        from tramites.models import Tramite
        from catalogos.models import CatActividad

        assert router.allow_relation(Tramite, CatActividad) is True, (
            'Tramite-CatActividad relation should be allowed'
        )
        print('  ✓ Tramite ↔ CatActividad (both PostgreSQL) → True')
    except ImportError:
        print('  ⊗ Business models not available (skipping)')

    # Test cross-database relations - should be blocked
    print('\nCross-database relations (blocked):')
    try:
        from tramites.models import Tramite

        assert router.allow_relation(User, Tramite) is False, (
            'User-Tramite cross-DB relation should be blocked'
        )
        print('  ✓ User (SQLite) ↔ Tramite (PostgreSQL) → False')
    except ImportError:
        print('  ⊗ Tramite model not available (skipping)')


def test_db_router_allow_migrate():
    """Test that migrations are routed to the correct database."""
    router = MultiDatabaseRouter()

    print('\n=== Testing allow_migrate ===')

    # Test auth apps → only migrate on SQLite (default)
    print('\nAuth app migrations (SQLite only):')
    assert router.allow_migrate('default', 'auth') is True, 'Auth should migrate on SQLite'
    print("  ✓ auth on 'default' (SQLite) → True")

    assert router.allow_migrate('business', 'auth') is False, (
        'Auth should not migrate on PostgreSQL'
    )
    print("  ✓ auth on 'business' (PostgreSQL) → False")

    assert router.allow_migrate('default', 'contenttypes') is True, (
        'ContentTypes should migrate on SQLite'
    )
    print("  ✓ contenttypes on 'default' (SQLite) → True")

    assert router.allow_migrate('default', 'admin') is True, 'Admin should migrate on SQLite'
    print("  ✓ admin on 'default' (SQLite) → True")

    # Test business apps → never migrate (managed=False)
    print('\nBusiness app migrations (never):')
    assert router.allow_migrate('default', 'tramites') is False, (
        'Tramites should not migrate on SQLite'
    )
    print("  ✓ tramites on 'default' (SQLite) → False")

    assert router.allow_migrate('business', 'tramites') is False, (
        'Tramites should not migrate on PostgreSQL'
    )
    print("  ✓ tramites on 'business' (PostgreSQL) → False")

    assert router.allow_migrate('default', 'catalogos') is False, (
        'Catalogos should not migrate on SQLite'
    )
    print("  ✓ catalogos on 'default' (SQLite) → False")

    assert router.allow_migrate('business', 'catalogos') is False, (
        'Catalogos should not migrate on PostgreSQL'
    )
    print("  ✓ catalogos on 'business' (PostgreSQL) → False")


def test_router_attributes():
    """Test that router attributes are correctly defined."""
    router = MultiDatabaseRouter()

    print('\n=== Testing Router Attributes ===')

    # Check auth apps
    print('\nAuth Apps (SQLite):')
    assert 'auth' in router.AUTH_APPS, 'auth should be in AUTH_APPS'
    print("  ✓ 'auth' in AUTH_APPS")

    assert 'contenttypes' in router.AUTH_APPS, 'contenttypes should be in AUTH_APPS'
    print("  ✓ 'contenttypes' in AUTH_APPS")

    assert 'admin' in router.AUTH_APPS, 'admin should be in AUTH_APPS'
    print("  ✓ 'admin' in AUTH_APPS")

    assert 'sessions' in router.AUTH_APPS, 'sessions should be in AUTH_APPS'
    print("  ✓ 'sessions' in AUTH_APPS")

    # Check business apps
    print('\nBusiness Apps (PostgreSQL):')
    assert 'tramites' in router.BUSINESS_APPS, 'tramites should be in BUSINESS_APPS'
    print("  ✓ 'tramites' in BUSINESS_APPS")

    assert 'catalogos' in router.BUSINESS_APPS, 'catalogos should be in BUSINESS_APPS'
    print("  ✓ 'catalogos' in BUSINESS_APPS")

    assert 'costos' in router.BUSINESS_APPS, 'costos should be in BUSINESS_APPS'
    print("  ✓ 'costos' in BUSINESS_APPS")

    assert 'bitacora' in router.BUSINESS_APPS, 'bitacora should be in BUSINESS_APPS'
    print("  ✓ 'bitacora' in BUSINESS_APPS")

    assert 'core' in router.BUSINESS_APPS, 'core should be in BUSINESS_APPS'
    print("  ✓ 'core' in BUSINESS_APPS")

    # Check database aliases
    print('\nDatabase Aliases:')
    assert router.AUTH_DB == 'default', "AUTH_DB should be 'default'"
    print("  ✓ AUTH_DB = 'default'")

    assert router.BUSINESS_DB == 'business', "BUSINESS_DB should be 'business'"
    print("  ✓ BUSINESS_DB = 'business'")


def run_all_tests():
    """Run all router tests."""
    print('=' * 70)
    print('MultiDatabaseRouter Test Suite')
    print('=' * 70)

    try:
        test_router_attributes()
        test_db_router_read_routing()
        test_db_router_write_routing()
        test_db_router_allow_relation()
        test_db_router_allow_migrate()

        print('\n' + '=' * 70)
        print('✓ All tests passed successfully!')
        print('=' * 70)
        return 0

    except AssertionError as e:
        print('\n' + '=' * 70)
        print(f'✗ Test failed: {e}')
        print('=' * 70)
        return 1

    except Exception as e:
        print('\n' + '=' * 70)
        print(f'✗ Unexpected error: {e}')
        import traceback

        traceback.print_exc()
        print('=' * 70)
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
