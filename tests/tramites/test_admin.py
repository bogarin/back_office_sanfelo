"""Tests for tramites admin classes: permissions and queryset filtering.

Covers:
- B5-30 (H-002-014): has_change_permission role checks across 4 admin classes
- B5-31 (H-002-015): get_queryset filters for each admin class
"""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from core.rbac.constants import BackOfficeRole
from tramites.models import Buzon, Cerrado, Disponible, Tramite


def _make_user(*, roles=frozenset(), is_superuser=False, user_id=1):
    user = MagicMock()
    user.is_superuser = is_superuser
    user.id = user_id
    user.is_administrador = BackOfficeRole.ADMINISTRADOR in roles
    user.is_coordinador = BackOfficeRole.COORDINADOR in roles
    user.is_analista = BackOfficeRole.ANALISTA in roles
    return user


def _make_request(user=None):
    request = MagicMock()
    request.user = user or _make_user()
    return request


def _get_admin_instance(model_class):
    return admin.site._registry[model_class]


# =============================================================================
# B5-30: has_change_permission — role checks
# ---- BuzonTramitesAdmin ----
# =============================================================================


@pytest.fixture
def admin_perms_buzon():
    return _get_admin_instance(Buzon), _make_request()


@pytest.mark.parametrize(
    'role',
    [
        frozenset({BackOfficeRole.ANALISTA}),
        frozenset({BackOfficeRole.COORDINADOR}),
        frozenset({BackOfficeRole.ADMINISTRADOR}),
    ],
)
def test_has_change_permission_obj_none_allows_role_buzon(admin_perms_buzon, role):
    admin, request = admin_perms_buzon
    request.user = _make_user(roles=role)
    assert admin.has_change_permission(request, obj=None) is True


def test_has_change_permission_obj_none_superuser_allowed_buzon(admin_perms_buzon):
    admin, request = admin_perms_buzon
    request.user = _make_user(is_superuser=True)
    assert admin.has_change_permission(request, obj=None) is True


def test_has_change_permission_obj_none_anonymous_denied_buzon(admin_perms_buzon):
    admin, request = admin_perms_buzon
    request.user = _make_user(roles=frozenset())
    assert admin.has_change_permission(request, obj=None) is False


@pytest.mark.parametrize(
    'role',
    [
        frozenset({BackOfficeRole.ANALISTA}),
        frozenset({BackOfficeRole.COORDINADOR}),
        frozenset({BackOfficeRole.ADMINISTRADOR}),
    ],
)
def test_has_change_permission_with_obj_denied_buzon(admin_perms_buzon, role):
    admin, request = admin_perms_buzon
    request.user = _make_user(roles=role)
    assert admin.has_change_permission(request, obj=MagicMock()) is False


def test_has_change_permission_superuser_with_obj_denied_buzon(admin_perms_buzon):
    admin, request = admin_perms_buzon
    request.user = _make_user(is_superuser=True)
    assert admin.has_change_permission(request, obj=MagicMock()) is False


# ---- TramitesDisponiblesAdmin ----


@pytest.fixture
def admin_perms_disponibles():
    return _get_admin_instance(Disponible), _make_request()


@pytest.mark.parametrize(
    'role',
    [
        frozenset({BackOfficeRole.ANALISTA}),
        frozenset({BackOfficeRole.COORDINADOR}),
        frozenset({BackOfficeRole.ADMINISTRADOR}),
    ],
)
def test_has_change_permission_obj_none_allows_role_disponibles(admin_perms_disponibles, role):
    admin, request = admin_perms_disponibles
    request.user = _make_user(roles=role)
    assert admin.has_change_permission(request, obj=None) is True


def test_has_change_permission_obj_none_anonymous_denied_disponibles(admin_perms_disponibles):
    admin, request = admin_perms_disponibles
    request.user = _make_user(roles=frozenset())
    assert admin.has_change_permission(request, obj=None) is False


@pytest.mark.parametrize(
    'role',
    [
        frozenset({BackOfficeRole.ANALISTA}),
        frozenset({BackOfficeRole.COORDINADOR}),
    ],
)
def test_has_change_permission_with_obj_denied_disponibles(admin_perms_disponibles, role):
    admin, request = admin_perms_disponibles
    request.user = _make_user(roles=role)
    assert admin.has_change_permission(request, obj=MagicMock()) is False


# ---- TramitesAdmin ----


@pytest.fixture
def admin_perms_tramites():
    return _get_admin_instance(Tramite), _make_request()


