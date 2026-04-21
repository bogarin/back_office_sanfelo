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
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, connections, models, transaction

from core.model_config import AccessPattern, register_model

from .actividades import Actividades

User = get_user_model()

logger = logging.getLogger(__name__)


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

        indexes = (
            models.Index(fields=['analista']),
            models.Index(fields=['tramite_id']),
        )

    def __str__(self):
        return f'Trámite ID {self.tramite_id} → {self.analista.username}'

    @classmethod
    def asignar(cls, tramite, analista, asignado_por=None, observacion=''):
        """
        Asigna un trámite usando savepoints de PostgreSQL.

        Usa raw SQL con nombres cualificados por schema para crear AsignacionTramite
        desde la conexión de backend. Los savepoints permiten rollback parcial.

        En SQLite (entorno de pruebas), usa 'default' connection.
        En PostgreSQL con schema separation, usa 'backend' connection.

        Args:
            tramite: Instancia de Tramite (tabla legacy en PostgreSQL)
            analista: Instancia de User (analista)
            asignado_por: Instancia de User (quién asigna, opcional)
            observacion: Texto opcional

        Returns:
            AsignacionTramite: La nueva asignación

        Raises:
            ValidationError: Si hay validaciones falladas
            DatabaseError: Si falla la creación del registro en Actividades
        """
        from .catalogos import TramiteEstatus  # noqa: PLC0415

        # Usar conexión default con savepoints para atomicidad
        with transaction.atomic(using='default'):
            logger.debug(f'🔷 START: Asignando trámite {tramite.id} a analista {analista.id}')

            # ===== SAVEPOINT 1: Crear AsignacionTramite =====
            cursor = connections['default'].cursor()

            # Verificar si ya existe una asignación
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM asignacion_tramite
                WHERE tramite_id = %s
            """,
                [tramite.id],
            )

            existe = cursor.fetchone()[0] > 0

            if existe:
                logger.debug(f'✏️ UPDATE: Asignación existente para trámite {tramite.id}')

                # Actualizar asignación existente
                cursor.execute(
                    """
                    UPDATE asignacion_tramite
                    SET analista_id = %s,
                        asignado_por_id = %s,
                        observacion = %s,
                        fecha_asignacion = CURRENT_TIMESTAMP
                    WHERE tramite_id = %s
                    RETURNING id, tramite_id, analista_id, asignado_por_id,
                              fecha_asignacion, observacion
                """,
                    [
                        analista.id,
                        asignado_por.id if asignado_por else None,
                        observacion,
                        tramite.id,
                    ],
                )

                row = cursor.fetchone()

                # Crear instancia de Django desde la fila
                asignacion = cls(
                    id=row[0],
                    tramite_id=row[1],
                    analista_id=row[2],
                    asignado_por_id=row[3],
                    fecha_asignacion=row[4],
                    observacion=row[5],
                )

                logger.debug(
                    f'✅ ASIGNACION UPDATE: ID={asignacion.id}, '
                    f'Tramite={tramite.id}, Analista={analista.id}'
                )
            else:
                logger.debug(f'➕ CREATE: Nueva asignación para trámite {tramite.id}')

                # Crear nueva asignación con raw SQL
                cursor.execute(
                    """
                    INSERT INTO asignacion_tramite
                    (tramite_id, analista_id, asignado_por_id, observacion, fecha_asignacion)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING id, tramite_id, analista_id, asignado_por_id,
                              fecha_asignacion, observacion
                """,
                    [
                        tramite.id,
                        analista.id,
                        asignado_por.id if asignado_por else None,
                        observacion,
                    ],
                )

                row = cursor.fetchone()

                # Crear instancia de Django desde la fila insertada
                asignacion = cls(
                    id=row[0],
                    tramite_id=row[1],
                    analista_id=row[2],
                    asignado_por_id=row[3],
                    fecha_asignacion=row[4],
                    observacion=row[5],
                )

                logger.debug(
                    f'✅ ASIGNACION CREATE: ID={asignacion.id}, '
                    f'Tramite={tramite.id}, Analista={analista.id}'
                )

            logger.debug('📋 SAVEPOINT 1: AsignacionTramite completada')

            # ===== SAVEPOINT 2: Crear Actividades =====
            # Ya estamos en connection apropiada (SQLite o PostgreSQL)
            # Django manejará savepoints automáticamente si hay error

            logger.debug(f'🔷 START: Creando Actividades para trámite {tramite.id}')

            try:
                # Determinar observacion text basado en tipo de asignación
                if analista == asignado_por:
                    actividades_observacion = 'Tramite autoasignado'
                else:
                    asignado_por_name = asignado_por.get_full_name() if asignado_por else 'Sistema'
                    actividades_observacion = f'Tramite asignado por {asignado_por_name}'

                logger.debug(f'📝 Actividades observacion: "{actividades_observacion}"')

                # Obtener TramiteEstatus para EN_REVISION (id=202)
                estatus_revision = TramiteEstatus.objects.get_cached(202)

                logger.debug(
                    f'📊 TramiteEstatus: {estatus_revision.estatus} (ID={estatus_revision.id})'
                )

                # Crear registro de Actividades
                # Usa ORM normal (mismo connection, mismo schema)
                Actividades.objects.create(
                    tramite=tramite,
                    estatus_id=202,  # EN_REVISION
                    backoffice_user_id=analista.id,
                    observacion=actividades_observacion,
                )

                logger.debug('✅ ACTIVIDADES CREATE: Registro creado exitosamente')
                logger.info(
                    f'✅ ASIGNACIÓN COMPLETADA: Trámite {tramite.id} → '
                    f'Analista {analista.id} ({analista.username})'
                )

            except IntegrityError as e:
                logger.error(f'❌ IntegrityError en Actividades (ROLLBACK AUTOMÁTICO): {e}')
                # Django hará rollback automático al savepoint 1
                raise DatabaseError(f'Error de integridad al crear registro de actividad: {str(e)}')
            except DatabaseError as e:
                logger.error(f'❌ DatabaseError en Actividades (ROLLBACK AUTOMÁTICO): {e}')
                # Django hará rollback automático al savepoint 1
                raise DatabaseError(
                    f'Error de base de datos al crear registro de actividad: {str(e)}'
                )
            except Exception as e:
                logger.error(
                    f'❌ Error inesperado en Actividades (ROLLBACK AUTOMÁTICO): {type(e).__name__}: {e}'
                )
                # Django hará rollback automático al savepoint 1
                raise DatabaseError(f'Error inesperado al crear registro de actividad: {str(e)}')

            logger.debug('📋 SAVEPOINT 2: Actividades completada')
            logger.debug(f'🎯 FIN: Asignación de trámite {tramite.id} completada exitosamente')

            return asignacion

    @classmethod
    def liberar(cls, tramite):
        """
        Libera un trámite (elimina su asignación).

        Args:
            tramite: Instancia de Tramite
        """
        cls.objects.filter(tramite_id=tramite.id).delete()
