"""Template tags for the tramite dashboard.

Provides the ``{% tramite_dashboard_cards %}`` inclusion tag used by
``admin/index.html`` to render the dashboard cards with live statistics
— without requiring a custom view or AdminSite.
"""

from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag('admin/includes/dashboard_cards.html')
def tramite_dashboard_cards():
    """Render the 5-card tramite statistics dashboard.

    Fetches statistics via ``Tramite.objects.get_statistics()`` (cached)
    and builds filtered changelist URLs with ``reverse()``.
    """
    from tramites.models import Tramite

    stats = Tramite.objects.get_statistics()

    def _url(name: str, params: dict | None = None) -> str:
        url = reverse(name)
        if params:
            qs = '&'.join(f'{k}={v}' for k, v in params.items())
            url = f'{url}?{qs}'
        return url

    return {
        'listados': [
            {
                'titulo': '📋 General de Trámites',
                'descripcion': 'Todos los trámites del sistema',
                'url': _url('admin:tramites_tramite_changelist'),
                'icono': 'fa-list',
                'count': stats['total'],
                'color': '#1e3a8a',
            },
            {
                'titulo': '📦 Sin Asignar',
                'descripcion': 'Trámites disponibles para asignación',
                'url': _url('admin:tramites_tramite_changelist', {'esta_asignado': False}),
                'icono': 'fa-box-open',
                'count': stats['sin_asignar'],
                'color': '#d97706',
            },
            {
                'titulo': '👤 Asignados',
                'descripcion': 'Trámites asignados a analistas',
                'url': _url('admin:tramites_tramite_changelist', {'esta_asignado': True}),
                'icono': 'fa-user-check',
                'count': stats['asignados'],
                'color': '#059669',
            },
            {
                'titulo': '✅ Finalizados',
                'descripcion': 'Trámites finalizados (estatus >= 300)',
                'url': _url('admin:tramites_tramite_changelist', {'finalizado': True}),
                'icono': 'fa-check-circle',
                'count': stats['finalizados'],
                'color': '#0891b2',
            },
            {
                'titulo': '❌ Cancelados',
                'descripcion': 'Trámites cancelados (estatus 304)',
                'url': _url('admin:tramites_tramite_changelist', {'cancelado': True}),
                'icono': 'fa-times-circle',
                'count': stats['cancelados'],
                'color': '#dc2626',
            },
        ],
    }
