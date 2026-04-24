"""
Tests for the SFTP service module.

P0 tests cover critical functionality:
- Input validation (folio, filename) with path traversal defense
- Authorization logic per role (superuser, admin, coordinador, analista)
- Response building (dev FileResponse vs prod X-Accel-Redirect)
- Full serve pipeline (cache hit, cache miss, validation errors)
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import paramiko
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponse
from django.test import override_settings
from django.urls import reverse

from core.rbac.constants import BackOfficeRole
from tramites.constants import (
    FILE_COUNT_WARNING_THRESHOLD,
    MAX_DOWNLOAD_FILE_SIZE_BYTES,
)
from tramites.exceptions import SFTPConnectionError
from tramites.sftp import (
    SFTPService,
    _try_load_key,
    validate_filename,
    validate_folio,
)
from tramites.views import _check_download_permission, download_requisito_pdf

# =============================================================================
# Helpers
# =============================================================================


def _make_tramite(folio='DAU-260420-AAAE-B', **kwargs):
    """Create a mock Tramite with minimal required attributes."""
    tramite = MagicMock()
    tramite.folio = folio
    tramite.pk = kwargs.get('pk', 1)
    for key, value in kwargs.items():
        setattr(tramite, key, value)
    return tramite


def _make_user(**kwargs):
    """Create a mock user with roles attribute."""
    user = MagicMock()
    user.is_superuser = kwargs.get('is_superuser', False)
    user.id = kwargs.get('id', 1)
    user.username = kwargs.get('username', 'testuser')
    user.roles = kwargs.get('roles', frozenset())
    return user


def _make_analista(**kwargs):
    """Create a mock analista user."""
    defaults = {
        'id': 42,
        'roles': frozenset({BackOfficeRole.ANALISTA}),
    }
    defaults.update(kwargs)
    return _make_user(**defaults)


def _make_analista_tramite(*, assigned_to=None, estatus_id: int | None = 201):
    """Create a mock tramite for authorization tests."""
    tramite = _make_tramite()
    tramite.asignado_user_id = assigned_to
    tramite.ultima_actividad_estatus_id = estatus_id
    return tramite


# =============================================================================
# P0-1: validate_folio()
# =============================================================================


@pytest.mark.parametrize(
    'folio',
    [
        'DAU-260420-AAAE-B',
        'XYZ-999999-ZZZZ-A',
        'AB-000001-ABCD-Z',
    ],
)
def test_validate_folio_returns_valid_folio_unchanged(folio):
    assert validate_folio(folio) == folio


@pytest.mark.parametrize(
    'folio',
    [
        'DAU-260420-AAAE/../etc/passwd',  # ../
        'DAU-260420-AAAE..',  # trailing ..
        '.DAU-260420-AAAE-B',  # leading dot
        'DAU-260420\\AAAE-B',  # backslash
        'DAU-260420\x00AAAE-B',  # null byte
        'DAU/260420/AAAE/B',  # forward slash
    ],
)
def test_validate_folio_rejects_path_traversal_characters(folio):
    with pytest.raises(SFTPConnectionError, match='caracteres no permitidos'):
        validate_folio(folio)


@pytest.mark.parametrize(
    'folio',
    [
        '',
        'invalid',
        '12345',
        '   ',
        'dau-260420-AAAE-B',  # lowercase
        'DAU-2604200-AAAE-B',  # 7 digits
        'DAU-26042-AAAE-B',  # 5 digits
        'DAU-260420-AAA-B',  # 3 letters
        'DAU-260420-AAABA-B',  # 5 letters
        'DAU-260420-AAAE-BC',  # 2 letter suffix
    ],
)
def test_validate_folio_rejects_invalid_format(folio):
    with pytest.raises(SFTPConnectionError):
        validate_folio(folio)


def test_validate_folio_empty_raises_specific_message():
    with pytest.raises(SFTPConnectionError, match='no puede estar vacío'):
        validate_folio('')


# =============================================================================
# P0-2: validate_filename()
# =============================================================================


@pytest.mark.parametrize(
    'filename',
    [
        'DAU-260420-AAAE-B-19.pdf',
        'XYZ-999999-ZZZZ-A-1.pdf',
        'AB-000001-ABCD-Z-999.pdf',
    ],
)
def test_validate_filename_returns_valid_filename_unchanged(filename):
    assert validate_filename(filename) == filename


@pytest.mark.parametrize(
    'filename',
    [
        '../etc/passwd.pdf',
        '..\\..\\windows\\system32\\config.pdf',
        'file\x00malicious.pdf',  # null byte
        'DAU-260420-AAAE-B/19.pdf',  # forward slash in middle
        '/etc/passwd',  # leading slash
    ],
)
def test_validate_filename_rejects_path_traversal_characters(filename):
    with pytest.raises(SFTPConnectionError, match='caracteres no permitidos'):
        validate_filename(filename)


@pytest.mark.parametrize(
    'filename',
    [
        '',
        'document.pdf',
        'DAU-260420-AAAE-B.txt',  # wrong extension
        'DAU-260420-AAAE-B.pdf',  # missing requisito_id
        'DAU-260420-AAAE-B-abc.pdf',  # non-numeric requisito_id
    ],
)
def test_validate_filename_rejects_invalid_format(filename):
    with pytest.raises(SFTPConnectionError):
        validate_filename(filename)


def test_validate_filename_empty_raises_specific_message():
    with pytest.raises(SFTPConnectionError, match='no puede estar vacío'):
        validate_filename('')


def test_validate_filename_dot_allowed_for_pdf_extension():
    """Dot must be allowed for .pdf extension (unlike folio)."""
    assert validate_filename('DAU-260420-AAAE-B-1.pdf') == 'DAU-260420-AAAE-B-1.pdf'


# =============================================================================
# P0-3: SFTPService.serve_requisito_pdf()
# =============================================================================


def test_serve_requisito_pdf_rejects_invalid_folio():
    tramite = _make_tramite(folio='../../../etc')
    with pytest.raises(SFTPConnectionError, match='caracteres no permitidos'):
        SFTPService.serve_requisito_pdf(tramite, 'DAU-260420-AAAE-B-19.pdf')


def test_serve_requisito_pdf_rejects_invalid_filename():
    tramite = _make_tramite()
    with pytest.raises(SFTPConnectionError):
        SFTPService.serve_requisito_pdf(tramite, '../../etc/passwd.pdf')


@patch.object(SFTPService, '_download_with_cache')
@patch.object(SFTPService, 'close_connection')
def test_serve_requisito_pdf_cache_hit_returns_response(mock_close, mock_download):
    """Cache hit: _download_with_cache returns path, response is built."""
    mock_download.return_value = Path('/tmp/.sftp_cache/DAU-260420-AAAE-B/DAU-260420-AAAE-B-19.pdf')

    with patch.object(SFTPService, 'build_file_response') as mock_build:
        mock_build.return_value = HttpResponse()
        SFTPService.serve_requisito_pdf(
            _make_tramite(),
            'DAU-260420-AAAE-B-19.pdf',
        )

    mock_download.assert_called_once()
    mock_build.assert_called_once()
    mock_close.assert_called_once()


@patch.object(SFTPService, '_download_with_cache')
@patch.object(SFTPService, 'close_connection')
def test_serve_requisito_pdf_closes_connection_on_sftp_error(mock_close, mock_download):
    """Connection is closed even when SFTPConnectionError is raised."""
    mock_download.side_effect = SFTPConnectionError('download failed')

    with pytest.raises(SFTPConnectionError, match='download failed'):
        SFTPService.serve_requisito_pdf(
            _make_tramite(),
            'DAU-260420-AAAE-B-19.pdf',
        )

    mock_close.assert_called_once()


@patch.object(SFTPService, '_download_with_cache')
@patch.object(SFTPService, 'close_connection')
def test_serve_requisito_pdf_wraps_unexpected_error(mock_close, mock_download):
    """Unexpected exceptions are wrapped in SFTPConnectionError."""
    mock_download.side_effect = RuntimeError('boom')

    with pytest.raises(SFTPConnectionError):
        SFTPService.serve_requisito_pdf(
            _make_tramite(),
            'DAU-260420-AAAE-B-19.pdf',
        )

    mock_close.assert_called_once()


@patch.object(SFTPService, '_download_with_cache')
@patch.object(SFTPService, 'close_connection')
def test_serve_requisito_pdf_valid_input_passes_traversal_assertion(mock_close, mock_download):
    """Defense-in-depth: valid folio+filename passes the '..' assertion."""
    mock_download.return_value = Path('/safe/DAU-260420-AAAE-B/DAU-260420-AAAE-B-19.pdf')

    with patch.object(SFTPService, 'build_file_response') as mock_build:
        mock_build.return_value = HttpResponse()
        SFTPService.serve_requisito_pdf(
            _make_tramite(),
            'DAU-260420-AAAE-B-19.pdf',
        )


# =============================================================================
# P0-4: _check_download_permission() — authorization per role
# =============================================================================


def test_download_permission_superuser_has_access():
    _check_download_permission(
        _make_user(is_superuser=True, roles=frozenset()),
        _make_tramite(),
    )


def test_download_permission_administrador_has_access():
    _check_download_permission(
        _make_user(roles=frozenset({BackOfficeRole.ADMINISTRADOR})),
        _make_tramite(),
    )


def test_download_permission_coordinador_has_access():
    _check_download_permission(
        _make_user(roles=frozenset({BackOfficeRole.COORDINADOR})),
        _make_tramite(),
    )


def test_download_permission_analista_assigned_any_estatus():
    """Analista can download assigned trámites regardless of estatus."""
    _check_download_permission(
        _make_analista(id=42),
        _make_analista_tramite(assigned_to=42, estatus_id=301),
    )


def test_download_permission_analista_unassigned_valid_estatus():
    """Analista can download unassigned trámites with estatus 200-299."""
    _check_download_permission(
        _make_analista(id=42),
        _make_analista_tramite(assigned_to=None, estatus_id=201),
    )


def test_download_permission_analista_unassigned_estatus_200():
    """Estatus 200 is the lower bound of the allowed range."""
    _check_download_permission(
        _make_analista(id=42),
        _make_analista_tramite(assigned_to=None, estatus_id=200),
    )


def test_download_permission_analista_unassigned_estatus_299():
    """Estatus 299 is the upper bound of the allowed range."""
    _check_download_permission(
        _make_analista(id=42),
        _make_analista_tramite(assigned_to=None, estatus_id=299),
    )


def test_download_permission_analista_estatus_none_rejected():
    """None estatus must not crash with TypeError (fixed bug)."""
    with pytest.raises(PermissionDenied):
        _check_download_permission(
            _make_analista(id=42),
            _make_analista_tramite(assigned_to=None, estatus_id=None),
        )


def test_download_permission_analista_estatus_out_of_range_rejected():
    with pytest.raises(PermissionDenied):
        _check_download_permission(
            _make_analista(id=42),
            _make_analista_tramite(assigned_to=None, estatus_id=301),
        )


def test_download_permission_analista_assigned_to_other_rejected():
    with pytest.raises(PermissionDenied):
        _check_download_permission(
            _make_analista(id=42),
            _make_analista_tramite(assigned_to=99, estatus_id=202),
        )


def test_download_permission_no_roles_rejected():
    with pytest.raises(PermissionDenied):
        _check_download_permission(
            _make_user(roles=frozenset()),
            _make_analista_tramite(assigned_to=None, estatus_id=201),
        )


# =============================================================================
# P0-5: build_file_response() — DEBUG vs PROD
# =============================================================================


@override_settings(DEBUG=True)
def test_build_file_response_dev_mode_returns_file_response(tmp_path):
    pdf_file = tmp_path / 'test.pdf'
    pdf_file.write_bytes(b'%PDF-1.4 fake content')

    response = SFTPService.build_file_response(
        final_path=pdf_file,
        cache_path_for_nginx='folio/file.pdf',
        filename='file.pdf',
    )

    assert isinstance(response, FileResponse)
    assert response['Content-Disposition'] == 'attachment; filename="file.pdf"'
    assert response['X-Content-Type-Options'] == 'nosniff'
    assert response['X-Frame-Options'] == 'DENY'
    assert 'X-Accel-Redirect' not in response


@override_settings(DEBUG=False)
def test_build_file_response_prod_mode_returns_x_accel_redirect(tmp_path):
    pdf_file = tmp_path / 'test.pdf'
    pdf_file.write_bytes(b'%PDF-1.4 fake content')

    response = SFTPService.build_file_response(
        final_path=pdf_file,
        cache_path_for_nginx='DAU-260420-AAAE-B/DAU-260420-AAAE-B-19.pdf',
        filename='DAU-260420-AAAE-B-19.pdf',
    )

    assert isinstance(response, HttpResponse)
    assert response['X-Accel-Redirect'] == (
        '/sftp-cache/DAU-260420-AAAE-B/DAU-260420-AAAE-B-19.pdf'
    )
    assert response['Content-Disposition'] == ('attachment; filename="DAU-260420-AAAE-B-19.pdf"')
    assert response['X-Content-Type-Options'] == 'nosniff'
    assert response['X-Frame-Options'] == 'DENY'


@override_settings(DEBUG=True)
def test_build_file_response_dev_mode_content_type_is_pdf(tmp_path):
    pdf_file = tmp_path / 'test.pdf'
    pdf_file.write_bytes(b'%PDF-1.4 fake content')

    response = SFTPService.build_file_response(
        final_path=pdf_file,
        cache_path_for_nginx='folio/file.pdf',
        filename='file.pdf',
    )

    assert response['Content-Type'] == 'application/pdf'


# =============================================================================
# P0 bonus: _is_cache_hit() — cache integrity checks
# =============================================================================


def test_is_cache_hit_valid_file(tmp_path):
    pdf = tmp_path / 'test.pdf'
    pdf.write_bytes(b'%PDF-1.4 content')

    assert SFTPService._is_cache_hit(pdf) is True


def test_is_cache_hit_nonexistent_file(tmp_path):
    assert SFTPService._is_cache_hit(tmp_path / 'missing.pdf') is False


def test_is_cache_hit_empty_file(tmp_path):
    empty = tmp_path / 'empty.pdf'
    empty.write_bytes(b'')

    assert SFTPService._is_cache_hit(empty) is False


def test_is_cache_hit_symlink_returns_false(tmp_path):
    """O_NOFOLLOW prevents symlink attacks."""
    real_file = tmp_path / 'real.pdf'
    real_file.write_bytes(b'%PDF-1.4 content')

    symlink = tmp_path / 'link.pdf'
    symlink.symlink_to(real_file)

    assert SFTPService._is_cache_hit(symlink) is False


def test_is_cache_hit_directory_returns_false(tmp_path):
    subdir = tmp_path / 'subdir'
    subdir.mkdir()

    assert SFTPService._is_cache_hit(subdir) is False


# =============================================================================
# P0 bonus: _is_within_cache() — path containment check
# =============================================================================


def test_is_within_cache_path_inside(tmp_path):
    cache_dir = tmp_path / 'cache'
    file_path = cache_dir / 'DAU-260420-AAAE-B' / 'file.pdf'

    assert SFTPService._is_within_cache(file_path, cache_dir) is True


def test_is_within_cache_path_outside(tmp_path):
    cache_dir = tmp_path / 'cache'
    outside = tmp_path / 'etc' / 'passwd'

    assert SFTPService._is_within_cache(outside, cache_dir) is False


def test_is_within_cache_traversal_attempt_rejected(tmp_path):
    cache_dir = tmp_path / 'cache'
    traversal = cache_dir / '..' / '..' / 'etc' / 'passwd'

    assert SFTPService._is_within_cache(traversal, cache_dir) is False


# =============================================================================
# P0 bonus: _check_file_count_warning()
# =============================================================================


def test_check_file_count_warning_below_threshold():
    assert SFTPService._check_file_count_warning(10, 'DAU-260420-AAAE-B') is None


def test_check_file_count_warning_at_threshold():
    assert (
        SFTPService._check_file_count_warning(
            FILE_COUNT_WARNING_THRESHOLD,
            'DAU-260420-AAAE-B',
        )
        is None
    )


def test_check_file_count_warning_above_threshold():
    result = SFTPService._check_file_count_warning(
        FILE_COUNT_WARNING_THRESHOLD + 1,
        'DAU-260420-AAAE-B',
    )
    assert result is not None
    assert '101' in result
    assert 'DAU-260420-AAAE-B' in result


# =============================================================================
# P0-6: close_connection() — connection lifecycle
# =============================================================================


def test_close_connection_closes_client_and_resets_attribute():
    """close_connection() calls _safe_close and sets _sftp_client to None."""
    service = SFTPService()
    mock_client = MagicMock()
    service._sftp_client = mock_client

    service.close_connection()

    mock_client.close.assert_called_once()
    assert service._sftp_client is None


def test_close_connection_no_op_without_client():
    """close_connection() is safe when no connection was opened."""
    service = SFTPService()
    # _sftp_client was never set — should not raise
    service.close_connection()


def test_close_connection_swallows_socket_error():
    """Socket errors during close must not propagate (avoids masking original exception)."""
    service = SFTPService()
    mock_client = MagicMock()
    mock_client.close.side_effect = paramiko.SSHException('connection dead')
    service._sftp_client = mock_client

    # Must not raise
    service.close_connection()
    assert service._sftp_client is None


def test_close_connection_swallows_os_error():
    """OSError during close must not propagate."""
    service = SFTPService()
    mock_client = MagicMock()
    mock_client.close.side_effect = OSError('broken pipe')
    service._sftp_client = mock_client

    service.close_connection()
    assert service._sftp_client is None


def test_close_connection_swallows_eof_error():
    """EOFError during close must not propagate."""
    service = SFTPService()
    mock_client = MagicMock()
    mock_client.close.side_effect = EOFError('unexpected eof')
    service._sftp_client = mock_client

    service.close_connection()
    assert service._sftp_client is None


def test_close_connection_does_not_suppress_critical_errors():
    """MemoryError, KeyboardInterrupt, SystemExit must propagate."""
    service = SFTPService()
    mock_client = MagicMock()
    mock_client.close.side_effect = MemoryError('oom')
    service._sftp_client = mock_client

    with pytest.raises(MemoryError):
        service.close_connection()


# =============================================================================
# P0-7: download_requisito_pdf (view) — integration tests
# =============================================================================


VALID_FILENAME = 'DAU-260420-AAAE-B-19.pdf'


@pytest.fixture
def download_url():
    """Resolve the download URL using reverse() to avoid hardcoded paths.

    Uses a sentinel pk=1; tests that need different PKs can call
    reverse() directly with the desired kwargs.
    """
    return reverse('tramites:download-requisito-pdf', kwargs={'pk': 1, 'filename': VALID_FILENAME})


def test_download_view_redirects_anonymous_user(client, db, download_url):
    """Anonymous users are redirected to login (staff_member_required)."""
    response = client.get(download_url)
    assert response.status_code == 302
    assert '/login/' in response['Location']


def test_download_view_rejects_non_staff_user(client, db, download_url):
    """Non-staff authenticated users are also redirected to login."""
    User = get_user_model()
    user = User.objects.create_user(username='regular', password='pass')
    client.force_login(user)

    response = client.get(download_url)
    assert response.status_code == 302
    assert '/login/' in response['Location']


@patch('tramites.views.SFTPService.serve_requisito_pdf')
@patch('tramites.views._log_download')
def test_download_view_rejects_invalid_filename(mock_log, mock_serve, admin_client, db):
    """Invalid filename is rejected before any DB or SFTP access.

    The view calls validate_filename() which raises SFTPConnectionError for
    filenames that don't match the expected pattern. Since SFTPConnectionError
    is not caught into a response, the test client re-raises it — so we use
    a direct view call instead.
    """
    request = MagicMock()
    request.user = MagicMock(is_superuser=True)

    with pytest.raises(SFTPConnectionError):
        download_requisito_pdf(request, pk=1, filename='malicious.pdf')

    # serve_requisito_pdf should never be called — filename is validated first
    mock_serve.assert_not_called()


@patch('tramites.views.SFTPService.serve_requisito_pdf')
@patch('tramites.views._log_download')
def test_download_view_returns_404_for_missing_tramite(mock_log, mock_serve, admin_client, db):
    """Non-existent tramite PK returns 404.

    Tramite is a managed=False model backed by a DB view, so we must
    mock get_object_or_404 to avoid the missing table error.
    """
    with patch('tramites.views.get_object_or_404', side_effect=Http404):
        url = reverse(
            'tramites:download-requisito-pdf', kwargs={'pk': 99999, 'filename': VALID_FILENAME}
        )
        response = admin_client.get(url)

    mock_serve.assert_not_called()
    assert response.status_code == 404


@patch('tramites.views._check_download_permission', side_effect=PermissionDenied)
@patch('tramites.views._log_download')
def test_download_view_rejects_unauthorized_user(
    mock_log, mock_perm, superuser, client, db, download_url
):
    """PermissionDenied from _check_download_permission returns 403."""
    client.force_login(superuser)

    # Need a real Tramite in DB for get_object_or_404 — mock it
    with patch('tramites.views.get_object_or_404') as mock_get:
        mock_tramite = MagicMock()
        mock_tramite.folio = 'DAU-260420-AAAE-B'
        mock_get.return_value = mock_tramite

        response = client.get(download_url)

    assert response.status_code == 403


@patch('tramites.views.SFTPService.serve_requisito_pdf')
@patch('tramites.views._log_download')
def test_download_view_success_logs_download(
    mock_log, mock_serve, superuser, client, db, download_url
):
    """Successful download logs with success=True."""
    mock_serve.return_value = HttpResponse(b'%PDF', content_type='application/pdf')
    client.force_login(superuser)

    with patch('tramites.views.get_object_or_404') as mock_get:
        mock_tramite = MagicMock()
        mock_tramite.folio = 'DAU-260420-AAAE-B'
        mock_get.return_value = mock_tramite

        response = client.get(download_url)

    assert response.status_code == 200
    mock_log.assert_called_once()
    # _log_download(request, tramite, filename, success=True)
    assert mock_log.call_args.kwargs['success'] is True


@patch('tramites.views.SFTPService.serve_requisito_pdf')
@patch('tramites.views._log_download')
def test_download_view_sftp_error_logs_failure(
    mock_log, mock_serve, superuser, client, db, download_url
):
    """SFTPConnectionError is logged with success=False and re-raised."""
    mock_serve.side_effect = SFTPConnectionError('connection failed')

    with (
        patch('tramites.views.get_object_or_404') as mock_get,
        pytest.raises(SFTPConnectionError, match='connection failed'),
    ):
        mock_tramite = MagicMock()
        mock_tramite.folio = 'DAU-260420-AAAE-B'
        mock_get.return_value = mock_tramite

        request = MagicMock()
        request.user = superuser
        download_requisito_pdf(request, pk=1, filename=VALID_FILENAME)

    mock_log.assert_called_once()
    assert mock_log.call_args.kwargs['success'] is False


@patch('tramites.views.SFTPService.serve_requisito_pdf')
@patch('tramites.views._log_download')
def test_download_view_passes_correct_args_to_service(
    mock_log, mock_serve, superuser, client, db, download_url
):
    """View passes tramite and filename to SFTPService.serve_requisito_pdf."""
    mock_serve.return_value = HttpResponse(b'%PDF', content_type='application/pdf')
    client.force_login(superuser)

    with patch('tramites.views.get_object_or_404') as mock_get:
        mock_tramite = MagicMock()
        mock_tramite.folio = 'DAU-260420-AAAE-B'
        mock_get.return_value = mock_tramite

        response = client.get(download_url)

    mock_serve.assert_called_once_with(tramite=mock_tramite, filename=VALID_FILENAME)


# =============================================================================
# P1-a: _try_load_key() — SSH key loading
# =============================================================================


def test_try_load_key_returns_none_for_nonexistent_file(tmp_path):
    """Non-existent key file returns None (no type matches)."""
    result = _try_load_key(str(tmp_path / 'nonexistent'))
    assert result is None


def test_try_load_key_returns_none_for_garbage_file(tmp_path):
    """File with invalid content returns None (all types fail to parse)."""
    bad_key = tmp_path / 'bad_key'
    bad_key.write_text('not a valid SSH key')
    result = _try_load_key(str(bad_key))
    assert result is None


@patch('paramiko.RSAKey.from_private_key_file')
def test_try_load_key_rsa_success(mock_rsa):
    """Successfully loading an RSA key returns (key, 'RSA')."""
    fake_key = MagicMock()
    mock_rsa.return_value = fake_key

    result = _try_load_key('/fake/path')

    assert result is not None
    assert result == (fake_key, 'RSA')


@patch('paramiko.Ed25519Key.from_private_key_file')
@patch('paramiko.RSAKey.from_private_key_file', side_effect=paramiko.SSHException('not RSA'))
def test_try_load_key_ed25519_fallback(mock_rsa, mock_ed25519):
    """Falls back to Ed25519 when RSA fails."""
    fake_key = MagicMock()
    mock_ed25519.return_value = fake_key

    result = _try_load_key('/fake/path')

    assert result is not None
    assert result == (fake_key, 'Ed25519')


@patch('paramiko.RSAKey.from_private_key_file')
def test_try_load_key_with_passphrase(mock_rsa):
    """Passphrase is passed through to from_private_key_file."""
    fake_key = MagicMock()
    mock_rsa.return_value = fake_key

    result = _try_load_key('/fake/path', passphrase='secret')

    mock_rsa.assert_called_once_with('/fake/path', password='secret')
    assert result is not None
    assert 'passphrase' in result[1]


@patch('paramiko.RSAKey.from_private_key_file', side_effect=paramiko.SSHException('bad'))
@patch('paramiko.Ed25519Key.from_private_key_file', side_effect=OSError('nope'))
@patch('paramiko.ECDSAKey.from_private_key_file', side_effect=paramiko.SSHException('nope'))
def test_try_load_key_all_types_fail_returns_none(mock_ecdsa, mock_ed25519, mock_rsa):
    """Returns None when every key type raises an exception."""
    result = _try_load_key('/fake/path')
    assert result is None


# =============================================================================
# P1-b: _load_known_host_key() — host key parsing
# =============================================================================


def _make_settings_dict(host='sftp.example.com', port=22):
    """Create a minimal settings override dict for host key tests."""
    return {'SFTP_HOST': host, 'SFTP_PORT': port}


@override_settings(**_make_settings_dict())
@patch('paramiko.RSAKey')
def test_load_known_host_key_rsa_success(mock_rsa_cls):
    """RSA host key is parsed and added to client with RejectPolicy."""
    mock_rsa_cls.return_value = MagicMock()

    client = paramiko.SSHClient()
    key_b64 = 'AAAA' + 'B' * 80  # valid base64 shape

    SFTPService._load_known_host_key(client, f'ssh-rsa {key_b64}')

    mock_rsa_cls.assert_called_once()
    assert isinstance(client._policy, paramiko.RejectPolicy)


@override_settings(**_make_settings_dict())
@patch('paramiko.Ed25519Key')
def test_load_known_host_key_ed25519_success(mock_ed_cls):
    """Ed25519 host key is parsed and added to client with RejectPolicy."""
    mock_ed_cls.return_value = MagicMock()

    client = paramiko.SSHClient()
    key_b64 = 'AAAA' + 'B' * 80

    SFTPService._load_known_host_key(client, f'ssh-ed25519 {key_b64}')

    mock_ed_cls.assert_called_once()
    assert isinstance(client._policy, paramiko.RejectPolicy)


@override_settings(**_make_settings_dict())
def test_load_known_host_key_invalid_format_no_space():
    """Host key without space separator raises SFTPConnectionError."""
    client = paramiko.SSHClient()

    with pytest.raises(SFTPConnectionError, match='formato inválido'):
        SFTPService._load_known_host_key(client, 'invalid-no-space')


@override_settings(**_make_settings_dict())
def test_load_known_host_key_invalid_base64():
    """Host key with invalid base64 data raises SFTPConnectionError."""
    client = paramiko.SSHClient()

    with pytest.raises(SFTPConnectionError, match='datos inválidos'):
        SFTPService._load_known_host_key(client, 'ssh-rsa not-valid-base64!!!')


@override_settings(**_make_settings_dict())
def test_load_known_host_key_unsupported_type():
    """Unsupported key type (ssh-dss) raises SFTPConnectionError."""
    client = paramiko.SSHClient()

    with pytest.raises(SFTPConnectionError, match='Tipo de host key no soportado'):
        SFTPService._load_known_host_key(client, 'ssh-dss AAAAB3NzaC1kZW1v')


@override_settings(SFTP_HOST='sftp.example.com', SFTP_PORT=2222)
@patch('paramiko.RSAKey')
def test_load_known_host_key_non_standard_port_uses_brackets(mock_rsa_cls):
    """Non-standard port uses [host]:port format in host keys dict."""
    mock_rsa_cls.return_value = MagicMock()

    client = paramiko.SSHClient()
    key_b64 = 'AAAA' + 'B' * 80

    SFTPService._load_known_host_key(client, f'ssh-rsa {key_b64}')

    # Verify the host key was added with bracket notation
    host_keys = client.get_host_keys()
    assert '[sftp.example.com]:2222' in host_keys


# =============================================================================
# P1-c: _configure_host_key_policy() — host key policy selection
# =============================================================================


@override_settings(SFTP_HOST_KEY='ssh-rsa AAAAB3NzaC1kZW1vZGF0YQ==', SFTP_HOST='h', SFTP_PORT=22)
@patch('paramiko.RSAKey')
def test_configure_host_key_policy_with_key_uses_reject_policy(mock_rsa_cls):
    """When SFTP_HOST_KEY is set, RejectPolicy is used."""
    mock_rsa_cls.return_value = MagicMock()
    service = SFTPService()
    client = paramiko.SSHClient()

    service._configure_host_key_policy(client)

    assert isinstance(client._policy, paramiko.RejectPolicy)


@override_settings(SFTP_HOST_KEY='', DEBUG=True)
def test_configure_host_key_policy_dev_without_key_uses_warning_policy():
    """In DEBUG mode without host key, WarningPolicy is used."""
    service = SFTPService()
    client = paramiko.SSHClient()

    service._configure_host_key_policy(client)

    assert isinstance(client._policy, paramiko.WarningPolicy)


@override_settings(SFTP_HOST_KEY='', DEBUG=False)
def test_configure_host_key_policy_prod_without_key_raises():
    """In production without host key, raises SFTPConnectionError."""
    service = SFTPService()
    client = paramiko.SSHClient()

    with pytest.raises(SFTPConnectionError, match='SFTP_HOST_KEY no está configurado'):
        service._configure_host_key_policy(client)


# =============================================================================
# P1-d: _create_sftp_connection() — connection establishment
# =============================================================================


def _sftp_settings(**overrides):
    """Build settings dict for connection tests. Defaults are minimal valid config."""
    defaults = {
        'SFTP_HOST': 'sftp.example.com',
        'SFTP_PORT': 22,
        'SFTP_USERNAME': 'testuser',
        'SFTP_PASSWORD': 'testpass',
        'SFTP_PRIVATE_KEY_PATH': '',
        'SFTP_PRIVATE_KEY_PASSPHRASE': '',
        'SFTP_TIMEOUT': 10,
        'SFTP_HOST_KEY': '',  # triggers WarningPolicy in DEBUG
        'DEBUG': True,
    }
    defaults.update(overrides)
    return defaults


@patch('paramiko.SSHClient.connect')
def test_create_sftp_connection_password_auth(mock_connect):
    """Password authentication connects with username/password."""
    service = SFTPService()

    with override_settings(**_sftp_settings()):
        client = service._create_sftp_connection()

    mock_connect.assert_called_once_with(
        hostname='sftp.example.com',
        port=22,
        username='testuser',
        password='testpass',
        timeout=10,
    )
    assert client is not None


@patch.object(SFTPService, '_configure_host_key_policy')
@patch('paramiko.SSHClient.connect')
def test_create_sftp_connection_key_auth(mock_connect, mock_policy):
    """Private key authentication connects with pkey."""
    service = SFTPService()
    fake_key = MagicMock(spec=paramiko.PKey)

    with (
        patch('tramites.sftp._try_load_key', return_value=(fake_key, 'RSA')),
        override_settings(
            **_sftp_settings(
                SFTP_PRIVATE_KEY_PATH='/home/user/.ssh/id_rsa',
                SFTP_PASSWORD='',
            )
        ),
        patch.object(Path, 'exists', return_value=True),
        patch.object(Path, 'is_absolute', return_value=True),
        patch.object(Path, 'resolve', return_value=Path('/home/user/.ssh/id_rsa')),
    ):
        client = service._create_sftp_connection()

    mock_connect.assert_called_once()
    call_kwargs = mock_connect.call_args.kwargs
    assert call_kwargs['pkey'] is fake_key
    assert 'password' not in call_kwargs or call_kwargs.get('password') is None


@override_settings(**_sftp_settings(SFTP_PASSWORD='', SFTP_PRIVATE_KEY_PATH=''))
def test_create_sftp_connection_no_auth_method():
    """No password and no key raises SFTPConnectionError."""
    service = SFTPService()

    with pytest.raises(SFTPConnectionError, match='No hay método de autenticación'):
        service._create_sftp_connection()


@patch.object(SFTPService, '_configure_host_key_policy')
@patch(
    'paramiko.SSHClient.connect',
    side_effect=paramiko.AuthenticationException('bad creds'),
)
def test_create_sftp_connection_auth_failure_password(mock_connect, mock_policy):
    """AuthenticationException is wrapped in SFTPConnectionError."""
    service = SFTPService()

    with override_settings(**_sftp_settings()):
        with pytest.raises(SFTPConnectionError, match='Autenticación fallida'):
            service._create_sftp_connection()


@patch.object(SFTPService, '_configure_host_key_policy')
@patch('paramiko.SSHClient.connect', side_effect=OSError('connection refused'))
def test_create_sftp_connection_os_error(mock_connect, mock_policy):
    """OSError (network) is wrapped in SFTPConnectionError."""
    service = SFTPService()

    with override_settings(**_sftp_settings()):
        with pytest.raises(SFTPConnectionError, match='No se pudo conectar'):
            service._create_sftp_connection()


@patch.object(SFTPService, '_configure_host_key_policy')
@patch('paramiko.SSHClient.connect', side_effect=paramiko.SSHException('ssh error'))
def test_create_sftp_connection_ssh_exception(mock_connect, mock_policy):
    """SSHException is wrapped in SFTPConnectionError."""
    service = SFTPService()

    with override_settings(**_sftp_settings()):
        with pytest.raises(SFTPConnectionError, match='Error al conectar'):
            service._create_sftp_connection()


# =============================================================================
# P1-e: fetch_requisito_files() — file listing
# =============================================================================


@patch.object(SFTPService, '_get_cached_requisitos', return_value={})
@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_requisito_files_returns_files(mock_get_client, mock_close, mock_reqs):
    """Returns list of RequisitoFile for matching PDFs."""
    # Simulate SFTP listdir_attr response
    mock_sftp = MagicMock()
    entry = MagicMock()
    entry.filename = 'DAU-260420-AAAE-B-19.pdf'
    entry.st_size = 2 * 1024 * 1024  # 2 MB
    mock_sftp.listdir_attr.return_value = [entry]

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    with override_settings(SFTP_BASE_DIR='/remote/pdfs'):
        files, warning = SFTPService.fetch_requisito_files('DAU-260420-AAAE-B')

    assert len(files) == 1
    assert files[0].file_name == 'DAU-260420-AAAE-B-19.pdf'
    assert files[0].requisito_id == 19
    assert files[0].requisito_nombre is None  # not in catalog
    assert warning is None
    mock_close.assert_called_once()


@patch.object(SFTPService, '_get_cached_requisitos', return_value={})
@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_requisito_files_empty_directory(mock_get_client, mock_close, mock_reqs):
    """FileNotFoundError on remote returns empty list."""
    mock_sftp = MagicMock()
    mock_sftp.listdir_attr.side_effect = FileNotFoundError('no dir')
    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    with override_settings(SFTP_BASE_DIR='/remote/pdfs'):
        files, warning = SFTPService.fetch_requisito_files('DAU-260420-AAAE-B')

    assert files == []
    assert warning is None


@patch.object(SFTPService, '_get_cached_requisitos', return_value={})
@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_requisito_files_filters_non_matching(mock_get_client, mock_close, mock_reqs):
    """Files not matching FILENAME_REGEX are excluded."""
    mock_sftp = MagicMock()
    entry_ok = MagicMock()
    entry_ok.filename = 'DAU-260420-AAAE-B-19.pdf'
    entry_ok.st_size = 1024
    entry_bad = MagicMock()
    entry_bad.filename = 'random-notes.txt'
    entry_bad.st_size = 512
    mock_sftp.listdir_attr.return_value = [entry_ok, entry_bad]

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    with override_settings(SFTP_BASE_DIR='/remote/pdfs'):
        files, warning = SFTPService.fetch_requisito_files('DAU-260420-AAAE-B')

    assert len(files) == 1
    assert files[0].file_name == 'DAU-260420-AAAE-B-19.pdf'


@patch.object(SFTPService, '_get_cached_requisitos')
@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_requisito_files_enriches_with_catalog(mock_get_client, mock_close, mock_reqs):
    """Files are enriched with requisito name from cached catalog."""
    # Catalog has requisito_id=19 named "Acta de nacimiento"
    mock_req = MagicMock()
    mock_req.requisito = 'Acta de nacimiento'
    mock_reqs.return_value = {19: mock_req}

    mock_sftp = MagicMock()
    entry = MagicMock()
    entry.filename = 'DAU-260420-AAAE-B-19.pdf'
    entry.st_size = 3 * 1024 * 1024
    mock_sftp.listdir_attr.return_value = [entry]

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    with override_settings(SFTP_BASE_DIR='/remote/pdfs'):
        files, warning = SFTPService.fetch_requisito_files('DAU-260420-AAAE-B')

    assert len(files) == 1
    assert files[0].requisito_nombre == 'Acta de nacimiento'


@patch.object(SFTPService, '_get_cached_requisitos', return_value={})
@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_requisito_files_invalid_folio_raises(mock_get_client, mock_close, mock_reqs):
    """Invalid folio raises SFTPConnectionError before any SFTP access."""
    with pytest.raises(SFTPConnectionError, match='caracteres no permitidos'):
        SFTPService.fetch_requisito_files('../../../etc')

    mock_get_client.assert_not_called()


@patch.object(SFTPService, '_get_cached_requisitos', return_value={})
@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_fetch_requisito_files_sftp_error_raises(mock_get_client, mock_close, mock_reqs):
    """SFTP errors are wrapped and connection is still closed."""
    mock_client = MagicMock()
    mock_sftp = MagicMock()
    mock_sftp.listdir_attr.side_effect = paramiko.SSHException('broken')
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    with override_settings(SFTP_BASE_DIR='/remote/pdfs'):
        with pytest.raises(SFTPConnectionError):
            SFTPService.fetch_requisito_files('DAU-260420-AAAE-B')

    mock_close.assert_called_once()


# =============================================================================
# P1-f: ping() — connectivity test
# =============================================================================


@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_ping_success(mock_get_client, mock_close):
    """Successful ping lists base directory without error."""
    mock_sftp = MagicMock()
    mock_sftp.listdir.return_value = ['DAU-260420-AAAE-B']

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    with override_settings(SFTP_BASE_DIR='/remote/pdfs'):
        SFTPService.ping()  # should not raise

    mock_close.assert_called_once()


@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_ping_dir_not_found(mock_get_client, mock_close):
    """Missing base directory raises SFTPConnectionError."""
    mock_sftp = MagicMock()
    mock_sftp.listdir.side_effect = FileNotFoundError('no dir')

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    with override_settings(SFTP_BASE_DIR='/remote/pdfs'):
        with pytest.raises(SFTPConnectionError, match='no existe'):
            SFTPService.ping()

    mock_close.assert_called_once()


@patch.object(SFTPService, 'close_connection')
@patch.object(SFTPService, 'get_sftp_client')
def test_ping_os_error(mock_get_client, mock_close):
    """Network error during ping raises SFTPConnectionError."""
    mock_sftp = MagicMock()
    mock_sftp.listdir.side_effect = OSError('connection lost')

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    with override_settings(SFTP_BASE_DIR='/remote/pdfs'):
        with pytest.raises(SFTPConnectionError, match='Error al conectar'):
            SFTPService.ping()

    mock_close.assert_called_once()


# =============================================================================
# P2-a: _download_file() — file download with size enforcement
# =============================================================================


@patch.object(SFTPService, 'get_sftp_client')
@override_settings(SFTP_BASE_DIR='/remote/pdfs')
def test_download_file_success(mock_get_client, tmp_path):
    """Successful download writes file to local_path."""
    mock_sftp = MagicMock()
    file_stat = MagicMock()
    file_stat.st_size = 1024
    mock_sftp.stat.return_value = file_stat
    mock_sftp.get.return_value = None

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    local_path = tmp_path / 'DAU-260420-AAAE-B-19.pdf'
    service = SFTPService()
    service._download_file('DAU-260420-AAAE-B', 'DAU-260420-AAAE-B-19.pdf', local_path)

    mock_sftp.get.assert_called_once_with(
        '/remote/pdfs/DAU-260420-AAAE-B/DAU-260420-AAAE-B-19.pdf',
        str(local_path),
    )
    mock_sftp.close.assert_called_once()


@patch.object(SFTPService, 'get_sftp_client')
@override_settings(SFTP_BASE_DIR='/remote/pdfs')
def test_download_file_rejects_oversized_file(mock_get_client, tmp_path):
    """Files exceeding MAX_DOWNLOAD_FILE_SIZE_BYTES are rejected before download."""
    mock_sftp = MagicMock()
    file_stat = MagicMock()
    file_stat.st_size = MAX_DOWNLOAD_FILE_SIZE_BYTES + 1  # 50 MB + 1 byte
    mock_sftp.stat.return_value = file_stat

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    local_path = tmp_path / 'DAU-260420-AAAE-B-19.pdf'
    service = SFTPService()

    with pytest.raises(SFTPConnectionError, match='demasiado grande'):
        service._download_file('DAU-260420-AAAE-B', 'DAU-260420-AAAE-B-19.pdf', local_path)

    # sftp.get should NOT be called — size check prevents download
    mock_sftp.get.assert_not_called()
    mock_sftp.close.assert_called_once()


@patch.object(SFTPService, 'get_sftp_client')
@override_settings(SFTP_BASE_DIR='/remote/pdfs')
def test_download_file_accepts_max_size(mock_get_client, tmp_path):
    """File exactly at MAX_DOWNLOAD_FILE_SIZE_BYTES is allowed."""
    mock_sftp = MagicMock()
    file_stat = MagicMock()
    file_stat.st_size = MAX_DOWNLOAD_FILE_SIZE_BYTES
    mock_sftp.stat.return_value = file_stat

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    local_path = tmp_path / 'DAU-260420-AAAE-B-19.pdf'
    service = SFTPService()
    service._download_file('DAU-260420-AAAE-B', 'DAU-260420-AAAE-B-19.pdf', local_path)

    mock_sftp.get.assert_called_once()


@patch.object(SFTPService, 'get_sftp_client')
@override_settings(SFTP_BASE_DIR='/remote/pdfs')
def test_download_file_file_not_found(mock_get_client, tmp_path):
    """FileNotFoundError on remote raises SFTPConnectionError."""
    mock_sftp = MagicMock()
    mock_sftp.stat.side_effect = FileNotFoundError('gone')

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    local_path = tmp_path / 'DAU-260420-AAAE-B-19.pdf'
    service = SFTPService()

    with pytest.raises(SFTPConnectionError, match='no existe'):
        service._download_file('DAU-260420-AAAE-B', 'DAU-260420-AAAE-B-19.pdf', local_path)

    mock_sftp.close.assert_called_once()


@patch.object(SFTPService, 'get_sftp_client')
@override_settings(SFTP_BASE_DIR='/remote/pdfs')
def test_download_file_os_error_wrapped(mock_get_client, tmp_path):
    """OSError during download is wrapped in SFTPConnectionError."""
    mock_sftp = MagicMock()
    file_stat = MagicMock()
    file_stat.st_size = 1024
    mock_sftp.stat.return_value = file_stat
    mock_sftp.get.side_effect = OSError('network error')

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    local_path = tmp_path / 'DAU-260420-AAAE-B-19.pdf'
    service = SFTPService()

    with pytest.raises(SFTPConnectionError, match='Error al descargar'):
        service._download_file('DAU-260420-AAAE-B', 'DAU-260420-AAAE-B-19.pdf', local_path)

    mock_sftp.close.assert_called_once()


@patch.object(SFTPService, 'get_sftp_client')
@override_settings(SFTP_BASE_DIR='/remote/pdfs')
def test_download_file_creates_parent_directory(mock_get_client, tmp_path):
    """Parent directory of local_path is created if it doesn't exist."""
    mock_sftp = MagicMock()
    file_stat = MagicMock()
    file_stat.st_size = 100
    mock_sftp.stat.return_value = file_stat

    mock_client = MagicMock()
    mock_client.open_sftp.return_value = mock_sftp
    mock_get_client.return_value = mock_client

    # Nested path that doesn't exist yet
    local_path = tmp_path / 'nested' / 'dir' / 'file.pdf'
    service = SFTPService()
    service._download_file('DAU-260420-AAAE-B', 'DAU-260420-AAAE-B-19.pdf', local_path)

    assert local_path.parent.exists()


