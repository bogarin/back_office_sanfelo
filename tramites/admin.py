"""
Django Admin configuration for tramites app.

Provides a comprehensive admin interface for managing trámites
with filtering, search, and bulk actions.
Integrates with Buzón de Trámites system for analyst assignment.
"""

import logging
from datetime import datetime

from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from core.admin import (
    ActionableReadOnlyMixin,
    ReadOnlyModelAdmin,
)
from core.admin_utils import (
    render_activo_badge,
    render_badge,
    render_quick_action,
    render_status_badge,
)
from core.rbac.constants import BackOfficeRole
from tramites.exceptions import (
    EstadoNoPermitidoError,
    TramiteNoAsignableError,
)
from tramites.forms import TramiteDetailForm
from tramites.models import (
    Actividades,
    AsignacionTramite,
    Buzon,
    Disponible,
    Perito,
    Tramite,
    TramiteCatalogo,
    TramiteEstatus,
)
from tramites.exceptions import SFTPConnectionError
from tramites.sftp import SFTPService


logger = logging.getLogger(__name__)

User = get_user_model()


def _display_timestamp(dt: datetime | None) -> str:
    """Format datetime for display in admin.

    Args:
        dt: DateTime object or None

    Returns:
        Formatted timestamp string or '—' if None
    """
    if dt is None:
        return '—'
    return dt.strftime('%Y-%m-%d %H:%M:%S')


# =============================================================================
# Custom List Filter para TramiteUnificado
# =============================================================================


class AsignadoUserFilter(admin.SimpleListFilter):
    """
    Filter to show only trámites assigned to a user, None and current Logged-In user.
    """

    title = 'Analista Asignado'
    parameter_name = 'analista'

    def lookups(self, request, model_admin):
        users = User.objects.filter(groups__name='Analista')
        options = [
            ('', 'Todos'),
            ('_none', 'Sin Asignar'),
            ('_user', 'Asignados a mí'),
        ]
        options.extend([(str(user.id), user.get_full_name() or user.username) for user in users])
        return options

    def queryset(self, request, queryset):
        match self.value():
            case None:
                qset = queryset
            case '_none':
                qset = queryset.filter(asignado_user_id__isnull=True)
            case '_user':
                qset = queryset.filter(asignado_user_id=request.user.id)
            case _:
                qset = queryset.filter(asignado_user_id=int(self.value()))
        return qset


class TramiteTipoFilter(admin.SimpleListFilter):
    """
    Filter por Tipo de Trámite usando el campo denormalizado tramite_nombre.
    """

    title = 'Tipo de Trámite'
    parameter_name = 'tramite_tipo'

    def lookups(self, request, model_admin):
        # Obtener tipos únicos de tramite_nombre (campo denormalizado)
        tipos = TramiteCatalogo.objects.order_by('nombre')
        return [(tipo.id, tipo.nombre) for tipo in tipos]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tramite_catalogo_id=self.value())
        return queryset


class TramiteEstatusFilter(admin.SimpleListFilter):
    """
    Filter por Estatus usando campos denormalizados (ultima_actividad_estatus_id, ultima_actividad_estatus).
    """

    title = 'Estatus'
    parameter_name = 'tramite_estatus'

    def lookups(self, request, model_admin):
        # Obtener estatus únicos de ultima_actividad_estatus (campo denormalizado)
        estatus = (
            Tramite.objects.exclude(ultima_actividad_estatus__isnull=True)
            .values_list('ultima_actividad_estatus_id', 'ultima_actividad_estatus')
            .distinct()
            .order_by('ultima_actividad_estatus')
        )
        return [(est_id, est_nombre) for est_id, est_nombre in estatus]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(ultima_actividad_estatus_id=self.value())
        return queryset


class TramiteUrgenteFilter(admin.SimpleListFilter):
    title = 'Urgencia'
    parameter_name = 'urgente'

    def lookups(self, request, model_admin):
        return [
            ('1', 'Trámite Urgente'),
            ('0', 'Trámite Normal'),
        ]

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(urgente=True)
        if self.value() == '0':
            return queryset.filter(urgente=False)
        return queryset


DEFAULT_FILTERS = (
    TramiteUrgenteFilter,
    'creado',
    'actualizado',
)


# =============================================================================
# TramiteBaseAdmin
# =============================================================================


