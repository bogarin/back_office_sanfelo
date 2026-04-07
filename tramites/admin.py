"""
Django Admin configuration for tramites app.

Provides a comprehensive admin interface for managing trámites
with filtering, search, and bulk actions.
Integrates with Buzón de Trámites system for analyst assignment.
"""

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Subquery
from django.shortcuts import redirect, render

# Try to import ACTION_CHECKBOX_NAME, fallback to a known value
try:
    ACTION_CHECKBOX_NAME = admin.ACTION_CHECKBOX_NAME
except AttributeError:
    ACTION_CHECKBOX_NAME = 'action_checkbox_name'

from buzon.models import AsignacionTramite
from buzon.services import (
    EstadoNoPermitidoError,
    TramiteNoAsignableError,
    asignar_tramite,
    liberar_tramite,
    obtener_analista_asignado,
)
from core.admin import (
    BaseModelAdmin,
    RoleBasedAccessMixin,
    mark_as_active,
    mark_as_inactive,
)
from core.admin_utils import (
    render_activo_badge,
    render_pagado_badge,
    render_status_badge,
    render_urgente_badge,
)
from tramites.models import (
    Actividades,
    Perito,
    Tramite,
    TramiteCatalogo,
    TramiteEstatus,
)

User = get_user_model()


# =============================================================================
# Catalog Admins (migrated from catalogos app)
# =============================================================================


# Perito model - kept for internal use, not registered in admin
# @admin.register(Perito)
class PeritoAdmin(BaseModelAdmin, RoleBasedAccessMixin):
    """Admin interface for Perito model."""

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
        'tramite',
        'actividad',
        'estatus',
        'fecha_inicio',
        'fecha_fin',
        'id_cat_usuario',
        'secuencia',
        'observacion',
    )
    list_filter = ('fecha_inicio', 'fecha_fin')
    search_fields = ('observacion',)
    ordering = ('-secuencia',)


# =============================================================================
# Custom list filters for Tramite
# =============================================================================


# Custom list filter para 'esta_asignado'
class TramiteAssignmentFilter(admin.SimpleListFilter):
    title = '¿Asignado?'
    parameter_name = 'esta_asignado'

    def lookups(self, request, model_admin):
        return (
            (True, 'Asignado'),
            (False, 'Libre'),
        )

    def queryset(self, request, queryset):
        if self.value():
            qs = queryset.filter(Exists(AsignacionTramite.objects.filter(tramite=OuterRef('pk'))))
        else:
            qs = queryset.filter(~Exists(AsignacionTramite.objects.filter(tramite=OuterRef('pk'))))
        return qs


