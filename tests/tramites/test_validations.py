"""Tests for Tramite state machine: transition validation, permission checks,
available_actions, and Estatus helper methods.

These tests complement test_models.py which focuses on workflow methods
(asignar, cerrar, etc.) by testing the guards and helpers they depend on.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from core.rbac.constants import BackOfficeRole
from tramites import workflow
from tramites.constants import ESTATUS_EN_DILIGENCIA
from tramites.exceptions import EstadoNoPermitidoError, TramiteNoAsignableError
from tramites.models import Tramite
from tramites.models.catalogos import TramiteEstatus
from tramites.models.tramite import TRANSITIONS

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def analista(django_db_setup):  # noqa: ARG001
    user = User.objects.create_user(
        username='val_analista',
        email='val_analista@example.com',
        password='testpass123',
        is_staff=True,
    )
    group = Group.objects.get_or_create(name=BackOfficeRole.ANALISTA)[0]
    user.groups.add(group)
    return user


@pytest.fixture
def tramite_en_revision(django_db_setup, django_db_blocker):  # noqa: ARG001
    """Tramite in EN_REVISION (202), unassigned."""
    return Tramite(
        id=100,
        folio='VAL-001',
        tramite_id=1,
        tramite_nombre='Validación',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.EN_REVISION,
        ultima_actividad_estatus='EN REVISIÓN',
        asignado_user_id=None,
        asignado_username=None,
        asignado_nombre=None,
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


# ---------------------------------------------------------------------------
# TramiteEstatus helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('estatus_id', 'expected'),
    [
        (TramiteEstatus.Estatus.PRESENTADO, True),
        (TramiteEstatus.Estatus.EN_REVISION, True),
        (TramiteEstatus.Estatus.REQUERIMIENTO, True),
        (TramiteEstatus.Estatus.SUBSANADO, True),
        (TramiteEstatus.Estatus.EN_DILIGENCIA, True),
        (TramiteEstatus.Estatus.BORRADOR, False),
        (TramiteEstatus.Estatus.PENDIENTE_PAGO, False),
        (TramiteEstatus.Estatus.POR_RECOGER, False),
        (TramiteEstatus.Estatus.RECHAZADO, False),
        (TramiteEstatus.Estatus.FINALIZADO, False),
        (TramiteEstatus.Estatus.CANCELADO, False),
        (TramiteEstatus.Estatus.PAGO_EXPIRADO, False),
    ],
    ids=lambda v: f'estatus_{v}' if isinstance(v, int) else str(v),
)
def test_es_activo(estatus_id, expected):
    """es_activo returns True only for active (2xx) statuses."""
    assert TramiteEstatus.Estatus.es_activo(estatus_id) is expected


def test_finalizados_contains_all_terminal_statuses():
    """finalizados() includes all terminal/closed statuses."""
    final = TramiteEstatus.Estatus.finalizados()
    assert TramiteEstatus.Estatus.POR_RECOGER in final
    assert TramiteEstatus.Estatus.RECHAZADO in final
    assert TramiteEstatus.Estatus.FINALIZADO in final
    assert TramiteEstatus.Estatus.CANCELADO in final
    assert TramiteEstatus.Estatus.PAGO_EXPIRADO in final


def test_finalizados_excludes_active_statuses():
    """finalizados() does NOT include active statuses."""
    final = TramiteEstatus.Estatus.finalizados()
    assert TramiteEstatus.Estatus.PRESENTADO not in final
    assert TramiteEstatus.Estatus.EN_REVISION not in final
    assert TramiteEstatus.Estatus.REQUERIMIENTO not in final


def test_estatus_en_diligencia_constant_matches_enum():
    """The ESTATUS_EN_DILIGENCIA constant must match the Estatus enum (205).

    Guards against the two sources of truth silently diverging: the constant
    is used in managers/querysets, the enum in model permission methods.
    """
    assert ESTATUS_EN_DILIGENCIA == TramiteEstatus.Estatus.EN_DILIGENCIA


# ---------------------------------------------------------------------------
# TRANSITIONS dict coverage
# ---------------------------------------------------------------------------


def test_all_active_to_close_transitions_exist():
    """Closure matrix per active status (refined workflow, Aug 2026).

    - 202/203/204 close to RECHAZADO (302) and CANCELADO (304) only.
    - 205 closes to POR_RECOGER (301), RECHAZADO (302) and CANCELADO (304)
      and is the ONLY route to 301.
    """
    expected = {
        TramiteEstatus.Estatus.EN_REVISION: (
            TramiteEstatus.Estatus.RECHAZADO,
            TramiteEstatus.Estatus.CANCELADO,
        ),
        TramiteEstatus.Estatus.REQUERIMIENTO: (
            TramiteEstatus.Estatus.RECHAZADO,
            TramiteEstatus.Estatus.CANCELADO,
        ),
        TramiteEstatus.Estatus.SUBSANADO: (
            TramiteEstatus.Estatus.RECHAZADO,
            TramiteEstatus.Estatus.CANCELADO,
        ),
        TramiteEstatus.Estatus.EN_DILIGENCIA: (
            TramiteEstatus.Estatus.POR_RECOGER,
            TramiteEstatus.Estatus.RECHAZADO,
            TramiteEstatus.Estatus.CANCELADO,
        ),
    }

    for active, targets in expected.items():
        for target in targets:
            assert (active, target) in TRANSITIONS, f'Missing transition: {active} → {target}'

    # 301 is unreachable from revision states
    for active in (
        TramiteEstatus.Estatus.EN_REVISION,
        TramiteEstatus.Estatus.REQUERIMIENTO,
        TramiteEstatus.Estatus.SUBSANADO,
    ):
        assert (active, TramiteEstatus.Estatus.POR_RECOGER) not in TRANSITIONS


def test_reiterar_self_loop_and_subsanado_transitions_exist():
    """203→203 self-loop and 204 review transitions are defined."""
    assert (TramiteEstatus.Estatus.REQUERIMIENTO, TramiteEstatus.Estatus.REQUERIMIENTO) in (
        TRANSITIONS
    )
    assert (TramiteEstatus.Estatus.SUBSANADO, TramiteEstatus.Estatus.REQUERIMIENTO) in TRANSITIONS
    assert (TramiteEstatus.Estatus.SUBSANADO, TramiteEstatus.Estatus.EN_DILIGENCIA) in TRANSITIONS


# ---------------------------------------------------------------------------
# workflow.closure_targets (dropdown de cancelación)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        (TramiteEstatus.Estatus.PRESENTADO, ()),
        (TramiteEstatus.Estatus.EN_REVISION, (302, 304)),
        (TramiteEstatus.Estatus.REQUERIMIENTO, (302, 304)),
        (TramiteEstatus.Estatus.SUBSANADO, (302, 304)),
        (TramiteEstatus.Estatus.EN_DILIGENCIA, (301, 302, 304)),
    ],
)
def test_closure_targets_by_source(source, expected):
    """Solo los destinos de cierre alcanzables desde cada estatus."""
    assert workflow.closure_targets(source) == expected


def test_closure_targets_respects_disabled():
    """BACKOFFICE_DISABLED_TRANSITIONS elimina destinos del dropdown."""
    assert workflow.closure_targets(TramiteEstatus.Estatus.EN_DILIGENCIA, disabled={301}) == (
        302,
        304,
    )
    assert workflow.closure_targets(TramiteEstatus.Estatus.EN_REVISION, disabled={302, 304}) == ()


def test_invalid_transition_not_in_dict():
    """Borrador → EN_REVISION is not a valid direct transition."""
    assert (
        TramiteEstatus.Estatus.BORRADOR,
        TramiteEstatus.Estatus.EN_REVISION,
    ) not in TRANSITIONS


# ---------------------------------------------------------------------------
# Tramite._validate_transition
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_valid_transition_passes(tramite_en_revision):
    """EN_REVISION → REQUERIMIENTO does not raise."""
    tramite_en_revision._validate_transition(TramiteEstatus.Estatus.REQUERIMIENTO)


@pytest.mark.django_db
def test_invalid_transition_raises(tramite_en_revision):
    """EN_REVISION → BORRADOR raises EstadoNoPermitidoError."""
    with pytest.raises(EstadoNoPermitidoError, match='estatus actual'):
        tramite_en_revision._validate_transition(TramiteEstatus.Estatus.BORRADOR)


# ---------------------------------------------------------------------------
# Tramite._assert_activo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    'estatus_id',
    [
        TramiteEstatus.Estatus.PRESENTADO,
        TramiteEstatus.Estatus.EN_REVISION,
        TramiteEstatus.Estatus.REQUERIMIENTO,
        TramiteEstatus.Estatus.EN_DILIGENCIA,
    ],
)
def test_active_statuses_pass(tramite_en_revision, estatus_id):
    """Active statuses should not raise."""
    tramite_en_revision.ultima_actividad_estatus_id = estatus_id
    tramite_en_revision._assert_activo()  # Should not raise


@pytest.mark.django_db
@pytest.mark.parametrize(
    'estatus_id',
    [
        TramiteEstatus.Estatus.BORRADOR,
        TramiteEstatus.Estatus.PENDIENTE_PAGO,
        TramiteEstatus.Estatus.POR_RECOGER,
        TramiteEstatus.Estatus.RECHAZADO,
        TramiteEstatus.Estatus.FINALIZADO,
        TramiteEstatus.Estatus.CANCELADO,
    ],
)
def test_inactive_statuses_raise(tramite_en_revision, estatus_id):
    """Non-active statuses should raise TramiteNoAsignableError."""
    tramite_en_revision.ultima_actividad_estatus_id = estatus_id
    with pytest.raises(TramiteNoAsignableError, match='no se encuentra activo'):
        tramite_en_revision._assert_activo()


# ---------------------------------------------------------------------------
# Tramite.can_* permission methods
# ---------------------------------------------------------------------------


@pytest.fixture
def perms_superuser(db):  # noqa: ARG001
    return User.objects.create_superuser(
        username='val_superuser',
        email='su@example.com',
        password='testpass123',
    )


@pytest.fixture
def perms_coordinador(db):  # noqa: ARG001
    user = User.objects.create_user(
        username='val_coordinador',
        email='coord@example.com',
        password='testpass123',
        is_staff=True,
    )
    group = Group.objects.get_or_create(name=BackOfficeRole.COORDINADOR)[0]
    user.groups.add(group)
    return user


@pytest.fixture
def assigned_tramite(tramite_en_revision, analista):
    """Tramite assigned to analista."""
    tramite_en_revision.asignado_user_id = analista.id
    return tramite_en_revision


# -- can_view --
@pytest.mark.django_db
def test_can_view_superuser(assigned_tramite, perms_superuser):
    assert assigned_tramite.can_view(perms_superuser) is True


@pytest.mark.django_db
def test_can_view_coordinador(assigned_tramite, perms_coordinador):
    assert assigned_tramite.can_view(perms_coordinador) is True


@pytest.mark.django_db
def test_can_view_assigned_analista(assigned_tramite, analista):
    assert assigned_tramite.can_view(analista) is True


@pytest.mark.django_db
def test_cannot_view_unassigned_analista(assigned_tramite):
    other = User.objects.create_user(
        username='val_other_analista',
        password='testpass123',
        is_staff=True,
    )
    assert assigned_tramite.can_view(other) is False


# -- can_assign / can_release --
@pytest.mark.django_db
def test_can_assign_coordinador(tramite_en_revision, perms_coordinador):
    assert tramite_en_revision.can_assign(perms_coordinador) is True


@pytest.mark.django_db
def test_cannot_assign_analista(tramite_en_revision, analista):
    assert tramite_en_revision.can_assign(analista) is False


@pytest.mark.django_db
def test_can_release_coordinador(assigned_tramite, perms_coordinador):
    assert assigned_tramite.can_release(perms_coordinador) is True


@pytest.mark.django_db
def test_cannot_release_analista(assigned_tramite, analista):
    assert assigned_tramite.can_release(analista) is False


# -- can_execute_action --
@pytest.mark.django_db
def test_can_execute_assigned_analista(assigned_tramite, analista):
    assert assigned_tramite.can_execute_action(analista) is True


@pytest.mark.django_db
def test_cannot_execute_unassigned_analista(assigned_tramite):
    other = User.objects.create_user(
        username='val_other',
        password='testpass123',
        is_staff=True,
    )
    assert assigned_tramite.can_execute_action(other) is False


# ---------------------------------------------------------------------------
# Tramite.available_actions
# ---------------------------------------------------------------------------


@pytest.fixture
def avail_superuser(db):  # noqa: ARG001
    return User.objects.create_superuser(
        username='act_superuser',
        email='su@example.com',
        password='testpass123',
    )


@pytest.mark.django_db
def test_en_revision_has_all_actions(tramite_en_revision, avail_superuser):
    tramite_en_revision.asignado_user_id = avail_superuser.id
    actions = tramite_en_revision.available_actions(avail_superuser)
    assert 'requerir_documentos' in actions
    assert 'enviar_a_firma' in actions
    assert 'cancelar' in actions


@pytest.mark.django_db
def test_requerimiento_reiterar_and_cancelar(tramite_en_revision, avail_superuser):
    tramite_en_revision.ultima_actividad_estatus_id = TramiteEstatus.Estatus.REQUERIMIENTO
    tramite_en_revision.asignado_user_id = avail_superuser.id
    actions = tramite_en_revision.available_actions(avail_superuser)
    assert actions == ['requerir_documentos', 'cancelar']


@pytest.mark.django_db
def test_subsanado_all_review_actions(tramite_en_revision, avail_superuser):
    tramite_en_revision.ultima_actividad_estatus_id = TramiteEstatus.Estatus.SUBSANADO
    tramite_en_revision.asignado_user_id = avail_superuser.id
    actions = tramite_en_revision.available_actions(avail_superuser)
    assert actions == ['requerir_documentos', 'enviar_a_firma', 'cancelar']


@pytest.mark.django_db
def test_enviar_a_firma_only_cancelar(tramite_en_revision, avail_superuser):
    tramite_en_revision.ultima_actividad_estatus_id = TramiteEstatus.Estatus.EN_DILIGENCIA
    tramite_en_revision.asignado_user_id = avail_superuser.id
    actions = tramite_en_revision.available_actions(avail_superuser)
    assert actions == ['cancelar']


@pytest.mark.django_db
def test_presentado_no_actions(tramite_en_revision, avail_superuser):
    tramite_en_revision.ultima_actividad_estatus_id = TramiteEstatus.Estatus.PRESENTADO
    tramite_en_revision.asignado_user_id = avail_superuser.id
    actions = tramite_en_revision.available_actions(avail_superuser)
    assert actions == []


@pytest.mark.django_db
def test_unassigned_user_no_actions(tramite_en_revision):
    """User not assigned to tramite gets no actions."""
    user = User.objects.create_user(
        username='act_unassigned',
        password='testpass123',
        is_staff=True,
    )
    actions = tramite_en_revision.available_actions(user)
    assert actions == []
