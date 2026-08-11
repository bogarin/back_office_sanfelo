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
# =============================================================================


class TestBuzonTramitesAdminPermissions:
    """BuzonTramitesAdmin: analista/coordinador/administrador for list actions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin = _get_admin_instance(Buzon)
        self.request = _make_request()

    @pytest.mark.parametrize(
        'role',
        [
            frozenset({BackOfficeRole.ANALISTA}),
            frozenset({BackOfficeRole.COORDINADOR}),
            frozenset({BackOfficeRole.ADMINISTRADOR}),
        ],
    )
    def test_has_change_permission_obj_none_allows_role(self, role):
        self.request.user = _make_user(roles=role)
        assert self.admin.has_change_permission(self.request, obj=None) is True

    def test_has_change_permission_obj_none_superuser_allowed(self):
        self.request.user = _make_user(is_superuser=True)
        assert self.admin.has_change_permission(self.request, obj=None) is True

    def test_has_change_permission_obj_none_anonymous_denied(self):
        self.request.user = _make_user(roles=frozenset())
        assert self.admin.has_change_permission(self.request, obj=None) is False

    @pytest.mark.parametrize(
        'role',
        [
            frozenset({BackOfficeRole.ANALISTA}),
            frozenset({BackOfficeRole.COORDINADOR}),
            frozenset({BackOfficeRole.ADMINISTRADOR}),
        ],
    )
    def test_has_change_permission_with_obj_denied(self, role):
        self.request.user = _make_user(roles=role)
        assert self.admin.has_change_permission(self.request, obj=MagicMock()) is False

    def test_has_change_permission_superuser_with_obj_denied(self):
        self.request.user = _make_user(is_superuser=True)
        assert self.admin.has_change_permission(self.request, obj=MagicMock()) is False


class TestTramitesDisponiblesAdminPermissions:
    """TramitesDisponiblesAdmin: same role pattern as Buzon."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin = _get_admin_instance(Disponible)
        self.request = _make_request()

    @pytest.mark.parametrize(
        'role',
        [
            frozenset({BackOfficeRole.ANALISTA}),
            frozenset({BackOfficeRole.COORDINADOR}),
            frozenset({BackOfficeRole.ADMINISTRADOR}),
        ],
    )
    def test_has_change_permission_obj_none_allows_role(self, role):
        self.request.user = _make_user(roles=role)
        assert self.admin.has_change_permission(self.request, obj=None) is True

    def test_has_change_permission_obj_none_anonymous_denied(self):
        self.request.user = _make_user(roles=frozenset())
        assert self.admin.has_change_permission(self.request, obj=None) is False

    @pytest.mark.parametrize(
        'role',
        [
            frozenset({BackOfficeRole.ANALISTA}),
            frozenset({BackOfficeRole.COORDINADOR}),
        ],
    )
    def test_has_change_permission_with_obj_denied(self, role):
        self.request.user = _make_user(roles=role)
        assert self.admin.has_change_permission(self.request, obj=MagicMock()) is False


class TestTramitesAdminPermissions:
    """TramitesAdmin: coordinador/administrador only (no analista)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin = _get_admin_instance(Tramite)
        self.request = _make_request()

    @pytest.mark.parametrize(
        'role',
        [
            frozenset({BackOfficeRole.COORDINADOR}),
            frozenset({BackOfficeRole.ADMINISTRADOR}),
        ],
    )
    def test_has_change_permission_obj_none_allows_role(self, role):
        self.request.user = _make_user(roles=role)
        assert self.admin.has_change_permission(self.request, obj=None) is True

    def test_has_change_permission_obj_none_analista_denied(self):
        self.request.user = _make_user(roles=frozenset({BackOfficeRole.ANALISTA}))
        assert self.admin.has_change_permission(self.request, obj=None) is False

    def test_has_change_permission_obj_none_anonymous_denied(self):
        self.request.user = _make_user(roles=frozenset())
        assert self.admin.has_change_permission(self.request, obj=None) is False

    def test_has_change_permission_obj_none_superuser_without_roles_allowed(self):
        """Superuser without any role group is still allowed."""
        self.request.user = _make_user(is_superuser=True, roles=frozenset())
        assert self.admin.has_change_permission(self.request, obj=None) is True

    @pytest.mark.parametrize(
        'role',
        [
            frozenset({BackOfficeRole.COORDINADOR}),
            frozenset({BackOfficeRole.ADMINISTRADOR}),
        ],
    )
    def test_has_change_permission_with_obj_denied(self, role):
        self.request.user = _make_user(roles=role)
        assert self.admin.has_change_permission(self.request, obj=MagicMock()) is False


class TestTramitesCerradosAdminPermissions:
    """TramitesCerradosAdmin: coordinador/administrador only (same as TramitesAdmin)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin = _get_admin_instance(Cerrado)
        self.request = _make_request()

    @pytest.mark.parametrize(
        'role',
        [
            frozenset({BackOfficeRole.COORDINADOR}),
            frozenset({BackOfficeRole.ADMINISTRADOR}),
        ],
    )
    def test_has_change_permission_obj_none_allows_role(self, role):
        self.request.user = _make_user(roles=role)
        assert self.admin.has_change_permission(self.request, obj=None) is True

    def test_has_change_permission_obj_none_analista_denied(self):
        self.request.user = _make_user(roles=frozenset({BackOfficeRole.ANALISTA}))
        assert self.admin.has_change_permission(self.request, obj=None) is False

    def test_has_change_permission_obj_none_superuser_without_roles_allowed(self):
        """Superuser without any role group is still allowed."""
        self.request.user = _make_user(is_superuser=True, roles=frozenset())
        assert self.admin.has_change_permission(self.request, obj=None) is True

    @pytest.mark.parametrize(
        'role',
        [
            frozenset({BackOfficeRole.COORDINADOR}),
            frozenset({BackOfficeRole.ADMINISTRADOR}),
        ],
    )
    def test_has_change_permission_with_obj_denied(self, role):
        self.request.user = _make_user(roles=role)
        assert self.admin.has_change_permission(self.request, obj=MagicMock()) is False


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


