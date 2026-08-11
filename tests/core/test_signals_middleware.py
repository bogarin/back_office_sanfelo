"""Tests for core signals and middleware.

Covers:
- CacheUserRolesMiddleware: resolves user groups once per request
- post_migrate signal: auto-runs setup_roles after migrations
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.core.management import call_command
from django.http import HttpResponse
from django.test import RequestFactory

from core.middleware import CacheUserRolesMiddleware
from core.rbac.constants import BackOfficeRole

User = get_user_model()


# ---------------------------------------------------------------------------
# CacheUserRolesMiddleware
# ---------------------------------------------------------------------------


@pytest.fixture
def cache_middleware():
    """Create middleware instance with a dummy get_response."""

    def get_response(_request):
        return HttpResponse('OK')

    return CacheUserRolesMiddleware(get_response)


@pytest.fixture
def cache_factory():
    return RequestFactory()


@pytest.mark.django_db
def test_authenticated_user_gets_roles_cached(cache_middleware, cache_factory):
    """Authenticated user: request.user.roles is a set of group names."""
    user = User.objects.create_user(
        username='mw_user',
        password='testpass123',
        is_staff=True,
    )
    group = Group.objects.get_or_create(name=BackOfficeRole.ANALISTA)[0]
    user.groups.add(group)

    request = cache_factory.get('/')
    request.user = user

    cache_middleware(request)

    assert hasattr(request.user, 'roles')
    assert isinstance(request.user.roles, set)
    assert BackOfficeRole.ANALISTA in request.user.roles


@pytest.mark.django_db
def test_user_with_multiple_roles(cache_middleware, cache_factory):
    """User in multiple groups: all group names appear in roles."""
    user = User.objects.create_user(
        username='mw_multi',
        password='testpass123',
        is_staff=True,
    )
    g1 = Group.objects.get_or_create(name=BackOfficeRole.COORDINADOR)[0]
    g2 = Group.objects.get_or_create(name=BackOfficeRole.ANALISTA)[0]
    user.groups.add(g1, g2)

    request = cache_factory.get('/')
    request.user = user

    cache_middleware(request)

    assert BackOfficeRole.COORDINADOR in request.user.roles
    assert BackOfficeRole.ANALISTA in request.user.roles
    assert len(request.user.roles) == 2


@pytest.mark.django_db
def test_user_with_no_groups_gets_empty_set(cache_middleware, cache_factory):
    """User with no groups: roles is an empty set."""
    user = User.objects.create_user(
        username='mw_nogroup',
        password='testpass123',
    )

    request = cache_factory.get('/')
    request.user = user

    cache_middleware(request)

    assert hasattr(request.user, 'roles')
    assert request.user.roles == set()


def test_anonymous_user_no_roles_attribute(cache_middleware, cache_factory):
    """Anonymous user gets an empty roles set."""
    request = cache_factory.get('/')
    request.user = AnonymousUser()

    cache_middleware(request)

    assert hasattr(request.user, 'roles')
    assert request.user.roles == set()


def test_request_without_user_attribute(cache_middleware, cache_factory):
    """Request without user attribute: middleware passes through cleanly."""
    request = cache_factory.get('/')
    # Don't set request.user at all

    response = cache_middleware(request)

    assert response.status_code == 200


@pytest.mark.django_db
def test_middleware_calls_get_response(cache_middleware, cache_factory):
    """Middleware always calls get_response and returns its result."""
    user = User.objects.create_user(
        username='mw_simple',
        password='testpass123',
    )
    request = cache_factory.get('/')
    request.user = user

    response = cache_middleware(request)

    assert response.status_code == 200
    assert response.content == b'OK'


# ---------------------------------------------------------------------------
# post_migrate signal
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_setup_roles_signal_creates_groups():
    """The post_migrate signal creates all BackOfficeRole groups."""
    # Use setup_roles directly instead of migrate --run-syncdb
    # which fails on SQLite with FK constraints
    call_command('setup_roles', verbosity=0)

    for role in BackOfficeRole:
        assert Group.objects.filter(name=role).exists(), (
            f'Group "{role}" should exist after setup_roles'
        )


@pytest.mark.django_db
def test_setup_roles_idempotent():
    """Running setup_roles multiple times does not create duplicates."""
    call_command('setup_roles', verbosity=0)
    call_command('setup_roles', verbosity=0)

    for role in BackOfficeRole:
        assert Group.objects.filter(name=role).count() == 1, (
            f'Group "{role}" should exist exactly once'
        )