# Custom list filter para 'finalizado'
class TramiteFinalizadoFilter(admin.SimpleListFilter):
    title = '¿Finalizado?'
    parameter_name = 'finalizado'

    def lookups(self, request, model_admin):
        return [(True, 'Finalizado (3xx)')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(estatus_id__gte=300)
        return queryset


# Custom list filter para 'cancelado'
class TramiteCanceladoFilter(admin.SimpleListFilter):
    title = '¿Cancelado?'
    parameter_name = 'cancelado'

    def lookups(self, request, model_admin):
        return [(True, 'Cancelado (304)')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(estatus_id=304)
        return queryset


# =============================================================================
# Tramite Admin
# =============================================================================


@admin.register(Tramite)
class TramiteAdmin(BaseModelAdmin):
    """
    Admin personalizado para el Buzón de Trámites.

    Características:
    - Usa select_related() para evitar N+1 queries
    - Filtra trámites según rol del usuario
    - Implementa permisos UPDATE granulares por rol
    - Implementa batch actions para Analista (tomar) y Coordinador (asignar)
    - Muestra analista asignado en cada trámite

    Lógica de filtrado (SELECT):
    - Admin/Superuser: Ve TODO
    - Coordinador: Ve TODO (asignados + no asignados) para poder reasignar
    - Analista: Ve SUS trámites + trámites libres

    Permisos UPDATE:
    - Admin/Superuser: UPDATE a TODO
    - Coordinador: UPDATE a TODO
    - Analista: UPDATE solo a SUS trámites
    """

    # List display configuration
    list_display = (
        'folio',
        'tramite_nombre',
        'estatus_columna',
        'importe_total',
        'pagado',
        'pagado_badge',
        'urgente',
        'urgente_badge',
        'creado',
        'analista_asignado',
    )

    # List filtering
    list_filter = (
        'estatus',
        'pagado',
        'urgente',
        'es_propietario',
        'creado',
        'modificado',
        TramiteAssignmentFilter,
        TramiteFinalizadoFilter,
        TramiteCanceladoFilter,
    )

    # Search fields
    search_fields = (
        'folio',
        'nom_sol',
        'tel_sol',
        'correo_sol',
        'clave_catastral',
        'observacion',
    )

    # Ordering
    ordering = ('-creado',)

    # Pagination
    list_per_page = 25
    list_max_show_all = 100

    # Fields that should be editable in list view
    list_editable = ('pagado', 'urgente')

    # Fieldsets for edit form
    fieldsets = (
        (
            'Información del Trámite',
            {
                'fields': (
                    'folio',
                    'tramite_catalogo',
                    'estatus',
                    'perito',
                    'tipo',
                ),
                'classes': ('wide',),
            },
        ),
        (
            'Información del Solicitante',
            {
                'fields': (
                    'nom_sol',
                    'tel_sol',
                    'correo_sol',
                    'clave_catastral',
                    'es_propietario',
                ),
                'classes': ('wide',),
            },
        ),
        (
            'Información Financiera',
            {
                'fields': ('importe_total', 'pagado', 'urgente'),
                'classes': ('wide',),
            },
        ),
        (
            'Información Adicional',
            {
                'fields': ('observacion',),
                'classes': ('wide',),
            },
        ),
        (
            'Auditoría',
            {
                'fields': (('creado', 'modificado'),),
                'classes': ('collapse',),
            },
        ),
    )

    # Read-only fields
    readonly_fields = ('folio', 'creado', 'modificado')

    def get_queryset(self, request):
        """
        Filtra trámites según rol del usuario de forma eficiente.

        Usa select_related() para evitar N+1 queries en catálogos
        y annotate() para la relación cross-database con AsignacionTramite.

        Lógica de SELECT por rol:
        - Admin/Superuser: Ve TODO
        - Coordinador: Ve TODO (para poder reasignar)
        - Analista: Ve SUS trámites + trámites libres

        Returns:
            QuerySet: Trámites filtrados según rol con todas las anotaciones
        """
        from django.db.models import Value
        from django.db.models.functions import Coalesce

        queryset = super().get_queryset(request).select_related('tramite_catalogo', 'estatus')
        user = request.user

        # Annotate con flag de asignación (cross-database safe)
        queryset = queryset.annotate(
            esta_asignado_flag=Exists(AsignacionTramite.objects.filter(tramite=OuterRef('pk'))),
        )

        # Annotate con analista asignado (cross-database safe)
        queryset = queryset.annotate(
            analista_asignado_id=Subquery(
                AsignacionTramite.objects.filter(tramite=OuterRef('pk')).values('analista_id')[:1]
            )
        )

        # Admin/Superuser: Ve TODO
        if user.is_superuser or user.is_staff:
            return queryset

        # Coordinador: Ve TODO (asignados + no asignados) para poder reasignar
        if user.groups.filter(name='Coordinador').exists():
            return queryset

        # Analista: Ve SUS trámites + trámites libres
        if user.groups.filter(name='Analista').exists():
            # Trámites asignados a este analista (usando analista_id)
            tramites_mios = queryset.filter(
                Exists(
                    AsignacionTramite.objects.filter(tramite=OuterRef('pk'), analista_id=user.id)
                )
            )

            # Trámites NO asignados a NADIE (libres)
            tramites_libres = queryset.filter(
                ~Exists(AsignacionTramite.objects.filter(tramite=OuterRef('pk')))
            )

            # Combinar: MÍOS | LIBRES
            return tramites_mios | tramites_libres

        # Otros: No ven nada
        return queryset.none()

    def has_change_permission(self, request, obj=None):
        """
        Controla quién puede hacer UPDATE a trámites.

        Permisos UPDATE granulares por rol:
        - Admin/Superuser: UPDATE a TODO
        - Coordinador: UPDATE a TODO
        - Analista: UPDATE solo a SUS trámites

        Returns:
            bool: True si tiene permiso, False en caso contrario
        """
        # Admin/Superuser: UPDATE a TODO
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Coordinador: UPDATE a TODO
        if request.user.groups.filter(name='Coordinador').exists():
            return True

        # Analista: UPDATE solo a SUS trámites
        if request.user.groups.filter(name='Analista').exists():
            if obj is None:
                # En changelist, verificar que tenga permisos generales
                return True
            else:
                # En detail view, verificar que sea SU trámite
                analista = obtener_analista_asignado(obj)
                return analista == request.user

        # Otros: Sin permiso
        return False

    def get_form(self, request, obj=None, **kwargs):
        """
        Personaliza form según el rol.

        Analistas no pueden modificar campos de asignación.
        """
        form = super().get_form(request, obj, **kwargs)

        # Para Analistas: readonly en campos de asignación
        if request.user.groups.filter(name='Analista').exists():
            # El Analista no puede modificar asignaciones
            # (se controla en has_change_permission, pero adicionalmente aquí)
            pass

        return form

    def save_model(self, request, obj, form, change):
        """
        Guarda el modelo con validaciones adicionales.

        Verifica que el analista solo modifique SUS trámites.
        """
        # Verificar permisos antes de guardar
        if not self.has_change_permission(request, obj):
            raise PermissionError('No tienes permiso para modificar este trámite')

        super().save_model(request, obj, form, change)

    # Custom display methods
    def tramite_nombre(self, obj):
        """Display tramite name from catalog (via select_related)."""
        return (
            obj.tramite_catalogo.nombre
            if obj.tramite_catalogo
            else (f'ID {obj.tramite_catalogo_id}')
        )

    tramite_nombre.short_description = 'Tipo de Trámite'
    tramite_nombre.admin_order_field = 'tramite_catalogo'

    def estatus_columna(self, obj):
        """Display estatus with color coding (via select_related)."""
        estatus_display = obj.estatus.estatus if obj.estatus else f'ID {obj.estatus_id}'
        return render_status_badge(obj.estatus_id, estatus_display)

    estatus_columna.short_description = 'Estatus'

    def pagado_badge(self, obj):
        """Display pagado status as badge."""
        return render_pagado_badge(obj.pagado)

    def urgente_badge(self, obj):
        """Display urgente status as badge."""
        return render_urgente_badge(obj.urgente)

    def analista_asignado(self, obj):
        """
        Muestra el analista asignado (o '📦 Libre').

        Usa el ID del analista anotado para evitar queries adicionales.
        """
        analista_id = getattr(obj, 'analista_asignado_id', None)

        if analista_id:
            try:
                analista = User.objects.get(id=analista_id)
                return f'👤 {analista.username}'
            except User.DoesNotExist:
                return f'📦 ID: {analista_id}'

        return '📦 Libre'

    analista_asignado.short_description = 'Asignado a'

    # Actions para Analista (auto-asignación)
    actions_analista = ['tomar_seleccionados']

    # Actions para Coordinador (asignación masiva)
    actions_coordinador = [
        'asignar_seleccionados',
        'reasignar_seleccionados',
        'liberar_seleccionados',
    ]

    def get_actions(self, request):
        """
        Retorna acciones según estatus y rol del usuario.

        Lógica:
        - Analista viendo "Sin Asignar" → puede tomar
        - Coordinador viendo "Asignados" → puede liberar
        - Otras combinaciones → acciones existentes
        """
        actions = super().get_actions(request)

        # Parsear URL params para detectar filtro activo
        url_params = request.GET.urlencode()

        # Para Analista: solo puede tomar trámites sin asignar
        if request.user.groups.filter(name='Analista').exists():
            if 'esta_asignado=False' in url_params:
                # Añadir acción de tomar
                actions['tomar_seleccionados'] = self.tomar_seleccionados
            else:
                # Para otros listados, solo acciones de lectura
                actions = {
                    k: v
                    for k, v in actions.items()
                    if k
                    not in [
                        'asignar_seleccionados',
                        'reasignar_seleccionados',
                        'liberar_seleccionados',
                    ]
                }

        # Para Coordinador: puede liberar asignados
        elif request.user.groups.filter(name='Coordinador').exists():
            if 'esta_asignado=True' in url_params:
                # Añadir acción de liberar
                actions['liberar_seleccionados'] = self.liberar_seleccionados
            # Mantener acciones de asignación existentes

        # Admin/Superuser: todas las acciones disponibles
        return actions

    # ========== ACTIONS PARA ANALISTA ==========

    @admin.action(description='📌 Tomar trámites seleccionados')
    def tomar_seleccionados(self, request, queryset):
        """
        Permite a los analistas asignarse trámites disponibles.

        Solo funciona para trámites NO asignados.
        Los analistas se auto-asignan estos trámites.
        """
        if not request.user.groups.filter(name='Analista').exists():
            messages.error(request, '❌ Solo los analistas pueden tomar trámites')
            return redirect(request.get_full_path())

        tomados = []
        errores = []

        for tramite in queryset:
            # Verificar que no esté asignado
            if AsignacionTramite.objects.filter(tramite=tramite).exists():
                errores.append(f'{tramite.folio}: Ya está asignado a otro analista')
                continue

            try:
                asignar_tramite(
                    tramite=tramite,
                    analista=request.user,
                    asignado_por=request.user,  # El analista se auto-asigna
                    observacion='Auto-asignado por analista',
                )
                tomados.append(tramite.folio)
            except EstadoNoPermitidoError as e:
                errores.append(f'{tramite.folio}: {str(e)}')
            except Exception as e:
                errores.append(f'{tramite.folio}: Error inesperado - {str(e)}')

        if tomados:
            messages.success(request, f'✅ Has tomado {len(tomados)} trámites exitosamente')
        if errores:
            messages.warning(request, f'⚠️ Errores: {"; ".join(errores[:5])}')

        return redirect(request.get_full_path())

    # ========== ACTIONS PARA COORDINADOR ==========

    @admin.action(description='👤 Asignar trámites seleccionados a analista')
    def asignar_seleccionados(self, request, queryset):
        """
        Action para asignar trámites en batch.

        Muestra un form para seleccionar el analista y ejecuta
        las asignaciones de forma atómica.
        """
        if request.method == 'POST':
            analista_id = request.POST.get('analista')
            analista = User.objects.get(id=analista_id)
            observacion = request.POST.get('observacion', '')

            asignados = []
            errores = []

            for tramite in queryset:
                try:
                    asignar_tramite(
                        tramite=tramite,
                        analista=analista,
                        asignado_por=request.user,
                        observacion=observacion,
                    )
                    asignados.append(tramite.folio)
                except EstadoNoPermitidoError as e:
                    errores.append(f'{tramite.folio}: {str(e)}')
                except TramiteNoAsignableError as e:
                    errores.append(f'{tramite.folio}: {str(e)}')
                except Exception as e:
                    errores.append(f'{tramite.folio}: Error inesperado - {str(e)}')

            if asignados:
                messages.success(
                    request, f'✅ {len(asignados)} trámites asignados a {analista.username}'
                )
            if errores:
                messages.warning(request, f'⚠️ Errores: {"; ".join(errores[:5])}')

            return redirect(request.get_full_path())

        # GET: Mostrar formulario de selección de analista
        analistas = User.objects.filter(groups__name='Analista')

        # Calculate load for each analyst (cross-database safe)
        analistas_con_carga = []
        for analista in analistas:
            carga = AsignacionTramite.objects.filter(analista_id=analista.id).count()
            analistas_con_carga.append({'analista': analista, 'carga': carga})

        context = {
            'analistas_con_carga': analistas_con_carga,
            'queryset': queryset,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
            'opts': self.model._meta,
            'action_name': 'asignar_seleccionados',
        }
        return render(request, 'admin/asignar_tramites.html', context)

    @admin.action(description='🔄 Reasignar trámites seleccionados')
    def reasignar_seleccionados(self, request, queryset):
        """
        Action para reasignar trámites a otro analista.

        Similar a asignar_seleccionados, pero más explícito en el nombre.
        """
        return self.asignar_seleccionados(request, queryset)

    @admin.action(description='🗑️ Liberar trámites seleccionados')
    def liberar_seleccionados(self, request, queryset):
        """
        Action para liberar trámites en batch.

        Elimina las asignaciones de los trámites seleccionados.
        """
        count = 0
        for tramite in queryset:
            liberar_tramite(tramite)
            count += 1

        messages.success(request, f'✅ {count} trámites liberados')
        return redirect(request.get_full_path())

    # Custom change list view (mantener estadísticas existentes)
    def changelist_view(self, request, extra_context=None):
        """
        Add statistics to change list view with optimized queries.

        Optimizaciones:
        - Usa TramiteManager.get_statistics() con caching para stats principales
        - Agregación single query para distribución por estatus
        - Fetch de TramiteEstatus en una sola query
        """
        extra_context = extra_context or {}

        # Use cached statistics from TramiteManager (much faster!)
        stats = Tramite.objects.get_statistics()

        # Get status distribution with optimized aggregation (single query)
        estatus_distribution = (
            Tramite.objects.values('estatus_id').annotate(total=Count('id')).order_by('estatus_id')
        )

        # Fetch all statuses once (single query to business DB)
        all_estatus = {e.id: e.estatus for e in TramiteEstatus.objects.all()}

        # Combine data in Python (avoids N+1 queries, maintains format)
        estatus_distribution_list = [
            (cat_id, all_estatus.get(cat_id, f'ID {cat_id}'), total)
            for cat_id, total in estatus_distribution.values_list('estatus_id', 'total')
        ]

        extra_context.update(
            {
                'total_tramites': stats['total'],
                'tramites_urgentes': stats.get('urgentes', 0),
                'tramites_pagados': stats.get('pagados', 0),
                'tramites_pendientes_pago': stats['total'] - stats.get('pagados', 0),
                'estatus_distribution': estatus_distribution_list,
            }
        )

        return super().changelist_view(request, extra_context=extra_context)

    # Custom form field widget customization
    def get_form_customized(self, request, obj=None, **kwargs):
        """Customize form with widget choices from catalog tables."""
        form = super().get_form(request, obj, **kwargs)

        # Populate choices dynamically
        tramites_choices = [(t.id, t.nombre) for t in TramiteCatalogo.objects.filter(activo=True)]
        estatus_choices = [(e.id, e.estatus) for e in TramiteEstatus.objects.all()]
        peritos_choices = [(p.id, p.nombre_completo) for p in Perito.objects.all()]

        form.base_fields['tramite_catalogo'].widget.choices = tramites_choices
        form.base_fields['estatus'].widget.choices = estatus_choices
        form.base_fields['perito'].widget.choices = peritos_choices

        return form
