"""
Tests for timeline-related features: DTOs, template filters, admin context.

Covers:
- validate_filename() for ACT-*.pdf pattern (security-critical)
- fetch_actividad_files() SFTP method
- ActividadFile / TimelineEntry dataclasses
- status_group / status_badge_class template filters
- admin change_view timeline context building
"""

from __future__ import annotations

from collections import defaultdict
from unittest.mock import MagicMock, patch

import pytest
from django.template import Template, Context
from django.template.engine import Engine
from django.test import override_settings

from tramites.constants import ACTIVIDAD_FILENAME_REGEX
from tramites.exceptions import SFTPConnectionError
from tramites.models import ActividadFile, RequisitoFile, TimelineEntry
from tramites.models.catalogos import TramiteEstatus
from tramites.sftp import SFTPService, validate_filename
from tramites.templatetags.admin_extras import status_badge_class, status_group


# =============================================================================
# P0: validate_filename() — ACT-*.pdf pattern
# =============================================================================


@pytest.mark.parametrize(
    'filename',
    [
        'ACT-145-2026-04-30T02-54-49.pdf',
        'ACT-1-2025-01-01T00-00-00.pdf',
        'ACT-999999-2099-12-31T23-59-59.pdf',
    ],
)
def test_validate_filename_act_pattern_accepted(filename):
    """ACT-* filenames with valid actividad_id and timestamp pass validation."""
    assert validate_filename(filename) == filename


@pytest.mark.parametrize(
    'filename',
    [
        'ACT-abc-2026-04-30T02-54-49.pdf',      # non-numeric actividad_id
        'ACT-145-2026-04-30.pdf',                # missing timestamp
        'ACT--145-2026-04-30T02-54-49.pdf',      # negative actividad_id
        'ACT-145-2026-04-30T02-54-49',           # missing .pdf extension
        'ACT-145-2026-04-30T02-54-49.txt',       # wrong extension
    ],
)
def test_validate_filename_act_pattern_rejected_invalid(filename):
    """ACT-* filenames with invalid format are rejected."""
    with pytest.raises(SFTPConnectionError):
        validate_filename(filename)


def test_validate_filename_act_path_traversal_rejected():
    """ACT-* filenames with path traversal characters are rejected."""
    with pytest.raises(SFTPConnectionError, match='caracteres no permitidos'):
        validate_filename('../ACT-145-2026-04-30T02-54-49.pdf')


def test_validate_filename_act_null_byte_rejected():
    """ACT-* filenames with null bytes are rejected."""
    with pytest.raises(SFTPConnectionError, match='caracteres no permitidos'):
        validate_filename('ACT-14\x005-2026-04-30T02-54-49.pdf')


def test_validate_filename_act_backslash_rejected():
    """ACT-* filenames with backslashes are rejected."""
    with pytest.raises(SFTPConnectionError, match='caracteres no permitidos'):
        validate_filename('ACT-145\\2026-04-30T02-54-49.pdf')


# Both DAU-* and ACT-* patterns must still work after the refactor
@pytest.mark.parametrize(
    'filename',
    [
        'DAU-260420-AAAE-B-19.pdf',          # requisito file
        'ACT-145-2026-04-30T02-54-49.pdf',   # actividad file
    ],
)
def test_validate_filename_both_schemas_accepted(filename):
    """validate_filename accepts both DAU-* and ACT-* schemas."""
    assert validate_filename(filename) == filename


# =============================================================================
# P0: ACTIVIDAD_FILENAME_REGEX — regex parsing
# =============================================================================


def test_actividad_regex_parses_valid_filename():
    """Regex extracts actividad_id and timestamp from ACT filename."""
    match = ACTIVIDAD_FILENAME_REGEX.match('ACT-145-2026-04-30T02-54-49.pdf')
    assert match is not None
    assert match.group('actividad_id') == '145'
    assert match.group('timestamp') == '2026-04-30T02-54-49'


@pytest.mark.parametrize(
    'filename',
    [
        'DAU-260420-AAAE-B-19.pdf',       # requisito pattern, not ACT
        'ACT-145.pdf',                     # missing timestamp
        'act-145-2026-04-30T02-54-49.pdf', # lowercase
        '',                                 # empty
        'random-file.pdf',                  # unrelated
    ],
)
def test_actividad_regex_rejects_non_matching(filename):
    """Regex rejects filenames that don't match ACT pattern."""
    assert ACTIVIDAD_FILENAME_REGEX.match(filename) is None


# =============================================================================
# P1: fetch_actividad_files() — SFTP listing
# =============================================================================


