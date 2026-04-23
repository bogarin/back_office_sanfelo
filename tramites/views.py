"""
Views for tramites app.

NOTE: This project uses Django Admin almost exclusively for backoffice UI.
Custom views are not needed as Django Admin provides:
- List views with filtering, search, and pagination
- Create/Edit forms with validation
- Delete confirmation
- Bulk actions for status changes and assignments
- Inline editing

If custom views are needed in the future (e.g., API endpoints, custom dashboards),
they can be added here.
"""

import logging
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.rbac.constants import BackOfficeRole
from tramites.exceptions import SFTPConnectionError
from tramites.models import Tramite
from tramites.services import SFTPService


logger = logging.getLogger(__name__)


# =============================================================================
# Helper Classes
# =============================================================================


class _AutoDeleteFileWrapper:
    """File wrapper that auto-deletes the file on close.

    Used in dev mode to clean up temp cache files after serving.
    Django's FileResponse holds the file object and calls .close() after
    the response is sent, so this wrapper ensures cleanup happens.

    Example:
        with open('/tmp/file.txt', 'rb') as raw_file:
            wrapper = _AutoDeleteFileWrapper(raw_file, '/tmp/file.txt')
            return FileResponse(wrapper)
    """

    def __init__(self, file_obj, file_path: Path) -> None:
        self._file = file_obj
        self._path = Path(file_path)

    def __iter__(self):
        return iter(self._file)

    def read(self, size=-1):
        return self._file.read(size)

    def close(self) -> None:
        # Close the underlying file
        self._file.close()
        # Delete the temp file (ignore errors if it's already gone)
        try:
            self._path.unlink()
        except OSError:
            pass


logger = logging.getLogger(__name__)

# =============================================================================
# Download Views
# =============================================================================


