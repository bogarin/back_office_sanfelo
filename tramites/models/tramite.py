"""
Tramite model and TramiteManager.

Maps to the external SQL table 'tramite'. The folio is auto-generated
by SQL triggers. Uses ForeignKey for catalog lookups (db_column preserves
the original column names in PostgreSQL).
"""

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Exists, OuterRef

# =============================================================================
# Custom Manager for Tramite Statistics
# =============================================================================


class TramiteManager(models.Manager):
    """Custom manager for Tramite model with optimized statistics queries.

    Provides cached methods for counting trámites by different criteria.
    Uses Django cache to avoid slow round-trip queries to external database.

    Cache strategy:
    - Default timeout: 300 seconds (5 minutes)
    - Cache key: 'tramite_stats:{statistic_name}'
    - Invalidates on tramite save/delete via signals

    Usage:
        Tramite.objects.get_statistics()
        Tramite.objects.invalidate_statistics_cache()

    Note: Uses lazy loading of AsignacionTramite to avoid circular imports.
    """

    # Cache configuration
    CACHE_TIMEOUT = getattr(settings, 'TRAMITE_STATS_CACHE_TIMEOUT', 300)  # 5 minutes default
    CACHE_KEY_PREFIX = 'tramite_stats'

    def _get_cached_count(self, key: str, queryset_func) -> int:
        """Get cached count or execute query and cache result.

        Args:
            key: Suffix for cache key (e.g., 'total', 'sin_asignar')
            queryset_func: Callable that returns a QuerySet to count

        Returns:
            int: Cached count of records
        """
        cache_key = f'{self.CACHE_KEY_PREFIX}:{key}'
        cached_value = cache.get(cache_key)

        if cached_value is not None:
            return cached_value

        # Execute query and cache result
        count = queryset_func().count()
        cache.set(cache_key, count, self.CACHE_TIMEOUT)
        return count

    def get_total_count(self) -> int:
        """Get total count of all trámites.

        Returns:
            int: Total number of trámites
        """
        return self._get_cached_count('total', self.all)

    def get_sin_asignar_count(self) -> int:
        """Get count of trámites without assignment.

        Uses lazy loading of AsignacionTramite to avoid circular imports.

        Returns:
            int: Count of unassigned trámites
        """
        # Lazy load AsignacionTramite inside lambda to avoid circular import
        return self._get_cached_count(
            'sin_asignar',
            lambda: self.annotate(
                libre=~Exists(
                    apps.get_model('buzon', 'AsignacionTramite').objects.filter(
                        tramite=OuterRef('pk')
                    )
                )
            ).filter(libre=True),
        )

    def get_asignados_count(self) -> int:
        """Get count of assigned trámites.

        Uses lazy loading of AsignacionTramite to avoid circular imports.

        Returns:
            int: Count of assigned trámites
        """
        # Lazy load AsignacionTramite inside lambda to avoid circular import
        return self._get_cached_count(
            'asignados',
            lambda: self.annotate(
                asignado=Exists(
                    apps.get_model('buzon', 'AsignacionTramite').objects.filter(
                        tramite=OuterRef('pk')
                    )
                )
            ).filter(asignado=True),
        )

    def get_finalizados_count(self) -> int:
        """Get count of finished trámites (estatus >= 300).

        Returns:
            int: Count of finished trámites
        """
        return self._get_cached_count('finalizados', lambda: self.filter(estatus_id__gte=300))

    def get_cancelados_count(self) -> int:
        """Get count of cancelled trámites (estatus = 304).

        Returns:
            int: Count of cancelled trámites
        """
        return self._get_cached_count('cancelados', lambda: self.filter(estatus_id=304))

    def get_urgentes_count(self) -> int:
        """Get count of urgent trámites.

        Returns:
            int: Count of urgent trámites
        """
        return self._get_cached_count('urgentes', lambda: self.filter(urgente=True))

    def get_pagados_count(self) -> int:
        """Get count of paid trámites.

        Returns:
            int: Count of paid trámites
        """
        return self._get_cached_count('pagados', lambda: self.filter(pagado=True))

    def get_statistics(self) -> dict:
        """Get all statistics in a single dictionary.

        This method is optimized to retrieve all counts efficiently.
        Uses caching to avoid multiple database queries.

        Returns:
            dict: Dictionary with all statistics keys
        """
        return {
            'total': self.get_total_count(),
            'sin_asignar': self.get_sin_asignar_count(),
            'asignados': self.get_asignados_count(),
            'finalizados': self.get_finalizados_count(),
            'cancelados': self.get_cancelados_count(),
            'urgentes': self.get_urgentes_count(),
            'pagados': self.get_pagados_count(),
        }

    def invalidate_statistics_cache(self) -> None:
        """Invalidate all statistics cache.

        Call this method after bulk operations that affect counts.
        Typically called from Django signals on save/delete.

        Usage:
            Tramite.objects.invalidate_statistics_cache()
        """
        # Delete all cache keys with our prefix
        cache_keys = [
            f'{self.CACHE_KEY_PREFIX}:{key}'
            for key in [
                'total',
                'sin_asignar',
                'asignados',
                'finalizados',
                'cancelados',
                'urgentes',
                'pagados',
            ]
        ]
        cache.delete_many(cache_keys)


