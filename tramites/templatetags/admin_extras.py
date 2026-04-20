"""Template tags y filtros personalizados para admin de trámites."""

from django import template

register = template.Library()


@register.filter(name='status_badge_class')
def status_badge_class(estatus_id: int) -> str:
    """
    Retorna la clase CSS de badge según el ID de estatus.

    Compatible con render_status_badge de core/admin_utils.py.

    Args:
        estatus_id: ID del estatus (100-399)

    Returns:
        Clase CSS para el badge
    """
    if estatus_id is None:
        return 'otro'
    elif 100 <= estatus_id < 200:
        return 'inicio'
    elif 200 <= estatus_id < 300:
        return 'proceso'
    elif 300 <= estatus_id < 400:
        return 'finalizado'
    else:
        return 'otro'
