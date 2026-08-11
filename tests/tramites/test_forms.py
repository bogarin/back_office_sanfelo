"""Tests for tramites.forms: TramiteDetailForm, CerrarTramiteForm, ESTATUS_CIERRE_CHOICES.

Validates field configuration, choice correctness, and whitespace rejection
in observacion fields (H-002-028).
"""

import pytest

from tramites.forms import CerrarTramiteForm, TramiteDetailForm
from tramites.models.catalogos import TramiteEstatus

# ---------------------------------------------------------------------------
# ESTATUS_CIERRE_CHOICES module constant
# ---------------------------------------------------------------------------


class TestEstatusCierreChoices:
    """Verify ESTATUS_CIERRE_CHOICES contains exactly the closure statuses."""

    def test_contains_three_choices(self):
        assert len(CerrarTramiteForm.base_fields['estatus_cierre'].choices) == 3

    @pytest.mark.parametrize(
        'estatus_value',
        [
            TramiteEstatus.Estatus.POR_RECOGER,
            TramiteEstatus.Estatus.RECHAZADO,
            TramiteEstatus.Estatus.CANCELADO,
        ],
    )
    def test_includes_closure_status(self, estatus_value):
        """Each terminal status must appear in estatus_cierre choices."""
        form = CerrarTramiteForm()
        values = [choice[0] for choice in form.fields['estatus_cierre'].choices]
        assert estatus_value in values

    @pytest.mark.parametrize(
        'estatus_value',
        [
            TramiteEstatus.Estatus.BORRADOR,
            TramiteEstatus.Estatus.PRESENTADO,
            TramiteEstatus.Estatus.EN_REVISION,
            TramiteEstatus.Estatus.REQUERIMIENTO,
            TramiteEstatus.Estatus.SUBSANADO,
            TramiteEstatus.Estatus.EN_DILIGENCIA,
            TramiteEstatus.Estatus.FINALIZADO,
        ],
    )
    def test_excludes_non_closure_status(self, estatus_value):
        """Non-closure statuses must NOT appear in estatus_cierre choices."""
        form = CerrarTramiteForm()
        values = [choice[0] for choice in form.fields['estatus_cierre'].choices]
        assert estatus_value not in values


# ---------------------------------------------------------------------------
# TramiteDetailForm
# ---------------------------------------------------------------------------


class TestTramiteDetailForm:
    """Tests for TramiteDetailForm — single observacion field."""

    def test_valid_with_content(self):
        form = TramiteDetailForm(data={'observacion': 'Revisión completada'})
        assert form.is_valid()

    def test_observacion_required(self):
        form = TramiteDetailForm(data={})
        assert not form.is_valid()
        assert 'observacion' in form.errors

    def test_observacion_empty_string_rejected(self):
        form = TramiteDetailForm(data={'observacion': ''})
        assert not form.is_valid()
        assert 'observacion' in form.errors

    def test_observacion_whitespace_only_rejected(self):
        """Whitespace-only observacion must be rejected (H-002-028)."""
        form = TramiteDetailForm(data={'observacion': '   \t\n  '})
        assert not form.is_valid()
        assert 'observacion' in form.errors

    def test_observacion_strips_whitespace(self):
        """Valid content surrounded by whitespace is accepted and stripped."""
        form = TramiteDetailForm(data={'observacion': '  contenido válido  '})
        assert form.is_valid()
        assert form.cleaned_data['observacion'] == 'contenido válido'

    def test_observacion_long_text_accepted(self):
        """Long observacion is accepted (no max_length constraint)."""
        form = TramiteDetailForm(data={'observacion': 'x' * 2000})
        assert form.is_valid()

    def test_observacion_single_char_accepted(self):
        """Single non-whitespace char is accepted."""
        form = TramiteDetailForm(data={'observacion': 'a'})
        assert form.is_valid()


# ---------------------------------------------------------------------------
# CerrarTramiteForm
# ---------------------------------------------------------------------------


class TestCerrarTramiteForm:
    """Tests for CerrarTramiteForm — estatus_cierre + observacion."""

    # -- estatus_cierre field --

    def test_valid_with_por_recoger(self):
        form = CerrarTramiteForm(
            data={
                'estatus_cierre': TramiteEstatus.Estatus.POR_RECOGER,
                'observacion': 'Trámite listo para entrega',
            }
        )
        assert form.is_valid()

    def test_valid_with_rechazado(self):
        form = CerrarTramiteForm(
            data={
                'estatus_cierre': TramiteEstatus.Estatus.RECHAZADO,
                'observacion': 'Documentación incompleta',
            }
        )
        assert form.is_valid()

    def test_valid_with_cancelado(self):
        form = CerrarTramiteForm(
            data={
                'estatus_cierre': TramiteEstatus.Estatus.CANCELADO,
                'observacion': 'Solicitante desistió',
            }
        )
        assert form.is_valid()

    def test_estatus_cierre_required(self):
        form = CerrarTramiteForm(
            data={
                'observacion': 'Motivo válido',
            }
        )
        assert not form.is_valid()
        assert 'estatus_cierre' in form.errors

    def test_estatus_cierre_invalid_value_rejected(self):
        form = CerrarTramiteForm(
            data={
                'estatus_cierre': 9999,
                'observacion': 'Motivo válido',
            }
        )
        assert not form.is_valid()
        assert 'estatus_cierre' in form.errors

    def test_estatus_cierre_active_status_rejected(self):
        """Active statuses (e.g. EN_REVISION) must not be accepted as cierre."""
        form = CerrarTramiteForm(
            data={
                'estatus_cierre': TramiteEstatus.Estatus.EN_REVISION,
                'observacion': 'Motivo válido',
            }
        )
        assert not form.is_valid()
        assert 'estatus_cierre' in form.errors

    # -- observacion field --

    def test_observacion_required(self):
        form = CerrarTramiteForm(
            data={
                'estatus_cierre': TramiteEstatus.Estatus.POR_RECOGER,
            }
        )
        assert not form.is_valid()
        assert 'observacion' in form.errors

    def test_observacion_empty_string_rejected(self):
        form = CerrarTramiteForm(
            data={
                'estatus_cierre': TramiteEstatus.Estatus.POR_RECOGER,
                'observacion': '',
            }
        )
        assert not form.is_valid()
        assert 'observacion' in form.errors

    def test_observacion_whitespace_only_rejected(self):
        """Whitespace-only observacion must be rejected (H-002-028)."""
        form = CerrarTramiteForm(
            data={
                'estatus_cierre': TramiteEstatus.Estatus.POR_RECOGER,
                'observacion': '  \n\t  ',
            }
        )
        assert not form.is_valid()
        assert 'observacion' in form.errors

    def test_observacion_strips_whitespace(self):
        """Valid content surrounded by whitespace is accepted and stripped."""
        form = CerrarTramiteForm(
            data={
                'estatus_cierre': TramiteEstatus.Estatus.POR_RECOGER,
                'observacion': '  motivo válido  ',
            }
        )
        assert form.is_valid()
        assert form.cleaned_data['observacion'] == 'motivo válido'

    # -- both fields missing --

    def test_both_fields_missing(self):
        form = CerrarTramiteForm(data={})
        assert not form.is_valid()
        assert 'estatus_cierre' in form.errors
        assert 'observacion' in form.errors
