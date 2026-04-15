"""
AsignacionTramite model for managing tramite assignments to analysts.

This model is stored in SQLite (default database) and maintains a cross-database
relationship with the Tramite model (PostgreSQL) using IntegerField for tramite_id.

Architecture:
- Database: SQLite (default)
- Cross-DB relationship: tramite_id is IntegerField (no Django FK to Tramite)
- User FKs: Real Django ForeignKeys to auth.User (SQLite)
- Performance: Cross-DB queries are acceptable
"""

import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, models, transaction
from django.contrib.auth import get_user_model

from core.model_config import register_model, AccessPattern

User = get_user_model()

logger = logging.getLogger(__name__)

# Estados permitidos para asignación (200s - proceso activo)
ESTADOS_PERMITIDOS_PARA_ASIGNACION = [201, 202, 203, 204, 205]


@register_model('default', AccessPattern.FULL_ACCESS, True)
class AsignacionTramite(models.Model):
    """
    Asignación de trámite a analista.

    Routed to default database (SQLite) with full access permissions.

    Características:
    - Solo permite UNA asignación por trámite (UniqueConstraint a nivel BD)
    - Reemplaza asignaciones anteriores automáticamente
    - Incluye validaciones de negocio
    - Usa transacciones atómicas para evitar race conditions
    - Solo permite asignar trámites en estados 200s (proceso activo)
    - Almacena tramite_id como IntegerField (cross-database safe)
    - Almacena analista y asignado_por como real Django FKs (mismo DB)

    NO modifica tablas legacy - solo crea esta tabla nueva en SQLite.
    """

    tramite_id = models.IntegerField(verbose_name='ID Trámite')

    # Real FKs to User model (same database)
    analista = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Analista',
        related_name='asignaciones_recibidas',
    )

    asignado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Asignado Por',
        related_name='asignaciones_realizadas',
    )

    fecha_asignacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Asignación')

    observacion = models.TextField(blank=True, null=True, verbose_name='Observación')

    class Meta:
        verbose_name = 'Asignación de Trámite'
        verbose_name_plural = 'Asignaciones de Trámites'
        db_table = 'asignacion_tramite'
        ordering = ('-fecha_asignacion',)

        # UniqueConstraint garantiza 1-a-1 a nivel BD
        constraints = [
            models.UniqueConstraint(
                fields=['tramite_id'],
                name='una_sola_asignacion_por_tramite',
                violation_error_message='Este trámite ya está asignado a otro analista',
            )
        ]

        indexes = [
            models.Index(fields=['analista']),
            models.Index(fields=['tramite_id']),
        ]

    def __str__(self):
        return f'Trámite ID {self.tramite_id} → {self.analista.username}'

    def clean(self):
        """
        Validaciones de negocio.

        Raises:
            ValidationError: Si el trámite no puede ser asignado
        """
        # Solo asignar trámites en estados 200s (proceso activo)
        # Need to fetch Tramite instance from PostgreSQL to check status
        from tramites.models import Tramite, TramiteEstatus

        try:
            tramite = Tramite.objects.using('backend').get(id=self.tramite_id)
            estatus_id = tramite.estatus_id
        except Tramite.DoesNotExist:
            raise ValidationError(f'El trámite con ID {self.tramite_id} no existe.')

        if estatus_id not in ESTADOS_PERMITIDOS_PARA_ASIGNACION:
            estatus_nombre = 'DESCONOCIDO'
            estatus = TramiteEstatus.objects.get_cached(estatus_id)
            if estatus:
                estatus_nombre = estatus.estatus
            else:
                estatus_nombre = f'ID {estatus_id}'

            raise ValidationError(
                f'No se pueden asignar trámites en estatus "{estatus_nombre}". '
                f'Solo se pueden asignar trámites en proceso activo (estados 200s: PRESENTADO, EN_REVISION, REQUERIMIENTO, SUBSANADO, EN_DILIGENCIA).'
            )

        # Límite de asignaciones por analista
        asignaciones_actuales = AsignacionTramite.objects.filter(analista=self.analista).count()
        max_asignaciones = getattr(settings, 'MAX_TRAMITES_POR_ANALISTA', 50)
        if asignaciones_actuales >= max_asignaciones:
            raise ValidationError(
                f'El analista ya tiene {asignaciones_actuales} trámites asignados. '
                f'Límite: {max_asignaciones}'
            )

    @classmethod
    def asignar(cls, tramite, analista, asignado_por=None, observacion=''):
        """
        Asigna un trámite a un analista de forma atómica.

        Reemplaza asignación anterior si existe.
        Usa UniqueConstraint para garantizar atomicidad.
        También crea un registro en Actividades en la base de datos de negocios.

        Args:
            tramite: Instancia de Tramite (tabla legacy en PostgreSQL)
            analista: Instancia de User (analista) - FK se almacena
            asignado_por: Instancia de User (quién asigna, opcional) - FK se almacena
            observacion: Texto opcional

        Returns:
            AsignacionTramite: La nueva asignación

        Raises:
            ValidationError: Si hay validaciones falladas
            DatabaseError: Si falla la creación del registro en Actividades
        """
        from .actividades import Actividades
        from .catalogos import TramiteEstatus

        # Wrap everything in a transaction for atomicity
        with transaction.atomic(using='default'):
            # Verificar si ya existe una asignación
            existente = cls.objects.filter(tramite_id=tramite.id).first()

            if existente:
                # Reemplazar asignación existente
                existente.analista = analista
                existente.asignado_por = asignado_por
                existente.observacion = observacion
                existente.full_clean()
                existente.save()
                asignacion = existente
            else:
                # Crear nueva asignación
                asignacion = cls(
                    tramite_id=tramite.id,
                    analista=analista,
                    asignado_por=asignado_por,
                    observacion=observacion,
                )
                asignacion.full_clean()
                asignacion.save()

            # After successful assignment, create Actividades record
            # This is wrapped in try/except to catch database errors
            try:
                # Determine observacion text based on assignment type
                if analista == asignado_por:
                    actividades_observacion = 'Tramite autoasignado'
                else:
                    asignado_por_name = asignado_por.get_full_name() if asignado_por else 'Sistema'
                    actividades_observacion = f'Tramite asignado por {asignado_por_name}'

                # Get TramiteEstatus instance for EN_REVISION (id=202)
                estatus_revision = TramiteEstatus.objects.get_cached(202)

                # Create Actividades record in backend database
                Actividades.objects.using('backend').create(
                    tramite=tramite,
                    estatus_id=202,  # EN_REVISION
                    backoffice_user_id=analista.id,
                    observacion=actividades_observacion,
                )

                logger.info(
                    f'Actividades record created for tramite {tramite.id} '
                    f'assigned to analista {analista.id}'
                )

            except IntegrityError as e:
                logger.error(f'IntegrityError creating Actividades for tramite {tramite.id}: {e}')
                raise DatabaseError(f'Error de integridad al crear registro de actividad: {str(e)}')
            except DatabaseError as e:
                logger.error(f'DatabaseError creating Actividades for tramite {tramite.id}: {e}')
                raise DatabaseError(
                    f'Error de base de datos al crear registro de actividad: {str(e)}'
                )
            except Exception as e:
                logger.error(f'Unexpected error creating Actividades for tramite {tramite.id}: {e}')
                raise DatabaseError(f'Error inesperado al crear registro de actividad: {str(e)}')

            return asignacion

    @classmethod
    def liberar(cls, tramite):
        """
        Libera un trámite (elimina su asignación).

        Args:
            tramite: Instancia de Tramite
        """
        cls.objects.filter(tramite_id=tramite.id).delete()
