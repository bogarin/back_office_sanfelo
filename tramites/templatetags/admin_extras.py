"""Template tags y filtros personalizados para admin de trámites."""

from django import template

register = template.Library()

_STATUS_GROUPS = {1: 'inicio', 2: 'proceso', 3: 'finalizado'}


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
    if 100 <= estatus_id < 200:
        return f'inicio-{estatus_id}'
    if 200 <= estatus_id < 300:
        return f'proceso-{estatus_id}'
    if 300 <= estatus_id < 400:
        return f'finalizado-{estatus_id}'
    return 'otro'


@register.filter(name='status_group')
def status_group(estatus_id: int) -> str:
    """Retorna el grupo de estatus (inicio, proceso, finalizado, otro).

    Usado para aplicar estilos CSS contextuales por familia de estatus.
    """
    if estatus_id is None:
        return 'otro'
    group = _STATUS_GROUPS.get(estatus_id // 100)
    return group or 'otro'
