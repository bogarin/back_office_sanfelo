"""
Views for core application.

This module contains main views for Backoffice San Felipe.
Following Django's best practices with proper separation of concerns.
"""

from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
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
        return HttpResponseRedirect(reverse_lazy('admin:auth_user_changelist'))

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

        # Assign role to selected users
        count = 0
        for user in users:
            # Remove all groups first
            user.groups.clear()
            user.is_superuser = False

            # Assign selected role
            group = Group.objects.filter(name=role_choice).first()
            if group:
                user.groups.add(group)
                user.is_staff = True
            else:
                user.is_staff = False

            user.save()
            count += 1

        # Clear session
        request.session.pop('selected_user_ids', None)
        request.session.pop('user_ids_count', None)

        messages.success(request, f'Se asignó el rol a {count} usuario(s).')
        return HttpResponseRedirect(reverse_lazy('admin:auth_user_changelist'))

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
    return HttpResponseRedirect(reverse_lazy('admin:index'))
