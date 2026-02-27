"""Django Admin configuration for tramites app.

Provides a comprehensive admin interface for managing trámites
with filtering, search, and bulk actions.
"""

from django.contrib import admin

from core.admin import (
    AuditTrailMixin,
    BaseModelAdmin,
    mark_as_paid,
    mark_as_unpaid,
    mark_not_urgent,
    mark_urgent,
)
from core.admin_utils import (
    render_pagado_badge,
    render_status_badge,
    render_urgente_badge,
)
from tramites.models import Tramite


@admin.register(Tramite)
class TramiteAdmin(AuditTrailMixin, BaseModelAdmin):
    """Admin interface for Tramite model."""

    # List display configuration
    list_display = (
        "folio",
        "tramite_nombre",
        "estatus_display",
        "importe_total",
        "pagado",
        "pagado_badge",
        "urgente",
        "urgente_badge",
        "creado",
    )

    # List filtering
    list_filter = (
        "id_cat_estatus",
        "pagado",
        "urgente",
        "es_propietario",
        "creado",
        "modificado",
    )

    # Search fields
    search_fields = (
        "folio",
        "nom_sol",
        "tel_sol",
        "correo_sol",
        "clave_catastral",
        "observacion",
    )

    # Ordering
    ordering = ("-creado",)

    # Pagination
    list_per_page = 25
    list_max_show_all = 100

    # Fields that should be editable in the list view
    list_editable = ("pagado", "urgente")

    # Actions
    actions = [mark_urgent, mark_not_urgent, mark_as_paid, mark_as_unpaid]

    # Fieldsets for the edit form
    fieldsets = (
        (
            "Información del Trámite",
            {
                "fields": (
                    "folio",
                    "id_cat_tramite",
                    "id_cat_estatus",
                    "id_cat_perito",
                    "tipo",
                ),
                "classes": ("wide",),
            },
        ),
        (
            "Información del Solicitante",
            {
                "fields": (
                    "nom_sol",
                    "tel_sol",
                    "correo_sol",
                    "clave_catastral",
                    "es_propietario",
                ),
                "classes": ("wide",),
            },
        ),
        (
            "Información Financiera",
            {
                "fields": ("importe_total", "pagado", "urgente"),
                "classes": ("wide",),
            },
        ),
        (
            "Información Adicional",
            {
                "fields": ("observacion",),
                "classes": ("wide",),
            },
        ),
        (
            "Auditoría",
            {
                "fields": (("creado", "modificado"),),
                "classes": ("collapse",),
            },
        ),
    )

    # Read-only fields
    readonly_fields = ("folio", "creado", "modificado")

    # Custom form field widget customization
    def get_form(self, request, obj=None, **kwargs):
        """Customize form with widget choices from catalog tables."""
        form = super().get_form(request, obj, **kwargs)
        from catalogos.models import CatEstatus, CatPerito, CatTramite

        # Populate choices dynamically
        tramites_choices = [
            (t.id, t.nombre) for t in CatTramite.objects.filter(activo=True)
        ]
        estatus_choices = [(e.id, e.estatus) for e in CatEstatus.objects.all()]
        peritos_choices = [(p.id, p.nombre_completo) for p in CatPerito.objects.all()]

        form.base_fields["id_cat_tramite"].widget.choices = tramites_choices
        form.base_fields["id_cat_estatus"].widget.choices = estatus_choices
        form.base_fields["id_cat_perito"].widget.choices = peritos_choices

        return form

    # Custom display methods
    def tramite_nombre(self, obj):
        """Display tramite name from catalog."""
        return obj.tramite_display

    tramite_nombre.short_description = "Tipo de Trámite"
    tramite_nombre.admin_order_field = "id_cat_tramite"

    def estatus_display(self, obj):
        """Display estatus with color coding."""
        return render_status_badge(obj.id_cat_estatus, obj.estatus_display)

    def pagado_badge(self, obj):
        """Display pagado status as badge."""
        return render_pagado_badge(obj.pagado)

    def urgente_badge(self, obj):
        """Display urgente status as badge."""
        return render_urgente_badge(obj.urgente)

    # Custom change list view
    def changelist_view(self, request, extra_context=None):
        """Add statistics to change list view."""
        extra_context = extra_context or {}

        # Calculate statistics
        total_tramites = Tramite.objects.count()
        tramites_urgentes = Tramite.objects.filter(urgente=True).count()
        tramites_pagados = Tramite.objects.filter(pagado=True).count()
        tramites_pendientes_pago = Tramite.objects.filter(pagado=False).count()

        # Get status distribution
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.id, c.estatus, COUNT(t.id) as total
                FROM tramite t
                JOIN cat_estatus c ON t.id_cat_estatus = c.id
                GROUP BY c.id, c.estatus
                ORDER BY c.id
            """
            )
            estatus_distribution = cursor.fetchall()

        extra_context.update(
            {
                "total_tramites": total_tramites,
                "tramites_urgentes": tramites_urgentes,
                "tramites_pagados": tramites_pagados,
                "tramites_pendientes_pago": tramites_pendientes_pago,
                "estatus_distribution": estatus_distribution,
            }
        )

        return super().changelist_view(request, extra_context)
