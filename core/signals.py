"""Signal handlers for the core app."""

import logging

from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def setup_roles(sender, **kwargs):
    """Setup roles and permissions after database migrations."""
    try:
        call_command('setup_roles')
    except Exception as e:
        logger.error(f'Error setting up roles: {e}')