class TestBuzonTramitesAdminQueryset:
    """Buzon: en_proceso() + asignados_a(user.id)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin = _get_admin_instance(Buzon)
        self.base_qs = _mock_base_queryset()
        self.request = _make_request(
            _make_user(user_id=42, roles=frozenset({BackOfficeRole.ANALISTA}))
        )

    @patch('tramites.admin.TramiteBaseAdmin.get_queryset')
    def test_calls_en_proceso(self, mock_super_qs):
        mock_super_qs.return_value = self.base_qs
        self.admin.get_queryset(self.request)
        self.base_qs.en_proceso.assert_called_once()

    @patch('tramites.admin.TramiteBaseAdmin.get_queryset')
    def test_filters_by_user_id(self, mock_super_qs):
        mock_super_qs.return_value = self.base_qs
        self.admin.get_queryset(self.request)
        self.base_qs.asignados_a.assert_called_once_with(42)


class TestTramitesDisponiblesAdminQueryset:
    """Disponible: en_proceso() + sin_asignar()."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin = _get_admin_instance(Disponible)
        self.base_qs = _mock_base_queryset()
        self.request = _make_request()

    @patch('tramites.admin.TramiteBaseAdmin.get_queryset')
    def test_calls_en_proceso(self, mock_super_qs):
        mock_super_qs.return_value = self.base_qs
        self.admin.get_queryset(self.request)
        self.base_qs.en_proceso.assert_called_once()

    @patch('tramites.admin.TramiteBaseAdmin.get_queryset')
    def test_filters_unassigned(self, mock_super_qs):
        mock_super_qs.return_value = self.base_qs
        self.admin.get_queryset(self.request)
        self.base_qs.sin_asignar.assert_called_once()

    @patch('tramites.admin.TramiteBaseAdmin.get_queryset')
    def test_does_not_filter_by_user_id(self, mock_super_qs):
        mock_super_qs.return_value = self.base_qs
        self.admin.get_queryset(self.request)
        self.base_qs.asignados_a.assert_not_called()


class TestTramitesAdminQueryset:
    """Tramites: en_proceso() only (no user/assignment filter)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin = _get_admin_instance(Tramite)
        self.base_qs = _mock_base_queryset()
        self.request = _make_request()

    @patch('tramites.admin.TramiteBaseAdmin.get_queryset')
    def test_calls_en_proceso(self, mock_super_qs):
        mock_super_qs.return_value = self.base_qs
        self.admin.get_queryset(self.request)
        self.base_qs.en_proceso.assert_called_once()

    @patch('tramites.admin.TramiteBaseAdmin.get_queryset')
    def test_no_user_or_assignment_filter(self, mock_super_qs):
        mock_super_qs.return_value = self.base_qs
        self.admin.get_queryset(self.request)
        self.base_qs.asignados_a.assert_not_called()
        self.base_qs.sin_asignar.assert_not_called()


class TestTramitesCerradosAdminQueryset:
    """Cerrado: finalizados() only."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin = _get_admin_instance(Cerrado)
        self.base_qs = _mock_base_queryset()
        self.request = _make_request()

    @patch('tramites.admin.TramiteBaseAdmin.get_queryset')
    def test_calls_finalizados(self, mock_super_qs):
        mock_super_qs.return_value = self.base_qs
        self.admin.get_queryset(self.request)
        self.base_qs.finalizados.assert_called_once()

    @patch('tramites.admin.TramiteBaseAdmin.get_queryset')
    def test_does_not_call_en_proceso(self, mock_super_qs):
        mock_super_qs.return_value = self.base_qs
        self.admin.get_queryset(self.request)
        self.base_qs.en_proceso.assert_not_called()


# =============================================================================
# get_search_fields — dynamic by ACTIVE_DEPARTMENT
# =============================================================================


class TestTramitesBaseAdminSearchFields:
    """get_search_fields returns folio + solicitante_nombre, plus clave_catastral
    only when ACTIVE_DEPARTMENT == 'DAU'."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin = _get_admin_instance(Tramite)
        self.request = _make_request()

    @override_settings(ACTIVE_DEPARTMENT='DAU')
    def test_dau_includes_clave_catastral(self):
        fields = self.admin.get_search_fields(self.request)
        assert 'folio' in fields
        assert 'solicitante_nombre' in fields
        assert 'clave_catastral' in fields

    @pytest.mark.parametrize('dept', ['SEC', 'TES'])
    def test_non_dau_excludes_clave_catastral(self, dept):
        with override_settings(ACTIVE_DEPARTMENT=dept):
            fields = self.admin.get_search_fields(self.request)
        assert 'folio' in fields
        assert 'solicitante_nombre' in fields
        assert 'clave_catastral' not in fields
