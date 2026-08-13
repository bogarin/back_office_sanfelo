"""
Views for core application.

This module contains main views for Backoffice San Felipe.
Following Django's best practices with proper separation of concerns.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST

from core.rbac.constants import BackOfficeRole
from tramites.models import (
    Actividad,
    Categoria,
    Perito,
    Requisito,
    Tipo,
    TramiteCatalogo,
    TramiteEstatus,
)


def health_check(request: HttpRequest) -> HttpResponse:
    """
    Health check endpoint for monitoring.

    This endpoint returns a simple 'OK' response for health checks.
    It's commonly used by load balancers, monitoring systems, and orchestration tools.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Simple 'OK' response with status 200.
    """
    return HttpResponse('OK', status=200)


@cache_control(max_age=3600)
def pwa_manifest(request: HttpRequest) -> JsonResponse:
    department = settings.BACKOFFICE_DEPARTMENT.lower()
    icon_base = f'{settings.STATIC_URL}{department}'
    icons = [
        {
            'src': f'{icon_base}/icon.png',
            'sizes': '512x512',
            'type': 'image/png',
            'purpose': 'any maskable',
        },
        {
            'src': f'{icon_base}/icon-192.png',
            'sizes': '192x192',
            'type': 'image/png',
            'purpose': 'any maskable',
        },
    ]
    return JsonResponse(
        {
            'id': f'{settings.BACKOFFICE_DEPARTMENT}/v1',
            'name': f'{settings.BACKOFFICE_DEPARTMENT} - {settings.BACKOFFICE_SITE_TITLE}',
            'short_name': f'Backoffice {settings.BACKOFFICE_DEPARTMENT}',
            'description': settings.BACKOFFICE_WELCOME_SIGN,
            'display': 'minimal-ui',
            'start_url': '/admin/',
            'scope': '/',
            'background_color': '#9d2638',
            'theme_color': '#9d2638',
            'categories': ['productivity', 'government'],
            'icons': icons,
            'shortcuts': [
                {
                    'name': 'Mis trámites',
                    'url': '/admin/tramites/buzon/',
                },
                {
                    'name': 'Trámites disponibles',
                    'url': '/admin/tramites/disponible/',
                },
            ],
        }
    )


@staff_member_required
def asignar_rol(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    """
    View to assign roles to selected users.

    This view is called after selecting users in the admin and choosing
    the "Asignar rol" action. It displays a form to select which role to assign.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Form page or redirect back to admin.
    """
    # Get selected user IDs from session
    selected_user_ids = request.session.get('selected_user_ids', [])

    # If no users selected, redirect back to admin
    if not selected_user_ids:
        messages.warning(request, 'No hay usuarios seleccionados para asignar rol.')
        return HttpResponseRedirect(reverse('admin:core_user_changelist'))

    User = get_user_model()

    # Get selected users
    users = User.objects.filter(id__in=selected_user_ids)

    # Get all available groups (roles)
    role_groups = [
        {
            'name': role.name.capitalize(),
            'value': role,
            'group': Group.objects.filter(name=role).first(),
        }
        for role in BackOfficeRole
    ]

    if request.method == 'POST':
        # Get selected role from form
        role_choice = request.POST.get('role')

        if role_choice not in BackOfficeRole:
            messages.error(request, 'Rol inválido.')
            return HttpResponseRedirect(reverse('admin:core_user_changelist'))

        # Assign role to selected users atomically
        count = 0
        with transaction.atomic():
            for user in users:
                # Remove only RBAC role groups (preserve non-RBAC groups)
                user.groups.remove(*user.groups.filter(name__in=list(BackOfficeRole)))
                user.is_superuser = False

                # Any valid role grants admin access (consistent with save_model)
                user.is_staff = True
                group = Group.objects.filter(name=role_choice).first()
                if group:
                    user.groups.add(group)

                user.save()
                count += 1

        # Clear session
        request.session.pop('selected_user_ids', None)
        request.session.pop('user_ids_count', None)

        messages.success(request, f'Se asignó el rol a {count} usuario(s).')
        return HttpResponseRedirect(reverse('admin:core_user_changelist'))

    # GET request - display form
    return render(
        request,
        'admin/auth/user/asignar_rol.html',
        {
            'users': users,
            'role_groups': role_groups,
            'opts': User._meta,
        },
    )


@require_POST
@staff_member_required
def invalidate_catalog_cache(request: HttpRequest) -> HttpResponse:
    """Invalidate all cached catalog data.

    Restricted to users in the Administrador group (or superusers).
    Clears the cache for every catalog model so that fresh data is
    loaded from the database on the next read.

    Returns:
        Redirect to admin index with a success message, or 403 if
        the user lacks permission.
    """
    user = request.user

    is_admin = user.is_superuser or BackOfficeRole.ADMINISTRADOR in getattr(user, 'roles', set())

    if not is_admin:
        return HttpResponseForbidden('Permiso denegado.')

    catalog_models = [
        TramiteCatalogo,
        TramiteEstatus,
        Perito,
        Actividad,
        Categoria,
        Requisito,
        Tipo,
    ]

    for model in catalog_models:
        model.objects.invalidate_cache()

    messages.success(request, 'Caché de catálogos invalidada correctamente.')
    return HttpResponseRedirect(reverse('admin:index'))


@staff_member_required
def test_rendering(request: HttpRequest) -> HttpResponse:
    """Design system rendering test page.

    Displays all styled components used in the project for visual
    verification. Only available in DEBUG mode (URL is gated by
    settings.DEBUG in sanfelipe/urls.py).

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered test page with all design system components.
    """
    return render(request, 'debug/test_rendering.html')


# =============================================================================
# Custom HTTP Error Handlers
# =============================================================================


def custom_permission_denied(
    request: HttpRequest, exception: Exception | None = None
) -> HttpResponse:
    """Custom 403 Permission Denied handler.

    Renders a styled error page instead of Django's default.

    Args:
        request: The HTTP request object.
        exception: The PermissionDenied exception, if available.

    Returns:
        HttpResponse with status 403.
    """
    return render(request, '403.html', status=403)


def custom_csrf_failure(request: HttpRequest, reason: str = '') -> HttpResponse:
    """Custom CSRF failure handler.

    Renders a styled CSRF error page instead of Django's default
    plain HTML page.

    Args:
        request: The HTTP request object.
        reason: Short reason string for the CSRF failure.

    Returns:
        HttpResponse with status 403.
    """
    return render(request, '403_csrf.html', status=403)


def custom_page_not_found(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    """Custom 404 Page Not Found handler.

    Renders a styled error page instead of Django's default.

    Args:
        request: The HTTP request object.
        exception: The Http404 exception, if available.

    Returns:
        HttpResponse with status 404.
    """
    return render(request, '404.html', status=404)


def custom_server_error(request: HttpRequest) -> HttpResponse:
    """Custom 500 Server Error handler.

    Uses RequestContext to ensure template context processors work
    (Django's default server_error view does not use RequestContext).

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse with status 500.
    """
    return render(request, '500.html', status=500)


# =============================================================================
# Test Page for Error Templates (DEBUG only)
# =============================================================================

_VALID_ERROR_TYPES = ('403', '403_csrf', '404', '500')


@staff_member_required
def test_errors(request: HttpRequest) -> HttpResponse:
    """Preview page for error templates.

    Displays a menu with links to preview each error page.
    Accepts ``?error=403``, ``?error=403_csrf``, ``?error=404``, ``?error=500``
    to render the corresponding error template directly.

    Only available in DEBUG mode (URL gated in sanfelipe/urls.py).

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Error template preview or menu page.
    """
    error_type = request.GET.get('error')

    if error_type in _VALID_ERROR_TYPES:
        template_name = f'{error_type}.html'
        return render(request, template_name)

    return render(request, 'debug/test_errors.html')
