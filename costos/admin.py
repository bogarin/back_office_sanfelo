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
from costos.models import Costo, Uma


@admin.register(Costo)
class CostoAdmin(BaseModelAdmin, RoleBasedAccessMixin):
    """Admin interface for Costo model."""

    # List display configuration
    list_display = (
        'id',
        'descripcion',
        'id_tramite',
        'axo',
        'importe_calculado',
        'activo',
        'activo_badge',
        'fomento',
        'fecha_actualiza',
    )

    # List filtering
    list_filter = ('axo', 'activo', 'fomento', 'fecha_actualiza', 'id_tipo')

    # Search fields
    search_fields = ('descripcion', 'formula', 'observacion')

    # Ordering
    ordering = ('-axo', 'id_tramite', 'rango_ini')

    # Pagination
    list_per_page = 50

    # Fields that should be editable in the list view
    list_editable = ('activo', 'fomento')

    # Actions
    actions = [mark_as_active, mark_as_inactive]

    # Fieldsets for the edit form
    fieldsets = (
        (
            'Información del Costo',
            {
                'fields': (
                    'id_tramite',
                    'descripcion',
                    'formula',
                    'axo',
                    'id_tipo',
                ),
            },
        ),
        (
            'Valores de Costo',
            {
                'fields': (
                    'cant_umas',
                    'rango_ini',
                    'rango_fin',
                    'inciso',
                ),
            },
        ),
        (
            'Aportaciones Especiales',
            {
                'fields': (
                    'cruz_roja',
                    'bomberos',
                ),
            },
        ),
        (
            'Configuración',
            {
                'fields': (
                    'activo',
                    'fomento',
                ),
            },
        ),
        (
            'Información de Actualización',
            {
                'fields': (
                    'id_usuario',
                    'fecha_actualiza',
                    'observacion',
                ),
                'classes': ('collapse',),
            },
        ),
    )

    # Read-only fields
    readonly_fields = ('id',)

    # Custom display methods
    def activo_badge(self, obj):
        """Display activo status as badge."""
        return render_activo_badge(obj.activo)

    activo_badge.short_description = 'Estado'
    activo_badge.admin_order_field = 'activo'
    activo_badge.allow_tags = True

    def importe_calculado(self, obj):
        """Calculate and display the estimated cost based on UMA value."""
        if obj.cant_umas:
            uma = Uma.get_current_uma()
            if uma:
                importe = obj.cant_umas * uma
                return format_html(
                    '<span class="importe-calculado">${:,.2f} ({} UMA × ${})</span>',
                    importe,
                    obj.cant_umas,
                    uma,
                )
        return 'N/A'

    importe_calculado.short_description = 'Importe Calculado'
    importe_calculado.allow_tags = True

    # Custom form field widget customization
    def get_form(self, request, obj=None, **kwargs):
        """Customize form with widget choices from catalog tables."""
        form = super().get_form(request, obj, **kwargs)
        from catalogos.models import CatTipo

        # Populate choices dynamically
        tipos_choices = [(t.id, t.tipo) for t in CatTipo.objects.all()]

        form.base_fields['id_tipo'].widget.choices = tipos_choices

        return form

    # Custom querysets
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs

    # Save method override
    def save_model(self, request, obj, form, change):
        """Custom save with automatic user and date."""
        from datetime import date

        # Set the user who made the change
        if hasattr(request, 'user'):
            obj.id_usuario = request.user.id if hasattr(request.user, 'id') else 1

        # Set the update date
        obj.fecha_actualiza = date.today()

        super().save_model(request, obj, form, change)


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