def _make_sftp_entry(filename: str, size: int) -> MagicMock:
    """Create a mock SFTP directory entry."""
    entry = MagicMock()
    entry.filename = filename
    entry.st_size = size
    return entry


@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_actividad_files_returns_files(mock_get_client, mock_close):
    """Returns list of ActividadFile for matching ACT-*.pdf files."""
    mock_sftp = MagicMock()
    mock_sftp.listdir_attr.return_value = [
        _make_sftp_entry('ACT-145-2026-04-30T02-54-49.pdf', 1024 * 1024),
    ]
    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    with (
        patch.object(SFTPService, '_list_files_for_tramite', return_value=[
            ('ACT-145-2026-04-30T02-54-49.pdf', 1.0),
        ]),
        patch('tramites.sftp.Actividades') as mock_act_model,
        patch.object(SFTPService, '_check_file_count_warning', return_value=None),
        override_settings(SFTP_BASE_DIR='/remote/pdfs'),
    ):
        mock_act_model.objects.filter.return_value = []
        files, warning = SFTPService.fetch_actividad_files('DAU-260420-AAAE-B')

    assert len(files) == 1
    assert files[0].actividad_id == 145
    assert files[0].file_name == 'ACT-145-2026-04-30T02-54-49.pdf'
    assert files[0].timestamp_str == '2026-04-30T02-54-49'
    assert warning is None
    mock_close.assert_called_once()


@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_actividad_files_invalid_folio_raises(mock_get_client, mock_close):
    """Invalid folio raises SFTPConnectionError before SFTP access."""
    with pytest.raises(SFTPConnectionError, match='caracteres no permitidos'):
        SFTPService.fetch_actividad_files('../../../etc')

    mock_get_client.assert_not_called()


@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_actividad_files_empty_directory(mock_get_client, mock_close):
    """No ACT files returns empty list."""
    with (
        patch.object(SFTPService, '_list_files_for_tramite', return_value=[]),
        override_settings(SFTP_BASE_DIR='/remote/pdfs'),
    ):
        files, warning = SFTPService.fetch_actividad_files('DAU-260420-AAAE-B')

    assert files == []
    assert warning is None


@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_actividad_files_filters_non_act(mock_get_client, mock_close):
    """Only ACT-*.pdf files are included; DAU-*.pdf and others are excluded."""
    with (
        patch.object(SFTPService, '_list_files_for_tramite', return_value=[
            ('ACT-145-2026-04-30T02-54-49.pdf', 1.0),
            ('DAU-260420-AAAE-B-19.pdf', 0.5),       # requisito file — excluded
            ('random-notes.txt', 0.1),                 # unrelated — excluded
        ]),
        patch('tramites.sftp.Actividades') as mock_act_model,
        patch.object(SFTPService, '_check_file_count_warning', return_value=None),
        override_settings(SFTP_BASE_DIR='/remote/pdfs'),
    ):
        mock_act_model.objects.filter.return_value = []
        files, warning = SFTPService.fetch_actividad_files('DAU-260420-AAAE-B')

    assert len(files) == 1
    assert files[0].actividad_id == 145


@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_actividad_files_sftp_error_closes_connection(
    mock_get_client, mock_close,
):
    """Connection is closed even on SFTP error."""
    with (
        patch.object(
            SFTPService, '_list_files_for_tramite',
            side_effect=SFTPConnectionError('connection failed'),
        ),
        pytest.raises(SFTPConnectionError, match='connection failed'),
    ):
        SFTPService.fetch_actividad_files('DAU-260420-AAAE-B')

    mock_close.assert_called_once()


@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_actividad_files_sorts_by_timestamp_desc(mock_get_client, mock_close):
    """Files are sorted by timestamp descending (most recent first)."""
    with (
        patch.object(SFTPService, '_list_files_for_tramite', return_value=[
            ('ACT-100-2026-04-30T10-00-00.pdf', 1.0),
            ('ACT-100-2026-04-30T08-00-00.pdf', 0.5),
            ('ACT-100-2026-04-30T12-00-00.pdf', 2.0),
        ]),
        patch('tramites.sftp.Actividades') as mock_act_model,
        patch.object(SFTPService, '_check_file_count_warning', return_value=None),
        override_settings(SFTP_BASE_DIR='/remote/pdfs'),
    ):
        mock_act_model.objects.filter.return_value = []
        files, _ = SFTPService.fetch_actividad_files('DAU-260420-AAAE-B')

    timestamps = [f.timestamp_str for f in files]
    assert timestamps == [
        '2026-04-30T12-00-00',
        '2026-04-30T10-00-00',
        '2026-04-30T08-00-00',
    ]


