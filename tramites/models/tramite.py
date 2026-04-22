"""
Tramite model (Unificado).

Maps to the view v_tramites_unificado in the backoffice schema.
"""

import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, models

from core.model_config import AccessPattern, register_model
from tramites.exceptions import EstadoNoPermitidoError, SFTPConnectionError, TramiteNoAsignableError
from tramites.models.actividades import Actividades
from tramites.models.catalogos import RequisitoFile, TramiteEstatus

User = get_user_model()
logger = logging.getLogger(__name__)


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
        """
        Retorna el queryset de actividades relacionadas a este trámite, ordenadas por fecha.

        Returns:
            QuerySet de Actividades
        """
        return Actividades.objects.filter(tramite_id=self.pk).order_by('-timestamp')

    def fetch_requisitos(self) -> list[RequisitoFile]:
        """Fetch requisito PDFs from SFTP for this trámite.

        Unlike a property, this method makes the network side-effect
        and potential :class:`SFTPConnectionError` explicit.

        Raises:
            SFTPConnectionError: On SFTP connection or listing failure.

        Returns:
            List of :class:`RequisitoFile` matching this trámite's folio.
        """
        # Defense-in-depth: reject suspicious folios before SFTP call
        from tramites.constants import FORBIDDEN_FOLIO_CHARS

        folio = self.folio
        if any(c in folio for c in FORBIDDEN_FOLIO_CHARS):
            logger.error(
                'Seguridad: folio sospechoso detectado (id=%s, folio=%r)',
                self.pk,
                folio,
            )
            return []

        # Lazy import to avoid circular dependency with services.py
        from tramites.services import SFTPService

        service = SFTPService()
        try:
            files, _ = service.list_requisito_files(folio)
            return files
        finally:
            service.close_connection()

    def verificar_activo(self):
        if not TramiteEstatus.Estatus.es_activo(self.ultima_actividad_estatus_id):
            raise TramiteNoAsignableError(f'El trámite {self.folio} ya no se encuentra activo')

    def verificar_usuario_asignado(self, usuario: User):
        if self.asignado_user_id != usuario.id:
            msg = f'El usuario {usuario.username} intento realizar una acción sobre el tramite {self.folio} pero el tramite esta asignado a {self.asignado_username}.'
            logger.error(msg)
            msg = 'Este tramite esta asignado a otro analista, solo el analista asignado puede realizar esta acción.'
            raise PermissionDenied(msg)

    def registrar_actividad(
        self, estatus_id: int, analista_id: int | None, observacion: str
    ) -> Actividades:
        """
        Registra una actividad al tramite

        Args:
            estatus_id: ID del estatus de la actividad
            responsable_id: ID del usuario responsable
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
            logging.error(f'❌ Error al crear registro de actividad: {e}')
            raise DatabaseError(
                f'Error de base de datos al crear registro de actividad {estatus_id} para el tramite {self.pk}: {e}'
            ) from e

        logger.info(f'Actividad agregada al trámite {self.folio}: {act.estatus.estatus}')
        return act

    def asignar(
        self,
        analista: User,
        asignado_por: User,
        observacion: str,
    ):
        """
        Asigna un trámite creando registro en Actividades.

        Source of truth: Actividades table (backend database).
        La vista v_tramites_unificado se actualiza automáticamente.

        Args:
            analista: Instancia de User que recibe la asignación
            asignado_por: Instancia de User que hace la asignación
            observacion: Texto opcional para la actividad

        Returns:
            bool: La asignación se realizó exitosamente

        Raises:
            TramiteNoAsignableError: Estatus no está en rango 200-299
            DatabaseError: Si falla el INSERT en Actividades
        """
        autoasignado = analista == asignado_por

        # Liberación: el trámite vuelve al pool de disponibles
        if analista is None:
            self.registrar_actividad(
                TramiteEstatus.Estatus.PRESENTADO,  # 201, no 202
                analista_id=None,
                observacion=observacion or f'Trámite liberado por {asignado_por.get_full_name()}',
            )
            logger.info(f'Trámite {self.folio} liberado por {asignado_por.username}')
            return

        if not TramiteEstatus.Estatus.es_activo(self.ultima_actividad_estatus_id):
            if autoasignado:
                msg = f'El usuario {asignado_por.username} intento autoasignarse el tramite {self.folio} '
            else:
                msg = f'El usuario {asignado_por.username} intento asignar el tramite {self.folio} a {analista.username} '
            msg += f'pero el tramite no se encuentra en un estatus asignable (estatus actual: {self.ultima_actividad_estatus_id})'
            logger.warning(msg)
            raise TramiteNoAsignableError(
                f'El trámite {self.folio} no se puede asignar ya que no se encuentra activo'
            )

        # Validar si ya está asignado al mismo analista (reasignación silenciosa)
        if self.asignado_user_id == analista.id:
            return

        # Determinar observación si no se provee (Este mensaje sera visible desde el frontend tambien)
        if not observacion:
            if autoasignado:
                observacion = (
                    f'El analista {analista.get_full_name()} ha tomado el trámite para su gestión.'
                )
            else:
                observacion = (
                    f'El trámite ha sido asignado a {analista.get_full_name()} para su gestión.'
                )

        _ = self.registrar_actividad(
            TramiteEstatus.Estatus.EN_REVISION, analista_id=analista.id, observacion=observacion
        )
        logger.info(
            f'Trámite {self.folio} asignado a {analista.username} por {asignado_por.username}'
        )

    def requerir_documentos(
        self,
        analista: User,
        observacion: str,
    ):
        tmt_status = self.ultima_actividad_estatus_id
        self.verificar_activo()

        if tmt_status != TramiteEstatus.Estatus.EN_REVISION:
            msg = f'El usuario {analista.username} intento requerir documentos '
            msg += f'para el tramite {self.folio} pero el tramite no ha sido asignado a un analista aún.'
            logger.warning(msg)
            msg = 'El trámite debe ser asignado a un Analista antes de requerir documentos.'
            raise EstadoNoPermitidoError(msg)

        self.verificar_usuario_asignado(analista)

        self.registrar_actividad(
            TramiteEstatus.Estatus.REQUERIMIENTO, analista_id=analista.id, observacion=observacion
        )

    def en_diligencia(
        self,
        analista: User,
        observacion: str,
    ):
        tmt_status = self.ultima_actividad_estatus_id
        self.verificar_activo()

        if tmt_status != TramiteEstatus.Estatus.EN_REVISION:
            msg = f'El usuario {analista.username} intento poner en diligencia el tramite {self.folio} pero el tramite no ha sido asignado a  un analista aún.'
            logger.warning(msg)
            msg = 'El trámite debe ser asignado a un Analista antes de ser puesto en diligencia.'
            raise EstadoNoPermitidoError(msg)

        self.verificar_usuario_asignado(analista)

        self.registrar_actividad(
            TramiteEstatus.Estatus.EN_DILIGENCIA, analista_id=analista.id, observacion=observacion
        )

    def finalizar(
        self,
        analista: User,
        observacion: str,
    ):
        observacion = observacion.strip()
        if not observacion:
            raise ValueError('La observación es requerida para finalizar un trámite.')

        tmt_status = self.ultima_actividad_estatus_id
        if not TramiteEstatus.Estatus.es_activo(tmt_status):
            raise TramiteNoAsignableError(f'El trámite {self.folio} ya no se encuentra activo')

        if tmt_status not in (
            TramiteEstatus.Estatus.EN_REVISION,
            TramiteEstatus.Estatus.REQUERIMIENTO,
            TramiteEstatus.Estatus.EN_DILIGENCIA,
        ):
            msg = f'El usuario {analista.username} intento finalizar el tramite {self.folio} pero el no esta en un estatus que permita finalización (estatus actual: {tmt_status}).'
            logger.warning(msg)
            msg = 'No es posible finalizar el trámite en su estatus actual, el trámite debe estar en REVISION, REQUERIMIENTO o EN DILIGENCIA para poder ser finalizado.'
            raise EstadoNoPermitidoError(msg)

        self.verificar_usuario_asignado(analista)

        self.registrar_actividad(
            TramiteEstatus.Estatus.FINALIZADO, analista_id=analista.id, observacion=observacion
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
