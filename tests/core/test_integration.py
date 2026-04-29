"""Integration tests for RBAC system.

Verifies end-to-end RBAC workflows including role setup and admin access.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client

from core.rbac.constants import BackOfficeRole

User = get_user_model()


def test_superuser_can_access_admin(db):
    """Superuser can access /admin/ and gets 200."""
    call_command('setup_roles', verbosity=0)

    superuser = User.objects.create_superuser(
        username='test_superuser',
        email='superuser@example.com',
        password='testpass123',
    )
    client = Client()
    client.force_login(superuser)
    response = client.get('/admin/')
    assert response.status_code == 200


@pytest.mark.parametrize(
    'role',
    list(BackOfficeRole),
    ids=[r.name for r in BackOfficeRole],
)
def test_user_with_role_can_access_admin(db, role):
    """User with any RBAC role can access /admin/ after setup_roles."""
    call_command('setup_roles', verbosity=0)

    group = Group.objects.get(name=role)
    user = User.objects.create_user(
        username=f'test_{role.name.lower()}',
        password='testpass123',
        is_staff=True,
    )
    user.groups.add(group)

    client = Client()
    client.force_login(user)
    response = client.get('/admin/')
    assert response.status_code == 200


def test_user_without_role_cannot_access_admin(db):
    """User without RBAC role and is_staff=False gets redirected from /admin/."""
    User.objects.create_user(
        username='no_role_user',
        password='testpass123',
        is_staff=False,
    )

    client = Client()
    client.login(username='no_role_user', password='testpass123')
    response = client.get('/admin/')
    assert response.status_code == 302
    assert '/admin/login/' in response.url


def test_inactive_user_with_role_cannot_access_admin(db):
    """Inactive user with RBAC role cannot access /admin/."""
    call_command('setup_roles', verbosity=0)

    group = Group.objects.get(name=BackOfficeRole.ANALISTA)
    user = User.objects.create_user(
        username='inactive_user',
        password='testpass123',
        is_staff=True,
        is_active=False,
    )
    user.groups.add(group)

    client = Client()
    client.login(username='inactive_user', password='testpass123')
    response = client.get('/admin/')
    assert response.status_code == 302
    assert '/admin/login/' in response.url