# =============================================================================
# P2: ActividadFile dataclass
# =============================================================================


def test_actividad_file_basic_creation():
    """ActividadFile stores all fields correctly."""
    af = ActividadFile(
        actividad_id=145,
        file_name='ACT-145-2026-04-30T02-54-49.pdf',
        size_mb=0.11,
        timestamp_str='2026-04-30T02-54-49',
    )
    assert af.actividad_id == 145
    assert af.file_name == 'ACT-145-2026-04-30T02-54-49.pdf'
    assert af.size_mb == 0.11
    assert af.timestamp_str == '2026-04-30T02-54-49'
    # Optional fields default to None
    assert af.observacion is None
    assert af.estatus_nombre is None
    assert af.backoffice_user_id is None


def test_actividad_file_with_optional_fields():
    """ActividadFile can carry enriched data from DB."""
    af = ActividadFile(
        actividad_id=145,
        file_name='ACT-145-2026-04-30T02-54-49.pdf',
        size_mb=0.11,
        timestamp_str='2026-04-30T02-54-49',
        observacion='Prueba de peticion de documentos',
        estatus_nombre='REQUERIMIENTO',
        backoffice_user_id=5,
    )
    assert af.observacion == 'Prueba de peticion de documentos'
    assert af.estatus_nombre == 'REQUERIMIENTO'
    assert af.backoffice_user_id == 5


# =============================================================================
# P2: RequisitoFile dataclass
# =============================================================================


def test_requisito_file_basic_creation():
    """RequisitoFile stores all fields correctly."""
    rf = RequisitoFile(
        requisito_id=19,
        requisito_nombre='Identificación oficial',
        file_name='DAU-260420-AAAE-B-19.pdf',
        size_mb=0.05,
    )
    assert rf.requisito_id == 19
    assert rf.requisito_nombre == 'Identificación oficial'
    assert rf.file_name == 'DAU-260420-AAAE-B-19.pdf'
    assert rf.size_mb == 0.05


def test_requisito_file_without_catalog_name():
    """RequisitoFile accepts None for requisito_nombre (not in catalog)."""
    rf = RequisitoFile(
        requisito_id=999,
        requisito_nombre=None,
        file_name='DAU-260420-AAAE-B-999.pdf',
        size_mb=1.0,
    )
    assert rf.requisito_nombre is None


# =============================================================================
# P2: TimelineEntry dataclass
# =============================================================================


def _make_actividad_mock(estatus_id=203, actividad_id=145, user_id=5):
    """Create a mock Actividades instance for timeline tests."""
    act = MagicMock()
    act.id = actividad_id
    act.estatus_id = estatus_id
    act.backoffice_user_id = user_id
    act.observacion = 'Test observacion'
    return act


def test_timeline_entry_basic_creation():
    """TimelineEntry wraps actividad + files + user."""
    act = _make_actividad_mock()
    user = MagicMock()
    entry = TimelineEntry(
        actividad=act,
        actividad_files=[],
        requisito_files=[],
        user=user,
    )
    assert entry.actividad is act
    assert entry.actividad_files == []
    assert entry.requisito_files == []
    assert entry.user is user


def test_timeline_entry_user_defaults_to_none():
    """TimelineEntry.user is None when backoffice_user_id is missing."""
    act = _make_actividad_mock(user_id=None)
    entry = TimelineEntry(
        actividad=act,
        actividad_files=[],
        requisito_files=[],
    )
    assert entry.user is None


def test_timeline_entry_with_actividad_files():
    """TimelineEntry carries ACT files for REQUERIMIENTO/SUBSANADO."""
    act = _make_actividad_mock(estatus_id=TramiteEstatus.Estatus.REQUERIMIENTO)
    af = ActividadFile(
        actividad_id=145,
        file_name='ACT-145-2026-04-30T02-54-49.pdf',
        size_mb=0.11,
        timestamp_str='2026-04-30T02-54-49',
    )
    entry = TimelineEntry(
        actividad=act,
        actividad_files=[af],
        requisito_files=[],
    )
    assert len(entry.actividad_files) == 1
    assert entry.actividad_files[0].actividad_id == 145


