"""Tests for superuser protection and is_staff lifecycle in BackofficeUserAdmin.

Verifies:
- Non-superuser staff cannot edit/delete/change password on superuser accounts.
- All users created via admin get is_staff=True when assigned a valid role.
- Soft delete preserves group and is_staff; role removal sets is_staff=False.
"""

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages.storage.cookie import CookieStorage
from django.test import RequestFactory

from core.rbac.constants import BackOfficeRole

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_model_admin():
    """Return the BackofficeUserAdmin instance registered in the admin site."""
    User = get_user_model()
    return admin.site._registry[User]


def _build_request(user, *, with_messages=False):
    """Build a minimal GET request with the given user attached."""
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    if with_messages:
        request._messages = CookieStorage(request)  # ty: ignore[unresolved-attribute]
    return request


def _make_mock_form(role_value):
    """Create a mock form with cleaned_data containing the given role."""
    return type('MockForm', (), {'cleaned_data': {'role': role_value}})()


def _ensure_groups_exist():
    """Ensure all BackOfficeRole groups exist in the database."""
    for role in BackOfficeRole:
        Group.objects.get_or_create(name=role)


def _create_other_superuser(username='other_super'):
    """Create a second superuser for testing."""
    User = get_user_model()
    return User.objects.create_superuser(
        username=username,
        email=f'{username}@example.com',
        password='pass',
    )


# ---------------------------------------------------------------------------
# Superuser change protection
# ---------------------------------------------------------------------------


def test_administrador_cannot_change_superuser(admin_user, superuser):
    model_admin = _get_model_admin()
    request = _build_request(admin_user)
    assert model_admin.has_change_permission(request, obj=superuser) is False


def test_superuser_can_change_superuser(superuser):
    other = _create_other_superuser('other_super')
    model_admin = _get_model_admin()
    request = _build_request(superuser)
    assert model_admin.has_change_permission(request, obj=other) is True


# ---------------------------------------------------------------------------
# Superuser delete protection
# ---------------------------------------------------------------------------


def test_administrador_cannot_delete_superuser(admin_user, superuser):
    model_admin = _get_model_admin()
    request = _build_request(admin_user)
    assert model_admin.has_delete_permission(request, obj=superuser) is False


def test_superuser_can_delete_superuser(superuser):
    other = _create_other_superuser('other_super2')
    model_admin = _get_model_admin()
    request = _build_request(superuser)
    assert model_admin.has_delete_permission(request, obj=other) is True


# ---------------------------------------------------------------------------
# Superuser readonly fields
# ---------------------------------------------------------------------------


def test_administrador_sees_readonly_fields_for_superuser(admin_user, superuser):
    model_admin = _get_model_admin()
    request = _build_request(admin_user)
    readonly = model_admin.get_readonly_fields(request, obj=superuser)
    assert set(readonly) == {'username', 'first_name', 'last_name', 'email', 'password', 'role'}


def test_administrador_sees_normal_readonly_for_regular(admin_user, db):  # noqa: ARG001
    User = get_user_model()
    regular = User.objects.create_user(username='regular2', password='pass')
    model_admin = _get_model_admin()
    request = _build_request(admin_user)
    readonly = model_admin.get_readonly_fields(request, obj=regular)
    assert 'role' not in readonly


# ---------------------------------------------------------------------------
# Superuser acciones column
# ---------------------------------------------------------------------------


def test_administrador_no_password_link_for_superuser(admin_user, superuser):
    model_admin = _get_model_admin()
    request = _build_request(admin_user)
    model_admin._request = request  # set by changelist_view
    result = model_admin.acciones(superuser)
    assert 'Cambiar contraseña' not in result
    assert result == '—'


def test_superuser_sees_password_link_for_superuser(superuser):
    other = _create_other_superuser('other_super3')
    model_admin = _get_model_admin()
    request = _build_request(superuser)
    model_admin._request = request
    result = model_admin.acciones(other)
    assert 'Cambiar contraseña' in result


# ---------------------------------------------------------------------------
# Bulk action protection
# ---------------------------------------------------------------------------


