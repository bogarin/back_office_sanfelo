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

        # Verify groups exist
        self.assertTrue(Group.objects.filter(name=settings.ADMINISTRADOR_GROUP_NAME).exists())
        self.assertTrue(Group.objects.filter(name=settings.OPERADOR_GROUP_NAME).exists())

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

    def test_operador_access_business_apps(self) -> None:
        """Test that Operador can access business apps."""
        # Create Operador group
        operador_group, _ = Group.objects.get_or_create(name=settings.OPERADOR_GROUP_NAME)

        # Create an Operador user
        operador_user = User.objects.create_user(
            username='test_operator',
            email='operator@example.com',
            password='testpass123',
            is_staff=True,
        )
        operador_user.groups.add(operador_group)

        # Access admin (should work)
        client = Client()
        client.force_login(operador_user)
        response = client.get('/admin/')
        self.assertEqual(response.status_code, 200)