# =============================================================================
# Tramite Model
# =============================================================================


class Tramite(models.Model):
    """Main model for tramites.

    Maps to SQL table 'tramite' from external schema.
    The folio is auto-generated by SQL triggers.

    Uses ForeignKey for catalog lookups. The db_column parameter preserves
    the original column names (id_cat_tramite, id_cat_estatus, etc.) so
    the PostgreSQL schema does not change.

    Access pattern:
        obj.tramite_catalogo      → related TramiteCatalogo instance
        obj.tramite_catalogo_id   → raw integer value (same as old id_cat_tramite)
        obj.estatus               → related TramiteEstatus instance
        obj.estatus_id            → raw integer value (same as old id_cat_estatus)
        obj.perito                → related Perito instance (nullable)
        obj.perito_id             → raw integer value (same as old id_cat_perito)
    """

    # Custom manager for statistics
    objects = TramiteManager()

    class Meta:
        managed = getattr(settings, 'TESTING', False)
        db_table = 'tramite'
        verbose_name = 'Trámite'
        verbose_name_plural = 'Trámites'
        ordering = ('-creado',)

    # Primary key
    id = models.AutoField(primary_key=True)

    # Unique folio (auto-generated by SQL trigger)
    folio = models.CharField(max_length=50, unique=True, verbose_name='Folio')

    # Foreign keys to catalog tables
    tramite_catalogo = models.ForeignKey(
        'TramiteCatalogo',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_tramite',
        related_name='tramites',
        verbose_name='Catálogo Trámite',
    )
    estatus = models.ForeignKey(
        'TramiteEstatus',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_estatus',
        default=101,
        related_name='tramites',
        verbose_name='Estatus',
    )
    perito = models.ForeignKey(
        'Perito',
        on_delete=models.DO_NOTHING,
        db_column='id_cat_perito',
        null=True,
        blank=True,
        related_name='tramites',
        verbose_name='Perito',
    )

    # Solicitant information
    clave_catastral = models.CharField(
        max_length=16, blank=True, null=True, verbose_name='Clave Catastral'
    )
    es_propietario = models.BooleanField(default=True, verbose_name='Es Propietario')
    nom_sol = models.CharField(max_length=200, verbose_name='Nombre del Solicitante')
    tel_sol = models.CharField(max_length=16, blank=True, null=True, verbose_name='Teléfono')
    correo_sol = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Correo Electrónico'
    )

    # Financial information
    importe_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Importe Total',
    )
    pagado = models.BooleanField(default=False, verbose_name='Pagado')

    # Additional information
    tipo = models.CharField(max_length=120, blank=True, null=True, verbose_name='Tipo')
    observacion = models.TextField(blank=True, null=True, verbose_name='Observación')
    urgente = models.BooleanField(default=True, null=True, blank=True, verbose_name='Urgente')

    # Timestamps (managed by SQL triggers)
    creado = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    modificado = models.DateTimeField(auto_now=True, verbose_name='Modificado')

    def __str__(self) -> str:
        return str(self.folio)

    @property
    def estatus_display(self) -> str:
        """Get display name for estatus from related TramiteEstatus."""
        if not self.estatus:
            return 'DESCONOCIDO'
        return self.estatus.estatus.replace('_', ' ')

    @property
    def tramite_display(self) -> str:
        """Get display name for tramite from related TramiteCatalogo."""
        if self.tramite_catalogo:
            return self.tramite_catalogo.nombre
        return f'ID {self.tramite_catalogo.pk}'
