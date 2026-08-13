"""
Tramite model (Unificado).

Maps to the view v_tramites_unificado in the backoffice schema.
"""

import logging

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, models

from core.model_config import AccessPattern, register_model
from tramites.exceptions import EstadoNoPermitidoError, TramiteNoAsignableError
from tramites.models.actividades import Actividades
from tramites.models.catalogos import TramiteEstatus
from tramites.models.managers import TramiteQuerySet

User = get_user_model()
logger = logging.getLogger(__name__)

# =============================================================================
# Workflow transitions definition
# =============================================================================

# Maps (from_status, to_status) → True for all valid state transitions.
# Every business action (asignar, requerir, enviar_a_firma, cancelar) must
# go through _validate_transition() which checks this dict.
TRANSITIONS: dict[tuple[int, int], bool] = {
    # Assign: presentado → en revisión
    (TramiteEstatus.Estatus.PRESENTADO, TramiteEstatus.Estatus.EN_REVISION): True,
    # Reassign: en revisión → en revisión (change analyst, same status)
    (TramiteEstatus.Estatus.EN_REVISION, TramiteEstatus.Estatus.EN_REVISION): True,
    # Release: en revisión → presentado (back to pool)
    (TramiteEstatus.Estatus.EN_REVISION, TramiteEstatus.Estatus.PRESENTADO): True,
    # Require documents: en revisión → requerimiento
    (TramiteEstatus.Estatus.EN_REVISION, TramiteEstatus.Estatus.REQUERIMIENTO): True,
    # Enviar a firma: en revisión → en diligencia
    (TramiteEstatus.Estatus.EN_REVISION, TramiteEstatus.Estatus.EN_DILIGENCIA): True,
    # Cancelar from any active "in-process" state
    (TramiteEstatus.Estatus.EN_REVISION, TramiteEstatus.Estatus.POR_RECOGER): True,
    (TramiteEstatus.Estatus.EN_REVISION, TramiteEstatus.Estatus.RECHAZADO): True,
    (TramiteEstatus.Estatus.EN_REVISION, TramiteEstatus.Estatus.CANCELADO): True,
    (TramiteEstatus.Estatus.REQUERIMIENTO, TramiteEstatus.Estatus.POR_RECOGER): True,
    (TramiteEstatus.Estatus.REQUERIMIENTO, TramiteEstatus.Estatus.RECHAZADO): True,
    (TramiteEstatus.Estatus.REQUERIMIENTO, TramiteEstatus.Estatus.CANCELADO): True,
    (TramiteEstatus.Estatus.EN_DILIGENCIA, TramiteEstatus.Estatus.POR_RECOGER): True,
    (TramiteEstatus.Estatus.EN_DILIGENCIA, TramiteEstatus.Estatus.RECHAZADO): True,
    (TramiteEstatus.Estatus.EN_DILIGENCIA, TramiteEstatus.Estatus.CANCELADO): True,
}


def _get_disabled_transitions() -> set[int]:
    """Return disabled destination status IDs from settings (read at call time).

    Values are coerced to ``int`` as defense-in-depth: settings converts
    at load time, but ``override_settings()`` in tests may pass raw strings.
    """
    return {int(x) for x in getattr(django_settings, 'BACKOFFICE_DISABLED_TRANSITIONS', [])}


_CERRAR_DESTINATIONS = frozenset(
    {
        TramiteEstatus.Estatus.POR_RECOGER,
        TramiteEstatus.Estatus.RECHAZADO,
        TramiteEstatus.Estatus.CANCELADO,
    }
)


def _append_cancelar_if_available(
    disabled: set[int],
    actions: list[str],
) -> None:
    """Append ``'cancelar'`` to *actions* if at least one close destination is enabled."""
    if any(dest not in disabled for dest in _CERRAR_DESTINATIONS):
        actions.append('cancelar')