@pytest.mark.parametrize(
    'role',
    [
        frozenset({BackOfficeRole.COORDINADOR}),
        frozenset({BackOfficeRole.ADMINISTRADOR}),
    ],
)
def test_has_change_permission_obj_none_allows_role_tramites(admin_perms_tramites, role):
    admin, request = admin_perms_tramites
    request.user = _make_user(roles=role)
    assert admin.has_change_permission(request, obj=None) is True


def test_has_change_permission_obj_none_analista_denied_tramites(admin_perms_tramites):
    admin, request = admin_perms_tramites
    request.user = _make_user(roles=frozenset({BackOfficeRole.ANALISTA}))
    assert admin.has_change_permission(request, obj=None) is False


def test_has_change_permission_obj_none_anonymous_denied_tramites(admin_perms_tramites):
    admin, request = admin_perms_tramites
    request.user = _make_user(roles=frozenset())
    assert admin.has_change_permission(request, obj=None) is False


def test_has_change_permission_obj_none_superuser_without_roles_allowed_tramites(
    admin_perms_tramites,
):
    """Superuser without any role group is still allowed."""
    admin, request = admin_perms_tramites
    request.user = _make_user(is_superuser=True, roles=frozenset())
    assert admin.has_change_permission(request, obj=None) is True


@pytest.mark.parametrize(
    'role',
    [
        frozenset({BackOfficeRole.COORDINADOR}),
        frozenset({BackOfficeRole.ADMINISTRADOR}),
    ],
)
def test_has_change_permission_with_obj_denied_tramites(admin_perms_tramites, role):
    admin, request = admin_perms_tramites
    request.user = _make_user(roles=role)
    assert admin.has_change_permission(request, obj=MagicMock()) is False


# ---- TramitesCerradosAdmin ----


@pytest.fixture
def admin_perms_cerrados():
    return _get_admin_instance(Cerrado), _make_request()


@pytest.mark.parametrize(
    'role',
    [
        frozenset({BackOfficeRole.COORDINADOR}),
        frozenset({BackOfficeRole.ADMINISTRADOR}),
    ],
)
def test_has_change_permission_obj_none_allows_role_cerrados(admin_perms_cerrados, role):
    admin, request = admin_perms_cerrados
    request.user = _make_user(roles=role)
    assert admin.has_change_permission(request, obj=None) is True


def test_has_change_permission_obj_none_analista_denied_cerrados(admin_perms_cerrados):
    admin, request = admin_perms_cerrados
    request.user = _make_user(roles=frozenset({BackOfficeRole.ANALISTA}))
    assert admin.has_change_permission(request, obj=None) is False


def test_has_change_permission_obj_none_superuser_without_roles_allowed_cerrados(
    admin_perms_cerrados,
):
    """Superuser without any role group is still allowed."""
    admin, request = admin_perms_cerrados
    request.user = _make_user(is_superuser=True, roles=frozenset())
    assert admin.has_change_permission(request, obj=None) is True


@pytest.mark.parametrize(
    'role',
    [
        frozenset({BackOfficeRole.COORDINADOR}),
        frozenset({BackOfficeRole.ADMINISTRADOR}),
    ],
)
def test_has_change_permission_with_obj_denied_cerrados(admin_perms_cerrados, role):
    admin, request = admin_perms_cerrados
    request.user = _make_user(roles=role)
    assert admin.has_change_permission(request, obj=MagicMock()) is False


# =============================================================================
# M-002: RoleCheckMixin.__init_subclass__ validation
# =============================================================================


def test_invalid_allowed_roles_raises_improperly_configured():
    """Subclassing RoleCheckMixin with invalid role strings fails at import time."""
    from tramites.admin import RoleCheckMixin, TramiteBaseAdmin

    with pytest.raises(ImproperlyConfigured, match='is_staff'):
        type(
            'BadAdmin',
            (RoleCheckMixin, TramiteBaseAdmin),
            {
                'allowed_roles': ('is_staff',),
            },
        )


# =============================================================================
# B5-31: get_queryset — filter verification
# =============================================================================


def _mock_base_queryset():
    qs = MagicMock()
    qs.en_proceso.return_value = qs
    qs.finalizados.return_value = qs
    qs.asignados_a.return_value = qs
    qs.sin_asignar.return_value = qs
    return qs


# ---- BuzonTramitesAdminQueryset ----


@pytest.fixture
def admin_qs_buzon():
    return (
        _get_admin_instance(Buzon),
        _mock_base_queryset(),
        _make_request(_make_user(user_id=42, roles=frozenset({BackOfficeRole.ANALISTA}))),
    )


