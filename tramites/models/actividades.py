"""Modelo Actividades — registro transaccional por trámite.

Tracks each activity performed on a tramite, including the status change
and the user responsible.

Schema matches PostgreSQL actividades table:
- id (serial)
- id_tramite (int4)
- id_cat_estatus (int4)
- backoffice_user_id (int4, nullable)
- observacion (varchar)
- timestamp (timestamp, default=CURRENT_TIMESTAMP)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.db.models.functions import Now

from core.managers import CreateOnlyManager
from core.model_config import AccessPattern, register_model

if TYPE_CHECKING:
    from django.contrib.auth.models import User


# =============================================================================
# DTOs for SFTP file metadata + DB enrichment
# =============================================================================


@dataclass
class RequisitoFile:
    """Archivo PDF de requisito con información de SFTP y catálogo.

    DTO que combina metadata del archivo en SFTP con el nombre del
    requisito desde el catálogo en base de datos.
    """

    requisito_id: int
    requisito_nombre: str | None  # None si no existe en catálogo
    file_name: str
    size_mb: float


@dataclass
class ActividadFile:
    """Archivo PDF de actividad con información del registro actividades.

    DTO que combina metadata del archivo en SFTP con datos del
    registro de actividades desde la base de datos.
    """

    actividad_id: int
    file_name: str
    size_mb: float
    timestamp_str: str
    observacion: str | None = None
    estatus_nombre: str | None = None
    backoffice_user_id: int | None = None


@dataclass
class TimelineEntry:
    """Entrada del timeline del trámite.

    Une una actividad del historial con sus archivos adjuntos (ACT-*.pdf
    si aplica) y los documentos del ciudadano (DAU-*.pdf) solo para la
    primera actividad en estatus PENDIENTE_PAGO.
    """

    actividad: Actividades
    actividad_files: list[ActividadFile]
    requisito_files: list[RequisitoFile]
    user: User | None = None


@register_model('backend', AccessPattern.APPEND_ONLY, False)
class Actividades(models.Model):
    """
    Registro de actividades realizadas durante el trámite.

    Routed to backend database (PostgreSQL) with create-only access permissions.
    Uses CreateOnlyManager to enforce create-only behavior.

    Cada registro representa una acción realizada sobre un trámite:
    quién la hizo, qué estatus resultó, y cuándo.
    """

    objects = CreateOnlyManager()

    class Meta:
        managed = getattr(
            settings, 'TESTING', False
        )  # True for tests (SQLite), False for prod (PostgreSQL)
        db_table = 'actividades'
        verbose_name = 'Actividad de Trámite'
        verbose_name_plural = 'Actividades de Trámite'
        ordering = ['-timestamp']

    id = models.AutoField(primary_key=True)

    tramite = models.ForeignKey(
        'Tramite',
        on_delete=models.CASCADE,
        db_column='id_tramite',
        related_name='actividades',
        verbose_name='Trámite',
    )
    estatus = models.ForeignKey(
        'TramiteEstatus',
        on_delete=models.RESTRICT,
        db_column='id_cat_estatus',
        related_name='actividades',
        verbose_name='Estatus',
    )

    # Matches PostgreSQL: backoffice_user_id int4 NULL
    backoffice_user_id = models.IntegerField(
        null=True, blank=True, verbose_name='ID Usuario Backoffice'
    )

    # Matches PostgreSQL: observacion varchar(255) NULL
    observacion = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Observación'
    )

    # Matches PostgreSQL: timestamp DEFAULT CURRENT_TIMESTAMP
    # Uses db_default (Django 5.1+) so the ORM omits this field from INSERTs,
    # letting PostgreSQL evaluate DEFAULT CURRENT_TIMESTAMP at insert time.
    # The PostgreSQL session timezone is set to America/Tijuana, so
    # CURRENT_TIMESTAMP returns local time — consistent with Java apps.
    timestamp = models.DateTimeField(
        db_default=Now(),
        verbose_name='Fecha/Hora',
        editable=False,
    )

    def __str__(self) -> str:
        return f'Actividad {self.id} - Trámite {self.tramite_id}'
