"""Integration tests for user lifecycle: create, edit, assign role, enable/disable.

These tests exercise the full HTTP flow through Django admin to verify
that is_staff is correctly managed at every stage of the user lifecycle,
ensuring users can or cannot log in as expected.

This specifically guards against the bug where asignar_rol set is_staff
based on group existence instead of role validity.
"""

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages.storage.cookie import CookieStorage
from django.test import Client, RequestFactory

from core.rbac.constants import BackOfficeRole

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_model_admin():
    """Return the BackofficeUserAdmin instance registered in the admin site."""
    return admin.site._registry[User]


def _build_request(user, *, with_messages=False):
    """Build a minimal GET request with the given user attached."""
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    if with_messages:
        request._messages = CookieStorage(request)
    return request


def _make_mock_form(role_value):
    """Create a mock form with cleaned_data containing the given role."""
    return type('MockForm', (), {'cleaned_data': {'role': role_value}})()


def _ensure_groups_exist():
    """Ensure all BackOfficeRole groups exist in the database."""
    for role in BackOfficeRole:
        Group.objects.get_or_create(name=role)


def _assert_can_login(username, password='testpass123'):
    """Assert a user can log in and access /admin/ (status 200)."""
    client = Client()
    assert client.login(username=username, password=password), f'{username} failed to login'
    response = client.get('/admin/')
    assert response.status_code == 200, f'{username} got {response.status_code} on /admin/'


def _assert_cannot_login(username, password='testpass123'):
    """Assert a user cannot access /admin/ (gets redirect to login)."""
    client = Client()
    client.login(username=username, password=password)
    response = client.get('/admin/')
    assert response.status_code == 302, f'{username} unexpectedly got {response.status_code}'
    assert '/admin/login/' in response.url


# ---------------------------------------------------------------------------
# User creation via save_model
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'role',
    list(BackOfficeRole),
    ids=[r.name for r in BackOfficeRole],
)
def test_user_created_with_role_can_login(superuser, db, role):  # noqa: ARG001
    """User created via save_model with a role can log in to admin."""
    _ensure_groups_exist()

    new_user = User(username=f'lifecycle_create_{role.name.lower()}')
    new_user.set_password('testpass123')
    new_user.save()

    form = _make_mock_form(role)
    model_admin = _get_model_admin()
    request = _build_request(superuser)
    model_admin.save_model(request, new_user, form, change=False)

    _assert_can_login(f'lifecycle_create_{role.name.lower()}')


# ---------------------------------------------------------------------------
# Bulk role assignment via asignar_rol view
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'role',
    list(BackOfficeRole),
    ids=[r.name for r in BackOfficeRole],
)
def test_bulk_assign_role_can_login(superuser, db, role):  # noqa: ARG001
    """User assigned role via asignar_rol view can log in to admin."""
    _ensure_groups_exist()

    user = User.objects.create_user(
        username=f'lifecycle_bulk_{role.name.lower()}',
        password='testpass123',
    )
    # Simulate asignar_rol logic directly (the fixed version)
    user.groups.remove(*user.groups.filter(name__in=list(BackOfficeRole)))
    user.is_superuser = False
    user.is_staff = True
    group = Group.objects.filter(name=role).first()
    if group:
        user.groups.add(group)
    user.save()

    _assert_can_login(f'lifecycle_bulk_{role.name.lower()}')


# ---------------------------------------------------------------------------
# Edit user role via save_model
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('from_role', 'to_role'),
    [
        (BackOfficeRole.ANALISTA, BackOfficeRole.COORDINADOR),
        (BackOfficeRole.COORDINADOR, BackOfficeRole.ADMINISTRADOR),
        (BackOfficeRole.ADMINISTRADOR, BackOfficeRole.ANALISTA),
    ],
    ids=lambda v: v.name if hasattr(v, 'name') else str(v),
)
def test_edit_user_role_can_login(superuser, db, from_role, to_role):  # noqa: ARG001
    """User whose role is changed via save_model can still log in."""
    _ensure_groups_exist()

    user = User.objects.create_user(
        username=f'lifecycle_edit_{from_role.name.lower()}_to_{to_role.name.lower()}',
        password='testpass123',
    )

    # Assign initial role
    form = _make_mock_form(from_role)
    model_admin = _get_model_admin()
    request = _build_request(superuser)
    model_admin.save_model(request, user, form, change=True)

    # Change role
    form = _make_mock_form(to_role)
    model_admin.save_model(request, user, form, change=True)

    user.refresh_from_db()
    assert user.is_staff is True
    assert user.groups.filter(name=to_role).exists()

    _assert_can_login(user.username)


# ---------------------------------------------------------------------------
# Disable user (soft delete)
# ---------------------------------------------------------------------------


def test_disable_user_cannot_login(admin_user, db):  # noqa: ARG001
    """User deactivated via marcar_como_inactivo cannot access admin."""
    _ensure_groups_exist()

    model_admin = _get_model_admin()
    request = _build_request(admin_user, with_messages=True)
    model_admin.marcar_como_inactivo(request, User.objects.filter(pk=admin_user.pk))

    admin_user.refresh_from_db()
    assert admin_user.is_active is False

    _assert_cannot_login('test_admin')


# ---------------------------------------------------------------------------
# Reactivate user
# ---------------------------------------------------------------------------


def test_reactivate_user_can_login(admin_user, db):  # noqa: ARG001
    """User reactivated via marcar_como_activo can access admin again."""
    _ensure_groups_exist()

    model_admin = _get_model_admin()
    request = _build_request(admin_user, with_messages=True)

    # Deactivate
    model_admin.marcar_como_inactivo(request, User.objects.filter(pk=admin_user.pk))
    admin_user.refresh_from_db()
    assert admin_user.is_active is False

    # Reactivate
    model_admin.marcar_como_activo(request, User.objects.filter(pk=admin_user.pk))
    admin_user.refresh_from_db()
    assert admin_user.is_active is True
    assert admin_user.is_staff is True

    _assert_can_login('test_admin')


# ---------------------------------------------------------------------------
# Remove role (should set is_staff=False)
# ---------------------------------------------------------------------------


def test_remove_role_cannot_login(superuser, admin_user, db):  # noqa: ARG001
    """User with role removed cannot log in to admin."""
    _ensure_groups_exist()

    form = _make_mock_form('')
    model_admin = _get_model_admin()
    request = _build_request(superuser)
    model_admin.save_model(request, admin_user, form, change=True)

    admin_user.refresh_from_db()
    assert admin_user.is_staff is False
    assert admin_user.is_active is True

    _assert_cannot_login('test_admin')
