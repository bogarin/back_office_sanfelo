"""
Tramite model and TramiteManager.

Maps to the external SQL table 'tramite'. The folio is auto-generated
by SQL triggers. Uses ForeignKey for catalog lookups (db_column preserves
the original column names in PostgreSQL).
"""

import logging

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, models
from django.db.models import Case, Count, IntegerField, OuterRef, Subquery, Sum, Value, When

from core.managers import ReadOnlyManager
from core.model_config import AccessPattern, register_model
from tramites.exceptions import EstadoNoPermitidoError, TramiteNoAsignableError
from tramites.models.actividades import Actividades
from tramites.models.catalogos import TramiteEstatus

# =============================================================================
# Custom Manager for Tramite Statistics
# =============================================================================


class TramiteLegacyManager(models.Manager):
    """Custom manager for TramiteLegacy model with optimized statistics queries.

    Provides cached methods for counting trámites by different criteria.
    Uses Django cache to avoid slow round-trip queries to external database.

    Cache strategy:
    - Default timeout: 300 seconds (5 minutes)
    - Cache key: 'tramite_stats:{statistic_name}'
    - Invalidates on tramite save/delete via signals

    Usage:
        TramiteLegacy.objects.get_statistics()
        TramiteLegacy.objects.invalidate_statistics_cache()

    Note: Uses lazy loading of AsignacionTramite to avoid circular imports.
    """

    # Cache configuration
    CACHE_TIMEOUT = getattr(settings, 'TRAMITE_STATS_CACHE_TIMEOUT', 300)  # 5 minutes default
    CACHE_TIMEOUT_DISTRIBUTION = getattr(
        settings, 'TRAMITE_DISTRIBUTION_CACHE_TIMEOUT', 60
    )  # 1 minute — more volatile
    CACHE_KEY_PREFIX = 'tramite_stats'

    def with_estatus(self):
        """Annotate queryset with estatus_id from latest Actividades.

        Uses a subquery to find the id_cat_estatus of the Actividades
        record with the highest timestamp for each TramiteLegacy.

        Cross-database safe: annotates only integer IDs, no FK joins
        across databases.

        Returns:
            QuerySet[TramiteLegacy]: Annotated with ``_estatus_id``
        """

        # Import Actividades model directly to avoid apps.get_model() issues
        # Lazy import to avoid circular import at module level
        from tramites.models.actividades import Actividades

        # Create subquery: get estatus_id from latest Actividades record
        # for each tramite (highest timestamp)
        subquery = Subquery(
            Actividades.objects.filter(tramite=OuterRef('pk'))
            .order_by('-timestamp')
            .values_list('estatus_id')[:1]
        )

        return self.annotate(_estatus_id=subquery)

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

    def _get_asignados_count(self) -> int:
        """Count assigned trámites via a simple COUNT on AsignacionTramite.

        ``AsignacionTramite`` has a ``UniqueConstraint(fields=['tramite'])``,
        so one row = one assigned tramite.  A plain ``COUNT(*)`` is far
        cheaper than a correlated ``EXISTS`` subquery on the ``tramite`` table.
        """
        return apps.get_model('tramites', 'AsignacionTramite').objects.count()

    def get_asignados_count(self) -> int:
        """Get count of assigned trámites (cached).

        Returns:
            int: Count of assigned trámites
        """
        return self._get_cached_count('asignados', self._get_asignados_count)

    def get_sin_asignar_count(self) -> int:
        """Get count of trámites without assignment.

        Derived as ``total - asignados`` to avoid a second correlated subquery.

        Returns:
            int: Count of unassigned trámites
        """
        cache_key = f'{self.CACHE_KEY_PREFIX}:sin_asignar'
        cached_value = cache.get(cache_key)

        if cached_value is not None:
            return cached_value

        count = self.get_total_count() - self.get_asignados_count()
        cache.set(cache_key, count, self.CACHE_TIMEOUT)
        return count

    def get_finalizados_count(self) -> int:
        """Get count of finished trámites (estatus >= 300).

        Derives estatus from the latest Actividades record via Subquery.

        Returns:
            int: Count of finished trámites
        """
        return self._get_cached_count(
            'finalizados', lambda: self.with_estatus().filter(_estatus_id__gte=300)
        )

    def get_cancelados_count(self) -> int:
        """Get count of cancelled trámites (estatus = 304).

        Derives estatus from the latest Actividades record via Subquery.

        Returns:
            int: Count of cancelled trámites
        """
        return self._get_cached_count(
            'cancelados', lambda: self.with_estatus().filter(_estatus_id=304)
        )

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

    def get_estatus_distribution(self) -> list[tuple[int, str, int]]:
        """Get count of trámites grouped by estatus, cached with a shorter TTL.

        Returns a list of ``(estatus_id, estatus_name, count)`` tuples sorted
        by ``estatus_id``.  Because estatus is derived from ``Actividades``
        records (which change on every status transition), this cache uses a
        shorter timeout than the other statistics.

        Returns:
            list[tuple[int, str, int]]: Estatus distribution data.
        """
        cache_key = f'{self.CACHE_KEY_PREFIX}:estatus_distribution'
        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        subquery = Subquery(
            Actividades.objects.filter(tramite=OuterRef('pk'))
            .order_by('-timestamp')
            .values_list('estatus_id')[:1]
        )
        raw_distribution = (
            self.annotate(_estatus_id=subquery)
            .values('_estatus_id')
            .annotate(total=Count('id'))
            .order_by('_estatus_id')
        )

        # Resolve estatus names from in-process catalog cache (zero DB queries)
        all_estatus = {e.id: e.estatus for e in TramiteEstatus.objects.all_cached()}

        distribution = [
            (cat_id, all_estatus.get(cat_id, f'ID {cat_id}'), total)
            for cat_id, total in raw_distribution.values_list('_estatus_id', 'total')
        ]

        cache.set(cache_key, distribution, self.CACHE_TIMEOUT_DISTRIBUTION)
        return distribution

    def _compute_consolidated_stats(self) -> dict:
        """Run a single GROUP BY query with conditional aggregation.

        Produces ``total``, ``finalizados``, ``cancelados``, ``urgentes``,
        ``pagados``, and ``estatus_distribution`` in **one** round-trip to
        PostgreSQL.  ``asignados`` is fetched separately (cheap COUNT on a
        small table) and ``sin_asignar`` is derived as ``total - asignados``.

        Returns:
            dict: All stat keys ready for caching and returning.
        """

        subquery = Subquery(
            Actividades.objects.filter(tramite=OuterRef('pk'))
            .order_by('-timestamp')
            .values_list('estatus_id')[:1]
        )
        rows = list(
            self.annotate(_estatus_id=subquery)
            .values('_estatus_id')
            .annotate(
                total=Count('id'),
                urgentes=Sum(
                    Case(
                        When(urgente=True, then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ),
                pagados=Sum(
                    Case(
                        When(pagado=True, then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ),
            )
            .order_by('_estatus_id')
        )

        # Resolve estatus names from in-process catalog cache (zero DB queries)
        all_estatus = {e.id: e.estatus for e in TramiteEstatus.objects.all_cached()}

        distribution = [
            (
                row['_estatus_id'],
                all_estatus.get(row['_estatus_id'], f'ID {row["_estatus_id"]}'),
                row['total'],
            )
            for row in rows
        ]

        total = sum(r['total'] for r in rows)
        finalizados = sum(r['total'] for r in rows if (r['_estatus_id'] or 0) >= 300)
        cancelados = sum(r['total'] for r in rows if r['_estatus_id'] == 304)
        urgentes = sum(r['urgentes'] for r in rows)
        pagados = sum(r['pagados'] for r in rows)

        # Cheap separate query on a small table
        asignados = self._get_asignados_count()
        sin_asignar = total - asignados

        return {
            'total': total,
            'sin_asignar': sin_asignar,
            'asignados': asignados,
            'finalizados': finalizados,
            'cancelados': cancelados,
            'urgentes': urgentes,
            'pagados': pagados,
            'estatus_distribution': distribution,
        }

    # Stat key names managed by get_statistics()
    _STAT_KEYS = (
        'total',
        'sin_asignar',
        'asignados',
        'finalizados',
        'cancelados',
        'urgentes',
        'pagados',
    )

    def get_statistics(self) -> dict:
        """Get all statistics, using bulk cache read and a single query on miss.

        On a warm hit, reads all 7 stat keys with one ``cache.get_many()``
        call (zero SQL).  On a cold hit, runs **one** consolidated GROUP BY
        query with conditional aggregation plus one cheap
        ``AsignacionTramite.objects.count()``, then caches each key
        individually so that individual ``get_X_count()`` methods also benefit.

        Returns:
            dict: Dictionary with all statistics keys.
        """
        keys_to_check = [f'{self.CACHE_KEY_PREFIX}:{k}' for k in self._STAT_KEYS]
        cached = cache.get_many(keys_to_check)

        # All 7 keys present → return immediately
        if len(cached) == len(keys_to_check):
            return {k: cached[f'{self.CACHE_KEY_PREFIX}:{k}'] for k in self._STAT_KEYS}

        # Cold hit — one consolidated query
        stats = self._compute_consolidated_stats()

        # Cache each stat key individually (300s) so get_X_count() methods hit
        for key in self._STAT_KEYS:
            cache.set(
                f'{self.CACHE_KEY_PREFIX}:{key}',
                stats[key],
                self.CACHE_TIMEOUT,
            )

        # Cache distribution with shorter TTL
        cache.set(
            f'{self.CACHE_KEY_PREFIX}:estatus_distribution',
            stats['estatus_distribution'],
            self.CACHE_TIMEOUT_DISTRIBUTION,
        )

        return {k: stats[k] for k in self._STAT_KEYS}

    def invalidate_statistics_cache(self, include_distribution: bool = True) -> None:
        """Invalidate all statistics cache.

        Call this method after bulk operations that affect counts.
        Typically called from Django signals on save/delete.

        Args:
            include_distribution: Also invalidate the estatus distribution
                cache.  Set to ``False`` when only non-status counts changed
                (e.g., ``urgente`` or ``pagado`` toggle).
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

        if include_distribution:
            cache_keys.append(f'{self.CACHE_KEY_PREFIX}:estatus_distribution')

        cache.delete_many(cache_keys)


# =============================================================================
# Tramite Model
# =============================================================================


@register_model('backend', AccessPattern.READ_ONLY, False)
class TramiteLegacy(models.Model):
    """Main model for tramites (legacy).

    Maps to SQL table 'tramite' from external schema.
    The folio is auto-generated by SQL triggers.

    Uses ForeignKey for catalog lookups. The db_column parameter preserves
    the original column names (id_cat_tramite, id_cat_perito, etc.) so
    the PostgreSQL schema does not change.

    The ``estatus`` is derived from the latest ``Actividades`` record
    (highest ``secuencia``) via properties. Use ``TramiteLegacy.objects.with_estatus()``
    to annotate ``_estatus_id`` on querysets for efficient filtering.

    Access pattern:
        obj.tramite_catalogo      → related TramiteCatalogo instance
        obj.tramite_catalogo_id   → raw integer value (same as old id_cat_tramite)
        obj.estatus               → TramiteEstatus instance (from latest Actividades)
        obj.estatus_id            → raw integer value (from latest Actividades)
        obj.perito                → related Perito instance (nullable)
        obj.perito_id             → raw integer value (same as old id_cat_perito)
    """

    # Custom manager for statistics (replaced with ReadOnlyManager for read-only enforcement)
    # objects = TramiteLegacyManager()
    objects = ReadOnlyManager()

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
    def estatus_id(self) -> int | None:
        """Return the estatus ID from the latest Actividades record.

        Checks for an annotated ``_estatus_id`` first (set by
        ``TramiteManager.with_estatus()``) to avoid extra queries.
        Falls back to querying Actividades directly.

        Returns:
            int | None: The cat_estatus ID, or None if no activities exist.
        """
        # Use annotated value if available (avoids extra query).
        # hasattr distinguishes "annotated as None" (trámite has no
        # activities) from "not annotated at all" (needs fallback query).
        if hasattr(self, '_estatus_id'):
            return self._estatus_id

        # Fallback: query latest Actividades (ordered by timestamp desc)
        latest = self.actividades.order_by('-timestamp').values('estatus_id').first()
        return latest['estatus_id'] if latest else None

    @property
    def estatus(self):
        """Return the TramiteEstatus instance from the latest Actividades.

        Uses ``TramiteEstatus.objects.get_cached()`` to avoid repeated
        DB queries on read-only catalog data.

        Returns:
            TramiteEstatus | None: The estatus object, or None if no activities.
        """
        estatus_id = self.estatus_id
        if estatus_id is None:
            return None
        return TramiteEstatus.objects.get_cached(estatus_id)

    @property
    def estatus_display(self) -> str:
        """Get display name for estatus from latest Actividades."""
        estatus_obj = self.estatus
        if not estatus_obj:
            return 'DESCONOCIDO'
        return estatus_obj.estatus.replace('_', ' ')

    @property
    def tramite_display(self) -> str:
        """Get display name for tramite from related TramiteCatalogo."""
        if self.tramite_catalogo:
            return self.tramite_catalogo.nombre
        return f'ID {self.tramite_catalogo.pk}'

    @property
    def creado_formatted(self) -> str:
        """Format creado timestamp as YYYY-MM-DD HH:MM AM/PM."""
        return self.creado.strftime('%Y-%m-%d %I:%M %p')


# =============================================================================
# Tramite Model (Unificado - Nuevo)
# =============================================================================

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

    @property
    def requisitos(self):
        """
        Retorna la lista de requisitos asociados a este trámite.
        """
        return []

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
            # Verificar que el trámite esté activo
            if not TramiteEstatus.Estatus.es_activo(self.ultima_actividad_estatus_id):
                msg = f'El usuario {asignado_por.username} intento liberar el tramite {self.folio} '
                msg += f'pero el tramite no se encuentra en un estatus asignable (estatus actual: {self.ultima_actividad_estatus_id})'

                logger.warning(msg)
                raise TramiteNoAsignableError(
                    f'El trámite {self.folio} no se puede liberar ya que no se encuentra activo'
                )

            # Determinar observación si no se provee
            if not observacion:
                observacion = f'Trámite liberado por {asignado_por.get_full_name()}'

            # Registrar actividad con estatus PRESENTADO (201) al liberar
            _ = self.registrar_actividad(
                TramiteEstatus.Estatus.PRESENTADO, analista_id=None, observacion=observacion
            )
            logger.info(f'Trámite {self.folio} liberado por {asignado_por.username}')
            return

        # Asignación/Reasignación normal
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
    """Modelo proxy para implementar el admin de buzon de tramites para el Analista."""

    class Meta:
        proxy = True
        verbose_name = 'Mis trámites'
        verbose_name_plural = 'Buzón de trámites'
        ordering = ('-creado', '-urgente')


class Disponible(Tramite):
    """Modelo proxy para implementar el admin de tramites disponibles para el Analista."""

    class Meta:
        proxy = True
        verbose_name = 'Tramite disponible para autoasignación'
        verbose_name_plural = 'Trámites disponibles'
        ordering = ('-creado', '-urgente')
