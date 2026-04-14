"""Custom managers for read-heavy catalog tables.

Provides CachedCatalogManager — a reusable manager that caches the
entire table in process memory on first access.  Designed for small,
rarely-changing catalog tables (cat_* models) that are never written
to by Django.

Cache strategy:
    - Backend: ``functools.lru_cache`` (in-process memory).
    - Scope: Lives for the lifetime of the worker process.
    - Invalidation: Manual via ``invalidate_cache()`` or the maintenance
      URL at ``/admin/maintenance/invalidate-cache/``.  Also cleared on
      process restart (e.g. gunicorn reload).

Why not Django's cache framework?
    Catalog data is tiny (< 100 rows total across all tables) and never
    changes within Django's lifecycle.  Using ``DatabaseCache`` added a
    ``SELECT FROM cache_table`` roundtrip on every read — caching SQL
    behind SQL.  Process-level ``lru_cache`` collapses this to zero
    queries after the first call per worker.

Usage::

    from tramites.models.managers import CachedCatalogManager

    class MyCatalog(models.Model):
        objects = CachedCatalogManager()
        ...

    # Fetch all records (from process memory after first call)
    records = MyCatalog.objects.all_cached()

    # Fetch a single record by PK (from process memory)
    record = MyCatalog.objects.get_cached(42)

    # Manual invalidation (e.g. after external data load)
    MyCatalog.objects.invalidate_cache()
"""

from __future__ import annotations

from functools import lru_cache

from django.db import models


class CachedCatalogManager(models.Manager):
    """Manager for small, read-only catalog tables.

    Caches the full table contents as a Python list in process memory
    on first access.  Subsequent reads are served from the LRU cache
    — zero DB queries for the rest of the worker's lifetime.

    Not suitable for large tables (> ~500 rows) due to O(n) lookups
    and full-table materialization in memory.
    """

    def all_cached(self) -> list:
        """Return all records, cached in process memory.

        The first call per worker process fetches from PostgreSQL.
        Every subsequent call returns the cached list with zero
        queries.  Cache survives across requests until explicitly
        invalidated or the worker process restarts.

        Returns:
            list[model instance]: All records for this model.
        """
        return self._all_cached_impl()

    @lru_cache(maxsize=1)
    def _all_cached_impl(self) -> list:
        """Materialize the full table. Separated for lru_cache."""
        return list(self.all())

    def get_cached(self, pk: int):
        """Return a single record by primary key from the cached list.

        Performs a linear scan — fine for small tables (< 100 rows).

        Args:
            pk: Primary key value to look up.

        Returns:
            Model instance or ``None`` if not found.
        """
        for record in self.all_cached():
            if record.pk == pk:
                return record
        return None

    def invalidate_cache(self) -> None:
        """Clear the in-process cache for this model.

        Forces the next ``all_cached()`` call to fetch fresh data
        from PostgreSQL.  Safe to call even if nothing is cached.
        """
        self._all_cached_impl.cache_clear()
