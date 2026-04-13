"""Custom admin actions for batch operations.

Provides admin actions for:
- Marking items as active/inactive
- Marking tramites as urgent/not urgent
- Marking tramites as paid/unpaid
- Assigning roles to users
"""

from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _


# =============================================================================
# Custom Admin Actions
# =============================================================================


def mark_as_active(modeladmin, request, queryset):
    """Admin action to mark selected items as active."""
    rows_updated = queryset.update(activo=True)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "registro") or "registros"} marcados como activos.',
    )


mark_as_active.short_description = 'Marcar como activos'


def mark_as_inactive(modeladmin, request, queryset):
    """Admin action to mark selected items as inactive."""
    rows_updated = queryset.update(activo=False)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "registro") or "registros"} marcados como inactivos.',
    )


mark_as_inactive.short_description = 'Marcar como inactivos'


def mark_urgent(modeladmin, request, queryset):
    """Admin action to mark tramites as urgent."""
    rows_updated = queryset.update(urgente=True)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "trámite") or "trámites"} marcados como urgentes.',
    )


mark_urgent.short_description = 'Marcar como urgentes'


def mark_not_urgent(modeladmin, request, queryset):
    """Admin action to mark tramites as not urgent."""
    rows_updated = queryset.update(urgente=False)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "trámite") or "trámites"} marcados como no urgentes.',
    )


mark_not_urgent.short_description = 'Marcar como no urgentes'


def mark_as_paid(modeladmin, request, queryset):
    """Admin action to mark tramites as paid."""
    rows_updated = queryset.update(pagado=True)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "trámite") or "trámites"} marcados como pagados.',
    )


mark_as_paid.short_description = 'Marcar como pagados'


def mark_as_unpaid(modeladmin, request, queryset):
    """Admin action to mark tramites as unpaid."""
    rows_updated = queryset.update(pagado=False)
    modeladmin.message_user(
        request,
        f'{rows_updated} {((rows_updated == 1) and "trámite") or "trámites"} marcados como no pagados.',
    )


mark_as_unpaid.short_description = 'Marcar como no pagados'


def asignar_rol(modeladmin, request, queryset):
    """
    Admin action to assign roles to selected users.

    This action stores selected users in session for processing
    in a custom view that provides role assignment functionality.

    Args:
        modeladmin: The ModelAdmin instance
        request: The HTTP request object
        queryset: QuerySet of selected User objects
    """
    from django.contrib.auth.models import Group

    # Store selected users in session for use in the view
    selected_ids = list(queryset.values_list('id', flat=True))
    request.session['selected_user_ids'] = selected_ids
    request.session['user_ids_count'] = len(selected_ids)

    # Message to inform user
    modeladmin.message_user(
        request,
        f'{len(selected_ids)} usuario(s) seleccionado(s) para asignar rol. Usa el formulario para asignar el rol.',
    )


asignar_rol.short_description = 'Asignar rol'
