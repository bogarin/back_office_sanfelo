"""
Tests for tramites models.

This module contains tests for:
- Tramite model business logic
- Model methods (asignar, cerrar, etc.)
- Model properties
- Validation logic
"""

from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from core.rbac.constants import BackOfficeRole
from tramites.exceptions import EstadoNoPermitidoError, TramiteNoAsignableError
from tramites.models import Tramite
from tramites.models.catalogos import TramiteEstatus

User = get_user_model()


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def analista(django_db_setup):
    """Create an analyst user (member of the Analista group)."""
    user = User.objects.create_user(
        username='analista_test',
        email='analista@example.com',
        password='testpass123',
        first_name='Juan',
        last_name='Pérez',
    )
    group = Group.objects.get_or_create(name=BackOfficeRole.ANALISTA)[0]
    user.groups.add(group)
    return user


@pytest.fixture
def coordinador(django_db_setup):
    """Create a coordinator user (member of the Coordinador group)."""
    user = User.objects.create_user(
        username='coordinador_test',
        email='coordinador@example.com',
        password='testpass123',
        first_name='María',
        last_name='Gómez',
    )
    group = Group.objects.get_or_create(name=BackOfficeRole.COORDINADOR)[0]
    user.groups.add(group)
    return user


@pytest.fixture
def tramite_en_revision(django_db_blocker):
    """Create a tramite in memory with estatus 202 (EN_REVISION), unassigned."""
    return Tramite(
        id=3,
        folio='TRAM-000003',
        tramite_id=1,
        tramite_nombre='Prueba en Revisión',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.EN_REVISION,
        ultima_actividad_estatus='EN REVISIÓN',
        asignado_user_id=None,
        asignado_username=None,
        asignado_nombre=None,
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


@pytest.fixture
def tramite_no_activo(django_db_blocker):
    """Create a non-active tramite in memory (estatus 301 - POR_RECOGER)."""
    return Tramite(
        id=2,
        folio='TRAM-000002',
        tramite_id=1,
        tramite_nombre='Prueba Finalizado',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.POR_RECOGER,
        ultima_actividad_estatus='POR RECOGER',
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


@pytest.fixture
def tramite_activo(django_db_blocker):
    """Create an active tramite in memory (estatus 201 - PRESENTADO)."""
    return Tramite(
        id=1,
        folio='TRAM-000001',
        tramite_id=1,
        tramite_nombre='Prueba de Trámite',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.PRESENTADO,
        ultima_actividad_estatus='PRESENTADO',
        asignado_user_id=None,
        asignado_username=None,
        asignado_nombre=None,
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


@pytest.fixture
def tramite_en_revision_asignado(analista, django_db_blocker):
    """Create a tramite in EN_REVISION assigned to the shared analyst."""
    return Tramite(
        id=1,
        folio='TRAM-000001',
        tramite_id=1,
        tramite_nombre='Prueba en Revisión',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.EN_REVISION,
        ultima_actividad_estatus='EN REVISIÓN',
        asignado_user_id=analista.id,
        asignado_username=analista.username,
        asignado_nombre=analista.get_full_name(),
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


@pytest.fixture
def tramite_en_diligencia(analista, django_db_blocker):
    """Create a tramite in EN_DILIGENCIA (205) assigned to the shared analyst."""
    return Tramite(
        id=2,
        folio='TRAM-000002',
        tramite_id=1,
        tramite_nombre='Prueba en Diligencia',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.EN_DILIGENCIA,
        ultima_actividad_estatus='EN DILIGENCIA',
        asignado_user_id=analista.id,
        asignado_username=analista.username,
        asignado_nombre=analista.get_full_name(),
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


@pytest.fixture
def tramite_requerimiento(analista, django_db_blocker):
    """Create a tramite in REQUERIMIENTO (203) assigned to the shared analyst."""
    return Tramite(
        id=3,
        folio='TRAM-000003',
        tramite_id=1,
        tramite_nombre='Prueba Requerimiento',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.REQUERIMIENTO,
        ultima_actividad_estatus='REQUERIMIENTO',
        asignado_user_id=analista.id,
        asignado_username=analista.username,
        asignado_nombre=analista.get_full_name(),
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


# ---------------------------------------------------------------------------
# Fixtures previously in TestTramiteAsignar (hoisted to module level)
# ---------------------------------------------------------------------------


@pytest.fixture
def tramite_ya_asignado(analista, django_db_blocker):
    """Create a tramite in memory already assigned to an analyst."""
    return Tramite(
        id=4,
        folio='TRAM-000004',
        tramite_id=1,
        tramite_nombre='Prueba Ya Asignado',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.EN_REVISION,
        ultima_actividad_estatus='EN REVISIÓN',
        asignado_user_id=analista.id,
        asignado_username=analista.username,
        asignado_nombre=analista.get_full_name(),
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


@pytest.fixture
def tramite_borrador(django_db_blocker):
    """Create a tramite in estatus BORRADOR (101)."""
    return Tramite(
        id=5,
        folio='TRAM-000005',
        tramite_id=1,
        tramite_nombre='Prueba Borrador',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.BORRADOR,
        ultima_actividad_estatus='BORRADOR',
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


@pytest.fixture
def tramite_pendiente_pago(django_db_blocker):
    """Create a tramite in estatus PENDIENTE_PAGO (102)."""
    return Tramite(
        id=6,
        folio='TRAM-000006',
        tramite_id=1,
        tramite_nombre='Prueba Pendiente Pago',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.PENDIENTE_PAGO,
        ultima_actividad_estatus='PENDIENTE PAGO',
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


@pytest.fixture
def tramite_rechazado(django_db_blocker):
    """Create a tramite in estatus RECHAZADO (302)."""
    return Tramite(
        id=7,
        folio='TRAM-000007',
        tramite_id=1,
        tramite_nombre='Prueba Rechazado',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.RECHAZADO,
        ultima_actividad_estatus='RECHAZADO',
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


@pytest.fixture
def tramite_finalizado(django_db_blocker):
    """Create a tramite in estatus FINALIZADO (303)."""
    return Tramite(
        id=8,
        folio='TRAM-000008',
        tramite_id=1,
        tramite_nombre='Prueba Finalizado',
        ultima_actividad_estatus_id=TramiteEstatus.Estatus.FINALIZADO,
        ultima_actividad_estatus='FINALIZADO',
        tramite_categoria_id=1,
        tramite_categoria_nombre='General',
        urgente=False,
        es_propietario=True,
        creado='2024-01-01 00:00:00',
    )


# ---- Tests for Tramite.asignar() method ----


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_analista_nuevo_tramite_activo(
    mock_registrar, analista, coordinador, tramite_activo
):
    """
    Happy path: Assign active tramite to new analyst.

    Expected behavior:
    - Creates Actividades with estatus EN_REVISION (202)
    - Generates automatic observation
    - Logs assignment
    """
    tramite = tramite_activo

    # Assign
    tramite.asignar(
        analista=analista,
        asignado_por=coordinador,
        observacion='',
    )

    # Verify actividad was created
    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    # First argument is positional (estatus_id)
    assert call_args[0][0] == TramiteEstatus.Estatus.EN_REVISION
    # Second and third arguments are keyword arguments
    assert call_args.kwargs['analista_id'] == analista.id
    assert 'asignado' in call_args.kwargs['observacion'].lower()
    assert analista.get_full_name() in call_args.kwargs['observacion']


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_reasignacion_mismo_analista_no_op(mock_registrar, tramite_ya_asignado, analista):
    """
    Edge case: Try to assign to same analyst already assigned.

    Expected behavior:
    - Returns silently (no new Actividades)
    - No exception raised
    """
    tramite = tramite_ya_asignado

    # Assign to same analyst
    tramite.asignar(
        analista=analista,
        asignado_por=analista,
        observacion='',
    )

    # Verify no new actividad was created (registrar_actividad should not be called)
    assert mock_registrar.call_count == 0


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_autoasignacion_analista_toma_tramite(mock_registrar, analista, tramite_activo):
    """
    Edge case: Self-assignment (analista = asignado_por).

    Expected behavior:
    - Creates Actividades with estatus EN_REVISION (202)
    - Generates specific observation: "El analista... ha tomado el trámite..."
    - Logs self-assignment
    """
    tramite = tramite_activo

    # Self-assign
    tramite.asignar(
        analista=analista,
        asignado_por=analista,  # Same user
        observacion='',
    )

    # Verify actividad was created
    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.EN_REVISION
    assert call_args.kwargs['analista_id'] == analista.id
    assert 'ha tomado el trámite' in call_args.kwargs['observacion'].lower()
    assert analista.get_full_name() in call_args.kwargs['observacion']


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_autoasignacion_con_observacion_personalizada(
    mock_registrar, analista, tramite_activo
):
    """
    Edge case: Self-assignment with custom observation.

    Expected behavior:
    - Creates Actividades with estatus EN_REVISION (202)
    - Uses provided observation (not the auto-generated one)
    - Logs self-assignment with custom message
    """
    tramite = tramite_activo

    # Self-assign with custom observation
    custom_obs = 'Tomaré este trámite prioritariamente'
    tramite.asignar(
        analista=analista,
        asignado_por=analista,  # Same user
        observacion=custom_obs,
    )

    # Verify actividad was created with custom observation
    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.EN_REVISION
    assert call_args.kwargs['analista_id'] == analista.id
    assert call_args.kwargs['observacion'] == custom_obs


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_liberar_analista_none_estatus_vuelve_a_presentado(
    mock_registrar, tramite_en_revision, coordinador
):
    """
    Edge case: Liberate tramite (analista=None).

    Expected behavior:
    - Creates Actividades with estatus PRESENTADO (201)
    - Not EN_REVISION (202)
    - Observation: "Trámite liberado por..."
    """
    tramite = tramite_en_revision

    # Liberate
    tramite.asignar(
        analista=None,
        asignado_por=coordinador,
        observacion='',
    )

    # Verify actividad was created with PRESENTADO
    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.PRESENTADO
    assert call_args.kwargs['analista_id'] is None
    assert 'liberado' in call_args.kwargs['observacion'].lower()
    assert coordinador.get_full_name() in call_args.kwargs['observacion']


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_estatus_borrador_raises_no_asignable(
    mock_registrar, analista, coordinador, tramite_borrador
):
    """
    Edge case: Try to assign tramite in BORRADOR (101) status.

    Expected behavior:
    - Raises TramiteNoAsignableError
    - No Actividades created
    """
    tramite = tramite_borrador

    with pytest.raises(TramiteNoAsignableError, match='no se encuentra activo'):
        tramite.asignar(
            analista=analista,
            asignado_por=coordinador,
            observacion='Test',
        )

    assert mock_registrar.call_count == 0


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_estatus_pendiente_pago_raises_no_asignable(
    mock_registrar, analista, coordinador, tramite_pendiente_pago
):
    """
    Edge case: Try to assign tramite in PENDIENTE_PAGO (102) status.

    Expected behavior:
    - Raises TramiteNoAsignableError
    - No Actividades created
    """
    tramite = tramite_pendiente_pago

    with pytest.raises(TramiteNoAsignableError, match='no se encuentra activo'):
        tramite.asignar(
            analista=analista,
            asignado_por=coordinador,
            observacion='Test',
        )

    assert mock_registrar.call_count == 0


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_estatus_por_recoger_raises_no_asignable(
    mock_registrar, analista, coordinador, tramite_no_activo
):
    """
    Edge case: Try to assign tramite in POR_RECOGER (301) status.

    Expected behavior:
    - Raises TramiteNoAsignableError
    - No Actividades created
    """
    tramite = tramite_no_activo

    with pytest.raises(TramiteNoAsignableError, match='no se encuentra activo'):
        tramite.asignar(
            analista=analista,
            asignado_por=coordinador,
            observacion='Test',
        )

    assert mock_registrar.call_count == 0


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_estatus_rechazado_raises_no_asignable(
    mock_registrar, analista, coordinador, tramite_rechazado
):
    """
    Edge case: Try to assign tramite in RECHAZADO (302) status.

    Expected behavior:
    - Raises TramiteNoAsignableError
    - No Actividades created
    """
    tramite = tramite_rechazado

    with pytest.raises(TramiteNoAsignableError, match='no se encuentra activo'):
        tramite.asignar(
            analista=analista,
            asignado_por=coordinador,
            observacion='Test',
        )

    assert mock_registrar.call_count == 0


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_estatus_finalizado_raises_no_asignable(
    mock_registrar, analista, coordinador, tramite_finalizado
):
    """
    Edge case: Try to assign tramite in FINALIZADO (303) status.

    Expected behavior:
    - Raises TramiteNoAsignableError
    - No Actividades created
    """
    tramite = tramite_finalizado

    with pytest.raises(TramiteNoAsignableError, match='no se encuentra activo'):
        tramite.asignar(
            analista=analista,
            asignado_por=coordinador,
            observacion='Test',
        )

    assert mock_registrar.call_count == 0


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_liberar_con_asignado_por_none_lanza_value_error(
    mock_registrar, tramite_en_revision
):
    """
    Edge case: Liberate tramite with asignado_por=None.

    Expected behavior:
    - Raises ValueError: se requiere un usuario para liberar
    - No Actividades created
    """
    tramite = tramite_en_revision

    # When liberating (analista=None) and asignado_por is None,
    # the method validates that a user is provided
    with pytest.raises(ValueError, match='Se requiere un usuario'):
        tramite.asignar(
            analista=None,  # Liberar
            asignado_por=None,  # None
            observacion='',
        )

    # No actividad created due to error
    assert mock_registrar.call_count == 0


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_usuario_con_id_none_devuelve_silenciosamente(
    mock_registrar, coordinador, tramite_activo
):
    """
    Edge case: Assign with user where id is None (should not match).

    When tramite.asignado_user_id is None and analista.id is None,
    the guard `self.asignado_user_id is not None` prevents the
    False-silent-return. The assignment proceeds normally because
    a None-id user cannot match a None asignado_user_id.
    """
    tramite = tramite_activo

    # Create a mock user with id=None
    mock_analista = Mock()
    mock_analista.id = None
    mock_analista.username = 'mock_analista'
    mock_analista.get_full_name = Mock(return_value='Mock Analista')

    # Ensure tramite is not already assigned (asignado_user_id is already None)
    tramite.asignado_user_id = None

    # This proceeds with the assignment because None-id does NOT
    # short-circuit as a "same analyst" match anymore
    tramite.asignar(
        analista=mock_analista,
        asignado_por=coordinador,
        observacion='Test',
    )

    # Assignment proceeds — actividad IS created
    assert mock_registrar.call_count == 1


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_reasignar_a_diferente_analista(
    mock_registrar,
    analista,
    coordinador,
    tramite_ya_asignado,
):
    """
    Edge case: Reassign to a different analyst.

    Expected behavior:
    - Creates Actividades with estatus EN_REVISION (202)
    - Logs reassignment to different analyst
    - Updates analyst information
    """
    # Create another analyst
    nuevo_analista = User.objects.create_user(
        username='nuevo_analista',
        email='nuevo@example.com',
        password='testpass123',
        first_name='Carlos',
        last_name='Rodríguez',
    )

    tramite = tramite_ya_asignado

    # Reassign to different analyst
    tramite.asignar(
        analista=nuevo_analista,
        asignado_por=coordinador,
        observacion='Reasignación de analista',
    )

    # Verify actividad was created
    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.EN_REVISION
    assert call_args.kwargs['analista_id'] == nuevo_analista.id  # ty: ignore[unresolved-attribute]
    assert 'reasignación' in call_args.kwargs['observacion'].lower()


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_coordinadores_diferentes_asignan_analistas_diferentes(
    mock_registrar, analista, coordinador, tramite_activo
):
    """
    Edge case: Different coordinators assign different analysts to same tramite.

    Expected behavior:
    - Each assignment creates Actividades
    - Logs each assignment
    - Demonstrates that trámite can be reassigned multiple times
    """
    tramite = tramite_activo

    # First assignment
    tramite.asignar(
        analista=analista,
        asignado_por=coordinador,
        observacion='Primera asignación',
    )

    assert mock_registrar.call_count == 1

    # Create another analyst and coordinator
    nuevo_analista = User.objects.create_user(
        username='nuevo_analista',
        email='nuevo@example.com',
        password='testpass123',
        first_name='Carlos',
        last_name='Rodríguez',
    )

    otro_coordinador = User.objects.create_user(
        username='otro_coordinador',
        email='otro@example.com',
        password='testpass123',
        first_name='Ana',
        last_name='Martínez',
    )

    # Second assignment to different analyst by different coordinator
    # This should create a new activity
    tramite.asignar(
        analista=nuevo_analista,
        asignado_por=otro_coordinador,
        observacion='Segunda asignación',
    )

    # New activity created (not silent reassignment)
    assert mock_registrar.call_count == 2
    call_args = mock_registrar.call_args
    assert call_args.kwargs['analista_id'] == nuevo_analista.id  # ty: ignore[unresolved-attribute]
    assert 'segunda' in call_args.kwargs['observacion'].lower()


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_observacion_con_espacios_extra_se_mantiene(
    mock_registrar, analista, coordinador, tramite_activo
):
    """
    Edge case: Observation with extra spaces (preserved as-is).

    Expected behavior:
    - Uses observation with all spaces preserved
    - Creates Actividades with untrimmed observation
    """
    tramite = tramite_activo

    # Assign with observation containing extra spaces
    obs_con_espacios = '  Observación con espacios  '
    tramite.asignar(
        analista=analista,
        asignado_por=coordinador,
        observacion=obs_con_espacios,
    )

    # Verify actividad was created with spaces preserved
    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args.kwargs['observacion'] == obs_con_espacios
    assert call_args.kwargs['observacion'].startswith('  ')  # Has leading spaces
    assert call_args.kwargs['observacion'].endswith('  ')  # Has trailing spaces


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_observacion_muy_larga_se_mantiene_completa(
    mock_registrar, analista, coordinador, tramite_activo
):
    """
    Edge case: Very long observation text.

    Expected behavior:
    - Uses observation as-is (no truncation)
    - Creates Actividades with complete long observation
    """
    tramite = tramite_activo

    # Create a very long observation
    obs_larga = 'Observación muy larga ' * 50  # ~900 characters
    tramite.asignar(
        analista=analista,
        asignado_por=coordinador,
        observacion=obs_larga,
    )

    # Verify actividad was created with complete long observation
    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args.kwargs['observacion'] == obs_larga
    assert len(call_args.kwargs['observacion']) > 800  # Verify it's long


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_observacion_con_caracteres_especiales_se_mantiene(
    mock_registrar, analista, coordinador, tramite_activo
):
    """
    Edge case: Observation with special characters and emojis.

    Expected behavior:
    - Uses observation as-is
    - Creates Actividades preserving special characters
    """
    tramite = tramite_activo

    # Create observation with special characters and emoji
    obs_especial = 'Observación con émojis 🎉 y caráctères especiales: @#$%&*()'
    tramite.asignar(
        analista=analista,
        asignado_por=coordinador,
        observacion=obs_especial,
    )

    # Verify actividad was created with special characters preserved
    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args.kwargs['observacion'] == obs_especial
    assert '🎉' in call_args.kwargs['observacion']
    assert 'émojis' in call_args.kwargs['observacion']


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_observacion_solo_espacios_se_usa_como_es(
    mock_registrar, analista, coordinador, tramite_activo
):
    """
    Edge case: Observation with only spaces (used as-is).

    Expected behavior:
    - Uses spaces-only observation (not auto-generated)
    - Creates Actividades with spaces-only observation
    """
    tramite = tramite_activo

    # Assign with observation containing only spaces
    obs_solo_espacios = '     '
    tramite.asignar(
        analista=analista,
        asignado_por=coordinador,
        observacion=obs_solo_espacios,
    )

    # Verify actividad was created with spaces-only observation
    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args.kwargs['observacion'] == obs_solo_espacios
    # It's not auto-generated (doesn't contain 'asignado')
    assert 'asignado' not in call_args.kwargs['observacion'].lower()


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_liberar_y_reasignar_mismo_tramite(
    mock_registrar, analista, coordinador, tramite_activo
):
    """
    Extreme case: Assign, liberate, and reassign same tramit in quick succession.

    Expected behavior:
    - Each operation creates appropriate Actividades
    - Status changes: PRESENTADO -> EN_REVISION -> PRESENTADO -> EN_REVISION
    - Logs each operation
    """
    tramite = tramite_activo

    # Step 1: Assign
    tramite.asignar(
        analista=analista,
        asignado_por=coordinador,
        observacion='Primera asignación',
    )
    assert mock_registrar.call_count == 1
    assert mock_registrar.call_args[0][0] == TramiteEstatus.Estatus.EN_REVISION
    # Simulate view updating asignado_user_id after assignment
    tramite.asignado_user_id = analista.id

    # Step 2: Liberate
    tramite.asignar(
        analista=None,
        asignado_por=coordinador,
        observacion='Liberación',
    )
    assert mock_registrar.call_count == 2
    assert mock_registrar.call_args[0][0] == TramiteEstatus.Estatus.PRESENTADO
    # Simulate view clearing asignado_user_id after liberation
    tramite.asignado_user_id = None

    # Step 3: Reassign to same analyst (should create new activity)
    tramite.asignar(
        analista=analista,
        asignado_por=coordinador,
        observacion='Reasignación',
    )
    assert mock_registrar.call_count == 3
    assert mock_registrar.call_args[0][0] == TramiteEstatus.Estatus.EN_REVISION


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_multiple_asignaciones_mismo_analista_distintos_coordinadores(
    mock_registrar, analista, coordinador, tramite_activo
):
    """
    Extreme case: Multiple assignments by different coordinators.

    Expected behavior:
    - First assignment creates Actividades
    - Subsequent assignments to same analyst create new Actividades (not silent)
    - Tests that each assignment is logged, even to same analyst
    """
    tramite = tramite_activo

    # Create multiple coordinators
    coord1 = coordinador
    coord2 = User.objects.create_user(
        username='coordinador_2',
        email='coord2@example.com',
        password='testpass123',
        first_name='Roberto',
        last_name='Sánchez',
    )
    coord3 = User.objects.create_user(
        username='coordinador_3',
        email='coord3@example.com',
        password='testpass123',
        first_name='Laura',
        last_name='Díaz',
    )

    # First assignment
    tramite.asignar(
        analista=analista,
        asignado_por=coord1,
        observacion='Asignación por Coordinador 1',
    )
    assert mock_registrar.call_count == 1
    assert 'Coordinador 1' in mock_registrar.call_args.kwargs['observacion']

    # Update tramite.asignado_user_id to simulate real behavior
    tramite.asignado_user_id = analista.id

    # Second assignment to same analyst by different coordinator
    # This should be silent if already assigned to same analyst
    tramite.asignar(
        analista=analista,
        asignado_por=coord2,
        observacion='',
    )
    # No new activity created (silent reassignment)
    assert mock_registrar.call_count == 1

    # Third assignment to same analyst by another coordinator (silent)
    tramite.asignar(
        analista=analista,
        asignado_por=coord3,
        observacion='',
    )
    # Still no new activity
    assert mock_registrar.call_count == 1


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_asignar_autoasignacion_y_reasignacion_rapida(mock_registrar, analista, tramite_activo):
    """
    Extreme case: Self-assign followed by quick reassignment to different analyst.

    Expected behavior:
    - Self-assign creates Actividades with auto-generated observation
    - Reassignment to different analyst creates new Actividades
    - Tests observation generation and reassignment logic
    """
    tramite = tramite_activo

    # Step 1: Self-assign
    tramite.asignar(
        analista=analista,
        asignado_por=analista,
        observacion='',  # Auto-generated
    )
    assert mock_registrar.call_count == 1
    assert mock_registrar.call_args[0][0] == TramiteEstatus.Estatus.EN_REVISION
    assert 'ha tomado el trámite' in mock_registrar.call_args.kwargs['observacion'].lower()
    # Simulate view updating asignado_user_id after assignment
    tramite.asignado_user_id = analista.id

    # Create another analyst
    otro_analista = User.objects.create_user(
        username='otro_analista',
        email='otro@example.com',
        password='testpass123',
        first_name='Carlos',
        last_name='López',
    )

    # Step 2: Reassign to different analyst
    tramite.asignar(
        analista=otro_analista,
        asignado_por=analista,
        observacion='Traspaso de analista',
    )
    assert mock_registrar.call_count == 2
    assert mock_registrar.call_args[0][0] == TramiteEstatus.Estatus.EN_REVISION
    assert mock_registrar.call_args.kwargs['analista_id'] == otro_analista.id  # ty: ignore[unresolved-attribute]
    assert 'traspaso' in mock_registrar.call_args.kwargs['observacion'].lower()


# ---- Tests for Tramite.requerir_documentos() method ----


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_requerir_documentos_exitoso(mock_registrar, analista, tramite_en_revision_asignado):
    """
    Happy path: Request documents successfully.

    Expected behavior:
    - Creates Actividades with estatus REQUERIMIENTO (203)
    - Uses provided observation
    """
    tramite = tramite_en_revision_asignado

    tramite.requerir_documentos(
        analista=analista,
        observacion='Favor de proporcionar documentos adicionales',
    )

    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.REQUERIMIENTO
    assert call_args.kwargs['analista_id'] == analista.id
    assert 'documentos adicionales' in call_args.kwargs['observacion']


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_requerir_documentos_estatus_no_en_revision_raises_error(
    mock_registrar, analista, tramite_activo
):
    """
    Edge case: Request documents when not in EN_REVISION status.

    Expected behavior:
    - Raises EstadoNoPermitidoError
    """
    tramite = tramite_activo  # PRESENTADO, not EN_REVISION

    with pytest.raises(EstadoNoPermitidoError, match='estatus actual'):
        tramite.requerir_documentos(
            analista=analista,
            observacion='Test',
        )

    assert mock_registrar.call_count == 0


@pytest.mark.django_db
@patch('tramites.models.Tramite._assert_asignado_a')
@patch('tramites.models.Tramite.registrar_actividad')
def test_requerir_documentos_usuario_no_asignado_raises_permission(
    mock_registrar, mock_verificar, analista, tramite_en_revision_asignado
):
    """
    Edge case: Request documents by non-assigned analyst.

    Expected behavior:
    - Raises PermissionDenied from _assert_asignado_a
    """
    tramite = tramite_en_revision_asignado

    # Mock _assert_asignado_a to raise PermissionDenied
    mock_verificar.side_effect = PermissionDenied('No asignado')

    with pytest.raises(PermissionDenied):
        tramite.requerir_documentos(
            analista=analista,
            observacion='Test',
        )

    # _assert_asignado_a should be called
    mock_verificar.assert_called_once_with(analista)
    # No actividad created due to permission error
    assert mock_registrar.call_count == 0


# ---- Tests for Tramite.enviar_a_firma() method ----


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_enviar_a_firma_exitoso(mock_registrar, analista, tramite_en_revision_asignado):
    """
    Happy path: Send to signature successfully.

    Expected behavior:
    - Creates Actividades with estatus EN_DILIGENCIA (205)
    - Uses provided observation
    """
    tramite = tramite_en_revision_asignado

    tramite.enviar_a_firma(
        analista=analista,
        observacion='Trámite enviado a firma por falta de información',
    )

    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.EN_DILIGENCIA
    assert call_args.kwargs['analista_id'] == analista.id
    assert 'firma' in call_args.kwargs['observacion'].lower()


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_enviar_a_firma_estatus_no_en_revision_raises_error(
    mock_registrar, analista, tramite_activo
):
    """
    Edge case: Send to signature when not in EN_REVISION status.

    Expected behavior:
    - Raises EstadoNoPermitidoError
    """
    tramite = tramite_activo  # PRESENTADO, not EN_REVISION

    with pytest.raises(EstadoNoPermitidoError, match='estatus actual'):
        tramite.enviar_a_firma(
            analista=analista,
            observacion='Test',
        )

    assert mock_registrar.call_count == 0


@pytest.mark.django_db
@patch('tramites.models.Tramite._assert_asignado_a')
@patch('tramites.models.Tramite.registrar_actividad')
def test_enviar_a_firma_usuario_no_asignado_raises_permission(
    mock_registrar, mock_verificar, analista, tramite_en_revision_asignado
):
    """
    Edge case: Send to signature by non-assigned analyst.

    Expected behavior:
    - Raises PermissionDenied from _assert_asignado_a
    """
    tramite = tramite_en_revision_asignado

    # Mock _assert_asignado_a to raise PermissionDenied
    mock_verificar.side_effect = PermissionDenied('No asignado')

    with pytest.raises(PermissionDenied):
        tramite.enviar_a_firma(
            analista=analista,
            observacion='Test',
        )

    # _assert_asignado_a should be called
    mock_verificar.assert_called_once_with(analista)
    # No actividad created due to permission error
    assert mock_registrar.call_count == 0


# ---- Tests for Tramite.cancelar() method ----


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_cancelar_exitoso_actividad_por_recoger(
    mock_registrar, analista, tramite_en_revision_asignado
):
    """
    Happy path: Cancel tramite with POR_RECOGER status.

    Expected behavior:
    - Creates Actividades with estatus POR_RECOGER (301)
    - Uses provided observation
    """
    tramite = tramite_en_revision_asignado

    tramite.cancelar(
        analista=analista,
        estatus_cierre=TramiteEstatus.Estatus.POR_RECOGER,
        observacion='Trámite listo para recoger',
    )

    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.POR_RECOGER
    assert call_args.kwargs['analista_id'] == analista.id
    assert 'listo para recoger' in call_args.kwargs['observacion']


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_cancelar_exitoso_actividad_rechazado(
    mock_registrar, analista, tramite_en_revision_asignado
):
    """
    Happy path: Cancel tramite with RECHAZADO status.

    Expected behavior:
    - Creates Actividades with estatus RECHAZADO (302)
    """
    tramite = tramite_en_revision_asignado

    tramite.cancelar(
        analista=analista,
        estatus_cierre=TramiteEstatus.Estatus.RECHAZADO,
        observacion='Documentos incompletos',
    )

    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.RECHAZADO


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_cancelar_exitoso_actividad_cancelado(
    mock_registrar, analista, tramite_en_revision_asignado
):
    """
    Happy path: Cancel tramite with CANCELADO status.

    Expected behavior:
    - Creates Actividades with estatus CANCELADO (304)
    """
    tramite = tramite_en_revision_asignado

    tramite.cancelar(
        analista=analista,
        estatus_cierre=TramiteEstatus.Estatus.CANCELADO,
        observacion='Solicitante canceló el trámite',
    )

    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.CANCELADO


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_cancelar_observacion_vacia_raises_value_error(
    mock_registrar, analista, tramite_en_revision_asignado
):
    """
    Edge case: Try to cancel with empty observation.

    Expected behavior:
    - Raises ValueError
    - No Actividades created
    """
    tramite = tramite_en_revision_asignado

    with pytest.raises(ValueError, match='observación es requerida'):
        tramite.cancelar(
            analista=analista,
            estatus_cierre=TramiteEstatus.Estatus.POR_RECOGER,
            observacion='   ',  # Empty after strip
        )

    assert mock_registrar.call_count == 0


@pytest.mark.django_db
def test_cancelar_estatus_no_activo_raises_no_asignable(analista, tramite_no_activo):
    """
    Edge case: Try to cancel non-active tramite.

    Expected behavior:
    - Raises TramiteNoAsignableError
    """
    tramite = tramite_no_activo

    with pytest.raises(TramiteNoAsignableError, match='ya no se encuentra activo'):
        tramite.cancelar(
            analista=analista,
            estatus_cierre=TramiteEstatus.Estatus.POR_RECOGER,
            observacion='Test',
        )


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_cancelar_usuario_no_asignado_raises_permission_denied(
    mock_registrar,
    analista,
    tramite_en_revision_asignado,
):
    """
    Edge case: Try to cancel tramite not assigned to this analyst.

    Expected behavior:
    - Raises PermissionDenied
    - No Actividades created
    """
    User = get_user_model()
    other_analista = User.objects.create_user(
        username='other_analista',
        email='other@example.com',
        password='test123',
        first_name='Pedro',
        last_name='López',
    )

    tramite = tramite_en_revision_asignado

    with pytest.raises(PermissionDenied, match='Este tramite esta asignado a otro analista'):
        tramite.cancelar(
            analista=other_analista,
            estatus_cierre=TramiteEstatus.Estatus.POR_RECOGER,
            observacion='Test',
        )

    assert mock_registrar.call_count == 0


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_cancelar_estatus_cierre_invalido_raises_value_error(
    mock_registrar, analista, tramite_en_revision_asignado
):
    """
    Edge case: Try to cancel with invalid closing status.

    Expected behavior:
    - Raises ValueError
    - No Actividades created
    """
    tramite = tramite_en_revision_asignado

    with pytest.raises(ValueError, match='estatus de cierre seleccionado no es válido'):
        tramite.cancelar(
            analista=analista,
            estatus_cierre=TramiteEstatus.Estatus.FINALIZADO,
            observacion='Test',
        )

    assert mock_registrar.call_count == 0


# ---- Tests for DatabaseError handling in Tramite methods ----


@pytest.mark.django_db
def test_asignar_estatus_invalido_finaliza_sin_crear_actividad(
    analista, tramite_en_revision_asignado
):
    """
    Edge case: Try to cancel with invalid status (not in REVISION/REQUERIMIENTO/EN_DILIGENCIA).

    Expected behavior:
    - Raises EstadoNoPermitidoError
    - No Actividades created
    """
    tramite = tramite_en_revision_asignado
    # Change to invalid status (PRESENTADO instead of REVISION/REQUERIMIENTO/EN_DILIGENCIA)
    tramite.ultima_actividad_estatus_id = TramiteEstatus.Estatus.PRESENTADO

    with pytest.raises(EstadoNoPermitidoError, match='estatus actual'):
        tramite.cancelar(
            analista=analista,
            estatus_cierre=TramiteEstatus.Estatus.POR_RECOGER,
            observacion='Observación de prueba',
        )


# ---- Tests for EN_DILIGENCIA (205) behavior ----


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_cancelar_coordinador_desde_diligencia_exitoso(
    mock_registrar, analista, tramite_en_diligencia
):
    """
    Happy path: Coordinator can cancel from EN_DILIGENCIA (205).

    Expected behavior:
    - Creates Actividades with terminal estatus
    - Coordinator authorization passes
    """
    tramite = tramite_en_diligencia

    # Create a mock coordinator
    coordinador = Mock()
    coordinador.id = 999
    coordinador.is_superuser = False
    coordinador.is_administrador = False
    coordinador.is_coordinador = True
    coordinador.is_analista = False
    coordinador.username = 'coordinador_test'

    tramite.cancelar(
        analista=coordinador,
        estatus_cierre=TramiteEstatus.Estatus.CANCELADO,
        observacion='Cancelado por coordinador',
    )

    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.CANCELADO
    assert call_args.kwargs['analista_id'] == coordinador.id


@pytest.mark.django_db
def test_cancelar_analista_desde_diligencia_denied(analista, tramite_en_diligencia):
    """
    Edge case: Analyst cannot cancel from EN_DILIGENCIA (205).

    Expected behavior:
    - Raises PermissionDenied
    - No Actividades created
    """
    tramite = tramite_en_diligencia

    with pytest.raises(
        PermissionDenied, match='Solo el coordinador o administrador puede cancelar'
    ):
        tramite.cancelar(
            analista=analista,
            estatus_cierre=TramiteEstatus.Estatus.CANCELADO,
            observacion='Test',
        )


@pytest.mark.django_db
@patch('tramites.models.Tramite.registrar_actividad')
def test_cancelar_analista_desde_requerimiento_exitoso(
    mock_registrar, analista, tramite_requerimiento
):
    """
    Happy path: Analyst can still cancel from REQUERIMIENTO (203).

    Expected behavior:
    - Creates Actividades with terminal estatus
    - Analyst authorization passes
    """
    tramite = tramite_requerimiento

    tramite.cancelar(
        analista=analista,
        estatus_cierre=TramiteEstatus.Estatus.CANCELADO,
        observacion='Cancelado por analista',
    )

    assert mock_registrar.call_count == 1
    call_args = mock_registrar.call_args
    assert call_args[0][0] == TramiteEstatus.Estatus.CANCELADO
    assert call_args.kwargs['analista_id'] == analista.id


@pytest.mark.django_db
def test_liberar_desde_diligencia_raises_estado_no_permitido(coordinador, tramite_en_diligencia):
    """
    Edge case: Cannot liberate a trámite in EN_DILIGENCIA (205).

    Expected behavior:
    - Raises EstadoNoPermitidoError
    - No Actividades created
    """
    tramite = tramite_en_diligencia

    with pytest.raises(EstadoNoPermitidoError, match='No es posible liberar'):
        tramite._liberar(
            liberado_por=coordinador,
            observacion='Liberación',
        )


@pytest.mark.django_db
def test_available_actions_analista_diligencia_returns_empty(analista, tramite_en_diligencia):
    """
    Edge case: Analyst gets empty actions list for EN_DILIGENCIA (205).

    Expected behavior:
    - Returns [] for analyst
    """
    tramite = tramite_en_diligencia

    actions = tramite.available_actions(analista)
    assert actions == []


@pytest.mark.django_db
def test_available_actions_coordinador_diligencia_includes_cancelar(
    analista, tramite_en_diligencia
):
    """
    Happy path: Coordinator gets cancelar action for EN_DILIGENCIA (205).

    Expected behavior:
    - Returns ['cancelar'] for coordinator
    """
    tramite = tramite_en_diligencia

    # Create a mock coordinator
    coordinador = Mock()
    coordinador.is_superuser = False
    coordinador.is_administrador = False
    coordinador.is_coordinador = True
    coordinador.is_analista = False

    actions = tramite.available_actions(coordinador)
    assert 'cancelar' in actions


@pytest.mark.django_db
def test_can_view_analista_diligencia_returns_false(analista, tramite_en_diligencia):
    """
    Edge case: Analyst cannot view trámite in EN_DILIGENCIA (205).

    Expected behavior:
    - Returns False for analyst
    """
    tramite = tramite_en_diligencia

    result = tramite.can_view(analista)
    assert result is False


@pytest.mark.django_db
def test_can_view_coordinador_diligencia_returns_true(tramite_en_diligencia):
    """
    Happy path: Coordinator can view trámite in EN_DILIGENCIA (205).

    Expected behavior:
    - Returns True for coordinator
    """
    tramite = tramite_en_diligencia

    # Create a mock coordinator
    coordinador = Mock()
    coordinador.is_superuser = False
    coordinador.is_administrador = False
    coordinador.is_coordinador = True
    coordinador.is_analista = False

    result = tramite.can_view(coordinador)
    assert result is True


@pytest.mark.django_db
def test_can_release_diligencia_returns_false(tramite_en_diligencia):
    """
    Edge case: Cannot release trámite in EN_DILIGENCIA (205).

    Expected behavior:
    - Returns False even for coordinator
    """
    tramite = tramite_en_diligencia

    # Create a mock coordinator
    coordinador = Mock()
    coordinador.is_superuser = False
    coordinador.is_administrador = False
    coordinador.is_coordinador = True
    coordinador.is_analista = False

    result = tramite.can_release(coordinador)
    assert result is False


@pytest.mark.django_db
def test_can_assign_diligencia_returns_false(tramite_en_diligencia):
    """
    Edge case: Cannot assign/reassign trámite in EN_DILIGENCIA (205).

    Expected behavior:
    - Returns False even for coordinator
    """
    tramite = tramite_en_diligencia

    # Create a mock coordinator
    coordinador = Mock()
    coordinador.is_superuser = False
    coordinador.is_administrador = False
    coordinador.is_coordinador = True
    coordinador.is_analista = False

    result = tramite.can_assign(coordinador)
    assert result is False


@pytest.mark.django_db
def test_can_download_analista_diligencia_returns_false(analista, tramite_en_diligencia):
    """
    Edge case: Analyst cannot download documents from EN_DILIGENCIA (205).

    Expected behavior:
    - Returns False for analyst, even if assigned
    """
    tramite = tramite_en_diligencia

    result = tramite.can_download(analista)
    assert result is False


@pytest.mark.django_db
def test_can_download_coordinador_diligencia_returns_true(tramite_en_diligencia):
    """
    Happy path: Coordinator can download documents from EN_DILIGENCIA (205).

    Expected behavior:
    - Returns True for coordinator
    """
    tramite = tramite_en_diligencia

    # Create a mock coordinator
    coordinador = Mock()
    coordinador.is_superuser = False
    coordinador.is_administrador = False
    coordinador.is_coordinador = True
    coordinador.is_analista = False

    result = tramite.can_download(coordinador)
    assert result is True