def download_requisito_pdf(
    request: HttpRequest,
    pk: int,
    filename: str,
) -> HttpResponse:
    """Download a PDF requisito file from SFTP server.

    This view implements a secure file download pattern:
    1. Validates the user has permission to download (object-level authorization)
    2. Validates the tramite exists and user can access it
    3. Downloads file from SFTP to local cache with unique temp filename
    4. Serves the file (dev: FileResponse with auto-cleanup, prod: X-Accel-Redirect)
    5. Logs the download for audit purposes

    Args:
        request: The HTTP request.
        pk: Primary key of the Tramite.
        filename: Name of the PDF file to download.

    Returns:
        HttpResponse with FileResponse (dev) or X-Accel-Redirect header (prod).

    Raises:
        PermissionError: If user lacks download permission.
        SFTPConnectionError: If SFTP download fails.
        Http404: If tramite does not exist.
    """
    # Get the tramite instance (raises Http404 if not found)
    tramite = get_object_or_404(Tramite, pk=pk)

    # Check object-level authorization
    _check_download_permission(request.user, tramite)

    # Initialize SFTP service
    sftp_service = SFTPService()

    # Generate unique temp filename to prevent race conditions
    pid = os.getpid()
    uuid_suffix = uuid.uuid4().hex[:8]
    temp_filename = f'.{filename}.{pid}.{uuid_suffix}.tmp'
    cache_dir = Path(settings.SFTP_CACHE_DIR)
    local_path = cache_dir / temp_filename

    try:
        # Download file from SFTP to local cache
        sftp_service.download_file(
            folio=tramite.folio,
            filename=filename,
            local_path=local_path,
        )

        # Log successful download for audit
        _log_download(request, tramite, filename, success=True)

        # Dev mode: serve file directly with FileResponse + auto-cleanup
        # Prod mode: delegate to nginx via X-Accel-Redirect
        if settings.DEBUG:
            # Open file and wrap with auto-delete wrapper
            raw_file = open(local_path, 'rb')
            wrapper = _AutoDeleteFileWrapper(raw_file, local_path)

            # Serve file directly (FileResponse will close wrapper after sending)
            response = FileResponse(wrapper, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
        else:
            # Production: delegate to nginx via X-Accel-Redirect
            # Nginx will handle serving and cache cleanup
            response = HttpResponse()
            response['X-Accel-Redirect'] = f'/sftp-cache/{temp_filename}'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'

        return response

    except SFTPConnectionError:
        _log_download(request, tramite, filename, success=False)
        raise
    except Exception as exc:
        logger.error(
            'Error inesperado al descargar archivo %s para tramite %s: %s',
            filename,
            tramite.folio,
            exc,
        )
        _log_download(request, tramite, filename, success=False)
        raise SFTPConnectionError(
            'Error al descargar el archivo. Por favor intenta nuevamente más tarde.'
        ) from exc


def _check_download_permission(user, tramite: Tramite) -> None:
    """Check if user has permission to download a file from the given tramite.

    Authorization mirrors admin queryset rules:
    - Superuser: Full access
    - Administrador group: Full access
    - Coordinador group: Full access
    - Analista group: Assigned tramites (any estatus) + unassigned tramites (estatus 200-299)

    Note: Status filter is NOT applied here (documented risk acceptance).
    The admin queryset filters by estatus 200-299, but downloads are allowed
    for assigned tramites regardless of estatus to support workflows where
    analysts need to review documents before marking as received.

    Args:
        user: Django User instance.
        tramite: Tramite instance.

    Raises:
        PermissionError: If user lacks download permission.
    """
    # Superusers always have access
    if user.is_superuser:
        return

    # Get user roles (from cached property or fallback to group queries)
    roles = getattr(user, 'roles', frozenset())

    # Administrador has full access
    if BackOfficeRole.ADMINISTRADOR in roles:
        return

    # Coordinador has full access
    if BackOfficeRole.COORDINADOR in roles:
        return

    # Analista: assigned tramites (any estatus) OR unassigned tramites (estatus 200-299)
    if BackOfficeRole.ANALISTA in roles:
        if tramite.asignado_user_id == user.id:
            # Assigned to this analyst - allow download (any estatus)
            return

        if tramite.asignado_user_id is None and 200 <= tramite.ultima_actividad_estatus_id < 300:
            # Unassigned with valid estatus - allow download
            return

    # If we get here, user doesn't have permission
    raise PermissionError(
        'No tienes permiso para descargar archivos de este trámite. '
        'Verifica que el trámite esté asignado a ti o que sea un trámite disponible.'
    )


def _log_download(
    request: HttpRequest,
    tramite: Tramite,
    filename: str,
    success: bool,
) -> None:
    """Log download event for audit purposes.

    Args:
        request: The HTTP request.
        tramite: Tramite instance.
        filename: Name of the downloaded file.
        success: Whether the download was successful.
    """
    user = request.user
    ip_address = _get_client_ip(request)

    log_data = {
        'user_id': user.id,
        'username': user.username,
        'tramite_pk': tramite.pk,
        'tramite_folio': tramite.folio,
        'filename': filename,
        'ip_address': ip_address,
        'success': success,
        'timestamp': timezone.now(),
    }

    if success:
        logger.info(
            'Descarga exitosa: user=%s tramite=%s file=%s ip=%s',
            log_data['username'],
            log_data['tramite_folio'],
            log_data['filename'],
            log_data['ip_address'],
        )
    else:
        logger.warning(
            'Descarga fallida: user=%s tramite=%s file=%s ip=%s',
            log_data['username'],
            log_data['tramite_folio'],
            log_data['filename'],
            log_data['ip_address'],
        )


def _get_client_ip(request: HttpRequest) -> str:
    """Extract client IP address from request.

    Handles proxy and load balancer scenarios by checking
    X-Forwarded-For header first.

    Args:
        request: The HTTP request.

    Returns:
        Client IP address as string.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return x_forwarded_for.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR', 'unknown')
