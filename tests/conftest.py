"""Shared pytest configuration and fixtures for all tests.

This module provides a comprehensive set of pytest fixtures for testing the
Backoffice Trámites application, including:

- Authentication fixtures (superuser, admin users, role-based groups)
- Request fixtures (mock HTTP requests)
- Client fixtures (authenticated Django test clients)
- Catalog fixtures (initial catalog data from backend.json)

Fixtures are organized by category and follow PEP 8 naming conventions.
All fixtures include comprehensive docstrings explaining their purpose,
scope, and usage patterns.
"""

import json
from pathlib import Path
from typing import Dict, Any

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line('markers', "slow: marks tests as slow (deselect with -m 'not slow')")
    config.addinivalue_line('markers', 'integration: marks tests as integration tests')


# =============================================================================
# AUTH FIXTURES
# =============================================================================


@pytest.fixture
def superuser(db):
    """Create a superuser for testing."""
    return User.objects.create_superuser(
        username='test_superuser',
        email='superuser@example.com',
        password='testpass123',
    )


@pytest.fixture
def admin_group(db):
    """Get or create the Administrador group."""
    from django.contrib.auth.models import Group

    from core.rbac.constants import BackOfficeRole

    return Group.objects.get_or_create(name=BackOfficeRole.ADMINISTRADOR)[0]


@pytest.fixture
def coordinador_group(db):
    """Get or create the Coordinador group."""
    from django.contrib.auth.models import Group

    from core.rbac.constants import BackOfficeRole

    return Group.objects.get_or_create(name=BackOfficeRole.COORDINADOR)[0]


@pytest.fixture
def analista_group(db):
    """Get or create the Analista group."""
    from django.contrib.auth.models import Group

    from core.rbac.constants import BackOfficeRole

    return Group.objects.get_or_create(name=BackOfficeRole.ANALISTA)[0]


@pytest.fixture
def admin_user(db, admin_group):
    """Create an administrador user."""
    user = User.objects.create_user(
        username='test_admin',
        email='admin@example.com',
        password='testpass123',
        is_staff=True,
    )
    user.groups.add(admin_group)
    return user


# =============================================================================
# REQUEST FIXTURES
# =============================================================================


@pytest.fixture
def mock_http_request():
    """Create a mock HTTP request object."""
    from django.http import HttpRequest

    request = HttpRequest()
    request.user = type('User', (), {'username': 'testuser'})()
    request.META = {'REMOTE_ADDR': '127.0.0.1', 'REMOTE_HOST': 'localhost'}
    return request


# =============================================================================
# CLIENT FIXTURES
# =============================================================================


@pytest.fixture
def admin_client(db, superuser):
    """Create a Django test client logged in as superuser."""
    from django.test import Client

    client = Client()
    client.force_login(superuser)
    return client


@pytest.fixture
def admin_user_client(db, admin_user):
    """Create a Django test client logged in as administrador user."""
    from django.test import Client

    client = Client()
    client.force_login(admin_user)
    return client


# =============================================================================
# CATALOG FIXTURES
# =============================================================================


@pytest.fixture(scope='session')
def catalog_fixtures(django_db_setup, django_db_blocker):
    """
    Load and return catalog fixture data from backend.json.

    This fixture loads the backend.json fixture file which contains
    initial catalog data for testing purposes. The data includes
    categories, procedures, catalog items, and other catalog entries
    used across the Backoffice Trámites application.

    The fixture performs two actions:
    1. Loads the fixture data into the test database using Django's
       loaddata management command
    2. Parses and returns the fixture data as a Python dictionary for
       direct access in tests

    Scope: session - The fixtures are loaded once per test session to
    avoid redundant database operations and improve test performance.
    Use this fixture when you need access to catalog data across multiple
    tests and want to avoid the overhead of loading fixtures multiple times.

    Returns:
        Dict[str, Any]: A dictionary containing the loaded fixture data.
                       The structure mirrors the backend.json fixture file.
                       Typically contains keys like 'catalog.Category',
                       'catalog.CatalogItem', 'catalog.Procedure', etc.

    Example Usage:
        def test_catalog_structure(catalog_fixtures):
            # Access fixture data directly
            categories = catalog_fixtures.get('catalog.Category', [])
            assert len(categories) > 0

        def test_catalog_in_database(catalog_fixtures, db):
            # Data is also loaded into the database
            from catalog.models import Category
            assert Category.objects.exists()

    Note:
        - This fixture requires the 'django_db_setup' fixture to ensure
          the database is properly configured before loading fixtures
        - The fixture file path is relative to the project root:
          'fixtures/backend.json'
        - Changes to the backend.json file will require restarting the
          test session to take effect due to the session scope
        - For transaction-based tests, use the 'db' fixture alongside
          this fixture to ensure proper database transaction handling
    """
    # Define the fixture file path
    fixture_file = 'fixtures/backend.json'

    # Load the fixture data into the database
    with django_db_blocker.unblock():
        call_command('loaddata', fixture_file)

    # Read and parse the fixture data to return as a dictionary
    fixture_path = Path(fixture_file)
    if fixture_path.exists():
        with open(fixture_path, 'r', encoding='utf-8') as f:
            fixture_data: Dict[str, Any] = json.load(f)
        return fixture_data
    else:
        raise FileNotFoundError(
            f'Fixture file not found: {fixture_path.absolute()}. '
            'Ensure the fixtures/backend.json file exists in the project root.'
        )