def test_timeline_entry_with_requisito_files():
    """TimelineEntry carries requisito files for PENDIENTE_PAGO."""
    act = _make_actividad_mock(estatus_id=TramiteEstatus.Estatus.PENDIENTE_PAGO)
    rf = RequisitoFile(
        requisito_id=19,
        requisito_nombre='Identificación oficial',
        file_name='DAU-260420-AAAE-B-19.pdf',
        size_mb=0.05,
    )
    entry = TimelineEntry(
        actividad=act,
        actividad_files=[],
        requisito_files=[rf],
    )
    assert len(entry.requisito_files) == 1
    assert entry.requisito_files[0].requisito_id == 19


# =============================================================================
# P2: status_group template filter
# =============================================================================


@pytest.mark.parametrize(
    'estatus_id, expected',
    [
        (100, 'inicio'),
        (101, 'inicio'),
        (150, 'inicio'),
        (199, 'inicio'),
        (200, 'proceso'),
        (201, 'proceso'),
        (250, 'proceso'),
        (299, 'proceso'),
        (300, 'finalizado'),
        (301, 'finalizado'),
        (350, 'finalizado'),
        (399, 'finalizado'),
    ],
)
def test_status_group_returns_correct_group(estatus_id, expected):
    """status_group returns the correct family name for each range."""
    assert status_group(estatus_id) == expected


@pytest.mark.parametrize(
    'estatus_id',
    [0, 1, 50, 99, 400, 500, 999],
)
def test_status_group_out_of_range_returns_otro(estatus_id):
    """status_group returns 'otro' for IDs outside 100-399."""
    assert status_group(estatus_id) == 'otro'


def test_status_group_none_returns_otro():
    """status_group handles None gracefully."""
    assert status_group(None) == 'otro'


# =============================================================================
# P2: status_badge_class template filter (regression check)
# =============================================================================


@pytest.mark.parametrize(
    'estatus_id, expected_prefix',
    [
        (101, 'inicio'),
        (102, 'inicio'),
        (201, 'proceso'),
        (203, 'proceso'),
        (301, 'finalizado'),
        (303, 'finalizado'),
    ],
)
def test_status_badge_class_includes_group_and_id(estatus_id, expected_prefix):
    """status_badge_class returns '{group}-{estatus_id}' format."""
    result = status_badge_class(estatus_id)
    assert result == f'{expected_prefix}-{estatus_id}'


def test_status_badge_class_none_returns_otro():
    """status_badge_class handles None gracefully."""
    assert status_badge_class(None) == 'otro'


# =============================================================================
# P3: status_group in template context
# =============================================================================


def test_status_group_filter_in_template():
    """status_group can be used in Django templates via {% load admin_extras %}."""
    template = Template(
        '{% load admin_extras %}{{ estatus_id|status_group }}',
        engine=Engine.get_default(),
    )
    rendered = template.render(Context({'estatus_id': 203}))
    assert rendered.strip() == 'proceso'


def test_status_badge_class_filter_in_template():
    """status_badge_class can be used in Django templates."""
    template = Template(
        '{% load admin_extras %}{{ estatus_id|status_badge_class }}',
        engine=Engine.get_default(),
    )
    rendered = template.render(Context({'estatus_id': 203}))
    assert rendered.strip() == 'proceso-203'


# =============================================================================
# P3: Admin change_view timeline context logic (unit tests)
# =============================================================================

from tramites.timeline import build_timeline_entries


def test_timeline_building_requerimiento_gets_act_files():
    """ACT files are attached only to REQUERIMIENTO/SUBSANADO entries."""
    act_req = _make_actividad_mock(
        estatus_id=TramiteEstatus.Estatus.REQUERIMIENTO, actividad_id=145,
    )
    act_review = _make_actividad_mock(
        estatus_id=TramiteEstatus.Estatus.EN_REVISION, actividad_id=144,
    )
    historial = [act_req, act_review]

    act_file = ActividadFile(
        actividad_id=145,
        file_name='ACT-145-2026-04-30T02-54-49.pdf',
        size_mb=0.11,
        timestamp_str='2026-04-30T02-54-49',
    )

    entries = build_timeline_entries(historial, [act_file], [], {})

    # REQUERIMIENTO entry has ACT files
    req_entry = next(e for e in entries if e.actividad.estatus_id == 203)
    assert len(req_entry.actividad_files) == 1

    # EN_REVISION entry has no files
    rev_entry = next(e for e in entries if e.actividad.estatus_id == 202)
    assert len(rev_entry.actividad_files) == 0


