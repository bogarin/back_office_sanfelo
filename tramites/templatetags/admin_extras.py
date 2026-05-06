"""Template tags y filtros personalizados para admin de trámites."""

from django import template

from tramites.constants import get_status_badge_class as _get_status_badge_class
from tramites.constants import get_status_group as _get_status_group

register = template.Library()


@register.filter(name='status_badge_class')
def status_badge_class(estatus_id: int) -> str:
    """Retorna la clase CSS de badge según el ID de estatus.

    Delegates to tramites.constants.get_status_badge_class.
    """
    return _get_status_badge_class(estatus_id)


@register.filter(name='status_group')
def status_group(estatus_id: int) -> str:
    """Retorna el grupo de estatus (inicio, proceso, finalizado, otro).

    Delegates to tramites.constants.get_status_group.
    """
    return _get_status_group(estatus_id)
