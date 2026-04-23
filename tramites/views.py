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

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from core.rbac.constants import BackOfficeRole
from tramites.exceptions import SFTPConnectionError
from tramites.models import Tramite
from tramites.sftp import SFTPService, validate_filename

logger = logging.getLogger(__name__)


# =============================================================================
# Download Views
# =============================================================================


@staff_member_required
def download_requisito_pdf(
    request: HttpRequest,
    pk: int,
    filename: str,
) -> HttpResponse:
    """Download a PDF requisito file from SFTP server.

    This view implements a secure file download pattern:
    1. Validates filename format (defense-in-depth early reject)
    2. Fetches the tramite and checks object-level authorization
    3. Delegates to ``SFTPService.serve_requisito_pdf()`` which handles
       cache checking, SFTP download, and response building
    4. Logs the download for audit purposes

    Args:
        request: The HTTP request.
        pk: Primary key of the Tramite.
        filename: Name of the PDF file to download.

    Returns:
        HttpResponse with FileResponse (dev) or X-Accel-Redirect header (prod).

    Raises:
        PermissionDenied: If user lacks download permission.
        SFTPConnectionError: If SFTP download fails.
        Http404: If tramite does not exist.
    """
    # Validate filename BEFORE any filesystem access
    validate_filename(filename)

    # Get the tramite instance (raises Http404 if not found)
    tramite = get_object_or_404(Tramite, pk=pk)

    # Check object-level authorization
    _check_download_permission(request.user, tramite)

    try:
        response = SFTPService.serve_requisito_pdf(
            tramite=tramite,
            filename=filename,
        )
        _log_download(request, tramite, filename, success=True)
        return response

    except SFTPConnectionError:
        _log_download(request, tramite, filename, success=False)
        raise


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
        PermissionDenied: If user lacks download permission.
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
    raise PermissionDenied(
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

    if success:
        logger.info(
            'Descarga exitosa: user=%s tramite=%s file=%s ip=%s',
            user.username,
            tramite.folio,
            filename,
            ip_address,
        )
    else:
        logger.warning(
            'Descarga fallida: user=%s tramite=%s file=%s ip=%s',
            user.username,
            tramite.folio,
            filename,
            ip_address,
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
