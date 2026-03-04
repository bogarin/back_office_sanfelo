"""
Integration tests for RBAC system.

This module contains tests for:
- End-to-end RBAC workflows
- Complete permission workflows
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client, TestCase

User = get_user_model()


class TestRBACIntegration(TestCase):
    """Integration tests for complete RBAC system."""

    multi_db = True  # Allow access to both databases

    def test_end_to_end_workflow(self) -> None:
        """Test complete end-to-end workflow with RBAC."""
        # Run setup_roles
        call_command('setup_roles', verbosity=0)

        # Verify group exists
        self.assertTrue(Group.objects.filter(name=settings.ADMINISTRADOR_GROUP_NAME).exists())

        # Access admin (should work for superuser)
        client = Client()
        superuser = User.objects.create_superuser(
            username='test_superuser',
            email='superuser@example.com',
            password='testpass123',
        )
        client.force_login(superuser)
        response = client.get('/admin/')
        self.assertEqual(response.status_code, 200)
