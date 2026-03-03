"""
Tests for AuditTrailMixin.

This module contains tests for:
- Audit trail logging functionality
- Async background task enqueuing
- User information extraction
"""

from datetime import date
from unittest.mock import Mock, patch

from django.contrib import admin
from django.http import HttpRequest
from django.test import TestCase

from core.admin import AuditTrailMixin


class TestAuditTrailMixin(TestCase):
    """Test suite for AuditTrailMixin with async background tasks."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        try:
            from catalogos.models import CatTramite

            # Create a ModelAdmin with AuditTrailMixin
            class TestModelAdmin(AuditTrailMixin, admin.ModelAdmin):
                pass

            self.model_admin = TestModelAdmin(CatTramite, admin.site)  # type: ignore
        except ImportError:
            self.skipTest('Business models not available')

    def test_extract_user_info(self) -> None:
        """Test extraction of user information from request."""
        # Create a mock HTTP request
        request = HttpRequest()
        request.user = type('User', (), {'username': 'testuser'})()
        request.META = {'REMOTE_ADDR': '127.0.0.1', 'REMOTE_HOST': 'localhost'}

        username, remote_addr, remote_host = self.model_admin._extract_user_info(request)

        self.assertEqual(username, 'testuser')
        self.assertEqual(remote_addr, '127.0.0.1')
        self.assertEqual(remote_host, 'localhost')

    def test_save_model_logs_update(self) -> None:
        """Test that save_model enqueues audit log for updates."""
        # Create a mock request
        request = HttpRequest()
        request.user = type('User', (), {'username': 'testuser'})()
        request.META = {'REMOTE_ADDR': '127.0.0.1', 'REMOTE_HOST': 'localhost'}

        # Create a mock object
        obj = Mock()
        obj.__str__ = Mock(return_value='Test Tramite')

        # Mock the log_audit_entry_async task
        with patch('core.admin.log_audit_entry_async') as mock_log_task:
            mock_log_task.enqueue.return_value = None

            # Mock parent save_model to avoid actual DB operations
            with patch.object(self.model_admin.__class__.__bases__[1], 'save_model'):
                self.model_admin.save_model(request, obj, Mock(), change=True)

            # Verify task was enqueued
            self.assertTrue(mock_log_task.enqueue.called)

    def test_delete_model_logs_deletion(self) -> None:
        """Test that delete_model enqueues audit log for deletions."""
        # Create a mock request
        request = HttpRequest()
        request.user = type('User', (), {'username': 'testuser'})()
        request.META = {'REMOTE_ADDR': '127.0.0.1', 'REMOTE_HOST': 'localhost'}

        # Create a mock object
        obj = Mock()
        obj.__str__ = Mock(return_value='Test Tramite')

        # Mock the log_audit_entry_async task
        with patch('core.admin.log_audit_entry_async') as mock_log_task:
            mock_log_task.enqueue.return_value = None

            # Mock parent delete_model to avoid actual DB operations
            with patch.object(self.model_admin.__class__.__bases__[1], 'delete_model'):
                self.model_admin.delete_model(request, obj)

            # Verify task was enqueued
            self.assertTrue(mock_log_task.enqueue.called)

    def test_audit_task_enqueued_with_correct_params(self) -> None:
        """Test that audit task is enqueued with correct parameters."""
        # Create a mock request
        request = HttpRequest()
        request.user = type('User', (), {'username': 'testuser'})()
        request.META = {'REMOTE_ADDR': '127.0.0.1', 'REMOTE_HOST': 'localhost'}

        # Mock the log_audit_entry_async task
        with patch('core.admin.log_audit_entry_async') as mock_log_task:
            mock_log_task.enqueue.return_value = None

            self.model_admin._enqueue_audit_log(
                request=request,
                action_type='UPDATE',
                observaciones='Test observation',
                val_anterior='old_value',
                val_nuevo='new_value',
            )

            # Verify task was enqueued
            self.assertTrue(mock_log_task.enqueue.called)

            # Verify correct parameters
            call_kwargs = mock_log_task.enqueue.call_args.kwargs
            self.assertEqual(call_kwargs['usuario_sis'], 'testuser')
            self.assertEqual(call_kwargs['tipo_mov'], 'UPDATE')
            self.assertEqual(call_kwargs['observaciones'], 'Test observation')
            self.assertEqual(call_kwargs['val_anterior'], 'old_value')
            self.assertEqual(call_kwargs['val_nuevo'], 'new_value')
            self.assertEqual(call_kwargs['usuario_pc'], '127.0.0.1')
            self.assertEqual(call_kwargs['maquina'], 'localhost')
            self.assertEqual(call_kwargs['fecha'], date.today())
