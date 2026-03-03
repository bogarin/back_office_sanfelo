# Tests

This directory contains the complete test suite for the backoffice_tramites Django project using pytest-django.

## Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures + pytest config
├── factories/                 # factory-boy factories
│   ├── __init__.py
│   ├── auth.py                # User, Group, Permission factories
│   ├── catalogos.py           # Catalog model factories
│   ├── costos.py              # Costo, Uma factories
│   ├── bitacora.py            # Bitacora factories
│   └── tramites.py            # Tramite factory
├── core/
│   ├── __init__.py
│   ├── test_admin.py           # Admin site tests
│   ├── test_permissions.py     # Role-based access tests
│   ├── test_audit_trail.py     # Audit logging tests
│   ├── test_management.py      # Management command tests
│   ├── test_integration.py     # RBAC integration tests
│   └── test_error_handling.py  # Error handling tests
├── sanfelipe/
│   ├── __init__.py
│   ├── test_db_router.py        # Database router tests
│   └── test_csp.py            # CSP configuration tests
├── catalogos/
│   ├── __init__.py
│   ├── test_models.py           # Catalog model tests
│   └── test_admin.py           # Catalog admin tests
├── costos/
│   ├── __init__.py
│   ├── test_models.py           # Costo, Uma tests
│   └── test_admin.py           # Costos admin tests
├── bitacora/
│   ├── __init__.py
│   ├── test_models.py           # Bitacora tests
│   └── test_admin.py           # Bitacora admin tests
└── tramites/
    ├── __init__.py
    ├── test_models.py           # Tramite tests
    ├── test_admin.py           # Tramites admin tests
    └── test_views.py           # View tests (placeholder)
```

## How to Run Tests

### Run all tests
```bash
just test
```

### Run tests for a specific app
```bash
just test-app core
just test-app catalogos
just test-app costos
just test-app bitacora
just test-app tramites
just test-app sanfelipe
```

### Run tests with coverage
```bash
just test-cov
```

### Run tests skipping slow tests
```bash
just test-fast
```

### Run tests re-creating database
```bash
just test-create-db
```

### Run specific test file
```bash
just test tests/core/test_permissions.py
```

### Run specific test
```bash
just test tests/core/test_permissions.py::TestRoleBasedAccessMixin::test_superuser_has_full_access
```

### Run tests with verbose output
```bash
TESTING=1 uv run pytest tests/ -v
```

## Test Configuration

### Pytest Configuration

The test suite is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = 'sanfelipe.settings_test'
django_find_project = false
pythonpath = ['.']
testpaths = ['tests']
python_files = ['test_*.py', '*_test.py']
python_classes = ['Test*']
python_functions = ['test_*']
addopts = ['--reuse-db', '--tb=short', '--verbose']
markers = [
    'slow: marks tests as slow (deselect with -m "not slow")',
    'integration: marks tests as integration tests',
]
```

### Database Configuration

Tests use `sanfelipe.settings_test` which:
- Uses SQLite for all databases
- Routes all apps to `default` database via `TestRouter`
- Enables `managed=True` for business models during testing
- Uses dummy cache backend

## Writing New Tests

### Test Structure

Tests should follow Django testing best practices:

```python
from django.test import TestCase

class TestMyFeature(TestCase):
    """Test suite for MyFeature."""

    def setUp(self):
        """Set up test fixtures."""
        self.obj = MyModelFactory()

    def test_something(self):
        """Test something about MyFeature."""
        self.assertEqual(self.obj.field, "expected value")
```

### Using Fixtures

Shared fixtures are available in `tests/conftest.py`:

```python
def test_with_superuser(superuser, admin_client):
    """Test using superuser fixture."""
    response = admin_client.get('/admin/')
    self.assertEqual(response.status_code, 200)

def test_with_admin_user(admin_user):
    """Test using admin_user fixture."""
    # admin_user has Administrador group and is_staff
    self.assertTrue(admin_user.is_staff)
```

### Using Factories

Create test data using factory-boy:

```python
from tests.factories import CatTramiteFactory, TramiteFactory

def test_with_factory_data():
    """Test using factory data."""
    tramite = TramiteFactory()
    self.assertIsNotNone(tramite.folio)
```

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    """Mark slow tests to allow skipping."""
    pass

@pytest.mark.integration
def test_integration():
    """Mark integration tests."""
    pass
```

### Class-Based Tests

All tests preserve the class-based structure (no conversion to function style):

```python
from django.test import TestCase

class TestMyModel(TestCase):
    """Test suite for MyModel - class-based as required."""

    def setUp(self):
        """Set up test fixtures."""
        self.instance = MyModelFactory()

    def test_method_one(self):
        """Test one aspect."""
        pass

    def test_method_two(self):
        """Test another aspect."""
        pass
```

## Factories

Factory-boy factories are available in `tests/factories/`:

```python
from tests.factories import (
    # Auth factories
    UserFactory,
    SuperUserFactory,
    AdminUserFactory,
    OperadorUserFactory,
    GroupFactory,
    PermissionFactory,

    # Catalogos factories
    CatTramiteFactory,
    CatEstatusFactory,
    CatUsuarioFactory,
    CatPeritoFactory,
    CatActividadFactory,
    CatCategoriaFactory,
    CatIncisoFactory,
    CatRequisitoFactory,
    CatTipoFactory,

    # Costos factories
    CostoFactory,
    UmaFactory,

    # Bitacora factories
    BitacoraFactory,

    # Tramites factories
    TramiteFactory,
)
```

Each factory provides sensible defaults:
- Uses `Sequence` for unique fields
- Uses `Faker` for realistic data
- Handles IntegerField relationships correctly

## Test Coverage

Current test suite includes:

- **Core tests (31 tests):**
  - Permission mixin tests
  - Audit trail tests
  - Admin site tests
  - Management command tests
  - Integration tests
  - Error handling tests

- **Sanfelipe tests (7 tests):**
  - Database router tests
  - CSP configuration tests

- **Catalogos tests (18 tests):**
  - Model tests for all catalog models
  - Admin configuration tests

- **Costos tests (6 tests):**
  - Model tests for Costo and Uma
  - Admin configuration tests

- **Bitacora tests (6 tests):**
  - Model tests
  - Admin configuration tests

- **Tramites tests (13 tests):**
  - Model tests
  - Admin configuration tests
  - View tests (placeholder)

**Total: 81 tests**

## Notes

1. **Preserved class-based tests** - All tests use `django.test.TestCase` class-based structure as required

2. **TestRouter for testing** - Uses `TestRouter` which routes all databases to SQLite, simplifying multi-database testing

3. **Migrations for testing** - Migrations are created for testing purposes but won't run in production due to `MultiDatabaseRouter.allow_migrate()` returning `False` for business apps

4. **managed=True during testing** - Business models use `managed = getattr(settings, 'TESTING', False)` to enable table creation during tests

5. **factory-boy integration** - All test data creation uses factory-boy for consistency and maintainability

6. **Shared fixtures** - Common fixtures (superuser, admin_user, operador_user, etc.) are available in `tests/conftest.py`
