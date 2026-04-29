"""Integration tests for sidebar permissions and Jazzmin visibility.

Verifies that:
- Custom permissions (acceso_analista, acceso_coordinador) are created by setup_roles
- Each role gets exactly the permissions it should have
- Users see the correct sidebar links when logged in
- Users do NOT see sidebar links they lack permission for
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import Client

from core.rbac.constants import (
    ROLE_CUSTOM_PERMISSIONS,
    TRAMITES_CUSTOM_PERMISSIONS,
    BackOfficeRole,
    TramitePermission,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def setup_roles_run(db):
    """Run setup_roles and return the groups dict."""
    call_command('setup_roles', verbosity=0)
    return {
        role: Group.objects.get(name=role)
        for role in BackOfficeRole
    }


@pytest.fixture
def role_user(setup_roles_run):
    """Factory fixture to create a user with a specific role."""

    def _create(role, username=None):
        group = setup_roles_run[role]
        uname = username or f'sidebar_{role.name.lower()}'
        user = User.objects.create_user(
            username=uname,
            password='testpass123',
            is_staff=True,
        )
        user.groups.add(group)
        return user

    return _create


# ---------------------------------------------------------------------------
# Permission creation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'codename',
    TRAMITES_CUSTOM_PERMISSIONS,
    ids=lambda c: c,
)
def test_setup_roles_creates_acceso_perms(setup_roles_run, codename):
    """setup_roles creates each custom permission in the database."""
    # Get the tramites content type (permissions are created under this app)
    perm = Permission.objects.filter(
        codename=codename,
        content_type__app_label='tramites',
    ).first()
    assert perm is not None, f'Permission {codename} was not created'


# ---------------------------------------------------------------------------
# Permission assignment per role
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'role',
    list(BackOfficeRole),
    ids=[r.name for r in BackOfficeRole],
)
def test_role_has_exactly_expected_permissions(setup_roles_run, role):
    """Each role has exactly the custom permissions defined in ROLE_CUSTOM_PERMISSIONS."""
    group = setup_roles_run[role]
    expected = set(ROLE_CUSTOM_PERMISSIONS[role])

    actual = set(
        group.permissions.filter(
            content_type__app_label='tramites',
            codename__in=TRAMITES_CUSTOM_PERMISSIONS,
        ).values_list('codename', flat=True)
    )
    assert actual == expected, f'{role.name}: expected {expected}, got {actual}'


def test_administrador_has_both_acceso_perms(setup_roles_run):
    """Administrador has both acceso_analista and acceso_coordinador."""
    group = setup_roles_run[BackOfficeRole.ADMINISTRADOR]
    codenames = set(group.permissions.filter(
        codename__in=TRAMITES_CUSTOM_PERMISSIONS,
    ).values_list('codename', flat=True))

    assert TramitePermission.ACCESO_ANALISTA in codenames
    assert TramitePermission.ACCESO_COORDINADOR in codenames


def test_coordinador_has_coordinador_perm_only(setup_roles_run):
    """Coordinador has acceso_coordinador but NOT acceso_analista."""
    group = setup_roles_run[BackOfficeRole.COORDINADOR]
    codenames = set(group.permissions.filter(
        codename__in=TRAMITES_CUSTOM_PERMISSIONS,
    ).values_list('codename', flat=True))

    assert TramitePermission.ACCESO_COORDINADOR in codenames
    assert TramitePermission.ACCESO_ANALISTA not in codenames


def test_analista_has_analista_perm_only(setup_roles_run):
    """Analista has acceso_analista but NOT acceso_coordinador."""
    group = setup_roles_run[BackOfficeRole.ANALISTA]
    codenames = set(group.permissions.filter(
        codename__in=TRAMITES_CUSTOM_PERMISSIONS,
    ).values_list('codename', flat=True))

    assert TramitePermission.ACCESO_ANALISTA in codenames
    assert TramitePermission.ACCESO_COORDINADOR not in codenames


# ---------------------------------------------------------------------------
# Sidebar visibility via HTML
# ---------------------------------------------------------------------------


def _get_admin_html(client):
    """Fetch /admin/ and return the decoded HTML content."""
    response = client.get('/admin/')
    assert response.status_code == 200
    return response.content.decode('utf-8')


def test_administrador_sees_all_sidebar_links(role_user):
    """Administrador sees Usuarios + all 4 trámites links."""
    user = role_user(BackOfficeRole.ADMINISTRADOR)
    client = Client()
    client.force_login(user)

    html = _get_admin_html(client)

    # Auth link
    assert 'Usuarios' in html
    # Analista links
    assert 'Mis trámites' in html
    assert 'Disponibles' in html
    # Coordinador links
    assert 'Trámites en curso' in html
    assert 'Trámites finalizados' in html


def test_coordinador_sees_coordinador_links(role_user):
    """Coordinador sees Trámites en curso + Finalizados but NOT Mis trámites/Disponibles."""
    user = role_user(BackOfficeRole.COORDINADOR)
    client = Client()
    client.force_login(user)

    html = _get_admin_html(client)

    # No auth link
    assert 'Usuarios' not in html
    # No analista links
    assert 'Mis trámites' not in html
    assert 'Disponibles' not in html
    # Yes coordinador links
    assert 'Trámites en curso' in html
    assert 'Trámites finalizados' in html


def test_analista_sees_analista_links(role_user):
    """Analista sees Mis trámites + Disponibles but NOT en curso/Finalizados."""
    user = role_user(BackOfficeRole.ANALISTA)
    client = Client()
    client.force_login(user)

    html = _get_admin_html(client)

    # No auth link
    assert 'Usuarios' not in html
    # Yes analista links
    assert 'Mis trámites' in html
    assert 'Disponibles' in html
    # No coordinador links
    assert 'Trámites en curso' not in html
    assert 'Trámites finalizados' not in html


def test_administrador_sees_usuarios_link(role_user):
    """Administrador sees the Usuarios link (has auth.view_user)."""
    user = role_user(BackOfficeRole.ADMINISTRADOR)
    client = Client()
    client.force_login(user)

    html = _get_admin_html(client)
    assert 'Usuarios' in html


def test_coordinador_no_usuarios_link(role_user):
    """Coordinador does NOT see the Usuarios link."""
    user = role_user(BackOfficeRole.COORDINADOR)
    client = Client()
    client.force_login(user)

    html = _get_admin_html(client)
    assert 'Usuarios' not in html


def test_analista_no_usuarios_link(role_user):
    """Analista does NOT see the Usuarios link."""
    user = role_user(BackOfficeRole.ANALISTA)
    client = Client()
    client.force_login(user)

    html = _get_admin_html(client)
    assert 'Usuarios' not in html
