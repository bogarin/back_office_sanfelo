"""
Django signals for tramites app.

Handles cache invalidation for statistics when trámites are modified.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Tramite


@receiver(post_save, sender=Tramite)
def invalidate_tramite_stats_on_save(sender, instance, **kwargs):
    """
    Invalidate statistics cache after saving a tramite.

    This ensures that counts are updated when:
    - A new tramite is created
    - An existing tramite is modified
    - Status changes (e.g., from pending to finished)

    Args:
        sender: The model class that sent the signal
        instance: The instance that was saved
        **kwargs: Additional signal arguments
    """
    Tramite.objects.invalidate_statistics_cache()


@receiver(post_delete, sender=Tramite)
def invalidate_tramite_stats_on_delete(sender, instance, **kwargs):
    """
    Invalidate statistics cache after deleting a tramite.

    This ensures that counts are updated when a tramite is removed.

    Args:
        sender: The model class that sent the signal
        instance: The instance that was deleted
        **kwargs: Additional signal arguments
    """
    Tramite.objects.invalidate_statistics_cache()
