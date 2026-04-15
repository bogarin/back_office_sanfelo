"""
Django Admin configuration for tramites app.

Provides a comprehensive admin interface for managing trámites
with filtering, search, and bulk actions.
Integrates with Buzón de Trámites system for analyst assignment.
"""

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.db import DatabaseError, models
from django.db.models import Exists, OuterRef, Subquery
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.admin import (
    ActionableReadOnlyMixin,
    BaseModelAdmin,
    ReadOnlyModelAdmin,
    RoleBasedAccessMixin,
    mark_as_active,
    mark_as_inactive,
)
from core.admin_utils import (
    render_activo_badge,
    render_status_badge,
)
from core.rbac.constants import BackOfficeRole
from tramites.models import (
    Actividades,
    AsignacionTramite,
    Perito,
    Tramite,
    TramiteCatalogo,
    TramiteEstatus,
)
from tramites.services import (
    EstadoNoPermitidoError,
    TramiteNoAsignableError,
    asignar_tramite,
    liberar_tramite,
)

ACTION_CHECKBOX_NAME = 'action_checkbox_name'
User = get_user_model()


# =============================================================================
# Catalog Admins (migrated from catalogos app)
# =============================================================================


# Perito model - kept for internal use, not registered in admin
# @admin.register(Perito)
class PeritoAdmin(ReadOnlyModelAdmin, RoleBasedAccessMixin):
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
    actions = (mark_as_active, mark_as_inactive)

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
        'estatus',
        'backoffice_user_id',
        'observacion',
        'timestamp',
    )
    list_filter = ('timestamp',)
    search_fields = ('observacion',)
    ordering = ('-timestamp',)
    raw_id_fields = ('tramite', 'estatus')


# =============================================================================
# Custom list filters for Tramite
# =============================================================================