def test_timeline_building_subsanado_gets_act_files():
    """SUBSANADO entries also receive ACT files."""
    act_sub = _make_actividad_mock(
        estatus_id=TramiteEstatus.Estatus.SUBSANADO, actividad_id=150,
    )
    historial = [act_sub]

    act_file = ActividadFile(
        actividad_id=150,
        file_name='ACT-150-2026-04-30T03-00-00.pdf',
        size_mb=0.08,
        timestamp_str='2026-04-30T03-00-00',
    )

    entries = build_timeline_entries(historial, [act_file], [], {})

    assert len(entries) == 1
    assert len(entries[0].actividad_files) == 1


def test_timeline_building_requisitos_only_on_first_pendiente_pago():
    """Requisito files are attached ONLY to the first PENDIENTE_PAGO activity."""
    act_pago = _make_actividad_mock(
        estatus_id=TramiteEstatus.Estatus.PENDIENTE_PAGO, actividad_id=100,
    )
    act_review = _make_actividad_mock(
        estatus_id=TramiteEstatus.Estatus.EN_REVISION, actividad_id=101,
    )
    # historial is -timestamp order, so reversed() gives chronological
    historial = [act_review, act_pago]

    rf = RequisitoFile(
        requisito_id=19,
        requisito_nombre='Identificación oficial',
        file_name='DAU-260420-AAAE-B-19.pdf',
        size_mb=0.05,
    )

    entries = build_timeline_entries(historial, [], [rf], {})

    # Only the PENDIENTE_PAGO entry gets requisito files
    pago_entry = next(e for e in entries if e.actividad.id == 100)
    assert len(pago_entry.requisito_files) == 1

    # EN_REVISION has no requisito files
    review_entry = next(e for e in entries if e.actividad.id == 101)
    assert len(review_entry.requisito_files) == 0


def test_timeline_building_no_pendiente_pago_no_requisitos():
    """When no PENDIENTE_PAGO exists, no entry gets requisito files."""
    act_review = _make_actividad_mock(
        estatus_id=TramiteEstatus.Estatus.EN_REVISION, actividad_id=101,
    )
    historial = [act_review]

    rf = RequisitoFile(
        requisito_id=19,
        requisito_nombre='Identificación oficial',
        file_name='DAU-260420-AAAE-B-19.pdf',
        size_mb=0.05,
    )

    entries = build_timeline_entries(historial, [], [rf], {})

    assert len(entries) == 0
    assert all(len(e.requisito_files) == 0 for e in entries)


def test_timeline_building_user_resolution():
    """Users are resolved from backoffice_user_id."""
    act_with_user = _make_actividad_mock(user_id=42)
    act_without_user = _make_actividad_mock(actividad_id=200, user_id=None)
    historial = [act_with_user, act_without_user]

    entries = build_timeline_entries(historial, [], [], {})

    user_entry = next(e for e in entries if e.actividad.backoffice_user_id == 42)
    assert user_entry.user is not None

    no_user_entry = next(e for e in entries if e.actividad.backoffice_user_id is None)
    assert no_user_entry.user is None


def test_timeline_building_preserves_historial_order():
    """Timeline entries preserve historial ordering (-timestamp)."""
    acts = [
        _make_actividad_mock(actividad_id=3, estatus_id=203),
        _make_actividad_mock(actividad_id=2, estatus_id=202),
        _make_actividad_mock(actividad_id=1, estatus_id=102),
    ]
    entries = build_timeline_entries(acts, [], [], {})
    ids = [e.actividad.id for e in entries]
    assert ids == [3, 2, 1]


def test_timeline_building_empty_historial():
    """Empty historial produces empty timeline entries."""
    entries = build_timeline_entries([], [], [], {})
    assert entries == []
    assert len(entries) == 0


def test_timeline_building_multiple_act_files_per_actividad():
    """Multiple ACT files for same actividad_id are all attached."""
    act = _make_actividad_mock(
        estatus_id=TramiteEstatus.Estatus.REQUERIMIENTO, actividad_id=145,
    )
    historial = [act]

    act_files = [
        ActividadFile(
            actividad_id=145,
            file_name='ACT-145-2026-04-30T02-54-47.pdf',
            size_mb=0.05,
            timestamp_str='2026-04-30T02-54-47',
        ),
        ActividadFile(
            actividad_id=145,
            file_name='ACT-145-2026-04-30T02-54-48.pdf',
            size_mb=0.08,
            timestamp_str='2026-04-30T02-54-48',
        ),
        ActividadFile(
            actividad_id=145,
            file_name='ACT-145-2026-04-30T02-54-49.pdf',
            size_mb=0.11,
            timestamp_str='2026-04-30T02-54-49',
        ),
    ]

    entries = build_timeline_entries(historial, act_files, [], {})
    assert len(entries[0].actividad_files) == 3
