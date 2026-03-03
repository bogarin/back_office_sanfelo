"""Django Admin configuration for catalogos app.

Provides admin interface for managing catalog tables
with appropriate filtering, search, and inline configurations.
"""

from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from catalogos.models import (
    Actividades,
    CatPerito,
)
from core.admin import (
    BaseModelAdmin,
    mark_as_active,
    mark_as_inactive,
    RoleBasedAccessMixin,
)
from core.admin_utils import render_activo_badge

# ============================================================================
# CATALOG TABLES (cat_*)
# ============================================================================

# Note: According to PLAN.md, most catalog models should NOT be registered in admin.
# Only Actividades is registered, and CatPerito is kept for internal use.


@admin.register(CatPerito)
class CatPeritoAdmin(BaseModelAdmin, RoleBasedAccessMixin):
    """Admin interface for CatPerito model."""

    list_display = (
        'nombre_completo',
        'telefono',
        'correo',
        'estatus',
        'estatus_badge',
        'cedula',
    )
    list_filter = ('estatus',)
    search_fields = ('nombre', 'paterno', 'materno', 'correo', 'cedula', 'rfc')
    list_editable = ('estatus',)
    actions = [mark_as_active, mark_as_inactive]

    fieldsets = (
        (
            'Información Personal',
            {
                'fields': (
                    ('nombre', 'paterno', 'materno'),
                    ('rfc', 'cedula'),
                ),
            },
        ),
        (
            'Contacto',
            {
                'fields': (
                    'telefono',
                    'celular',
                    'correo',
                    'domicilio',
                    'colonia',
                    'ciudad',
                    'estado',
                    'cp',
                ),
            },
        ),
        (
            'Configuración',
            {
                'fields': (
                    'estatus',
                    ('fecha_registro', 'revalidacion'),
                ),
            },
        ),
    )

    def estatus_badge(self, obj):
        """Display estatus status as badge."""
        return render_activo_badge(obj.estatus)

    estatus_badge.short_description = 'Estado'
    estatus_badge.admin_order_field = 'estatus'
    estatus_badge.allow_tags = True


@admin.register(Actividades)
class ActividadesAdmin(BaseModelAdmin, RoleBasedAccessMixin):
    """Admin interface for Actividades model."""

    list_display = (
        'id',
        'descripcion',
        'observaciones',
        'activo',
        'activo_badge',
        'fecha_actualiza',
        'actualizado_por',
    )
    list_filter = ('activo', 'fecha_actualiza')
    search_fields = ('descripcion', 'observaciones')
    list_editable = ('activo',)
    actions = [mark_as_active, mark_as_inactive]
    ordering = ('-fecha_actualiza',)

    def activo_badge(self, obj):
        """Display activo status as badge."""
        return render_activo_badge(obj.activo)

    activo_badge.short_description = 'Estado'
    activo_badge.admin_order_field = 'activo'
    activo_badge.allow_tags = True