# Custom list filter para 'finalizado'
class TramiteFinalizadoFilter(admin.SimpleListFilter):
    title = '¿Finalizado?'
    parameter_name = 'finalizado'

    def lookups(self, request, model_admin):
        return [(True, 'Finalizado (3xx)')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(_estatus_id__gte=300)
        return queryset


# Custom list filter para 'cancelado'
class TramiteCanceladoFilter(admin.SimpleListFilter):
    title = '¿Cancelado?'
    parameter_name = 'cancelado'

    def lookups(self, request, model_admin):
        return [(True, 'Cancelado (304)')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(_estatus_id=304)
        return queryset


# Custom list filter para estatus (derived from Actividades)
class TramiteEstatusFilter(admin.SimpleListFilter):
    title = 'Estatus'
    parameter_name = 'estatus'

    def lookups(self, request, model_admin):
        return [(e.id, e.estatus) for e in TramiteEstatus.objects.all_cached()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(_estatus_id=self.value())
        return queryset


# =============================================================================
# Tramite Admin
# =============================================================================


@admin.register(Tramite)
class TramiteAdmin(ActionableReadOnlyMixin, ReadOnlyModelAdmin):
    """
    Admin de solo lectura con acciones de asignación.

    Hereda el comportamiento readonly de ``ReadOnlyModelAdmin`` y habilita
    batch actions (tomar, asignar, liberar) a través de
    ``ActionableReadOnlyMixin``.

    El change form es 100% readonly — toda modificación ocurre
    exclusivamente vía actions.

    Lógica de filtrado (SELECT):
    - Admin/Superuser: Ve TODO
    - Coordinador: Ve TODO (asignados + no asignados) para poder reasignar
    - Analista: Ve SUS trámites + trámites sin asignar

    Acciones disponibles por rol:
    - Admin/Superuser: Todas
    - Coordinador: asignar, reasignar, liberar
    - Analista: tomar (solo cuando filtra "Sin asignar")
    """

    # List display configuration
    list_display = (
        'folio',
        'tramite_nombre',
        'tramite_estatus',
        'urgente',
        'analista_asignado',
        'creado',
        'acciones_disponibles',
    )

    # List filtering
    list_filter = (
        TramiteEstatusFilter,
        'pagado',
        'urgente',
        'es_propietario',
        'creado',
        'modificado',
        TramiteFinalizadoFilter,
        TramiteCanceladoFilter,
    )

    # Search fields
    search_fields = (
        'folio',
        'clave_catastral',
        'nom_sol',
        'tel_sol',
        'correo_sol',
    )

    # Ordering
    ordering = ('-creado',)

    # Skip the expensive full_result_count query — we already show totals
    # in the dashboard stats. Saves one COUNT(*) (~200ms) per page load.
    show_full_result_count = False

    # Extra media (JS for quick action buttons in changelist)
    class Media:
        js = ('admin/js/quick_actions.js',)

    # Fields that should be editable in list view
    # list_editable = ('pagado', 'urgente')

    # Fieldsets for edit form
    fieldsets = (
        (
            'Información del Trámite',
            {
                'fields': (
                    'folio',
                    'tramite_catalogo',
                    'estatus_display',
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
            'Actividades',
            {
                'fields': (('creado', 'modificado'),),
                'classes': ('collapse',),
            },
        ),
    )

    # Read-only fields
    readonly_fields = (
        'folio',
        'tramite_catalogo',
        'clave_catastral',
        'estatus_display',
        'es_propietario',
        'nom_sol',
        'tel_sol',
        'correo_sol',
        'importe_total',
        'pagado',
        'tipo',
        'observacion',
        'urgente',
        'creado',
        'modificado',
    )

    def get_queryset(self, request: HttpRequest):
        """
        Filtra trámites según rol del usuario de forma eficiente.

        Usa select_related() para evitar N+1 queries en catálogos.
        Para relaciones cross-database, usa Python filtering en lugar de SQL joins
        para mantener compatibilidad con el router ModelBasedRouter.

        Lógica de SELECT por rol:
        - Admin/Superuser: Ve TODO
        - Coordinador: Ve TODO (para poder reasignar)
        - Analista: Ve SUS trámites + trámites sin asignar

        Returns:
            QuerySet: Trámites filtrados según rol con todas las anotaciones
        """

        queryset = super().get_queryset(request).select_related('tramite_catalogo')
        user = request.user

        # Annotate with estatus_id from latest Actividades (cross-database safe)
        # Use .annotate() directly since Manager's with_estatus() isn't available
        # on admin's queryset

        subquery = Subquery(
            Actividades.objects.filter(tramite=OuterRef('pk'))
            .order_by('-timestamp')
            .values_list('estatus_id')[:1]
        )
        queryset = queryset.annotate(_estatus_id=subquery)

        # Fetch assignment data from default database (AsignacionTramite)
        # Uses Python-level filtering to avoid cross-database SQL joins
        # This is required because ModelBasedRouter blocks cross-database JOINs
        asignaciones = AsignacionTramite.objects.using('default')
        tramites_asignados_ids = set(asignaciones.values_list('tramite_id', flat=True))

        # Build analista mapping for efficient lookup
        # Dict: {tramite_id: analista_id}
        analistas_by_tramite = dict(asignaciones.values_list('tramite_id', 'analista_id'))

        # Admin/Superuser: Ve TODO
        if user.is_superuser or user.is_staff:
            return queryset

        # Coordinador: Ve TODO (asignados + no asignados) para poder reasignar
        if BackOfficeRole.COORDINADOR in getattr(user, 'roles', set()):
            return queryset

        # Analista: Ve SUS trámites + trámites sin asignar
        if BackOfficeRole.ANALISTA in getattr(user, 'roles', set()):
            # Trámites asignados a este analista (filtra en Python usando IDs)
            tramites_mios = queryset.filter(
                pk__in=[
                    tramite_id
                    for tramite_id, analista_id in analistas_by_tramite.items()
                    if analista_id == user.id
                ]
            )

            # Trámites NO asignados a NADIE (excluye IDs asignados)
            tramites_libres = queryset.exclude(pk__in=tramites_asignados_ids)

            # Combinar: MÍOS | SIN ASIGNAR
            return tramites_mios | tramites_libres

        # Otros: No ven nada
        return queryset.none()

    # Custom display methods
    def tramite_nombre(self, obj: Tramite):
        """Display tramite name from catalog (via select_related)."""
        return obj.tramite_display

    tramite_nombre.short_description = 'Tipo de Trámite'

    def tramite_estatus(self, obj: Tramite):
        """Display estatus with color coding (via select_related)."""
        return render_status_badge(obj._estatus_id, obj.estatus_display)

    tramite_estatus.short_description = 'Estatus'

    def analista_asignado(self, obj: Tramite):
        """
        Muestra el analista asignado (o '📦 Sin Asignar').

        Uses ``self._analistas_by_id`` (prefetched in ``changelist_view``)
        for O(1) dict lookups instead of ``User.objects.get()`` per row.
        Falls back to a single query if the dict is unavailable (edge case).
        """
        analista_id = getattr(obj, 'analista_asignado_id', None)

        if not analista_id:
            return '📦 Sin Asignar'

        # Fast path: dict lookup from prefetched analysts
        cache = getattr(self, '_analistas_by_id', None)
        if cache is not None:
            username = cache.get(analista_id)
            if username:
                return f'👤 {username}'
            return f'📦 ID: {analista_id}'

        # Fallback: single query (should rarely happen)
        try:
            asignacion = AsignacionTramite.objects.get(tramite_id=obj.id)
            return f'👤 {asignacion.analista.username}'
        except AsignacionTramite.DoesNotExist:
            return '📦 Sin Asignar'

    analista_asignado.short_description = 'Asignado a'

    actions = (
        'tomar_seleccionados',
        'asignar_seleccionados',
        'reasignar_seleccionados',
        'liberar_seleccionados',
    )

    def get_actions(self, request: HttpRequest):
        """
        Retorna acciones según rol del usuario y filtro activo.

        Context-aware: muestra acciones relevantes según el listado:
        - Analista viendo "Sin Asignar" → puede tomar trámites
        - Coordinador viendo "Asignados" → puede liberar/reasignar
        - Admin/Superuser → todas las acciones siempre disponibles
        """
        actions = super().get_actions(request)
        user = request.user
        url_params = request.GET.urlencode()

        # Admin/Superuser: todas las acciones siempre
        if user.is_superuser or user.is_staff:
            return actions

        # Analista: solo puede tomar trámites sin asignar
        if BackOfficeRole.ANALISTA in getattr(user, 'roles', set()):
            if 'asignado=False' in url_params:
                return {k: v for k, v in actions.items() if k == 'tomar_seleccionados'}
            return {}

        # Coordinador: acciones contextuales
        if BackOfficeRole.COORDINADOR in getattr(user, 'roles', set()):
            coordinador_actions = {'asignar_seleccionados', 'reasignar_seleccionados'}
            if 'asignado=True' in url_params:
                coordinador_actions.add('liberar_seleccionados')
            return {k: v for k, v in actions.items() if k in coordinador_actions}

        return {}

    def acciones_disponibles(self, obj: Tramite):
        """
        Render quick action buttons that reuse batch actions.

        Uses ``<a>`` links with ``data-action`` and ``data-pk`` attributes.
        An event-delegation script (injected by ``changelist_view``) listens
        for clicks on these links and submits the parent changelist form
        with the correct action + selected object.

        CSP-safe: no inline ``onclick`` handlers; the script tag uses a nonce.
        """
        request = getattr(self, '_request', None)
        if request is None:
            return '—'

        user = request.user
        esta_asignado = getattr(obj, 'esta_asignado_flag', False)

        is_admin = user.is_superuser or user.is_staff
        roles = getattr(user, 'roles', set())
        is_coordinador = BackOfficeRole.COORDINADOR in roles
        is_analista = BackOfficeRole.ANALISTA in roles

        # (action_name, label) pairs for the applicable actions
        actions_map: list[tuple[str, str]] = []

        if is_admin or is_coordinador:
            if esta_asignado:
                actions_map.append(('liberar_seleccionados', '🗑️ Liberar'))
                actions_map.append(('asignar_seleccionados', '🔄 Reasignar'))
            else:
                actions_map.append(('asignar_seleccionados', '👤 Asignar'))
        elif is_analista and not esta_asignado:
            actions_map.append(('tomar_seleccionados', '📌 Tomar'))

        if not actions_map:
            return '—'

        buttons = []
        for action_name, label in actions_map:
            buttons.append(
                format_html(
                    '<a href="#" class="button quick-action" '
                    'data-action="{}" data-pk="{}" '
                    'style="padding:2px 10px;font-size:11px;white-space:nowrap;margin-right:4px;">'
                    '{}</a>',
                    action_name,
                    obj.pk,
                    label,
                )
            )

        return mark_safe(' '.join(buttons))

    acciones_disponibles.short_description = 'Acciones Rápidas'
    acciones_disponibles.allow_tags = True

    # ========== BATCH ACTIONS ==========

    @admin.action(description='📌 Tomar trámites seleccionados')
    def tomar_seleccionados(self, request: HttpRequest, queryset) -> HttpResponseRedirect:
        """
        Permite a los analistas asignarse trámites disponibles.

        Solo funciona para trámites NO asignados.
        Los analistas se auto-asignan estos trámites.
        """
        if BackOfficeRole.ANALISTA not in getattr(request.user, 'roles', set()):
            messages.error(request, '❌ Solo los analistas pueden tomar trámites')
            return redirect(request.get_full_path())

        tomados = []
        errores = []
        errores_asignacion = []  # Track assignment failures separately

        for tramite in queryset:
            # Verificar que no esté asignado
            if AsignacionTramite.objects.filter(tramite_id=tramite.id).exists():
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
            except DatabaseError as e:
                # Actividades creation failure - rollback will happen
                errores_asignacion.append(
                    f'{tramite.folio}: La asignación falló. Intente nuevamente'
                )
            except EstadoNoPermitidoError as e:
                errores.append(f'{tramite.folio}: {str(e)}')
            except Exception as e:
                errores.append(f'{tramite.folio}: Error inesperado - {str(e)}')

        if tomados:
            messages.success(request, f'✅ Has tomado {len(tomados)} trámites exitosamente')
        if errores_asignacion:
            messages.warning(
                request, f'⚠️ Errores de asignación: {"; ".join(errores_asignacion[:5])}'
            )
        if errores:
            messages.warning(request, f'⚠️ Errores: {"; ".join(errores[:5])}')

        return redirect(request.get_full_path())

    # ========== ACTIONS PARA COORDINADOR ==========

    @admin.action(description='👤 Asignar trámites seleccionados a analista')
    def asignar_seleccionados(self, request: HttpRequest, queryset) -> HttpResponse:
        """
        Action para asignar trámites en batch.

        Muestra un form para seleccionar el analista y ejecuta
        las asignaciones de forma atómica.
        """
        if request.POST.get('analista'):
            analista_id = request.POST['analista']
            analista = User.objects.get(id=analista_id)
            observacion = request.POST.get('observacion', '')

            asignados = []
            errores = []
            errores_asignacion = []  # Track assignment failures separately

            for tramite in queryset:
                try:
                    asignar_tramite(
                        tramite=tramite,
                        analista=analista,
                        asignado_por=request.user,
                        observacion=observacion,
                    )
                    asignados.append(tramite.folio)
                except DatabaseError as e:
                    # Actividades creation failure - rollback will happen
                    errores_asignacion.append(
                        f'{tramite.folio}: La asignación falló. Intente nuevamente'
                    )
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
            if errores_asignacion:
                messages.warning(
                    request, f'⚠️ Errores de asignación: {"; ".join(errores_asignacion[:5])}'
                )
            if errores:
                messages.warning(request, f'⚠️ Errores: {"; ".join(errores[:5])}')

            return redirect(request.get_full_path())

        # GET: Mostrar formulario de selección de analista
        analistas = User.objects.filter(groups__name='Analista')

        # Calculate load for each analyst (cross-database safe)
        analistas_con_carga = []
        for analista in analistas:
            carga = AsignacionTramite.objects.filter(analista=analista).count()
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
    def reasignar_seleccionados(self, request: HttpRequest, queryset) -> HttpResponse:
        """
        Action para reasignar trámites a otro analista.

        Similar a asignar_seleccionados, pero más explícito en el nombre.
        """
        return self.asignar_seleccionados(request, queryset)

    @admin.action(description='🗑️ Liberar trámites seleccionados')
    def liberar_seleccionados(self, request: HttpRequest, queryset) -> HttpResponse:
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
    def changelist_view(self, request: HttpRequest, extra_context: dict[str, str] | None = None):
        """
        Add statistics to change list view with optimized queries.

        Also stores ``request`` on ``self`` so that ``acciones_disponibles``
        can render role-aware quick action buttons.

        Optimizaciones:
        - Usa TramiteManager.get_statistics() con caching para stats principales
        - Usa TramiteManager.get_estatus_distribution() con caching para distribución
        - Deriva finalizados/cancelados de la distribución (sin queries extra)
        """
        # Store request for use in list_display methods (e.g. acciones_disponibles)
        self._request = request

        # Prefetch analysts for analista_asignado column (cross-database safe):
        # one query here instead of User.objects.get() per row.
        self._analistas_by_id = dict(
            User.objects.filter(groups__name='Analista').values_list('id', 'username')
        )

        # Use cached statistics from TramiteManager (much faster!)
        stats = Tramite.objects.get_statistics()

        # Use cached distribution — single GROUP BY query with shorter TTL
        estatus_distribution_list = Tramite.objects.get_estatus_distribution()

        # Derive finalizados/cancelados from distribution (zero extra queries)
        finalizados = sum(
            total
            for estatus_id, _, total in estatus_distribution_list
            if estatus_id is not None and estatus_id >= 300
        )
        cancelados = sum(
            total for estatus_id, _, total in estatus_distribution_list if estatus_id == 304
        )

        ctx = dict(extra_context) if extra_context else {}
        ctx.update(
            {
                'total_tramites': stats['total'],
                'tramites_urgentes': stats.get('urgentes', 0),
                'tramites_pagados': stats.get('pagados', 0),
                'tramites_pendientes_pago': stats['total'] - stats.get('pagados', 0),
                'tramites_finalizados': finalizados,
                'tramites_cancelados': cancelados,
                'estatus_distribution': estatus_distribution_list,
                'quick_action_js': True,
            }
        )

        return super().changelist_view(request, extra_context=ctx)

    # Custom form field widget customization
    def get_form_customized(self, request: HttpRequest, obj: Tramite | None = None, **kwargs):
        """Customize form with widget choices from catalog tables."""
        form = super().get_form(request, obj, **kwargs)

        # Populate choices dynamically from cached catalogs
        tramites_choices = [
            (t.id, t.nombre) for t in TramiteCatalogo.objects.all_cached() if t.activo
        ]
        peritos_choices = [(p.id, p.nombre_completo) for p in Perito.objects.all_cached()]

        form.base_fields['tramite_catalogo'].widget.choices = tramites_choices
        form.base_fields['perito'].widget.choices = peritos_choices

        return form
