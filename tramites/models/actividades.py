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

from django.conf import settings
from django.db import models

from core.managers import CreateOnlyManager
from core.model_config import AccessPattern, register_model


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
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Fecha/Hora')

    def __str__(self) -> str:
        return f'Actividad {self.id} - Trámite {self.tramite_id}'
