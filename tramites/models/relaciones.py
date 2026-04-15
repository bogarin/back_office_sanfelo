"""Tablas pivote (many-to-many) entre modelos de catálogo.

These represent the relationships between TramiteCatalogo and other
catalog tables. They use ForeignKey instead of raw IntegerField IDs.

All models in this file are routed to the 'backend' database with
read-only access.
"""

from django.db import models

from core.model_config import register_model, AccessPattern
from core.managers import ReadOnlyManager


@register_model('backend', AccessPattern.READ_ONLY, False)
class TramiteCatalogoCategoria(models.Model):
    """Relación entre tipos de trámite y categorías.

    Many-to-Many: TramiteCatalogo ↔ Categoria

    Routed to backend database with read-only access.
    """

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'rel_tmt_categoria'
        verbose_name = 'Relación Trámite-Categoría'
        verbose_name_plural = 'Relaciones Trámite-Categoría'

    id = models.AutoField(primary_key=True)
    tramite_catalogo = models.ForeignKey(
        'TramiteCatalogo',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_tramite',
        related_name='categorias',
        verbose_name='Catálogo Trámite',
    )
    categoria = models.ForeignKey(
        'Categoria',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_categoria',
        related_name='tramites_catalogo',
        verbose_name='Categoría',
    )

    def __str__(self) -> str:
        return f'Trámite {self.tramite_catalogo_id} - Categoría {self.categoria_id}'


@register_model('backend', AccessPattern.READ_ONLY, False)
class TramiteCatalogoRequisito(models.Model):
    """Relación entre tipos de trámite, requisitos y categorías.

    Many-to-Many: TramiteCatalogo ↔ Requisito ↔ Categoria (optional)

    Routed to backend database with read-only access.
    """

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'rel_tmt_cate_req'
        verbose_name = 'Relación Trámite-Requisito-Categoría'
        verbose_name_plural = 'Relaciones Trámite-Requisito-Categoría'

    id = models.AutoField(primary_key=True)
    tramite_catalogo = models.ForeignKey(
        'TramiteCatalogo',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_tramite',
        related_name='requisitos',
        verbose_name='Catálogo Trámite',
    )
    requisito = models.ForeignKey(
        'Requisito',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_requisito',
        related_name='tramites_catalogo',
        verbose_name='Requisito',
    )
    categoria = models.ForeignKey(
        'Categoria',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_categoria',
        null=True,
        blank=True,
        related_name='requisitos_por_tramite',
        verbose_name='Categoría',
    )

    def __str__(self) -> str:
        return f'Trámite {self.tramite_catalogo_id} - Requisito {self.requisito_id}'


@register_model('backend', AccessPattern.READ_ONLY, False)
class TramiteCatalogoTipoRequisito(models.Model):
    """Relación entre tipos, trámites y requisitos.

    Many-to-Many: Tipo ↔ TramiteCatalogo ↔ Requisito

    Routed to backend database with read-only access.
    """

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'rel_tmt_tipo_req'
        verbose_name = 'Relación Tipo-Trámite-Requisito'
        verbose_name_plural = 'Relaciones Tipo-Trámite-Requisito'

    id = models.AutoField(primary_key=True)
    tipo = models.ForeignKey(
        'Tipo',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_tipo',
        related_name='requisitos_por_tramite',
        verbose_name='Tipo',
    )
    tramite_catalogo = models.ForeignKey(
        'TramiteCatalogo',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_tramite',
        related_name='tipos_requisito',
        verbose_name='Catálogo Trámite',
    )
    requisito = models.ForeignKey(
        'Requisito',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_requisito',
        related_name='tipos_por_tramite',
        verbose_name='Requisito',
    )

    def __str__(self) -> str:
        return (
            f'Tipo {self.tipo_id} - '
            f'Trámite {self.tramite_catalogo_id} - '
            f'Requisito {self.requisito_id}'
        )


@register_model('backend', AccessPattern.READ_ONLY, False)
class TramiteCatalogoActividad(models.Model):
    """Relación entre tipos de trámite y actividades.

    Many-to-Many: TramiteCatalogo ↔ Actividad

    Routed to backend database with read-only access.
    """

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'rel_tmt_actividad'
        verbose_name = 'Relación Trámite-Actividad'
        verbose_name_plural = 'Relaciones Trámite-Actividad'

    id = models.AutoField(primary_key=True)
    tramite_catalogo = models.ForeignKey(
        'TramiteCatalogo',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_tramite',
        related_name='actividades',
        verbose_name='Catálogo Trámite',
    )
    actividad = models.ForeignKey(
        'Actividad',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_actividad',
        related_name='tramites_catalogo',
        verbose_name='Actividad',
    )

    def __str__(self) -> str:
        return f'Trámite {self.tramite_catalogo_id} - Actividad {self.actividad_id}'
