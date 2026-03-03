"""Shared pytest configuration and fixtures for all tests."""

import pytest
from django.contrib.auth import get_user_model

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
    from django.conf import settings
    from django.contrib.auth.models import Group

    return Group.objects.get_or_create(name=settings.ADMINISTRADOR_GROUP_NAME)[0]


@pytest.fixture
def operador_group(db):
    """Get or create the Operador group."""
    from django.conf import settings
    from django.contrib.auth.models import Group

    return Group.objects.get_or_create(name=settings.OPERADOR_GROUP_NAME)[0]


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


@pytest.fixture
def operador_user(db, operador_group):
    """Create an operador user."""
    user = User.objects.create_user(
        username='test_operator',
        email='operator@example.com',
        password='testpass123',
        is_staff=True,
    )
    user.groups.add(operador_group)
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


@pytest.fixture
def operador_client(db, operador_user):
    """Create a Django test client logged in as operador user."""
    from django.test import Client

    client = Client()
    client.force_login(operador_user)
    return client
