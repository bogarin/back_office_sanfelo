"""
Models for costos app.

Contains the Costo and Uma models for tracking procedure costs and UMA value.
Note: This is a mapping to the external SQL schema - do NOT use Django migrations.
"""

import decimal

from django.db import models


class Costo(models.Model):
    """Costo asociado a un trámite.

    Represents the cost structure for different tramite types,
    including formulas, ranges, and special contributions.
    """

    class Meta:
        managed = False
        db_table = "costo"
        verbose_name = "Costo"
        verbose_name_plural = "Costos"
        ordering = ["id_tramite", "rango_ini"]

    id = models.AutoField(primary_key=True)
    id_tramite = models.IntegerField(verbose_name="ID Trámite")
    axo = models.IntegerField(default=2020, verbose_name="Año")
    descripcion = models.CharField(max_length=255, verbose_name="Descripción")
    formula = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Fórmula"
    )
    cant_umas = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Cantidad de UMA",
    )
    rango_ini = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Rango Inicial",
    )
    rango_fin = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Rango Final",
    )
    inciso = models.IntegerField(blank=True, null=True, verbose_name="Inciso")
    fomento = models.BooleanField(default=True, verbose_name="Fomento")
    cruz_roja = models.DecimalField(
        max_digits=10, decimal_places=4, default=0, verbose_name="Cruz Roja"
    )
    bomberos = models.DecimalField(
        max_digits=10, decimal_places=4, default=0, verbose_name="Bomberos"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    id_usuario = models.IntegerField(verbose_name="ID Usuario")
    fecha_actualiza = models.DateField(verbose_name="Fecha de Actualización")
    observacion = models.CharField(
        max_length=600, blank=True, null=True, verbose_name="Observación"
    )
    id_tipo = models.IntegerField(blank=True, null=True, verbose_name="ID Tipo")

    def __str__(self) -> str:
        return f"{self.descripcion} ({self.id_tramite})"


class Uma(models.Model):
    """Valor de la UMA (Unidad de Medida y Actualización).

    This table maintains a single record with the current UMA value.
    Use the stored procedure sp_actualizar_uma() to update the value.
    """

    class Meta:
        managed = False
        db_table = "uma"
        verbose_name = "UMA"
        verbose_name_plural = "UMAs"

    id = models.AutoField(primary_key=True)
    valor = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Valor")

    def __str__(self) -> str:
        return f"UMA: ${self.valor}"

    @classmethod
    def get_current_uma(cls) -> decimal.Decimal:
        """Get the current UMA value.

        Returns:
            The current UMA value as Decimal, or None if not set.

        Raises:
            Costo.DoesNotExist: If no UMA record exists.
        """
        try:
            return cls.objects.get(id=1).valor
        except cls.DoesNotExist:
            return None

    @classmethod
    def update_uma(cls, valor: decimal.Decimal) -> None:
        """Update the UMA value using the stored procedure.

        Args:
            valor: New UMA value to set.

        Note:
            This executes the PostgreSQL stored procedure sp_actualizar_uma().
        """
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("CALL sp_actualizar_uma(%s)", [valor])
