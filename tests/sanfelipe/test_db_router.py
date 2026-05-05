"""Tests for ModelBasedRouter.

Validates database routing logic based on model configuration:
- Auth models → default database
- Business models → correct database per @register_model
- Cross-database relations are properly blocked
- Migration routing with label-based fallback
"""

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from core.db_router import ModelBasedRouter
from core.model_config import AccessPattern, get_model_config, get_model_config_by_label


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def router():
    """Fresh ModelBasedRouter instance."""
    return ModelBasedRouter()


@pytest.fixture
def business_models():
    """Import and return business models (skip if unavailable)."""
    from tramites.models import Actividad, Tramite

    return {'Tramite': Tramite, 'Actividad': Actividad}


# ---------------------------------------------------------------------------
# Auth / default routing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_auth_models_route_to_default(router):
    """Auth models (Permission, Group, ContentType) → 'default' database."""
    assert router.db_for_read(Permission) == 'default'
    assert router.db_for_write(Permission) == 'default'
    assert router.db_for_read(Group) == 'default'
    assert router.db_for_write(Group) == 'default'
    assert router.db_for_read(ContentType) == 'default'
    assert router.db_for_write(ContentType) == 'default'


@pytest.mark.django_db
def test_user_model_routes_to_default(router):
    """Custom User model → 'default' database with FULL_ACCESS."""
    from core.models import User

    assert router.db_for_read(User) == 'default'
    assert router.db_for_write(User) == 'default'

    config = get_model_config(User)
    assert config is not None
    assert config.db_alias == 'default'
    assert config.access_pattern == AccessPattern.FULL_ACCESS
    assert config.allow_migrations is True


# ---------------------------------------------------------------------------
# Business model routing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_business_models_routing(router, business_models):
    """Tramite → default, Actividad → backend (per @register_model)."""
    Tramite = business_models['Tramite']
    Actividad = business_models['Actividad']

    # Tramite → default
    assert router.db_for_read(Tramite) == 'default'
    assert router.db_for_write(Tramite) == 'default'

    # Actividad → backend
    assert router.db_for_read(Actividad) == 'backend'
    assert router.db_for_write(Actividad) == 'backend'

    # Verify configs
    tramite_config = get_model_config(Tramite)
    assert tramite_config is not None
    assert tramite_config.db_alias == 'default'

    actividad_config = get_model_config(Actividad)
    assert actividad_config is not None
    assert actividad_config.db_alias == 'backend'


# ---------------------------------------------------------------------------
# Cross-database relation blocking
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cross_db_relations_blocked(router, business_models):
    """Relations across different databases must be blocked."""
    from core.models import User

    Tramite = business_models['Tramite']
    Actividad = business_models['Actividad']

    # Cross-DB: Tramite (default) ↔ Actividad (backend) → blocked
    assert router.allow_relation(Tramite, Actividad) is False

    # Both unregistered: Group ↔ Permission → allowed
    assert router.allow_relation(Group, Permission) is True

    # Same-DB: Tramite (default) ↔ User (default) → allowed
    assert router.allow_relation(Tramite, User) is True

    # One registered (default), one unregistered: Tramite ↔ Group → allowed
    assert router.allow_relation(Tramite, Group) is True

    # One registered (backend), one unregistered: Actividad ↔ Group → blocked
    assert router.allow_relation(Actividad, Group) is False


# ---------------------------------------------------------------------------
# Migration routing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_read_only_models_block_migrations(router, business_models):
    """READ_ONLY models should not allow migrations on any database."""
    Tramite = business_models['Tramite']
    Actividad = business_models['Actividad']

    tramite_config = get_model_config(Tramite)
    assert tramite_config.access_pattern == AccessPattern.READ_ONLY
    assert tramite_config.allow_migrations is False

    actividad_config = get_model_config(Actividad)
    assert actividad_config.access_pattern == AccessPattern.READ_ONLY
    assert actividad_config.allow_migrations is False


@pytest.mark.django_db
def test_allow_migrate_label_lookup(router):
    """Label-based lookup works for migration stubs (type()-created classes).

    During migrations Django creates stub classes via type() that are
    distinct objects from the real model classes.  Identity-based lookup
    fails for these stubs, but (app_label, model_name) are stable strings.
    """
    # Backend models: allow_migrations=False → blocked on ANY database
    assert router.allow_migrate('default', 'tramites', 'tramitecatalogo') is False
    assert router.allow_migrate('backend', 'tramites', 'tramitecatalogo') is False

    # Tramite (default, READ_ONLY, allow_migrations=False) → blocked
    assert router.allow_migrate('default', 'tramites', 'tramite') is False

    # Actividades (backend, APPEND_ONLY, allow_migrations=False) → blocked
    assert router.allow_migrate('backend', 'tramites', 'actividades') is False

    # Core User: allow_migrations=True, db='default'
    assert router.allow_migrate('default', 'core', 'user') is True
    assert router.allow_migrate('backend', 'core', 'user') is False

    # Unregistered models: default behavior → True (allow)
    assert router.allow_migrate('default', 'auth', 'group') is True
    assert router.allow_migrate('default', 'contenttypes', 'contenttype') is True


# ---------------------------------------------------------------------------
# Unregistered models / label registry
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_unregistered_models_route_to_default(router):
    """Unregistered models (auth, contenttypes) → 'default' database."""
    assert router.db_for_read(Group) == 'default'
    assert router.db_for_write(Permission) == 'default'
    assert router.db_for_read(ContentType) == 'default'


@pytest.mark.django_db
def test_label_registry_populated():
    """Label-based registry matches @register_model declarations."""
    config = get_model_config_by_label('tramites', 'tramite')
    assert config is not None
    assert config.db_alias == 'default'

    config = get_model_config_by_label('tramites', 'tramitecatalogo')
    assert config is not None
    assert config.db_alias == 'backend'

    config = get_model_config_by_label('core', 'user')
    assert config is not None
    assert config.db_alias == 'default'
    assert config.allow_migrations is True

    # Unregistered models should return None
    assert get_model_config_by_label('auth', 'group') is None
