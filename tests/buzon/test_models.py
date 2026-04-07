"""
Unit tests for buzon models.

Tests for AsignacionTramite model including:
- Assignment functionality
- Unique constraint enforcement
- State validation
- Analyst limit validation
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from tramites.models import Tramite, TramiteEstatus, TramiteCatalogo
from buzon.models import AsignacionTramite

User = get_user_model()


@pytest.fixture
def catalogo(db):
    """Fixture para crear un catálogo de trámite."""
    return TramiteCatalogo.objects.create(id=1, nombre='Test Catálogo', activo=True)


@pytest.fixture
def estatus_presentado(db):
    """Fixture para crear estatus PRESENTADO (201)."""
    return TramiteEstatus.objects.create(id=201, estatus='PRESENTADO', responsable='Sistema')


@pytest.fixture
def estatus_borrador(db):
    """Fixture para crear estatus BORRADOR (101)."""
    return TramiteEstatus.objects.create(id=101, estatus='BORRADOR', responsable='Sistema')


@pytest.fixture
def tramite_presentado(db, estatus_presentado, catalogo):
    """Fixture para crear un trámite en estado PRESENTADO."""
    return Tramite.objects.create(
        folio='T-001',
        nom_sol='Juan Pérez',
        estatus_id=estatus_presentado.id,
        tramite_catalogo=catalogo,
    )


@pytest.fixture
def tramite_borrador(db, estatus_borrador, catalogo):
    """Fixture para crear un trámite en estado BORRADOR."""
    return Tramite.objects.create(
        folio='T-002',
        nom_sol='María López',
        estatus_id=estatus_borrador.id,
        tramite_catalogo=catalogo,
    )


@pytest.fixture
def tramite(db, estatus_presentado, catalogo):
    """Fixture genérico para crear un trámite."""
    return Tramite.objects.create(
        folio='T-999',
        nom_sol='Test User',
        estatus_id=estatus_presentado.id,
        tramite_catalogo=catalogo,
    )


@pytest.fixture
def analista(db, analista_group):
    """Fixture para crear un usuario analista."""
    user = User.objects.create_user(username='analista1', password='test123')
    user.groups.add(analista_group)
    return user


@pytest.fixture
def coordinador(db, coordinador_group):
    """Fixture para crear un usuario coordinador."""
    user = User.objects.create_user(username='coord1', password='test123')
    user.groups.add(coordinador_group)
    return user


def test_asignar_tramite_exitoso(tramite_presentado, analista, coordinador):
    """Test que asignar un trámite en estado PRESENTADO funciona."""
    from buzon.services import asignar_tramite

    asignacion = asignar_tramite(
        tramite=tramite_presentado, analista=analista, asignado_por=coordinador, observacion='Test'
    )

    assert asignacion.tramite == tramite_presentado
    assert asignacion.analista == analista
    assert asignacion.asignado_por == coordinador
    assert asignacion.observacion == 'Test'


def test_asignar_tramite_con_estatus_borrador_falla(tramite_borrador, analista):
    """Test que no se pueden asignar trámites en estado BORRADOR."""
    from buzon.services import asignar_tramite, EstadoNoPermitidoError

    with pytest.raises(EstadoNoPermitidoError) as exc_info:
        asignar_tramite(tramite=tramite_borrador, analista=analista)

    assert 'proceso activo' in str(exc_info.value).lower()


def test_asignar_tramite_con_estados_proceso_funciona(
    tramite, estatus_presentado, analista, catalogo
):
    """Test que se pueden asignar trámites en todos los estados 200s."""
    from buzon.services import asignar_tramite
    from buzon.models import ESTADOS_PERMITIDOS_PARA_ASIGNACION

    # Crear un trámite diferente para cada estado para evitar conflictos
    for estado_id in ESTADOS_PERMITIDOS_PARA_ASIGNACION:
        # Asegurar que existe el TramiteEstatus para este estado
        TramiteEstatus.objects.get_or_create(
            id=estado_id,
            defaults={'estatus': f'ESTADO_{estado_id}', 'responsable': 'Sistema'},
        )
        # Crear un nuevo trámite con el estado específico
        tramite_test = Tramite.objects.create(
            folio=f'T-TEST-{estado_id}',
            nom_sol=f'Test User {estado_id}',
            estatus_id=estado_id,
            tramite_catalogo=catalogo,
        )

        asignacion = asignar_tramite(
            tramite=tramite_test,
            analista=analista,
        )

        assert asignacion.tramite == tramite_test
        # Liberar para el siguiente test
        AsignacionTramite.liberar(tramite_test)


def test_reasignar_tramite_reemplaza_anterior(tramite_presentado, analista, coordinador):
    """Test que reasignar un trámite reemplaza la asignación anterior."""
    from buzon.services import asignar_tramite

    # Primera asignación
    analista2 = User.objects.create_user(username='analista2', password='test123')
    asignacion1 = asignar_tramite(
        tramite=tramite_presentado,
        analista=analista,
        asignado_por=coordinador,
    )

    assert asignacion1.analista == analista

    # Reasignación
    asignacion2 = asignar_tramite(
        tramite=tramite_presentado,
        analista=analista2,
        asignado_por=coordinador,
    )

    # Verificar que solo hay una asignación
    assert AsignacionTramite.objects.filter(tramite=tramite_presentado).count() == 1

    assert AsignacionTramite.objects.get(tramite=tramite_presentado).analista == analista2


def test_unique_constraint_preiene_asignaciones_duplicadas(tramite_presentado, analista):
    """Test que UniqueConstraint previene asignaciones duplicadas."""
    # Primera asignación
    asignacion1 = AsignacionTramite.objects.create(
        tramite=tramite_presentado,
        analista_id=analista.id,
    )

    # Intentar crear duplicado debe fallar
    with pytest.raises(IntegrityError):
        AsignacionTramite.objects.create(
            tramite=tramite_presentado,
            analista_id=analista.id,
        )


def test_liberar_tramite_elimina_asignacion(tramite_presentado, analista, coordinador):
    """Test que liberar un trámite elimina la asignación."""
    from buzon.services import asignar_tramite, liberar_tramite

    # Asignar trámite
    asignar_tramite(
        tramite=tramite_presentado,
        analista=analista,
        asignado_por=coordinador,
    )

    assert AsignacionTramite.objects.filter(tramite=tramite_presentado).count() == 1

    # Liberar trámite
    liberar_tramite(tramite_presentado)

    assert AsignacionTramite.objects.filter(tramite=tramite_presentado).count() == 0


def test_limite_de_asignaciones_por_analista(tramite, analista, coordinador, catalogo, db):
    """Test que se respeta el límite de asignaciones por analista."""
    from buzon.services import asignar_tramite, AnalistaConMuchasAsignacionesError
    from django.conf import settings as django_settings

    # Configurar límite bajo para este test
    original_limit = getattr(django_settings, 'MAX_TRAMITES_POR_ANALISTA', 50)
    django_settings.MAX_TRAMITES_POR_ANALISTA = 2

    try:
        # Asignar 1 trámite
        asignar_tramite(
            tramite=tramite,
            analista=analista,
            asignado_por=coordinador,
        )

        # Asignar segundo trámite (al límite)
        tramite2 = Tramite.objects.create(
            folio='T-002',
            nom_sol='Test User 2',
            estatus_id=tramite.estatus_id,
            tramite_catalogo=catalogo,
        )
        asignar_tramite(
            tramite=tramite2,
            analista=analista,
            asignado_por=coordinador,
        )

        # Intentar asignar tercero debe fallar
        tramite3 = Tramite.objects.create(
            folio='T-003',
            nom_sol='Test User 3',
            estatus_id=tramite.estatus_id,
            tramite_catalogo=catalogo,
        )
        with pytest.raises(AnalistaConMuchasAsignacionesError):
            asignar_tramite(
                tramite=tramite3,
                analista=analista,
                asignado_por=coordinador,
            )
    finally:
        # Restaurar límite original
        django_settings.MAX_TRAMITES_POR_ANALISTA = original_limit


def test_clean_valida_estados(tramite_borrador, analista):
    """Test que el método clean() valida correctamente los estados."""
    from django.core.exceptions import ValidationError

    asignacion = AsignacionTramite(
        tramite=tramite_borrador,
        analista_id=analista.id,
    )

    with pytest.raises(ValidationError) as exc_info:
        asignacion.full_clean()

    # Verificar que el error menciona el estado incorrecto
    assert 'borrador' in str(exc_info.value).lower()


def test_str_representation(tramite, analista):
    """Test que el método __str__ devuelve el formato correcto."""
    asignacion = AsignacionTramite.objects.create(
        tramite=tramite,
        analista_id=analista.id,
    )

    expected_str = f'{tramite.folio} → {analista.username}'
    assert str(asignacion) == expected_str


def test_fecha_asignacion_auto_now(tramite, analista):
    """Test que fecha_asignacion se asigna automáticamente al crear."""
    from django.utils import timezone
    import datetime

    asignacion = AsignacionTramite.objects.create(
        tramite=tramite,
        analista_id=analista.id,
    )

    assert asignacion.fecha_asignacion is not None
    # La fecha debe ser reciente (menos de 1 segundo)
    ahora = timezone.now()
    diferencia = ahora - asignacion.fecha_asignacion
    assert diferencia.total_seconds() < 1
