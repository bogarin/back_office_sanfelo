"""
Error handling tests.

This module contains tests for:
- Graceful error handling
- Setup roles error handling
"""

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase


class TestRBACErrorHandling(TestCase):
    """Test suite for graceful error handling."""

    def test_setup_roles_handles_missing_permissions(self) -> None:
        """Test that setup_roles handles missing permissions gracefully."""
        # This should not raise an exception even if some permissions don't exist
        try:
            call_command('setup_roles', verbosity=0)
        except Exception:
            self.fail('setup_roles should not raise exception for missing permissions')

        # Administrador group should be created
        self.assertTrue(Group.objects.filter(name=settings.ADMINISTRADOR_GROUP_NAME).exists())
