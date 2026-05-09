"""Tests for Tramite state machine: transition validation, permission checks,
available_actions, and Estatus helper methods.

These tests complement test_models.py which focuses on workflow methods
(asignar, cerrar, etc.) by testing the guards and helpers they depend on.
"""

import pytest
from django.contrib.auth import get_user_model

from core.rbac.constants import BackOfficeRole
from tramites.exceptions import EstadoNoPermitidoError, TramiteNoAsignableError
from tramites.models import Tramite
from tramites.models.catalogos import TramiteEstatus

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def analista(django_db_setup):
    from django.contrib.auth.models import Group

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
def tramite_en_revision(django_db_setup, django_db_blocker):
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


class TestTramiteEstatusHelpers:
    """Tests for TramiteEstatus.Estatus helper class methods."""

    @pytest.mark.parametrize(
        'estatus_id, expected',
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
    def test_es_activo(self, estatus_id, expected):
        """es_activo returns True only for active (2xx) statuses."""
        assert TramiteEstatus.Estatus.es_activo(estatus_id) is expected

    def test_finalizados_contains_all_terminal_statuses(self):
        """finalizados() includes all terminal/closed statuses."""
        final = TramiteEstatus.Estatus.finalizados()
        assert TramiteEstatus.Estatus.POR_RECOGER in final
        assert TramiteEstatus.Estatus.RECHAZADO in final
        assert TramiteEstatus.Estatus.FINALIZADO in final
        assert TramiteEstatus.Estatus.CANCELADO in final
        assert TramiteEstatus.Estatus.PAGO_EXPIRADO in final

    def test_finalizados_excludes_active_statuses(self):
        """finalizados() does NOT include active statuses."""
        final = TramiteEstatus.Estatus.finalizados()
        assert TramiteEstatus.Estatus.PRESENTADO not in final
        assert TramiteEstatus.Estatus.EN_REVISION not in final
        assert TramiteEstatus.Estatus.REQUERIMIENTO not in final


# ---------------------------------------------------------------------------
# TRANSITIONS dict coverage
# ---------------------------------------------------------------------------


class TestTransitionsDict:
    """Validate the TRANSITIONS constant covers all expected state changes."""

    def test_all_active_to_close_transitions_exist(self):
        """Every active status must be closable."""
        from tramites.models.tramite import TRANSITIONS

        active_statuses = [
            TramiteEstatus.Estatus.EN_REVISION,
            TramiteEstatus.Estatus.REQUERIMIENTO,
            TramiteEstatus.Estatus.EN_DILIGENCIA,
        ]
        close_targets = [
            TramiteEstatus.Estatus.POR_RECOGER,
            TramiteEstatus.Estatus.RECHAZADO,
            TramiteEstatus.Estatus.CANCELADO,
        ]

        for active in active_statuses:
            for target in close_targets:
                assert (active, target) in TRANSITIONS, (
                    f'Missing transition: {active} → {target}'
                )

    def test_invalid_transition_not_in_dict(self):
        """Borrador → EN_REVISION is not a valid direct transition."""
        from tramites.models.tramite import TRANSITIONS

        assert (
            TramiteEstatus.Estatus.BORRADOR,
            TramiteEstatus.Estatus.EN_REVISION,
        ) not in TRANSITIONS


# ---------------------------------------------------------------------------
# Tramite._validate_transition
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestValidateTransition:
    """Tests for Tramite._validate_transition() guard."""

    def test_valid_transition_passes(self, tramite_en_revision):
        """EN_REVISION → REQUERIMIENTO does not raise."""
        tramite_en_revision._validate_transition(TramiteEstatus.Estatus.REQUERIMIENTO)

    def test_invalid_transition_raises(self, tramite_en_revision):
        """EN_REVISION → BORRADOR raises EstadoNoPermitidoError."""
        with pytest.raises(EstadoNoPermitidoError, match='estatus actual'):
            tramite_en_revision._validate_transition(TramiteEstatus.Estatus.BORRADOR)


# ---------------------------------------------------------------------------
# Tramite._assert_activo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAssertActivo:
    """Tests for Tramite._assert_activo() guard."""

    @pytest.mark.parametrize(
        'estatus_id',
        [
            TramiteEstatus.Estatus.PRESENTADO,
            TramiteEstatus.Estatus.EN_REVISION,
            TramiteEstatus.Estatus.REQUERIMIENTO,
            TramiteEstatus.Estatus.EN_DILIGENCIA,
        ],
    )
    def test_active_statuses_pass(self, tramite_en_revision, estatus_id):
        """Active statuses should not raise."""
        tramite_en_revision.ultima_actividad_estatus_id = estatus_id
        tramite_en_revision._assert_activo()  # Should not raise

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
    def test_inactive_statuses_raise(self, tramite_en_revision, estatus_id):
        """Non-active statuses should raise TramiteNoAsignableError."""
        tramite_en_revision.ultima_actividad_estatus_id = estatus_id
        with pytest.raises(TramiteNoAsignableError, match='no se encuentra activo'):
            tramite_en_revision._assert_activo()


# ---------------------------------------------------------------------------
# Tramite.can_* permission methods
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTramitePermissions:
    """Tests for Tramite permission check methods."""

    @pytest.fixture
    def superuser(self, db):
        return User.objects.create_superuser(
            username='val_superuser', email='su@example.com', password='testpass123',
        )

    @pytest.fixture
    def coordinador(self, db):
        from django.contrib.auth.models import Group

        from core.rbac.constants import BackOfficeRole

        user = User.objects.create_user(
            username='val_coordinador', email='coord@example.com',
            password='testpass123', is_staff=True,
        )
        group = Group.objects.get_or_create(name=BackOfficeRole.COORDINADOR)[0]
        user.groups.add(group)
        return user

    @pytest.fixture
    def assigned_tramite(self, tramite_en_revision, analista):
        """Tramite assigned to analista."""
        tramite_en_revision.asignado_user_id = analista.id
        return tramite_en_revision

    # -- can_view --
    def test_can_view_superuser(self, assigned_tramite, superuser):
        assert assigned_tramite.can_view(superuser) is True

    def test_can_view_coordinador(self, assigned_tramite, coordinador):
        assert assigned_tramite.can_view(coordinador) is True

    def test_can_view_assigned_analista(self, assigned_tramite, analista):
        assert assigned_tramite.can_view(analista) is True

    def test_cannot_view_unassigned_analista(self, assigned_tramite, db):
        other = User.objects.create_user(
            username='val_other_analista', password='testpass123', is_staff=True,
        )
        assert assigned_tramite.can_view(other) is False

    # -- can_assign / can_release --
    def test_can_assign_coordinador(self, tramite_en_revision, coordinador):
        assert tramite_en_revision.can_assign(coordinador) is True

    def test_cannot_assign_analista(self, tramite_en_revision, analista):
        assert tramite_en_revision.can_assign(analista) is False

    def test_can_release_coordinador(self, assigned_tramite, coordinador):
        assert assigned_tramite.can_release(coordinador) is True

    def test_cannot_release_analista(self, assigned_tramite, analista):
        assert assigned_tramite.can_release(analista) is False

    # -- can_execute_action --
    def test_can_execute_assigned_analista(self, assigned_tramite, analista):
        assert assigned_tramite.can_execute_action(analista) is True

    def test_cannot_execute_unassigned_analista(self, assigned_tramite, db):
        other = User.objects.create_user(
            username='val_other', password='testpass123', is_staff=True,
        )
        assert assigned_tramite.can_execute_action(other) is False


# ---------------------------------------------------------------------------
# Tramite.available_actions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAvailableActions:
    """Tests for Tramite.available_actions() based on status + role."""

    @pytest.fixture
    def superuser(self, db):
        return User.objects.create_superuser(
            username='act_superuser', email='su@example.com', password='testpass123',
        )

    def test_en_revision_has_all_actions(self, tramite_en_revision, superuser):
        tramite_en_revision.asignado_user_id = superuser.id
        actions = tramite_en_revision.available_actions(superuser)
        assert 'requerir_documentos' in actions
        assert 'en_diligencia' in actions
        assert 'cerrar' in actions

    def test_requerimiento_only_cerrar(self, tramite_en_revision, superuser):
        tramite_en_revision.ultima_actividad_estatus_id = TramiteEstatus.Estatus.REQUERIMIENTO
        tramite_en_revision.asignado_user_id = superuser.id
        actions = tramite_en_revision.available_actions(superuser)
        assert actions == ['cerrar']

    def test_en_diligencia_only_cerrar(self, tramite_en_revision, superuser):
        tramite_en_revision.ultima_actividad_estatus_id = TramiteEstatus.Estatus.EN_DILIGENCIA
        tramite_en_revision.asignado_user_id = superuser.id
        actions = tramite_en_revision.available_actions(superuser)
        assert actions == ['cerrar']

    def test_presentado_no_actions(self, tramite_en_revision, superuser):
        tramite_en_revision.ultima_actividad_estatus_id = TramiteEstatus.Estatus.PRESENTADO
        tramite_en_revision.asignado_user_id = superuser.id
        actions = tramite_en_revision.available_actions(superuser)
        assert actions == []

    def test_unassigned_user_no_actions(self, tramite_en_revision, db):
        """User not assigned to tramite gets no actions."""
        user = User.objects.create_user(
            username='act_unassigned', password='testpass123', is_staff=True,
        )
        actions = tramite_en_revision.available_actions(user)
        assert actions == []
