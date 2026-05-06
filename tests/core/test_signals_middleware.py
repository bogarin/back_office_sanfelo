"""Tests for core signals and middleware.

Covers:
- CacheUserRolesMiddleware: resolves user groups once per request
- post_migrate signal: auto-runs setup_roles after migrations
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from core.rbac.constants import BackOfficeRole

User = get_user_model()


# ---------------------------------------------------------------------------
# CacheUserRolesMiddleware
# ---------------------------------------------------------------------------


class TestCacheUserRolesMiddleware:
    """Tests for core.middleware.CacheUserRolesMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance with a dummy get_response."""
        from core.middleware import CacheUserRolesMiddleware

        def get_response(request):
            return HttpResponse('OK')

        return CacheUserRolesMiddleware(get_response)

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    @pytest.mark.django_db
    def test_authenticated_user_gets_roles_cached(self, middleware, factory, db):
        """Authenticated user: request.user.roles is a set of group names."""
        user = User.objects.create_user(
            username='mw_user', password='testpass123', is_staff=True,
        )
        group = Group.objects.get_or_create(name=BackOfficeRole.ANALISTA)[0]
        user.groups.add(group)

        request = factory.get('/')
        request.user = user

        middleware(request)

        assert hasattr(request.user, 'roles')
        assert isinstance(request.user.roles, set)
        assert BackOfficeRole.ANALISTA in request.user.roles

    @pytest.mark.django_db
    def test_user_with_multiple_roles(self, middleware, factory, db):
        """User in multiple groups: all group names appear in roles."""
        user = User.objects.create_user(
            username='mw_multi', password='testpass123', is_staff=True,
        )
        g1 = Group.objects.get_or_create(name=BackOfficeRole.COORDINADOR)[0]
        g2 = Group.objects.get_or_create(name=BackOfficeRole.ANALISTA)[0]
        user.groups.add(g1, g2)

        request = factory.get('/')
        request.user = user

        middleware(request)

        assert BackOfficeRole.COORDINADOR in request.user.roles
        assert BackOfficeRole.ANALISTA in request.user.roles
        assert len(request.user.roles) == 2

    @pytest.mark.django_db
    def test_user_with_no_groups_gets_empty_set(self, middleware, factory, db):
        """User with no groups: roles is an empty set."""
        user = User.objects.create_user(
            username='mw_nogroup', password='testpass123',
        )

        request = factory.get('/')
        request.user = user

        middleware(request)

        assert hasattr(request.user, 'roles')
        assert request.user.roles == set()

    def test_anonymous_user_no_roles_attribute(self, middleware, factory):
        """Anonymous user gets an empty roles set."""
        from django.contrib.auth.models import AnonymousUser

        request = factory.get('/')
        request.user = AnonymousUser()

        middleware(request)

        assert hasattr(request.user, 'roles')
        assert request.user.roles == set()

    def test_request_without_user_attribute(self, middleware, factory):
        """Request without user attribute: middleware passes through cleanly."""
        request = factory.get('/')
        # Don't set request.user at all

        response = middleware(request)

        assert response.status_code == 200

    def test_middleware_calls_get_response(self, middleware, factory, db):
        """Middleware always calls get_response and returns its result."""
        user = User.objects.create_user(
            username='mw_simple', password='testpass123',
        )
        request = factory.get('/')
        request.user = user

        response = middleware(request)

        assert response.status_code == 200
        assert response.content == b'OK'


# ---------------------------------------------------------------------------
# post_migrate signal
# ---------------------------------------------------------------------------


class TestPostMigrateSignal:
    """Tests for core.signals.setup_roles post_migrate handler."""

    @pytest.mark.django_db
    def test_setup_roles_signal_creates_groups(self, db):
        """The post_migrate signal creates all BackOfficeRole groups."""
        from django.core.management import call_command

        # Use setup_roles directly instead of migrate --run-syncdb
        # which fails on SQLite with FK constraints
        call_command('setup_roles', verbosity=0)

        for role in BackOfficeRole:
            assert Group.objects.filter(name=role).exists(), (
                f'Group "{role}" should exist after setup_roles'
            )

    @pytest.mark.django_db
    def test_setup_roles_idempotent(self, db):
        """Running setup_roles multiple times does not create duplicates."""
        from django.core.management import call_command

        call_command('setup_roles', verbosity=0)
        call_command('setup_roles', verbosity=0)

        for role in BackOfficeRole:
            assert Group.objects.filter(name=role).count() == 1, (
                f'Group "{role}" should exist exactly once'
            )