# =============================================================================
# P2-b: _download_with_cache() — cache hit/miss with atomic rename
# =============================================================================


@patch.object(SFTPService, '_download_file')
@override_settings(SFTP_CACHE_DIR='/tmp/.sftp_cache_test')
def test_download_with_cache_hit_returns_existing(mock_download, tmp_path):
    """Cache hit: returns final_path without downloading."""
    cache_dir = tmp_path / 'cache'
    folio_dir = cache_dir / 'DAU-260420-AAAE-B'
    folio_dir.mkdir(parents=True)
    cached_file = folio_dir / 'DAU-260420-AAAE-B-19.pdf'
    cached_file.write_bytes(b'%PDF-1.4 cached content')

    service = SFTPService()
    tramite = _make_tramite()

    with (
        patch.object(SFTPService, '_is_cache_hit', return_value=True),
        patch.object(SFTPService, '_is_within_cache', return_value=True),
        override_settings(SFTP_CACHE_DIR=str(cache_dir)),
    ):
        result = service._download_with_cache(tramite, 'DAU-260420-AAAE-B-19.pdf')

    assert result == cached_file
    mock_download.assert_not_called()


@patch.object(SFTPService, '_download_file')
@override_settings(SFTP_CACHE_DIR='/tmp/.sftp_cache_test')
def test_download_with_cache_miss_downloads_and_renames(mock_download, tmp_path):
    """Cache miss: downloads to temp file, then atomically renames to final."""
    cache_dir = tmp_path / 'cache'
    folio_dir = cache_dir / 'DAU-260420-AAAE-B'

    # Simulate _download_file creating the temp file
    def fake_download(folio, filename, local_path):
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(b'%PDF-1.4 new content')

    mock_download.side_effect = fake_download

    service = SFTPService()
    tramite = _make_tramite()

    with (
        patch.object(SFTPService, '_is_cache_hit', return_value=False),
        override_settings(SFTP_CACHE_DIR=str(cache_dir)),
    ):
        result = service._download_with_cache(tramite, 'DAU-260420-AAAE-B-19.pdf')

    final_path = folio_dir / 'DAU-260420-AAAE-B-19.pdf'
    assert result == final_path
    assert final_path.exists()
    assert final_path.read_bytes() == b'%PDF-1.4 new content'

    # No temp files should remain
    remaining = list(folio_dir.iterdir())
    assert len(remaining) == 1
    assert remaining[0].name == 'DAU-260420-AAAE-B-19.pdf'


