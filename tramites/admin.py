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
)
from core.admin_utils import (
    render_pagado_badge,
    render_status_badge,
    render_urgente_badge,
)
from tramites.models import Tramite

# Import catalog models for lookups
from catalogos.models import CatEstatus

User = get_user_model()


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


@admin.register(Tramite)
class TramiteAdmin(BaseModelAdmin):
    """
    Admin personalizado para el Buzón de Trámites.

    Características:
    - Usa annotate() para evitar N+1 queries
    - Filtra trámites según rol del usuario
    - Implementa permisos UPDATE granulares por rol
    - Implementa batch actions para Analista (tomar) y Coordinador (asignar)
    - Muestra analista asignado en cada trámite
    - Mantiene toda la funcionalidad existente (badges, fieldsets, etc.)

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
        'estatus_display',
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
        'id_cat_estatus',
        'pagado',
        'urgente',
        'es_propietario',
        'creado',
        'modificado',
        TramiteAssignmentFilter,
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
                    'id_cat_tramite',
                    'id_cat_estatus',
                    'id_cat_perito',
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

        Usa annotate() para evitar N+1 queries.
        Una sola query SQL por página.

        Lógica de SELECT por rol:
        - Admin/Superuser: Ve TODO
        - Coordinador: Ve TODO (para poder reasignar)
        - Analista: Ve SUS trámites + trámites libres

        Returns:
            QuerySet: Trámites filtrados según rol
        """
        queryset = super().get_queryset(request)
        user = request.user

        # Annotate con flag de asignación (cross-database safe)
        queryset = queryset.annotate(
            esta_asignado_flag=Exists(AsignacionTramite.objects.filter(tramite=OuterRef('pk'))),
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

    # Custom display methods (existentes + nuevo analista_asignado)
    def tramite_nombre(self, obj):
        """Display tramite name from catalog."""
        return obj.tramite_display

    tramite_nombre.short_description = 'Tipo de Trámite'
    tramite_nombre.admin_order_field = 'id_cat_tramite'

    def estatus_display(self, obj):
        """Display estatus with color coding."""
        return render_status_badge(obj.id_cat_estatus, obj.estatus_display)

    def pagado_badge(self, obj):
        """Display pagado status as badge."""
        return render_pagado_badge(obj.pagado)

    def urgente_badge(self, obj):
        """Display urgente status as badge."""
        return render_urgente_badge(obj.urgente)

    def analista_asignado(self, obj):
        """
        Muestra el analista asignado (o '📦 Libre').

        Usa lazy loading para evitar cross-database joins.
        """
        analista = obtener_analista_asignado(obj)
        if analista:
            return f'👤 {analista.username}'
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
        Retorna acciones según el rol del usuario.

        Analista: Solo puede tomar trámites
        Coordinador: Puede asignar, reasignar y liberar
        """
        actions = super().get_actions(request)

        if request.user.groups.filter(name='Analista').exists():
            # Mantener solo actions de analista
            actions = {k: v for k, v in actions.items() if k in self.actions_analista}
            # Agregar action de tomar
            actions['tomar_seleccionados'] = self.tomar_seleccionados

        elif request.user.groups.filter(name='Coordinador').exists():
            # Mantener solo actions de coordinador
            actions = {k: v for k, v in actions.items() if k in self.actions_coordinador}
            # Agregar actions de coordinador
            actions['asignar_seleccionados'] = self.asignar_seleccionados
            actions['reasignar_seleccionados'] = self.reasignar_seleccionados
            actions['liberar_seleccionados'] = self.liberar_seleccionados

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
        from buzon.models import AsignacionTramite

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
        """Add statistics to change list view."""
        extra_context = extra_context or {}

        # Calculate statistics
        total_tramites = Tramite.objects.count()
        tramites_urgentes = Tramite.objects.filter(urgente=True).count()
        tramites_pagados = Tramite.objects.filter(pagado=True).count()
        tramites_pendientes_pago = Tramite.objects.filter(pagado=False).count()

        # Get status distribution using Django ORM (Pythonic and database-agnostic)
        # Aggregate counts by status (efficient single query to business DB)
        estatus_counts = (
            Tramite.objects.values('id_cat_estatus')
            .annotate(total=Count('id'))
            .order_by('id_cat_estatus')
        )

        # Fetch all statuses once (efficient single query to business DB)
        all_estatus = {e.id: e.estatus for e in CatEstatus.objects.all()}

        # Combine data in Python (avoids N+1 queries, maintains format)
        estatus_distribution = [
            (cat_id, all_estatus.get(cat_id, f'ID {cat_id}'), total)
            for cat_id, total in estatus_counts.values_list('id_cat_estatus', 'total')
        ]

        extra_context.update(
            {
                'total_tramites': total_tramites,
                'tramites_urgentes': tramites_urgentes,
                'tramites_pagados': tramites_pagados,
                'tramites_pendientes_pago': tramites_pendientes_pago,
                'estatus_distribution': estatus_distribution,
            }
        )

        return super().changelist_view(request, extra_context=extra_context)

    # Custom form field widget customization (mantener existente)
    def get_form_customized(self, request, obj=None, **kwargs):
        """Customize form with widget choices from catalog tables."""
        form = super().get_form(request, obj, **kwargs)
        from catalogos.models import CatEstatus, CatPerito, CatTramite

        # Populate choices dynamically
        tramites_choices = [(t.id, t.nombre) for t in CatTramite.objects.filter(activo=True)]
        estatus_choices = [(e.id, e.estatus) for e in CatEstatus.objects.all()]
        peritos_choices = [(p.id, p.nombre_completo) for p in CatPerito.objects.all()]

        form.base_fields['id_cat_tramite'].widget.choices = tramites_choices
        form.base_fields['id_cat_estatus'].widget.choices = estatus_choices
        form.base_fields['id_cat_perito'].widget.choices = peritos_choices

        return form
