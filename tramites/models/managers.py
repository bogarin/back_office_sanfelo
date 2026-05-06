"""Custom manager for read-heavy catalog tables.

Provides a caching manager for small, rarely-changing catalog tables:

``CachedReadOnlyManager``
    Combines ``ReadOnlyQuerySet`` (prevents all writes at the ORM level)
    with Django's cache framework for ``all_cached()`` / ``all_cached_as_dict()``.
    Ideal for models like ``Requisito`` that must be strictly read-only *and*
    benefit from caching.

Cache strategy:
    - Invalidation: Manual via ``invalidate_cache()`` or the maintenance
      URL at ``/admin/maintenance/invalidate-cache/``.

Usage::

    from tramites.models.managers import CachedReadOnlyManager

    # Django cache + read-only queryset (write-safe)
    class Requisito(models.Model):
        objects = CachedReadOnlyManager()

    # API
    records = Requisito.objects.all_cached()
    record  = Requisito.objects.get_cached(42)
    Requisito.objects.invalidate_cache()
"""

from __future__ import annotations

from django.core.cache import cache
from django.db import models

from core.managers import ReadOnlyQuerySet


class CachedReadOnlyManager(models.Manager.from_queryset(ReadOnlyQuerySet)):  # type: ignore[misc]
    """Manager combining read-only protections with Django cache.

    Inherits ``ReadOnlyQuerySet`` to prevent create/update/delete at the
    ORM level while adding ``all_cached()``, ``get_cached()``, and
    ``all_cached_as_dict()`` backed by Django's cache framework.

    Use on catalog models that must be strictly read-only *and* benefit
    from fast repeated lookups (e.g. ``Requisito`` with 28 rows).

    Cache timeout defaults to 1 hour.  Override ``CACHE_TIMEOUT`` on the
    manager or model to customise.
    """

    CACHE_TIMEOUT = 60 * 60  # 1 hour

    def _get_cache_key(self) -> str:
        """Generate cache key for this model.

        Returns:
            str: Cache key ``'sf_tramites:catalog:v1:{model_name}:all'``
        """
        return f'sf_tramites:catalog:v1:{self.model._meta.model_name}:all'

    def all_cached(self) -> list:
        """Return all records from Django cache or database.

        Returns:
            list[model instance]: All records for this model.
        """
        cached = cache.get(self._get_cache_key())
        if cached is not None:
            return cached

        objects = list(self.all())
        cache.set(self._get_cache_key(), objects, self.CACHE_TIMEOUT)
        return objects

    def get_cached(self, pk: int):
        """Return a single record by PK from cache or database.

        Args:
            pk: Primary key value.

        Returns:
            Model instance or ``None`` if not found.
        """
        for record in self.all_cached():
            if record.pk == pk:
                return record
        return None

    def all_cached_as_dict(self) -> dict[int, models.Model]:
        """Return all cached records as ``{pk: instance}`` dict.

        Provides O(1) lookups by primary key — ideal for matching
        SFTP filenames to catalog entries without per-row queries.

        Returns:
            dict[int, Model]: All records keyed by primary key.
        """
        return {obj.pk: obj for obj in self.all_cached()}

    def invalidate_cache(self) -> None:
        """Clear the Django cache for this model.

        Forces the next ``all_cached()`` call to hit the database.
        """
        cache.delete(self._get_cache_key())