class TramiteBaseAdmin(ActionableReadOnlyMixin, ReadOnlyModelAdmin):
    class Media:
        js = ('admin/js/quick_actions.js',)

    # Lista de columnas en la tabla
    list_display = (
        'folio',
        'tramite_nombre_display',
        'estatus_display',
        'urgencia_display',
        'asignado_display',
        'creado_display',
        'actualizado_display',
        'acciones_disponibles',
    )
    ordering = ('-urgente', '-creado', '-actualizado')

    # Filtros en la barra lateral
    list_filter = (
        TramiteTipoFilter,
        TramiteEstatusFilter,
        *DEFAULT_FILTERS,
    )

    # Acciones disponibles (solo modificar_asignacion)
    actions = ('modificar_asignacion',)

    @admin.display(description='Tipo de Trámite', ordering='tramite_nombre')
    def tramite_nombre_display(self, obj):
        return obj.tramite_nombre

    @admin.display(description='Estatus', ordering='ultima_actividad_estatus_id')
    def estatus_display(self, obj):
        return render_status_badge(obj.ultima_actividad_estatus_id, obj.ultima_actividad_estatus)

    @admin.display(description='Urgencia', ordering='urgente')
    def urgencia_display(self, obj):
        if obj.urgente:
            return render_badge('Urgente', 'badge-danger')
        return render_badge('Normal', 'badge-success')

    @admin.display(description='Asignado a', ordering='asignado_username')
    def asignado_display(self, obj):
        match (obj.asignado_user_id, obj.asignado_username, obj.asignado_nombre):
            case (None, _, _):
                return '📦 Sin Asignar'
            case (_, None, None):
                return f'📦 ID: {obj.asignado_user_id}'
            case (_, username, None):
                return f'👤 {username}'
            case (_, _, nombre):
                return f'👤 {nombre}'
        return '📦 Sin Asignar'

    @admin.display(description='Creado', ordering='-creado')
    def creado_display(self, obj):
        return _display_timestamp(obj.creado)

    @admin.display(description='Actualizado', ordering='-actualizado')
    def actualizado_display(self, obj):
        return _display_timestamp(obj.actualizado)

    @admin.display(description='Acciones Rápidas')
    def acciones_disponibles(self, obj):
        """
        Render quick action buttons for trámites.

        Acciones rápidas disponibles:
        - Tomar Tramite: Para analistas (se auto-asignan)
        - Liberar Tramite: Para coordinadores/admin (libera asignación)
        """
        request = getattr(self, '_request', None)
        if request is None:
            return '—'

        user = request.user
        esta_asignado = obj.asignado_user_id is not None

        is_admin = user.is_superuser or user.is_staff
        roles = getattr(user, 'roles', set())
        is_coordinador = BackOfficeRole.COORDINADOR in roles
        is_analista = BackOfficeRole.ANALISTA in roles

        # (action_name, label) pairs for applicable actions
        actions_map: list[tuple[str, str]] = []

        if is_analista and not esta_asignado:
            # Analista puede tomar trámites sin asignar
            actions_map.append(('tomar_rapido', '📌 Tomar'))

        if is_admin or is_coordinador:
            if esta_asignado:
                # Coordinador/Admin puede liberar trámites asignados
                actions_map.append(('liberar_rapido', '🗑️ Liberar'))

        if not actions_map:
            return '—'

        buttons = []
        for action_name, label in actions_map:
            buttons.append(render_quick_action(label, attrs={'action': action_name, 'pk': obj.pk}))

        return mark_safe(' '.join(buttons))

    def changelist_view(self, request, extra_context: dict[str, str] | None = None) -> None:
        """
        Override to store request for use in ``acciones_disponibles``.
        """
        self._request = request
        return super().changelist_view(request, extra_context)

    def get_actions(self, request: HttpRequest):
        """
        Retorna acciones según rol del usuario.

        Solo hay una acción disponible: modificar_asignacion
        """
        actions = super().get_actions(request)
        return actions

    # ========== BATCH ACTION: Modificar Asignación ==========

    @admin.action(description='👤 Modificar Asignación')
    def modificar_asignacion(self, request: HttpRequest, queryset) -> HttpResponse:
        """
        Action para Asignar/Reasignar/Liberar trámites.

        Muestra un formulario con opciones:
        - Seleccionar analista: Asignar o reasignar trámites
        - Ninguno (Liberar): Eliminar asignaciones de trámites seleccionados

        La acción se infiere del analista seleccionado (ninguno = liberar).
        """
        if 'analista' in request.POST:
            analista_id = request.POST.get('analista')
            observacion = request.POST.get('observacion', '')

            # Acción: Liberar (ninguno seleccionado)
            if analista_id == 'ninguno':
                count = 0
                errores = []

                for tramite in queryset:
                    try:
                        tramite.asignar(
                            analista=None,
                            asignado_por=request.user,
                            observacion=observacion,
                        )
                        count += 1
                    except Exception as e:
                        logger.error(f'Error liberando {tramite.folio}: {e}')
                        errores.append(f'{tramite.folio}: {str(e)}')

                if count:
                    messages.success(request, f'✅ {count} trámites liberados')
                if errores:
                    messages.warning(request, f'⚠️ Errores: {"; ".join(errores[:5])}')

            # Acción: Asignar o Reasignar (analista seleccionado)
            else:
                if not analista_id:
                    messages.error(request, '❌ Debe seleccionar un analista o "Ninguno"')
                    return redirect(request.get_full_path())

                analista = User.objects.get(id=analista_id)
                asignados = []
                errores = []

                for tramite in queryset:
                    try:
                        tramite.asignar(
                            analista=analista,
                            asignado_por=request.user,
                            observacion=observacion,
                        )
                        asignados.append(tramite.folio)
                    except Exception as e:
                        logger.error(f'Error asignando {tramite.folio} a {analista.username}: {e}')
                        errores.append(f'{tramite.folio}: {str(e)}')

                if asignados:
                    messages.success(
                        request,
                        f'✅ {len(asignados)} trámites asignados a {analista.get_full_name()}',
                    )
                if errores:
                    messages.warning(request, f'⚠️ Errores: {"; ".join(errores[:5])}')

            return redirect(request.get_full_path())

        # GET: Mostrar formulario de modificación de asignación
        analistas = User.objects.filter(groups__name='Analista')

        context = {
            'analistas': analistas,
            'queryset': queryset,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
            'opts': self.model._meta,
            'action_name': 'modificar_asignacion',
        }
        return render(request, 'admin/modificar_asignacion.html', context)

    # ========== QUICK ACTIONS HANDLERS ==========

    def tomar_rapido(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        """
        Quick action: Permite a los analistas asignarse un trámite.

        Solo funciona para trámites NO asignados.
        """
        if BackOfficeRole.ANALISTA not in getattr(request.user, 'roles', set()):
            messages.error(request, '❌ Solo los analistas pueden tomar trámites')
            return redirect(request.get_full_path())

        try:
            tramite = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            messages.error(request, '❌ Trámite no encontrado')
            return redirect(request.get_full_path())

        try:
            tramite.asignar(
                analista=request.user,
                asignado_por=request.user,
                observacion='Trámite autoasignado',
            )
            messages.success(request, f'✅ Has tomado el trámite {tramite.folio}')
        except TramiteNoAsignableError as e:
            messages.error(request, f'❌ {str(e)}')
        except Exception as e:
            logger.error(f'Error tomando {tramite.folio}: {e}')
            messages.error(request, '❌ Error inesperado al tomar el trámite')

        return redirect(request.get_full_path())

    def liberar_rapido(self, request: HttpRequest, object_id: str) -> HttpResponseRedirect:
        """
        Quick action: Libera un trámite asignado.

        Solo disponible para coordinadores/admin.
        """
        user = request.user
        if not (
            user.is_superuser
            or user.is_staff
            or BackOfficeRole.COORDINADOR in getattr(user, 'roles', set())
        ):
            messages.error(request, '❌ Solo los coordinadores pueden liberar trámites')
            return redirect(request.get_full_path())

        try:
            tramite = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            messages.error(request, '❌ Trámite no encontrado')
            return redirect(request.get_full_path())

        try:
            tramite.asignar(
                analista=None,
                asignado_por=request.user,
                observacion='Trámite liberado',
            )
            messages.success(request, f'✅ Trámite {tramite.folio} liberado')
        except Exception as e:
            logger.error(f'Error liberando {tramite.folio}: {e}')
            messages.error(request, '❌ Error inesperado al liberar el trámite')

        return redirect(request.get_full_path())

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Override para usar template personalizado de detalle de trámite.

        Muestra:
        - Información completa del trámite (readonly)
        - Historial de actividades (via tramite.actividades property)
        - Documentos PDF desde SFTP (via SFTPService.fetch_requisito_files())
        - Acciones disponibles (requerir documentos, en diligencia, finalizar)
        """

        tramite = self.get_object(request, object_id)

        if not tramite:
            messages.error(request, '❌ Trámite no encontrado')
            return redirect('admin:index')

        # Procesar acciones POST (requerir, diligencia, finalizar)
        if request.method == 'POST':
            form = TramiteDetailForm(request.POST)
            if form.is_valid():
                action = request.POST.get('action')
                observacion = form.cleaned_data['observacion']

                try:
                    if action == 'requerir_documentos':
                        tramite.requerir_documentos(analista=request.user, observacion=observacion)
                        messages.success(request, '✅ Requerimiento de documentos registrado')
                    elif action == 'en_diligencia':
                        tramite.en_diligencia(analista=request.user, observacion=observacion)
                        messages.success(request, '✅ Trámite puesto en diligencia')
                    elif action == 'finalizar':
                        tramite.finalizar(analista=request.user, observacion=observacion)
                        messages.success(request, '✅ Trámite finalizado')

                except (TramiteNoAsignableError, EstadoNoPermitidoError, ValueError) as e:
                    messages.error(request, f'❌ {str(e)}')
                except Exception as e:
                    logger.error(f'Error procesando acción en trámite {tramite.folio}: {e}')
                    messages.error(request, '❌ Error al procesar la acción')

        else:
            form = TramiteDetailForm()

        requisitos = []
        try:
            requisitos, _ = SFTPService.fetch_requisito_files(tramite.folio)
        except SFTPConnectionError as e:
            logger.warning('SFTP error for tramite %s: %s', tramite.folio, e)
            messages.error(
                request, 'Error al cargar los documentos. Por favor intenta nuevamente más tarde.'
            )

        context = {
            'tramite': tramite,
            'requisitos': requisitos,
            'form': form,
            'opts': self.model._meta,
            'is_popup': False,
            'has_change_permission': self.has_change_permission(request, tramite),
            'has_view_permission': self.has_view_permission(request, tramite),
            **(extra_context or {}),
        }

        return render(request, 'admin/tramite_detail.html', context)


# =============================================================================
# Admin registrations
# =============================================================================


@admin.register(Buzon)
class BuzonTramitesAdmin(TramiteBaseAdmin):
    """
    Admin para ver trámites asignados al usuario actual. Principalmente orientado a que los analistas
    vean sus trámites asignados.
    """

    list_filter = (
        TramiteTipoFilter,
        TramiteEstatusFilter,
        *DEFAULT_FILTERS,
    )

    def get_queryset(self, request):
        """
        Filter to only show trámites assigned to current user with estatus 200-299.

        Range: 200 <= ultima_actividad_estatus_id < 300
        """
        return (
            super()
            .get_queryset(request)
            .filter(
                asignado_user_id=request.user.id,
                ultima_actividad_estatus_id__gte=TramiteEstatus.Estatus.PRESENTADO.value,
                ultima_actividad_estatus_id__lt=TramiteEstatus.Estatus.POR_RECOGER.value,
            )
        )


@admin.register(Disponible)
class TramitesDisponiblesAdmin(TramiteBaseAdmin):
    """
    Admin para ver trámites disponibles (estatus 200-299).
    Orientado a Analistas que buscan tramites para tomar.
    """

    list_filter = (
        TramiteTipoFilter,
        TramiteEstatusFilter,
        *DEFAULT_FILTERS,
    )

    actions = ('tomar_asignacion',)

    def get_actions(self, request: HttpRequest):
        """
        Retorna solo la acción de tomar asignación.

        Este admin está diseñado exclusivamente para analistas que toman
        trámites disponibles, por lo que la única acción permitida es
        tomar asignación.
        """
        actions = super().get_actions(request)
        return {k: v for k, v in actions.items() if k == 'tomar_asignacion'}

    def get_queryset(self, request):
        """
        Filter to only show trámites with estatus 200-299.

        Range: 200 <= ultima_actividad_estatus_id < 300
        """
        return (
            super()
            .get_queryset(request)
            .filter(
                ultima_actividad_estatus_id__gte=TramiteEstatus.Estatus.PRESENTADO.value,
                ultima_actividad_estatus_id__lt=TramiteEstatus.Estatus.POR_RECOGER.value,
                asignado_user_id__isnull=True,
            )
        )

    @admin.display(description='Acciones Rápidas')
    def acciones_disponibles(self, obj):
        """
        Render quick action buttons for trámites disponibles.

        Única acción disponible: Tomar asignación.
        """
        return render_quick_action('📌 Tomar', attrs={'action': 'tomar_rapido', 'pk': obj.pk})


@admin.register(Tramite)
class TramitesAdmin(TramiteBaseAdmin):
    """
    Admin de tramites orientado a Coordinadores y Administradores para gestión completa de trámites.
    """

    def get_list_filter(self, request):
        """
        Conditionally include AsignadoUserFilter based on user role.

        - Coordinadores y Admins ven el filtro para gestionar asignaciones
        - Analistas no ven el filtro, solo su listado personalizado (Buzon)
        """
        return [AsignadoUserFilter, *super().get_list_filter(request)]

    def get_queryset(self, request):
        """
        Filter to only show trámites with estatus 200-299.

        Range: 200 <= ultima_actividad_estatus_id < 300
        """
        return (
            super()
            .get_queryset(request)
            .filter(
                ultima_actividad_estatus_id__gte=TramiteEstatus.Estatus.PRESENTADO.value,
                ultima_actividad_estatus_id__lt=TramiteEstatus.Estatus.POR_RECOGER.value,
            )
        )

    @admin.display(description='Acciones Rápidas')
    def acciones_disponibles(self, obj):
        """
        Render quick action button for trámites (Coordinador/Admin).

        Única acción disponible: Modificar Asignación.
        """
        return render_quick_action(
            'Modificar Asignación', attrs={'action': 'modificar_asignacion', 'pk': obj.pk}
        )
