"""Django Admin configuration for catalogos app.

Provides admin interface for managing all catalog tables
with appropriate filtering, search, and inline configurations.
"""

from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from catalogos.models import (
    Actividades,
    CatActividad,
    CatCategoria,
    CatEstatus,
    CatInciso,
    CatPerito,
    CatRequisito,
    CatTipo,
    CatTramite,
    CatUsuario,
    Cobro,
    RelTmtActividad,
    RelTmtCategoria,
    RelTmtCateReq,
    RelTmtInciso,
    RelTmtTipoReq,
)
from core.admin import (
    AuditTrailMixin,
    BaseModelAdmin,
    CatalogBaseAdmin,
    mark_as_active,
    mark_as_inactive,
    OperatorPermissionMixin,
)
from core.admin_utils import render_activo_badge

# ============================================================================
# CATALOG TABLES (cat_*)
# ============================================================================


@admin.register(CatTramite)
class CatTramiteAdmin(AuditTrailMixin, CatalogBaseAdmin, OperatorPermissionMixin):
    """Admin interface for CatTramite model."""

    list_display = (
        'id',
        'nombre',
        'area',
        'activo',
        'activo_badge',
        'respuesta_dias',
        'pago_inicial',
    )
    list_filter = ('area', 'activo', 'pago_inicial')
    search_fields = ('nombre', 'descripcion', 'area')
    list_editable = ('activo',)
    actions = [mark_as_active, mark_as_inactive]

    fieldsets = (
        (
            'Información del Trámite',
            {
                'fields': ('nombre', 'descripcion', 'area', 'tipo'),
            },
        ),
        (
            'Configuración',
            {
                'fields': (
                    'respuesta_dias',
                    'pago_inicial',
                    'activo',
                    'url',
                ),
            },
        ),
    )

    def activo_badge(self, obj):
        """Display activo status as badge."""
        return render_activo_badge(obj.activo)

    activo_badge.short_description = 'Estado'
    activo_badge.admin_order_field = 'activo'
    activo_badge.allow_tags = True

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(CatEstatus)
class CatEstatusAdmin(AuditTrailMixin, CatalogBaseAdmin, OperatorPermissionMixin):
    """Admin interface for CatEstatus model."""

    list_display = ('id', 'estatus', 'responsable', 'estatus_group')
    list_filter = ('responsable',)
    search_fields = ('estatus', 'responsable', 'descripcion')

    fieldsets = (
        (
            'Información del Estatus',
            {
                'fields': ('estatus', 'responsable', 'descripcion'),
            },
        ),
    )

    def estatus_group(self, obj):
        """Display estatus group based on ID."""
        if 100 <= obj.id < 200:
            return format_html('<span class="badge badge-inicio">Inicio</span>')
        if 200 <= obj.id < 300:
            return format_html('<span class="badge badge-proceso">Proceso</span>')
        if 300 <= obj.id < 400:
            return format_html('<span class="badge badge-finalizado">Finalizado</span>')
        return format_html('<span class="badge badge-otro">Otro</span>')

    estatus_group.short_description = 'Grupo'
    estatus_group.allow_tags = True

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(CatUsuario)
class CatUsuarioAdmin(AuditTrailMixin, BaseModelAdmin, OperatorPermissionMixin):
    """Admin interface for CatUsuario model."""

    list_display = (
        'nombre',
        'usuario',
        'nivel',
        'correo',
        'activo',
        'activo_badge',
        'fecha_alta',
    )
    list_filter = ('activo', 'nivel')
    search_fields = ('nombre', 'usuario', 'correo')
    list_editable = ('activo',)
    actions = [mark_as_active, mark_as_inactive]

    fieldsets = (
        (
            'Información del Usuario',
            {
                'fields': ('nombre', 'usuario', 'correo', 'nivel'),
            },
        ),
        (
            'Configuración',
            {
                'fields': (
                    'activo',
                    ('fecha_alta', 'fecha_baja'),
                ),
            },
        ),
    )

    def activo_badge(self, obj):
        """Display activo status as badge."""
        return render_activo_badge(obj.activo)

    activo_badge.short_description = 'Estado'
    activo_badge.admin_order_field = 'activo'
    activo_badge.allow_tags = True

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(CatPerito)
class CatPeritoAdmin(AuditTrailMixin, BaseModelAdmin, OperatorPermissionMixin):
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
                    ('telefono', 'celular'),
                    'correo',
                    ('domicilio', 'colonia'),
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

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(CatActividad)
class CatActividadAdmin(AuditTrailMixin, CatalogBaseAdmin, OperatorPermissionMixin):
    """Admin interface for CatActividad model."""

    list_display = ('id', 'actividad')
    search_fields = ('actividad',)

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(CatCategoria)
class CatCategoriaAdmin(AuditTrailMixin, CatalogBaseAdmin, OperatorPermissionMixin):
    """Admin interface for CatCategoria model."""

    list_display = ('id', 'categoria')
    search_fields = ('categoria',)

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(CatInciso)
class CatIncisoAdmin(AuditTrailMixin, BaseModelAdmin, OperatorPermissionMixin):
    """Admin interface for CatInciso model."""

    list_display = ('id', 'inciso', 'descripcion')
    search_fields = ('inciso', 'descripcion')

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(CatRequisito)
class CatRequisitoAdmin(AuditTrailMixin, CatalogBaseAdmin, OperatorPermissionMixin):
    """Admin interface for CatRequisito model."""

    list_display = ('id', 'requisito')
    search_fields = ('requisito',)

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(CatTipo)
class CatTipoAdmin(AuditTrailMixin, CatalogBaseAdmin, OperatorPermissionMixin):
    """Admin interface for CatTipo model."""

    list_display = ('id', 'tipo')
    search_fields = ('tipo',)

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


