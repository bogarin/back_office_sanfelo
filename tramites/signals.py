"""
Django signals for tramites app.

Handles cache invalidation for statistics when trámites are modified
or when status transitions occur via Actividades records.
"""

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import TramiteLegacy


@receiver(post_save, sender=TramiteLegacy)
def invalidate_tramite_stats_on_save(sender, instance, **kwargs):
    """
    Invalidate statistics cache after saving a tramite.

    This ensures that counts are updated when:
    - A new tramite is created
    - An existing tramite is modified (urgente, pagado, etc.)

    Args:
        sender: The model class that sent the signal
        instance: The instance that was saved
        **kwargs: Additional signal arguments
    """
    TramiteLegacy.objects.invalidate_statistics_cache()


@receiver(post_delete, sender=TramiteLegacy)
def invalidate_tramite_stats_on_delete(sender, instance, **kwargs):
    """
    Invalidate statistics cache after deleting a tramite.

    This ensures that counts are updated when a tramite is removed.

    Args:
        sender: The model class that sent the signal
        instance: The instance that was deleted
        **kwargs: Additional signal arguments
    """
    TramiteLegacy.objects.invalidate_statistics_cache()


# ---------------------------------------------------------------------------
# Actividades signals — invalidate distribution cache on status transitions
# ---------------------------------------------------------------------------


def _invalidate_distribution(sender, instance, **kwargs):
    """Invalidate only the estatus distribution cache.

    Actividades records change on every status transition but don't
    affect TramiteLegacy-level counts (total, urgente, pagado, etc.), so we
    only bust the distribution key.

    Still invalidates ``finalizados`` / ``cancelados`` since those are
    derived from estatus.
    """
    prefix = TramiteLegacy.objects.CACHE_KEY_PREFIX
    cache.delete_many(
        [
            f'{prefix}:estatus_distribution',
            f'{prefix}:finalizados',
            f'{prefix}:cancelados',
        ]
    )


@receiver(post_save, sender='tramites.Actividades')
def invalidate_on_actividades_save(sender, instance, **kwargs):
    """Invalidate estatus-derived caches when an Actividades record is saved."""
    _invalidate_distribution(sender, instance, **kwargs)


@receiver(post_delete, sender='tramites.Actividades')
def invalidate_on_actividades_delete(sender, instance, **kwargs):
    """Invalidate estatus-derived caches when an Actividades record is deleted."""
    _invalidate_distribution(sender, instance, **kwargs)