def test_marcar_como_activo_excludes_superusers(admin_user, superuser, db):  # noqa: ARG001
    User = get_user_model()
    regular = User.objects.create_user(username='regular3', password='pass', is_active=False)

    model_admin = _get_model_admin()
    request = _build_request(admin_user, with_messages=True)
    queryset = User.objects.filter(pk__in=[superuser.pk, regular.pk])

    model_admin.marcar_como_activo(request, queryset)

    superuser.refresh_from_db()
    regular.refresh_from_db()
    assert superuser.is_active is True  # unchanged — was already True
    assert regular.is_active is True


def test_marcar_como_inactivo_excludes_superusers(admin_user, superuser, db):  # noqa: ARG001
    User = get_user_model()
    regular = User.objects.create_user(username='regular4', password='pass', is_active=True)

    model_admin = _get_model_admin()
    request = _build_request(admin_user, with_messages=True)
    queryset = User.objects.filter(pk__in=[superuser.pk, regular.pk])

    model_admin.marcar_como_inactivo(request, queryset)

    superuser.refresh_from_db()
    regular.refresh_from_db()
    assert superuser.is_active is True  # unchanged — excluded
    assert regular.is_active is False


# ---------------------------------------------------------------------------
# is_staff lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'role',
    list(BackOfficeRole),
    ids=[r.name for r in BackOfficeRole],
)
def test_new_user_with_role_gets_is_staff(superuser, db, role):  # noqa: ARG001
    User = get_user_model()
    _ensure_groups_exist()

    new_user = User(username=f'test_{role.name.lower()}')
    form = _make_mock_form(role)
    model_admin = _get_model_admin()
    request = _build_request(superuser)

    model_admin.save_model(request, new_user, form, change=False)

    new_user.refresh_from_db()
    assert new_user.is_staff is True
    assert new_user.is_active is True
    assert new_user.groups.filter(name=role).exists()


def test_new_user_is_active(superuser, db):  # noqa: ARG001
    User = get_user_model()
    _ensure_groups_exist()

    new_user = User(username='test_active')
    form = _make_mock_form(BackOfficeRole.ANALISTA)
    model_admin = _get_model_admin()
    request = _build_request(superuser)

    model_admin.save_model(request, new_user, form, change=False)

    new_user.refresh_from_db()
    assert new_user.is_active is True


def test_role_removed_sets_is_staff_false(superuser, admin_user, db):  # noqa: ARG001
    _ensure_groups_exist()

    # admin_user already has Administrador group via fixture
    form = _make_mock_form('')
    model_admin = _get_model_admin()
    request = _build_request(superuser)

    model_admin.save_model(request, admin_user, form, change=True)

    admin_user.refresh_from_db()
    assert admin_user.is_staff is False
    assert not admin_user.groups.filter(name__in=list(BackOfficeRole)).exists()


def test_soft_delete_preserves_group_and_is_staff(admin_user, admin_group, db):  # noqa: ARG001
    User = get_user_model()
    _ensure_groups_exist()

    model_admin = _get_model_admin()
    request = _build_request(admin_user, with_messages=True)
    queryset = User.objects.filter(pk=admin_user.pk)

    model_admin.marcar_como_inactivo(request, queryset)

    admin_user.refresh_from_db()
    assert admin_user.is_active is False
    assert admin_user.is_staff is True  # preserved
    assert admin_user.groups.filter(name=BackOfficeRole.ADMINISTRADOR).exists()


def test_reactivate_user_preserves_group_and_is_staff(admin_user, admin_group, db):  # noqa: ARG001
    User = get_user_model()
    _ensure_groups_exist()

    model_admin = _get_model_admin()

    # Deactivate
    request = _build_request(admin_user, with_messages=True)
    model_admin.marcar_como_inactivo(request, User.objects.filter(pk=admin_user.pk))
    admin_user.refresh_from_db()
    assert admin_user.is_active is False

    # Reactivate
    model_admin.marcar_como_activo(request, User.objects.filter(pk=admin_user.pk))
    admin_user.refresh_from_db()
    assert admin_user.is_active is True
    assert admin_user.is_staff is True
    assert admin_user.groups.filter(name=BackOfficeRole.ADMINISTRADOR).exists()
