"""Django Admin configuration for costos app.

Provides admin interface for managing costos (Costo) and UMA value (Uma).
"""

from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from core.admin import (
    BaseModelAdmin,
    mark_as_active,
    mark_as_inactive,
    RoleBasedAccessMixin,
)
from core.admin_utils import render_activo_badge
from costos.models import Uma


@admin.register(Uma)
class UmaAdmin(BaseModelAdmin, RoleBasedAccessMixin):
    """Admin interface for Uma model.

    Note: Only one record (id=1) should exist in this table.
    """

    list_display = ('id', 'valor_display', 'ultima_actualizacion')

    def valor_display(self, obj):
        """Display UMA value with formatting."""
        return format_html(
            '<span class="uma-valor">${:,.4f}</span>',
            obj.valor,
        )

    valor_display.short_description = 'Valor de la UMA'
    valor_display.allow_tags = True

    def ultima_actualizacion(self, obj):
        """Display the last update date from the stored procedure."""
        from datetime import date

        from costos.models import Costo

        # Find the most recent costo update date
        last_update = (
            Costo.objects.filter(fecha_actualiza__lte=date.today())
            .order_by('-fecha_actualiza')
            .first()
        )
        if last_update:
            return last_update.fecha_actualiza.strftime('%d/%m/%Y')
        return 'N/A'

    ultima_actualizacion.short_description = 'Última Actualización'

    # Note: has_add_permission and has_delete_permission are handled by
    # RoleBasedAccessMixin based on user role (superuser, Administrador, Operador).
    # No database queries are needed - permissions are role-based, not data-based.

    def save_model(self, request, obj, form, change):
        """Save model and update UMA using stored procedure."""
        super().save_model(request, obj, form, change)

        # Update the UMA value using the stored procedure
        if obj.valor:
            Uma.update_uma(obj.valor)

    fieldsets = (
        (
            'Valor de la UMA',
            {
                'fields': ('valor',),
                'description': (
                    'El valor de la UMA (Unidad de Medida y Actualización) se utiliza '
                    'para calcular los costos de los trámites. Solo debe existir un '
                    'registro en esta tabla (id=1).'
                ),
            },
        ),
    )
