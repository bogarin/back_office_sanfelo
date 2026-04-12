"""
Admin interface for buzon app.

Provides admin interface for managing tramite assignments to analysts.
"""

from django.conf import settings
from django.contrib import admin, messages
from django.utils.html import format_html

from buzon.models import AsignacionTramite
from buzon.services import liberar_tramite, obtener_carga_analistas, reasignar_tramite
from core.admin import BaseModelAdmin
from tramites.models import TramiteEstatus


# @admin.register(AsignacionTramite)
class AsignacionTramiteAdmin(BaseModelAdmin):
    """
    Admin interface para gestión de asignaciones.

    Solo accesible para Coordinador.
    Muestra carga actual de cada analista.
    """

    change_list_template = 'admin/buzon_asignacion_changelist.html'

    list_display = (
        'tramite_folio',
        'tramite_estatus',
        'analista_con_carga',
        'asignado_por_username',
        'fecha_asignacion',
        'observacion_truncada',
    )

    list_filter = (
        'fecha_asignacion',
        'tramite__estatus',
    )

    search_fields = (
        'tramite__folio',
        'observacion',
    )

    readonly_fields = ('fecha_asignacion',)

    fieldsets = (
        (
            'Información de la Asignación',
            {
                'fields': (
                    'tramite',
                    'analista_id',
                    'asignado_por_id',
                ),
            },
        ),
        (
            'Auditoría',
            {
                'fields': (
                    'fecha_asignacion',
                    'observacion',
                ),
            },
        ),
    )

    def changelist_view(self, request, extra_context=None):
        """
        Agrega contexto con carga de analistas para el Coordinador.

        Muestra analistas ordenados por carga (menos carga primero).
        """
        extra_context = extra_context or {}

        # Mostrar analistas ordenados por carga (menos carga primero)
        analistas_ordenados = obtener_carga_analistas()

        # Encontrar analistas con menos carga (top 5)
        analistas_disponibles = analistas_ordenados[:5]

        # Encontrar analistas con más carga (top 5)
        analistas_saturados = list(analistas_ordenados.reverse())[:5]

        extra_context.update(
            {
                'analistas_disponibles': analistas_disponibles,
                'analistas_saturados': analistas_saturados,
                'balance_recomendado': True,
            }
        )

        return super().changelist_view(request, extra_context=extra_context)

    # Custom display methods
    def tramite_folio(self, obj):
        """Muestra el folio del trámite con badge."""
        return format_html('<span class="badge badge-primary">{}</span>', obj.tramite.folio)

    tramite_folio.short_description = 'Folio'
    tramite_folio.admin_order_field = 'tramite__folio'

    def tramite_estatus(self, obj):
        """Muestra el estatus del trámite."""
        try:
            estatus = TramiteEstatus.objects.get(id=obj.tramite.estatus_id)
            return estatus.estatus
        except TramiteEstatus.DoesNotExist:
            return f'ID {obj.tramite.estatus_id}'

    tramite_estatus.short_description = 'Estatus'
    tramite_estatus.admin_order_field = 'tramite__estatus'

    def analista_con_carga(self, obj):
        """Muestra el analista con badge de carga."""

        # Use property to get User instance
        analista = obj.analista
        if not analista:
            return '—'

        # Count assignments using filter on IntegerField
        carga = AsignacionTramite.objects.filter(analista_id=obj.analista_id).count()
        return format_html(
            '<span class="badge badge-info">{}</span> '
            '<span class="badge badge-secondary">{} trámites</span>',
            analista.username,
            carga,
        )

    analista_con_carga.short_description = 'Analista'

    def asignado_por_username(self, obj):
        """Muestra quién asignó el trámite."""
        asignado_por = obj.asignado_por
        return asignado_por.username if asignado_por else '—'

    asignado_por_username.short_description = 'Asignado Por'

    def observacion_truncada(self, obj):
        """Muestra observación truncada."""
        if obj.observacion:
            return obj.observacion[:50] + '...' if len(obj.observacion) > 50 else obj.observacion
        return '—'

    observacion_truncada.short_description = 'Observación'

    # Actions
    actions = ('liberar_seleccionados', 'reasignar_a_analista_disponible')

    @admin.action(description='🗑️ Liberar trámites seleccionados')
    def liberar_seleccionados(self, request, queryset):
        """
        Libera los trámites seleccionados (elimina asignaciones).

        Solo disponible para Coordinador.
        """
        count = queryset.count()
        for asignacion in queryset:
            liberar_tramite(asignacion.tramite)

        messages.success(request, f'✅ {count} trámites liberados exitosamente')

    @admin.action(description='⚖️ Reasignar a analista con menos carga')
    def reasignar_a_analista_disponible(self, request, queryset):
        """
        Reasigna los trámites seleccionados al analista con menos carga.

        Automatiza el balanceo de carga.
        Solo disponible para Coordinador.
        """
        # Obtener analista con menos carga
        analistas_ordenados = obtener_carga_analistas()

        if not analistas_ordenados:
            messages.error(request, '❌ No hay analistas disponibles')
            return

        analista_objetivo = analistas_ordenados.first()

        reasignados = []
        errores = []

        for asignacion in queryset:
            try:
                # Get previous analista username using property
                analista_anterior = asignacion.analista
                analista_anterior_nombre = (
                    analista_anterior.username if analista_anterior else 'Desconocido'
                )

                reasignar_tramite(
                    tramite=asignacion.tramite,
                    nuevo_analista=analista_objetivo,
                    reasignado_por=request.user,
                    observacion=f'Auto-reasignado para balancear carga (anterior: {analista_anterior_nombre})',
                )
                reasignados.append(f'{asignacion.tramite.folio} → {analista_objetivo.username}')
            except Exception as e:
                errores.append(f'{asignacion.tramite.folio}: {e!s}')

        if reasignados:
            messages.success(
                request,
                f'✅ {len(reasignados)} trámites reasignados a {analista_objetivo.username} (menos carga)',
            )
        if errores:
            messages.warning(request, f'⚠️ Errores: {"; ".join(errores[:5])}')

    # Solo visible para Coordinador
    def has_module_permission(self, request):
        return (
            request.user.is_superuser
            or request.user.is_staff
            or request.user.groups.filter(name=settings.COORDINADOR_GROUP_NAME).exists()
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)
