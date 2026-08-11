"""Tests for transaction atomicity in role and user management operations.

These tests verify that multi-step database operations are properly wrapped
in transaction.atomic() so that partial writes are rolled back on failure.

AUDIT-002, Block 3: transaction.atomic() enforcement.
"""

from unittest.mock import patch

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages.storage.cookie import CookieStorage
from django.db import IntegrityError
from django.test import RequestFactory

from core.rbac.constants import BackOfficeRole
from core.views import asignar_rol
from tramites.models import Tramite
from tramites.models.catalogos import TramiteEstatus

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_model_admin():
    """Return the BackofficeUserAdmin instance registered in the admin site."""
    return admin.site._registry[User]


def _build_post_request(user, data=None):
    """Build a minimal POST request with the given user and data."""
    factory = RequestFactory()
    request = factory.post('/', data or {})
    request.user = user
    request._messages = CookieStorage(request)
    request.session = {}
    return request


def _ensure_groups_exist():
    """Ensure all BackOfficeRole groups exist in the database."""
    for role in BackOfficeRole:
        Group.objects.get_or_create(name=role)


# ---------------------------------------------------------------------------
# 1. save_model rollback tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_save_model_rollback_on_group_add_failure(superuser):
    """If group assignment fails after save, is_staff must be rolled back.

    save_model does:
      1. Set is_staff=True on the instance
      2. Call super().save_model() → persists is_staff=True to DB
      3. Remove old RBAC groups
      4. Add new RBAC group → Group.objects.filter(name=role).first()

    If step 4 fails (e.g. DB error), steps 1-3 must be rolled back.
    """
    _ensure_groups_exist()

    user = User.objects.create_user(
        username='atomic_test_user',
        password='testpass123',
        is_staff=False,
    )
    assert user.is_staff is False

    form = type(
        'MockForm',
        (),
        {
            'cleaned_data': {'role': BackOfficeRole.ANALISTA},
        },
    )()
    model_admin = _get_model_admin()
    request = _build_post_request(superuser)

    # Make Group.objects.filter(name=role).first() return None AND then
    # raise when groups.add is called. We patch at the queryset level
    # to simulate a DB failure after the user has been saved.
    with patch(
        'core.admin.Group.objects.filter',
        side_effect=IntegrityError('DB connection lost'),
    ):
        try:
            model_admin.save_model(request, user, form, change=True)
        except IntegrityError:
            pass  # Expected — what matters is the rollback

    user.refresh_from_db()
    # Without transaction.atomic(), is_staff=True (partial write from step 2)
    # With transaction.atomic(), is_staff=False (full rollback)
    assert user.is_staff is False, (
        'save_model left is_staff=True after Group lookup failed — '
        'partial write not rolled back. Wrap in transaction.atomic().'
    )


@pytest.mark.django_db
def test_save_model_happy_path_unchanged(superuser):
    """Verify normal save_model still works correctly after adding atomic."""
    _ensure_groups_exist()

    user = User.objects.create_user(
        username='atomic_happy_test',
        password='testpass123',
        is_staff=False,
    )

    form = type(
        'MockForm',
        (),
        {
            'cleaned_data': {'role': BackOfficeRole.ANALISTA},
        },
    )()
    model_admin = _get_model_admin()
    request = _build_post_request(superuser)

    model_admin.save_model(request, user, form, change=True)

    user.refresh_from_db()
    assert user.is_staff is True
    assert user.groups.filter(name=BackOfficeRole.ANALISTA).exists()


