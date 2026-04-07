"""Modelo Actividades — registro transaccional por trámite.

Tracks each activity performed on a tramite, including the status change
and the user responsible.
"""

from django.db import models


class Actividades(models.Model):
    """Registro de actividades realizadas durante el trámite.

    Cada registro representa una acción realizada sobre un trámite:
    quién la hizo, qué actividad fue, qué estatus resultó, y cuándo.
    """

    class Meta:
        managed = True
        db_table = 'actividades'
        verbose_name = 'Actividad de Trámite'
        verbose_name_plural = 'Actividades de Trámite'
        ordering = ['-secuencia']

    id = models.AutoField(primary_key=True)

    tramite = models.ForeignKey(
        'Tramite',
        on_delete=models.DO_NOTHING,
        db_column='id_tramite',
        related_name='actividades',
        verbose_name='Trámite',
    )
    actividad = models.ForeignKey(
        'Actividad',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_actividad',
        related_name='registros',
        verbose_name='Actividad',
    )
    estatus = models.ForeignKey(
        'TramiteEstatus',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_estatus',
        related_name='actividades',
        verbose_name='Estatus',
    )

    # IntegerField because User lives in SQLite (cross-database)
    id_cat_usuario = models.IntegerField(verbose_name='ID Usuario')

    fecha_inicio = models.DateField(verbose_name='Fecha Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha Fin')
    secuencia = models.IntegerField(verbose_name='Secuencia')
    observacion = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Observación'
    )

    def __str__(self) -> str:
        return f'Actividad {self.id} - Trámite {self.tramite_id}'