@register_model('default', AccessPattern.READ_ONLY, False)
class Tramite(models.Model):
    """
    Modelo de Django que mapea a la vista v_tramites_unificado en el esquema backoffice.
    Esta vista unifica información de trámites con sus actividades, usuarios asignados y categorías.
    """

    id = models.IntegerField(primary_key=True)
    folio = models.CharField(max_length=50, help_text='Folio del trámite')
    tramite_id = models.IntegerField()
    tramite_nombre = models.CharField(max_length=255, help_text='Tipo de trámite')
    tramite_categoria_id = models.IntegerField(null=True, blank=True)
    tramite_categoria_nombre = models.CharField(
        max_length=255, null=True, blank=True, help_text='Categoría'
    )
    tramite_tipo_cobro_id = models.IntegerField(null=True, blank=True)
    tramite_tipo_cobro_nombre = models.CharField(
        max_length=100, null=True, blank=True, help_text='Tipo de cobro'
    )
    clave_catastral = models.CharField(
        max_length=100, null=True, blank=True, help_text='Clave catastral'
    )
    es_propietario = models.BooleanField(
        help_text='Indica si el solicitante es el propietario del inmueble'
    )
    importe_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Importe total del trámite',
    )
    urgente = models.BooleanField('Urgente', help_text='Indica si el trámite es urgente')
    solicitante_nombre = models.CharField(
        max_length=200, null=True, blank=True, help_text='Nombre del solicitante'
    )
    solicitante_telefono = models.CharField(
        max_length=20, null=True, blank=True, help_text='Teléfono del solicitante'
    )
    solicitante_correo = models.CharField(
        max_length=100, null=True, blank=True, help_text='Correo del solicitante'
    )
    solicitante_comentario = models.TextField(
        null=True, blank=True, help_text='Comentario del solicitante'
    )
    perito_id = models.IntegerField(null=True, blank=True)
    perito_nombre = models.CharField(
        max_length=200, null=True, blank=True, help_text='Nombre del perito'
    )
    ultima_actividad_estatus_id = models.IntegerField(null=True, blank=True)
    ultima_actividad_estatus = models.CharField(
        max_length=100, null=True, blank=True, help_text='Estado de la última actividad'
    )
    ultima_actividad_responsable = models.CharField(
        max_length=100, null=True, blank=True, help_text='Responsable de la última actividad'
    )
    ultima_actividad_descripcion = models.TextField(
        null=True, blank=True, help_text='Descripción de la última actividad'
    )
    ultima_actividad_observacion = models.TextField(
        null=True, blank=True, help_text='Observación de la última actividad'
    )
    asignado_user_id = models.IntegerField(null=True, blank=True)
    asignado_username = models.CharField(
        max_length=150, null=True, blank=True, help_text='Nombre de usuario del analista asignado'
    )
    asignado_nombre = models.CharField(
        max_length=150, null=True, blank=True, help_text='Nombre del analista asignado'
    )
    asignado_group_id = models.IntegerField(null=True, blank=True)
    asignado_rol = models.CharField(
        max_length=150, null=True, blank=True, help_text='Rol del analista asignado'
    )
    creado = models.DateTimeField(
        verbose_name='Fecha de creación', help_text='Fecha y hora de creación del trámite'
    )
    actualizado = models.DateTimeField(
        verbose_name='Fecha de actualización',
        null=True,
        blank=True,
        help_text='Fecha y hora de la última actualización del trámite',
    )

    objects = models.Manager.from_queryset(TramiteQuerySet)()

    class Meta:
        managed = False
        db_table = 'v_tramites_unificado'
        verbose_name = 'Lista de Trámites'
        verbose_name_plural = 'Trámites'
        ordering = ('-creado', 'urgente')

    def __str__(self):
        return f'{self.folio} - {self.tramite_nombre}'

    @property
    def historial_actividades(self):
        """QuerySet de actividades del trámite, ordenadas por fecha descendente."""
        return (
            Actividades.objects.filter(tramite_id=self.pk)
            .select_related('estatus')
            .order_by('-timestamp')
        )

    # =====================================================================
    # Permission checks
    # =====================================================================

    def can_view(self, user: User) -> bool:
        """Whether *user* is allowed to view this trámite's detail page.

        Rules:
        - Superuser / Administrador / Coordinador: always ``True``
        - Analista: only if assigned to this trámite AND not in EN_DILIGENCIA
        """
        if user.is_superuser or user.is_administrador or user.is_coordinador:
            return True
        if user.is_analista:
            if self.ultima_actividad_estatus_id == TramiteEstatus.Estatus.EN_DILIGENCIA:
                return False
            return self.asignado_user_id == user.id
        return False

    def can_download(self, user: User) -> bool:
        """Whether *user* may download documents attached to this trámite.

        Rules:
        - Superuser / Administrador / Coordinador: always ``True``
        - Analista: assigned trámites (any estatus) or unassigned active ones
        """
        if user.is_superuser or user.is_administrador or user.is_coordinador:
            return True
        if not user.is_analista:
            return False
        # Analysts cannot access documents of trámites en diligencia
        if self.ultima_actividad_estatus_id == TramiteEstatus.Estatus.EN_DILIGENCIA:
            return False
        # Assigned to this analyst → always allow
        if self.asignado_user_id == user.id:
            return True
        # Unassigned active trámite → allow
        estatus = self.ultima_actividad_estatus_id
        return (
            self.asignado_user_id is None
            and estatus is not None
            and TramiteEstatus.Estatus.PRESENTADO <= estatus < TramiteEstatus.Estatus.POR_RECOGER
        )

    def can_assign(self, user: User) -> bool:
        """Whether *user* may assign or reassign this trámite.

        Only Coordinadores and Administradores can assign trámites to analysts.
        A trámite in EN_DILIGENCIA cannot be assigned/reassigned.
        """
        if self.ultima_actividad_estatus_id == TramiteEstatus.Estatus.EN_DILIGENCIA:
            return False
        return user.is_coordinador or user.is_administrador or user.is_superuser

    def can_release(self, user: User) -> bool:
        """Whether *user* may release this trámite back to the pool.

        Only Coordinadores and Administradores can release assigned trámites.
        A trámite in EN_DILIGENCIA cannot be released.
        """
        if self.ultima_actividad_estatus_id == TramiteEstatus.Estatus.EN_DILIGENCIA:
            return False
        return user.is_coordinador or user.is_administrador or user.is_superuser

    def can_execute_action(self, user: User) -> bool:
        """Whether *user* may execute workflow actions on this trámite.

        Workflow actions: requerir_documentos, enviar_a_firma, cancelar.
        Only the assigned analyst (or a Coordinator/Admin) may execute them.
        """
        if user.is_superuser or user.is_administrador or user.is_coordinador:
            return True
        return user.is_analista and self.asignado_user_id == user.id

    def available_actions(self, user: User) -> list[str]:
        """Return the list of workflow action names *user* can perform right now.

        The returned list depends on the user's role, the current trámite
        status, and the active department's disabled transitions.  Useful
        for template rendering.

        Returns:
            List of action strings: ``'requerir_documentos'``,
            ``'enviar_a_firma'``, ``'cancelar'``.
        """
        if not self.can_execute_action(user):
            return []

        status = self.ultima_actividad_estatus_id  # type: ignore[assignment]
        disabled = _get_disabled_transitions()
        actions: list[str] = []

        if status == TramiteEstatus.Estatus.EN_REVISION:
            if TramiteEstatus.Estatus.REQUERIMIENTO not in disabled:
                actions.append('requerir_documentos')
            if TramiteEstatus.Estatus.EN_DILIGENCIA not in disabled:
                actions.append('enviar_a_firma')
            _append_cancelar_if_available(disabled, actions)
        elif status == TramiteEstatus.Estatus.REQUERIMIENTO:
            _append_cancelar_if_available(disabled, actions)
        elif status == TramiteEstatus.Estatus.EN_DILIGENCIA:
            if user.is_coordinador or user.is_administrador or user.is_superuser:
                _append_cancelar_if_available(disabled, actions)

        return actions

    # =====================================================================
    # Internal helpers
    # =====================================================================

    def _assert_activo(self) -> None:
        """Raise if the trámite is not in an active status."""
        if not TramiteEstatus.Estatus.es_activo(self.ultima_actividad_estatus_id):
            raise TramiteNoAsignableError(f'El trámite {self.folio} ya no se encuentra activo')

    def _assert_asignado_a(self, usuario: User) -> None:
        """Raise if the trámite is not assigned to *usuario*."""
        if self.asignado_user_id != usuario.id:
            logger.error(
                'El usuario %s intento realizar una acción sobre el tramite %s '
                'pero el tramite esta asignado a %s.',
                usuario.username,
                self.folio,
                self.asignado_username,
            )
            raise PermissionDenied(
                'Este tramite esta asignado a otro analista, '
                'solo el analista asignado puede realizar esta acción.'
            )

    def _validate_transition(self, to_status: int) -> None:
        """Validate that the current status can transition to *to_status*.

        Raises ``EstadoNoPermitidoError`` if the transition is not in
        TRANSITIONS or if the destination status is disabled for the
        active department.
        """
        from_status = self.ultima_actividad_estatus_id  # type: ignore[assignment]

        if (from_status, to_status) not in TRANSITIONS:
            logger.warning(
                'Transición inválida: tramite %s estatus %s → %s',
                self.folio,
                from_status,
                to_status,
            )
            raise EstadoNoPermitidoError(
                user_message=(
                    'No es posible realizar esta acción en el estatus '
                    f'actual del trámite {self.folio}.'
                ),
            )

        if to_status in _get_disabled_transitions():
            logger.warning(
                'Transición deshabilitada: tramite %s estatus %s → %s',
                self.folio,
                from_status,
                to_status,
            )
            raise EstadoNoPermitidoError(
                user_message=(
                    'Esta acción está deshabilitada para el departamento '
                    f'activo del trámite {self.folio}.'
                ),
            )

    def registrar_actividad(
        self, estatus_id: int, analista_id: int | None, observacion: str
    ) -> Actividades:
        """Registra una actividad al trámite.

        Args:
            estatus_id: ID del estatus de la actividad
            analista_id: ID del usuario responsable
            observacion: Texto de observación para la actividad

        Returns:
            Actividades: La instancia de Actividades creada
        """
        try:
            act: Actividades = Actividades.objects.create(
                tramite_id=self.pk,
                estatus_id=estatus_id,
                backoffice_user_id=analista_id,
                observacion=observacion,
            )
        except DatabaseError as e:
            logger.error(
                'Error al crear registro de actividad: tramite=%s estatus=%s error=%s',
                self.pk,
                estatus_id,
                e,
                exc_info=True,
            )
            # Intentionally raises DatabaseError (not BackofficeError) so callers
            # catch it via generic Exception and show "Error inesperado...".
            # The user-friendly message here is only for log context.
            raise DatabaseError(
                'Ocurrió un error al registrar la actividad. '
                'Por favor intenta nuevamente más tarde.'
            ) from e

        logger.info('Actividad agregada al trámite %s: %s', self.folio, act.estatus.estatus)
        return act

    # =====================================================================
    # Public workflow actions
    # =====================================================================

    def asignar(
        self,
        analista: User | None,
        asignado_por: User,
        observacion: str = '',
    ):
        """Asigna, reasigna o libera un trámite.

        - ``analista=None`` → liberar (volver al pool de disponibles)
        - ``analista=user`` → asignar a ese analista

        Args:
            analista: User que recibe la asignación, o None para liberar
            asignado_por: User que ejecuta la acción
            observacion: Texto opcional para la actividad

        Raises:
            TramiteNoAsignableError: Estatus no activo
        """
        if analista is None:
            self._liberar(asignado_por, observacion)
        else:
            self._asignar_analista(analista, asignado_por, observacion)

    def requerir_documentos(self, analista: User, observacion: str) -> None:
        """Requiere documentos adicionales al trámite (202 → 203)."""
        self._assert_activo()
        self._validate_transition(TramiteEstatus.Estatus.REQUERIMIENTO)
        self._assert_asignado_a(analista)
        self.registrar_actividad(
            TramiteEstatus.Estatus.REQUERIMIENTO,
            analista_id=analista.id,
            observacion=observacion,
        )

    def enviar_a_firma(self, analista: User, observacion: str) -> None:
        """Envía el trámite a firma (202 → 205)."""
        self._assert_activo()
        self._validate_transition(TramiteEstatus.Estatus.EN_DILIGENCIA)
        self._assert_asignado_a(analista)
        self.registrar_actividad(
            TramiteEstatus.Estatus.EN_DILIGENCIA,
            analista_id=analista.id,
            observacion=observacion,
        )

    def cancelar(self, analista: User, estatus_cierre: int, observacion: str) -> None:
        """Cancela el trámite con un estatus terminal (202/203/205 → 301/302/304).

        Args:
            analista: User que ejecuta la acción
            estatus_cierre: Estatus terminal seleccionado
                (POR_RECOGER, RECHAZADO o CANCELADO)
            observacion: **Required** — debe ser texto no vacío

        Raises:
            ValueError: Si la observación está vacía o el estatus de cierre
                no es un estatus terminal válido
            EstadoNoPermitidoError: Transición no válida
        """
        observacion = observacion.strip()
        if not observacion:
            raise ValueError('La observación es requerida para cancelar un trámite.')

        estatus_validos = (
            TramiteEstatus.Estatus.POR_RECOGER,
            TramiteEstatus.Estatus.RECHAZADO,
            TramiteEstatus.Estatus.CANCELADO,
        )
        if estatus_cierre not in estatus_validos:
            logger.warning(
                'Estatus de cierre inválido: %s (esperados: %s)',
                estatus_cierre,
                estatus_validos,
            )
            raise ValueError('El estatus de cierre seleccionado no es válido.')

        self._assert_activo()
        self._validate_transition(estatus_cierre)

        if self.ultima_actividad_estatus_id == TramiteEstatus.Estatus.EN_DILIGENCIA:
            if not (analista.is_coordinador or analista.is_administrador or analista.is_superuser):
                raise PermissionDenied(
                    'Solo el coordinador o administrador puede cancelar trámites en diligencia.'
                )
        else:
            self._assert_asignado_a(analista)
        self.registrar_actividad(
            estatus_cierre,
            analista_id=analista.id,
            observacion=observacion,
        )

    # =====================================================================
    # Private workflow sub-actions
    # =====================================================================

    def _liberar(self, liberado_por: User, observacion: str) -> None:
        """Libera el trámite: vuelve al pool de disponibles (→ 201).

        Liberation is a special action: any active status can be released
        back to the pool, so we only check that the trámite is active
        (not that a specific transition exists).
        """
        if liberado_por is None:
            raise ValueError('Se requiere un usuario para liberar el trámite.')

        if self.ultima_actividad_estatus_id == TramiteEstatus.Estatus.EN_DILIGENCIA:
            logger.warning(
                'Intento de liberar trámite %s en estatus EN_DILIGENCIA',
                self.folio,
            )
            raise EstadoNoPermitidoError(
                user_message='No es posible liberar un trámite que se encuentra en diligencia.'
            )

        self._assert_activo()
        self.registrar_actividad(
            TramiteEstatus.Estatus.PRESENTADO,
            analista_id=None,
            observacion=observacion or f'Trámite liberado por {liberado_por.get_full_name()}',
        )
        logger.info('Trámite %s liberado por %s', self.folio, liberado_por.username)

    def _asignar_analista(self, analista: User, asignado_por: User, observacion: str) -> None:
        """Asigna el trámite a un analista (201/202 → 202)."""
        autoasignado = analista == asignado_por

        self._assert_activo()

        # Already assigned to the same analyst — skip silently
        if self.asignado_user_id is not None and self.asignado_user_id == analista.id:
            return

        self._validate_transition(TramiteEstatus.Estatus.EN_REVISION)

        if not observacion:
            if autoasignado:
                observacion = (
                    f'El analista {analista.get_full_name()} ha tomado el trámite para su gestión.'
                )
            else:
                observacion = (
                    f'El trámite ha sido asignado a {analista.get_full_name()} para su gestión.'
                )

        self.registrar_actividad(
            TramiteEstatus.Estatus.EN_REVISION,
            analista_id=analista.id,
            observacion=observacion,
        )
        logger.info(
            'Trámite %s asignado a %s por %s',
            self.folio,
            analista.username,
            asignado_por.username,
        )


class Buzon(Tramite):
    """Modelo proxy para implementar el admin de buzón de tramites para el Analista."""

    class Meta:
        proxy = True
        verbose_name = 'Mis trámites'
        verbose_name_plural = 'Buzón de trámites'
        ordering = ('-creado', '-urgente')


class Disponible(Tramite):
    """Modelo proxy para implementar el admin de tramites disponibles para el Analista."""

    class Meta:
        proxy = True
        verbose_name = 'Trámite disponible para autoasignación'
        verbose_name_plural = 'Trámites disponibles'
        ordering = ('-creado', '-urgente')


class Cerrado(Tramite):
    """Modelo proxy para implementar el admin de tramites finalizados para el Coordinador."""

    class Meta:
        proxy = True
        verbose_name = 'Trámites finalizados'
        verbose_name_plural = 'Trámites finalizados'
        ordering = ('-creado', '-urgente')


class EnDiligencia(Tramite):
    """Modelo proxy para el admin de trámites en diligencia (Coordinador)."""

    class Meta:
        proxy = True
        verbose_name = 'Trámite en diligencia'
        verbose_name_plural = 'Trámites en diligencia'
        ordering = ('-creado', '-urgente')
