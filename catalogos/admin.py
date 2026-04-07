"""Django Admin configuration for catalogos app.

Provides admin interface for managing catalog tables
with appropriate filtering, search, and inline configurations.
"""

from django.contrib import admin

from catalogos.models import (
    Actividades,
    CatPerito,
)
from core.admin import (
    BaseModelAdmin,
    RoleBasedAccessMixin,
    mark_as_active,
    mark_as_inactive,
)
from core.admin_utils import render_activo_badge

# ============================================================================
# CATALOG TABLES (cat_*)
# ============================================================================

# Note: All catalog models are NOT registered in admin.
# Catalog tables are read-only and managed externally.
# Admin access is disabled to prevent accidental modifications.


# CatPerito model - kept for internal use, not registered in admin
# @admin.register(CatPerito)
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


# Actividades model - not registered in admin (read-only catalog)
# @admin.register(Actividades)
class ActividadesAdmin(BaseModelAdmin, RoleBasedAccessMixin):
    """Admin interface for Actividades model."""

    list_display = (
        'id',
        'id_tramite',
        'id_cat_actividad',
        'id_cat_estatus',
        'fecha_inicio',
        'fecha_fin',
        'id_cat_usuario',
        'secuencia',
        'observacion',
    )
    list_filter = ('fecha_inicio', 'fecha_fin')
    search_fields = ('observacion',)
    ordering = ('-secuencia',)
