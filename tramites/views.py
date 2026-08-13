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
from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from tramites.exceptions import (
    BackofficeError,
    SFTPConnectionError,
)
from tramites.forms import ESTATUS_CANCELACION_CHOICES, CancelarTramiteForm
from tramites.models import Tramite
from tramites.sftp import SFTPService, validate_filename

logger = logging.getLogger(__name__)


# =============================================================================
# Security helpers
# =============================================================================


def _safe_redirect_url(url: str, fallback: str) -> str:
    """Only allow relative URLs (no scheme, no netloc).

    Prevents open redirect attacks by rejecting absolute URLs,
    protocol-relative URLs (//evil.com), and non-/ paths.

    Args:
        url: The URL to validate.
        fallback: Safe fallback URL if validation fails.

    Returns:
        The validated URL or the fallback.
    """
    if not url:
        return fallback
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return fallback
    if not url.startswith('/'):
        return fallback
    return url


# =============================================================================
# Download Views
# =============================================================================


@staff_member_required
def download_pdf(
    request: HttpRequest,
    pk: int,
    filename: str,
) -> HttpResponse | FileResponse:
    """Download a PDF file from SFTP server.

    Supports both requisito files (DAU-*.pdf) and actividad files
    (ACT-*.pdf).

    This view implements a secure file download pattern:
    1. Validates filename format (defense-in-depth early reject)
    2. Fetches the tramite and checks object-level authorization
    3. Delegates to ``SFTPService.serve_pdf()`` which handles
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

    # Object-level authorization (delegates to Tramite.can_download)
    if not tramite.can_download(request.user):
        raise PermissionDenied(
            'No tienes permiso para descargar archivos de este trámite. '
            'Verifica que el trámite esté asignado a ti o que sea un trámite disponible.'
        )

    try:
        response = SFTPService.serve_pdf(
            tramite=tramite,
            filename=filename,
        )
        _log_download(request, tramite, filename, success=True)
        return response

    except SFTPConnectionError:
        _log_download(request, tramite, filename, success=False)
        raise


# =============================================================================
# Cancelar Trámite (intermediate form view)
# =============================================================================


@staff_member_required
def cancelar_tramite_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Vista intermedia para cancelar un trámite.

    Muestra un formulario con:
    - Dropdown con estatus de cancelación (Por Recoger, Rechazado, Cancelado)
    - Campo de observación obligatorio

    GET: Renderiza el formulario intermedio.
    POST: Valida y ejecuta ``tramite.cancelar()``, redirige al detalle.

    Args:
        request: The HTTP request.
        pk: Primary key of the Tramite.

    Returns:
        HttpResponse with the form page (GET) or redirect (POST).
    """
    tramite = get_object_or_404(Tramite, pk=pk)

    if not tramite.can_view(request.user):
        raise PermissionDenied

    # Redirect back to the originating admin change page after action.
    return_url = _safe_redirect_url(
        request.GET.get('next', ''),
        fallback=reverse('admin:tramites_tramite_change', args=[pk]),
    )

    if 'cancelar' not in tramite.available_actions(request.user):
        messages.error(request, 'No es posible cancelar este trámite en su estatus actual.')
        return redirect(return_url)

    if request.method == 'POST':
        form = CancelarTramiteForm(request.POST)
        if form.is_valid():
            estatus_cierre = int(form.cleaned_data['estatus_cierre'])
            observacion = form.cleaned_data['observacion']

            try:
                tramite.cancelar(
                    analista=request.user,
                    estatus_cierre=estatus_cierre,
                    observacion=observacion,
                )
                messages.success(request, f'Trámite {tramite.folio} cancelado exitosamente.')
                return redirect(return_url)

            except BackofficeError as e:
                messages.error(request, e.user_message)
            except ValueError as e:
                logger.warning('ValueError en cancelar_tramite %s: %s', tramite.folio, e)
                messages.error(
                    request,
                    'Los datos proporcionados no son válidos. '
                    'Verifica la información e intenta de nuevo.',
                )
            except Exception as e:
                logger.error('Error cancelando trámite %s: %s', tramite.folio, e, exc_info=True)
                messages.error(request, 'Error inesperado al cancelar el trámite.')
    else:
        form = CancelarTramiteForm()

    context = {
        'tramite': tramite,
        'form': form,
        'estatus_cancelacion_choices': ESTATUS_CANCELACION_CHOICES,
        'opts': Tramite._meta,
        'return_url': return_url,
    }
    return render(request, 'admin/tramite_cancelar.html', context)


# =============================================================================
# Helpers
# =============================================================================


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