@patch.object(SFTPService, '_download_file', side_effect=SFTPConnectionError('fail'))
def test_download_with_cache_cleanup_on_failure(mock_download, tmp_path):
    """Temp file is cleaned up when download fails."""
    cache_dir = tmp_path / 'cache'
    folio_dir = cache_dir / 'DAU-260420-AAAE-B'

    service = SFTPService()
    tramite = _make_tramite()

    with (
        patch.object(SFTPService, '_is_cache_hit', return_value=False),
        override_settings(SFTP_CACHE_DIR=str(cache_dir)),
        pytest.raises(SFTPConnectionError, match='fail'),
    ):
        service._download_with_cache(tramite, 'DAU-260420-AAAE-B-19.pdf')

    # No temp files should remain after failure
    if folio_dir.exists():
        remaining = [f for f in folio_dir.iterdir() if f.name.endswith('.downloading')]
        assert len(remaining) == 0


@patch.object(SFTPService, '_download_file')
def test_download_with_cache_temp_filename_format(mock_download, tmp_path):
    """Temp file follows .{filename}.{pid}.{uuid}.downloading pattern."""
    cache_dir = tmp_path / 'cache'

    captured_temp_path = None

    def capture_download(folio, filename, local_path):
        nonlocal captured_temp_path
        captured_temp_path = local_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(b'%PDF content')

    mock_download.side_effect = capture_download

    service = SFTPService()
    tramite = _make_tramite()

    with (
        patch.object(SFTPService, '_is_cache_hit', return_value=False),
        override_settings(SFTP_CACHE_DIR=str(cache_dir)),
    ):
        service._download_with_cache(tramite, 'DAU-260420-AAAE-B-19.pdf')

    assert captured_temp_path is not None
    temp_name = captured_temp_path.name
    assert temp_name.startswith('.DAU-260420-AAAE-B-19.pdf.')
    assert temp_name.endswith('.downloading')
    # Contains PID
    assert str(os.getpid()) in temp_name