# ---------------------------------------------------------------------------
# 2. asignar_rol view rollback tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_asignar_rol_rollback_on_save_failure(superuser):
    """If user.save() fails mid-batch, no users should be modified."""
    _ensure_groups_exist()

    user1 = User.objects.create_user(
        username='batch_user_1',
        password='testpass123',
        is_staff=False,
    )
    user2 = User.objects.create_user(
        username='batch_user_2',
        password='testpass123',
        is_staff=False,
    )

    # Pre-assign a role to user1 so we can verify rollback
    group = Group.objects.get(name=BackOfficeRole.COORDINADOR)
    user1.groups.add(group)
    user1.is_staff = True
    user1.save()

    # Store original save counts
    original_user1_staff = user1.is_staff
    original_user1_groups = set(user1.groups.values_list('name', flat=True))

    # Prepare request simulating the view's POST path
    request = _build_post_request(
        superuser,
        data={
            'role': BackOfficeRole.ANALISTA,
        },
    )
    request.session['selected_user_ids'] = [user1.pk, user2.pk]

    # Mock user.save() to fail on second call
    original_save = User.save
    call_count = 0

    def failing_save(user_instance, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception('DB connection lost on second user')
        return original_save(user_instance, *args, **kwargs)

    with patch.object(User, 'save', failing_save):
        try:
            asignar_rol(request)
        except Exception:
            pass  # Expected

    user1.refresh_from_db()
    user2.refresh_from_db()

    # Without atomicity, user1 was already saved but user2 wasn't
    assert user1.is_staff == original_user1_staff, (
        'asignar_rol partially modified user1 before failing on user2 — needs transaction.atomic().'
    )
    assert set(user1.groups.values_list('name', flat=True)) == original_user1_groups, (
        'asignar_rol partially modified user1 groups before failing — needs transaction.atomic().'
    )
    assert user2.is_staff is False, 'user2 should remain unmodified after rollback'


@pytest.mark.django_db
def test_asignar_rol_happy_path_unchanged(superuser):
    """Verify normal asignar_rol still works after adding atomic."""
    _ensure_groups_exist()

    user = User.objects.create_user(
        username='batch_happy_user',
        password='testpass123',
        is_staff=False,
    )

    request = _build_post_request(
        superuser,
        data={
            'role': BackOfficeRole.ANALISTA,
        },
    )
    request.session['selected_user_ids'] = [user.pk]

    asignar_rol(request)

    user.refresh_from_db()
    assert user.is_staff is True
    assert user.groups.filter(name=BackOfficeRole.ANALISTA).exists()
    assert user.is_superuser is False


# ---------------------------------------------------------------------------
# 3. modificar_asignacion rollback tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_batch_assign_partial_failure_reports_errors(superuser):
    """When some trámites fail in batch, errors are reported via messages."""

    model_admin = admin.site._registry.get(Tramite)
    if model_admin is None:
        pytest.skip('Tramite not registered in admin')

    analista = User.objects.create_user(
        username='batch_analista',
        password='testpass123',
    )

    # Build two trámites in memory
    tramite1 = Tramite(
        id=100,
        folio='BATCH-001',
        tramite_id=1,
        tramite_nombre='Batch Test 1',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.PRESENTADO,
        ultima_actividad_estatus='PRESENTADO',
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )

    tramite2 = Tramite(
        id=200,
        folio='BATCH-002',
        tramite_id=2,
        tramite_nombre='Batch Test 2',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.PRESENTADO,
        ultima_actividad_estatus='PRESENTADO',
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )

    # First asignar succeeds, second raises
    call_count = 0
    original_asignar = Tramite.asignar

    def asignar_with_failure(self, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception('SFTP connection lost')

    queryset = [tramite1, tramite2]

    request = _build_post_request(
        superuser,
        data={
            'analista': str(analista.pk),
            'observacion': 'Batch test',
        },
    )

    with patch.object(Tramite, 'asignar', asignar_with_failure):
        response = model_admin.modificar_asignacion(request, queryset)

    # Should redirect (not crash)
    assert response.status_code == 302

    # Error should be in messages
    messages_list = list(request._messages)
    error_msgs = [str(m) for m in messages_list if 'No se pudieron asignar' in str(m)]
    assert len(error_msgs) > 0, 'Batch failure should be reported in messages'


@pytest.mark.django_db
def test_batch_assign_happy_path(superuser):
    """Verify normal batch assign still works after adding atomic."""
    model_admin = admin.site._registry.get(Tramite)
    if model_admin is None:
        pytest.skip('Tramite not registered in admin')

    analista = User.objects.create_user(
        username='happy_analista',
        password='testpass123',
    )

    # Use empty queryset — just verify no crash
    queryset = Tramite.objects.none()

    request = _build_post_request(
        superuser,
        data={
            'analista': str(analista.pk),
            'observacion': 'Happy path test',
        },
    )

    response = model_admin.modificar_asignacion(request, queryset)
    assert response.status_code == 302, 'Should redirect after successful batch'