# ============================================================================
# RELATIONSHIP TABLES (rel_*)
# ============================================================================


@admin.register(RelTmtCateReq)
class RelTmtCateReqAdmin(AuditTrailMixin, BaseModelAdmin, OperatorPermissionMixin):
    """Admin interface for RelTmtCateReq model."""

    list_display = ('id', 'id_cat_tramite', 'id_cat_requisito', 'id_cat_categoria')
    list_filter = ('id_cat_tramite', 'id_cat_categoria')
    search_fields = ('id_cat_tramite', 'id_cat_requisito')

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(RelTmtCategoria)
class RelTmtCategoriaAdmin(AuditTrailMixin, BaseModelAdmin, OperatorPermissionMixin):
    """Admin interface for RelTmtCategoria model."""

    list_display = ('id', 'id_cat_tramite', 'id_cat_categoria')
    list_filter = ('id_cat_tramite', 'id_cat_categoria')
    search_fields = ('id_cat_tramite', 'id_cat_categoria')

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(RelTmtInciso)
class RelTmtIncisoAdmin(AuditTrailMixin, BaseModelAdmin, OperatorPermissionMixin):
    """Admin interface for RelTmtInciso model."""

    list_display = ('id', 'id_cat_inciso', 'id_cat_tramite')
    list_filter = ('id_cat_inciso', 'id_cat_tramite')
    search_fields = ('id_cat_inciso', 'id_cat_tramite')

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(RelTmtTipoReq)
class RelTmtTipoReqAdmin(AuditTrailMixin, BaseModelAdmin, OperatorPermissionMixin):
    """Admin interface for RelTmtTipoReq model."""

    list_display = ('id', 'id_cat_tipo', 'id_cat_tramite', 'id_cat_requisito')
    list_filter = ('id_cat_tipo', 'id_cat_tramite')
    search_fields = ('id_cat_tipo', 'id_cat_tramite', 'id_cat_requisito')

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(RelTmtActividad)
class RelTmtActividadAdmin(AuditTrailMixin, BaseModelAdmin, OperatorPermissionMixin):
    """Admin interface for RelTmtActividad model."""

    list_display = ('id', 'id_cat_tramite', 'id_cat_actividad')
    list_filter = ('id_cat_tramite', 'id_cat_actividad')
    search_fields = ('id_cat_tramite', 'id_cat_actividad')

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


# ============================================================================
# ADDITIONAL TABLES
# ============================================================================


@admin.register(Actividades)
class ActividadesAdmin(AuditTrailMixin, BaseModelAdmin, OperatorPermissionMixin):
    """Admin interface for Actividades model."""

    list_display = (
        'id',
        'id_tramite',
        'id_cat_actividad',
        'id_cat_estatus',
        'secuencia',
        'fecha_inicio',
        'fecha_fin',
    )
    list_filter = ('id_cat_actividad', 'id_cat_estatus', 'fecha_inicio', 'fecha_fin')
    search_fields = ('id_tramite', 'observacion')
    ordering = ('-secuencia',)

    fieldsets = (
        (
            'Información de la Actividad',
            {
                'fields': (
                    'id_tramite',
                    'id_cat_actividad',
                    'id_cat_estatus',
                    'secuencia',
                ),
            },
        ),
        (
            'Fechas',
            {
                'fields': (('fecha_inicio', 'fecha_fin'),),
            },
        ),
        (
            'Información Adicional',
            {
                'fields': ('id_cat_usuario', 'observacion'),
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Customize form with widget choices from catalog tables."""
        form = super().get_form(request, obj, **kwargs)
        from catalogos.models import CatActividad, CatEstatus, CatUsuario

        # Populate choices dynamically
        actividades_choices = [(a.id, a.actividad) for a in CatActividad.objects.all()]
        estatus_choices = [(e.id, e.estatus) for e in CatEstatus.objects.all()]
        usuarios_choices = [(u.id, u.nombre) for u in CatUsuario.objects.all()]

        form.base_fields['id_cat_actividad'].widget.choices = actividades_choices
        form.base_fields['id_cat_estatus'].widget.choices = estatus_choices
        form.base_fields['id_cat_usuario'].widget.choices = usuarios_choices

        return form

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)


@admin.register(Cobro)
class CobroAdmin(AuditTrailMixin, BaseModelAdmin, OperatorPermissionMixin):
    """Admin interface for Cobro model."""

    list_display = ('id', 'concepto', 'importe', 'inciso', 'id_tramite')
    list_filter = ('inciso',)
    search_fields = ('concepto', 'id_tramite')
    ordering = ('-id',)

    fieldsets = (
        (
            'Información del Cobro',
            {
                'fields': (
                    'concepto',
                    'importe',
                    'inciso',
                    'id_tramite',
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_change_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Operador').exists():
            return False
        return super().has_delete_permission(request)