@patch('tramites.admin.TramiteBaseAdmin.get_queryset')
def test_calls_en_proceso_buzon(mock_super_qs, admin_qs_buzon):
    admin, base_qs, request = admin_qs_buzon
    mock_super_qs.return_value = base_qs
    admin.get_queryset(request)
    base_qs.en_proceso.assert_called_once()


@patch('tramites.admin.TramiteBaseAdmin.get_queryset')
def test_filters_by_user_id(mock_super_qs, admin_qs_buzon):
    admin, base_qs, request = admin_qs_buzon
    mock_super_qs.return_value = base_qs
    admin.get_queryset(request)
    base_qs.asignados_a.assert_called_once_with(42)


# ---- TramitesDisponiblesAdminQueryset ----


@pytest.fixture
def admin_qs_disponibles():
    return (
        _get_admin_instance(Disponible),
        _mock_base_queryset(),
        _make_request(),
    )


@patch('tramites.admin.TramiteBaseAdmin.get_queryset')
def test_calls_en_proceso_disponibles(mock_super_qs, admin_qs_disponibles):
    admin, base_qs, request = admin_qs_disponibles
    mock_super_qs.return_value = base_qs
    admin.get_queryset(request)
    base_qs.en_proceso.assert_called_once()


@patch('tramites.admin.TramiteBaseAdmin.get_queryset')
def test_filters_unassigned(mock_super_qs, admin_qs_disponibles):
    admin, base_qs, request = admin_qs_disponibles
    mock_super_qs.return_value = base_qs
    admin.get_queryset(request)
    base_qs.sin_asignar.assert_called_once()


@patch('tramites.admin.TramiteBaseAdmin.get_queryset')
def test_does_not_filter_by_user_id(mock_super_qs, admin_qs_disponibles):
    admin, base_qs, request = admin_qs_disponibles
    mock_super_qs.return_value = base_qs
    admin.get_queryset(request)
    base_qs.asignados_a.assert_not_called()


# ---- TramitesAdminQueryset ----


@pytest.fixture
def admin_qs_tramites():
    return (
        _get_admin_instance(Tramite),
        _mock_base_queryset(),
        _make_request(),
    )


@patch('tramites.admin.TramiteBaseAdmin.get_queryset')
def test_calls_en_proceso_tramites(mock_super_qs, admin_qs_tramites):
    admin, base_qs, request = admin_qs_tramites
    mock_super_qs.return_value = base_qs
    admin.get_queryset(request)
    base_qs.en_proceso.assert_called_once()


@patch('tramites.admin.TramiteBaseAdmin.get_queryset')
def test_no_user_or_assignment_filter(mock_super_qs, admin_qs_tramites):
    admin, base_qs, request = admin_qs_tramites
    mock_super_qs.return_value = base_qs
    admin.get_queryset(request)
    base_qs.asignados_a.assert_not_called()
    base_qs.sin_asignar.assert_not_called()


# ---- TramitesCerradosAdminQueryset ----


@pytest.fixture
def admin_qs_cerrados():
    return (
        _get_admin_instance(Cerrado),
        _mock_base_queryset(),
        _make_request(),
    )


@patch('tramites.admin.TramiteBaseAdmin.get_queryset')
def test_calls_finalizados(mock_super_qs, admin_qs_cerrados):
    admin, base_qs, request = admin_qs_cerrados
    mock_super_qs.return_value = base_qs
    admin.get_queryset(request)
    base_qs.finalizados.assert_called_once()


@patch('tramites.admin.TramiteBaseAdmin.get_queryset')
def test_does_not_call_en_proceso(mock_super_qs, admin_qs_cerrados):
    admin, base_qs, request = admin_qs_cerrados
    mock_super_qs.return_value = base_qs
    admin.get_queryset(request)
    base_qs.en_proceso.assert_not_called()


# =============================================================================
# get_search_fields — dynamic by ACTIVE_DEPARTMENT
# =============================================================================


@pytest.fixture
def admin_search_tramites():
    return _get_admin_instance(Tramite), _make_request()


@override_settings(ACTIVE_DEPARTMENT='DAU')
def test_dau_includes_clave_catastral(admin_search_tramites):
    admin, request = admin_search_tramites
    fields = admin.get_search_fields(request)
    assert 'folio' in fields
    assert 'solicitante_nombre' in fields
    assert 'clave_catastral' in fields


@pytest.mark.parametrize('dept', ['SEC', 'TES'])
def test_non_dau_excludes_clave_catastral(admin_search_tramites, dept):
    admin, request = admin_search_tramites
    with override_settings(ACTIVE_DEPARTMENT=dept):
        fields = admin.get_search_fields(request)
    assert 'folio' in fields
    assert 'solicitante_nombre' in fields
    assert 'clave_catastral' not in fields
