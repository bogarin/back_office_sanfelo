"""Utility functions for Django Admin badge rendering.

Provides reusable functions for displaying badges and status indicators
in Django admin with consistent styling using CSS classes.
"""

from django.utils.html import format_html


def render_badge(text, badge_class):
    """Render a badge with given CSS class.

    Args:
        text: Text to display in the badge
        badge_class: CSS class name for the badge styling

    Returns:
        Safe HTML string for the badge
    """
    return format_html('<span class="badge {}">{}</span>', badge_class, text)


def render_status_badge(estatus_id, estatus_text):
    """Render status badge based on estatus ID.

    Args:
        estatus_id: The status ID (100-399 for known statuses)
        estatus_text: Text to display in the badge

    Returns:
        Safe HTML string for the status badge
    """
    if 100 <= estatus_id < 200:
        badge_class = 'badge-inicio'
    elif 200 <= estatus_id < 300:
        badge_class = 'badge-proceso'
    elif 300 <= estatus_id < 400:
        badge_class = 'badge-finalizado'
    else:
        badge_class = 'badge-otro'

    return render_badge(estatus_text, badge_class)


def render_activo_badge(is_activo):
    """Render activo/inactivo badge.

    Args:
        is_activo: Boolean indicating if the item is active

    Returns:
        Safe HTML string for the activo badge
    """
    if is_activo:
        return render_badge('Activo', 'badge-activo')
    return render_badge('Inactivo', 'badge-inactivo')


def render_pagado_badge(is_pagado):
    """Render pagado/no pagado badge.

    Args:
        is_pagado: Boolean indicating if the item is paid

    Returns:
        Safe HTML string for the pagado badge
    """
    if is_pagado:
        return render_badge('Pagado', 'badge-success')
    return render_badge('No Pagado', 'badge-danger')


def render_urgente_badge(is_urgente):
    """Render urgente/normal badge.

    Args:
        is_urgente: Boolean indicating if the item is urgent

    Returns:
        Safe HTML string for the urgente badge
    """
    if is_urgente:
        return render_badge('⚠ Urgente', 'badge-danger')
    return render_badge('Normal', 'badge-secondary')
