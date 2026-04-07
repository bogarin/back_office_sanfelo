"""
Views for core application.

This module contains main views for Backoffice San Felipe.
Following Django's best practices with proper separation of concerns.
"""

from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from tramites.models import Tramite


def build_admin_url(url_name: str, params: dict[str, Any] | None = None) -> str:
    """
    Build admin URL with optional query parameters.

    Uses Django's reverse() function to avoid hardcoding URLs.

    Args:
        url_name: Django URL pattern name (e.g., 'admin:tramites_tramite_changelist')
        params: Optional query parameters dictionary

    Returns:
        str: Full URL with query parameters

    Example:
        >>> build_admin_url('admin:tramites_tramite_changelist')
        '/admin/tramites/tramite/'
        >>> build_admin_url('admin:tramites_tramite_changelist', {'esta_asignado': False})
        '/admin/tramites/tramite/?esta_asignado=False'
    """
    url = reverse(url_name)

    if params:
        query_string = '&'.join(f'{key}={value}' for key, value in params.items())
        url = f'{url}?{query_string}'

    return url


@login_required
def admin_home(request: HttpRequest) -> HttpResponse:
    """
    Vista home minimalista con 5 listados de trámites.
    Muestra estadísticas y acceso a listados filtrados.

    Esta vista es accesible solo para usuarios autenticados.
    Muestra 5 cards con estadísticas de trámites diferentes.
    Usa TramiteManager con caching para evitar queries lentas a DB externa.

    Usa Django's reverse() function para generar URLs dinámicamente.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered admin home template.
    """
    # Obtener estadísticas usando manager optimizado con cache
    stats = Tramite.objects.get_statistics()

    # Construir URLs usando reverse() con parámetros (no hardcode)
    context = {
        'title': 'Panel de Trámites',
        'listados': [
            {
                'titulo': '📋 General de Trámites',
                'descripcion': 'Todos los trámites del sistema',
                'url': build_admin_url('admin:tramites_tramite_changelist'),
                'icono': 'fa-list',
                'count': stats['total'],
                'color': '#1e3a8a',
            },
            {
                'titulo': '📦 Sin Asignar',
                'descripcion': 'Trámites disponibles para asignación',
                'url': build_admin_url(
                    'admin:tramites_tramite_changelist', {'esta_asignado': False}
                ),
                'icono': 'fa-box-open',
                'count': stats['sin_asignar'],
                'color': '#d97706',
            },
            {
                'titulo': '👤 Asignados',
                'descripcion': 'Trámites asignados a analistas',
                'url': build_admin_url(
                    'admin:tramites_tramite_changelist', {'esta_asignado': True}
                ),
                'icono': 'fa-user-check',
                'count': stats['asignados'],
                'color': '#059669',
            },
            {
                'titulo': '✅ Finalizados',
                'descripcion': 'Trámites finalizados (estatus >= 300)',
                'url': build_admin_url('admin:tramites_tramite_changelist', {'finalizado': True}),
                'icono': 'fa-check-circle',
                'count': stats['finalizados'],
                'color': '#0891b2',
            },
            {
                'titulo': '❌ Cancelados',
                'descripcion': 'Trámites cancelados (estatus 304)',
                'url': build_admin_url('admin:tramites_tramite_changelist', {'cancelado': True}),
                'icono': 'fa-times-circle',
                'count': stats['cancelados'],
                'color': '#dc2626',
            },
        ],
    }
    return render(request, 'admin/index.html', context)


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
