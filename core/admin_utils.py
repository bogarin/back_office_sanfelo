"""Utility functions for Django Admin badge rendering.

Provides reusable functions for displaying badges and status indicators
in Django admin with consistent styling using CSS classes.
"""

from django.utils.html import format_html
from django.utils.safestring import mark_safe


def render_badge(text, badge_class):
    """Render a badge with given CSS class.

    Args:
        text: Text to display in the badge
        badge_class: CSS class name for the badge styling

    Returns:
        Safe HTML string for the badge
    """
    return format_html('<span class="badge {}">{}</span>', badge_class, text.replace('_', ' ').upper())


def render_status_badge(estatus_id, estatus_text):
    """Render status badge based on estatus ID.

    Uses specific badge classes (e.g. badge-proceso-202) when a matching
    CSS class exists, falling back to group classes (badge-inicio,
    badge-proceso, badge-finalizado) for unknown IDs within a known range.

    Args:
        estatus_id: The status ID (100-399 for known statuses)
        estatus_text: Text to display in the badge

    Returns:
        Safe HTML string for the status badge
    """
    if estatus_id is None:
        badge_class = 'badge-otro'
    elif 100 <= estatus_id < 200:
        badge_class = f'badge-inicio-{estatus_id}'
    elif 200 <= estatus_id < 300:
        badge_class = f'badge-proceso-{estatus_id}'
    elif 300 <= estatus_id < 400:
        badge_class = f'badge-finalizado-{estatus_id}'
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


def render_quick_action(label: str, attrs: dict[str, str] | None = None, target: str = '#') -> str:
    """
    Render a quick action button for Django admin.

    Args:
        label: Text to display in the button
        attrs: Dictionary of data-* attributes (e.g., {"action": "tomar", "pk": "1"})
        target: URL for navigation (default: "#" for JS-driven actions)

    Returns:
        Safe HTML string for the quick action button
    """
    attrs = attrs or {}
    data_attrs = ' '.join(str(format_html('data-{}="{}"', k, v)) for k, v in attrs.items())
    if target and target != '#':
        return str(
            format_html(
                '<a href="{}" role="button" class="btn btn-sm btn-outline-primary quick-action" {}>{}</a>',
                target,
                mark_safe(data_attrs),
                label,
            )
        )
    return str(
        format_html(
            '<button type="button" class="btn btn-sm btn-outline-primary quick-action" {}>{}</button>',
            mark_safe(data_attrs),
            label,
        )
    )
