"""
Tests for DISABLED_TRANSITIONS filtering.

Validates that _get_disabled_transitions() and Tramite.available_actions()
correctly filter workflow transitions based on settings.DISABLED_TRANSITIONS.

All tests use override_settings() so no .env changes are needed.
"""

import pytest
from django.test import override_settings

from tramites.models.catalogos import TramiteEstatus
from tramites.models.tramite import (
    TRANSITIONS,
    _get_disabled_transitions,
)

# ---------------------------------------------------------------------------
# _get_disabled_transitions()
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_no_disabled_returns_empty_set():
    """Without DISABLED_TRANSITIONS, the set is empty."""
    with override_settings(DISABLED_TRANSITIONS=[]):
        assert _get_disabled_transitions() == set()


@pytest.mark.django_db
def test_disabled_transitions_are_returned_as_int_set():
    """DISABLED_TRANSITIONS values are returned as a set of ints."""
    with override_settings(DISABLED_TRANSITIONS=[205, 203]):
        result = _get_disabled_transitions()
        assert result == {205, 203}


# ---------------------------------------------------------------------------
# String coercion defense-in-depth
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_string_coercion():
    """override_settings with string values is coerced to int (defense-in-depth)."""
    with override_settings(DISABLED_TRANSITIONS=['205']):
        result = _get_disabled_transitions()
        # The helper coerces to int, so '205' becomes 205 in the set.
        assert 205 in result
        assert '205' not in result


@pytest.mark.django_db
def test_transitions_constant_never_mutated():
    """The TRANSITIONS dict is never modified by the helpers."""
    original_count = len(TRANSITIONS)
    original_keys = set(TRANSITIONS.keys())

    with override_settings(DISABLED_TRANSITIONS=[205, 203]):
        _get_disabled_transitions()

    assert len(TRANSITIONS) == original_count
    assert set(TRANSITIONS.keys()) == original_keys


# ---------------------------------------------------------------------------
# available_actions() — requires in-memory Tramite
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_available_actions_excludes_disabled(analista, django_db_setup):
    """available_actions() hides en_diligencia when 205 is disabled."""
    from tramites.models import Tramite

    tramite = Tramite(
        id=99,
        folio='TEST-000099',
        tramite_id=1,
        tramite_nombre='Test Trámite',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.EN_REVISION,
        ultima_actividad_estatus='EN REVISIÓN',
        asignado_user_id=analista.id,
        asignado_username=analista.username,
        asignado_nombre=analista.get_full_name(),
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )

    with override_settings(DISABLED_TRANSITIONS=[205]):
        actions = tramite.available_actions(analista)

    assert 'en_diligencia' not in actions
    assert 'requerir_documentos' in actions
    assert 'cerrar' in actions


@pytest.mark.django_db
def test_available_actions_includes_non_disabled(analista, django_db_setup):
    """available_actions() includes all actions when nothing is disabled."""
    from tramites.models import Tramite

    tramite = Tramite(
        id=100,
        folio='TEST-000100',
        tramite_id=1,
        tramite_nombre='Test Trámite',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.EN_REVISION,
        ultima_actividad_estatus='EN REVISIÓN',
        asignado_user_id=analista.id,
        asignado_username=analista.username,
        asignado_nombre=analista.get_full_name(),
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )

    with override_settings(DISABLED_TRANSITIONS=[]):
        actions = tramite.available_actions(analista)

    assert 'requerir_documentos' in actions
    assert 'en_diligencia' in actions
    assert 'cerrar' in actions


# ---------------------------------------------------------------------------
# Fixtures needed by tests above
# ---------------------------------------------------------------------------


@pytest.fixture
def analista(django_db_setup):
    """Create an analyst user with the Analista role."""
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    User = get_user_model()
    user = User.objects.create_user(
        username='analista_disabled_test',
        email='analista_disabled@example.com',
        password='testpass123',
        first_name='Test',
        last_name='Analista',
    )
    user.groups.add(Group.objects.get_or_create(name='Analista')[0])
    return user
