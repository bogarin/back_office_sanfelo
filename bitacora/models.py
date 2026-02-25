"""
Models for bitacora app.

Contains the Bitacora model for tracking system changes.
Note: This is a mapping to the external SQL schema - do NOT use Django migrations.
"""

from django.db import models


class Bitacora(models.Model):
    """Bitácora de movimientos del sistema.

    Tracks all modifications to tramite records and related entities.
    """

    class Meta:
        db_table = "bitacora"
        verbose_name = "Bitácora"
        verbose_name_plural = "Bitácoras"
        ordering = ["-fecha"]

    id = models.AutoField(primary_key=True)
    usuario_sis = models.CharField(max_length=20, verbose_name="Usuario Sistema")
    tipo_mov = models.CharField(max_length=20, verbose_name="Tipo de Movimiento")
    usuario_pc = models.CharField(max_length=20, verbose_name="Usuario PC")
    fecha = models.DateField(verbose_name="Fecha")
    maquina = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Máquina"
    )
    val_anterior = models.CharField(
        max_length=120, blank=True, null=True, verbose_name="Valor Anterior"
    )
    val_nuevo = models.CharField(
        max_length=120, blank=True, null=True, verbose_name="Valor Nuevo"
    )
    observaciones = models.CharField(
        max_length=220, blank=True, null=True, verbose_name="Observaciones"
    )

    def __str__(self) -> str:
        return f"{self.usuario_sis} - {self.tipo_mov} ({self.fecha})"
