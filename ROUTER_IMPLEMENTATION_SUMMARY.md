# Database Router Implementation Summary

## Overview

This document summarizes the implementation of the `MultiDatabaseRouter` class for the Backoffice Trámites project, which enables intelligent routing of database operations between SQLite (for Django authentication) and PostgreSQL (for business domain data).

## Implementation Details

### Files Created/Modified

1. **NEW: `sanfelipe/db_router.py`** - The comprehensive multi-database router
2. **MODIFIED: `sanfelipe/settings.py`** - Updated to use the new router
3. **NEW: `DATABASE_ROUTER.md`** - Comprehensive documentation
4. **NEW: `tests/test_db_router.py`** - Test suite for the router

### Router Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Django Application                      │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌──────────────────────┐           ┌──────────────────────┐
│    SQLite (default)  │           │ PostgreSQL (business)│
│                      │           │                      │
│  - auth              │           │  - catalogos         │
│  - contenttypes      │           │  - costos            │
│  - admin             │           │  - bitacora          │
│  - sessions          │           │  - tramites          │
│  - messages          │           │  - core              │
│  - staticfiles       │           │                      │
│  - debug_toolbar     │           │  (managed=False)     │
└──────────────────────┘           └──────────────────────┘
```

### Key Features

#### 1. Intelligent App-Based Routing

The router automatically routes database operations based on the app label:

**Auth Apps → SQLite (default)**
- `auth` - User, Group, Permission models
- `contenttypes` - ContentType framework
- `admin` - Django admin interface
- `sessions` - Session storage
- `messages` - Messages framework
- `staticfiles` - Static files management
- `debug_toolbar` - Debug tools

**Business Apps → PostgreSQL (business)**
- `catalogos` - Catalog data (master tables)
- `costos` - Cost management
- `bitacora` - Audit logs/trails
- `tramites` - Business processes/tramites
- `core` - Core business models

#### 2. Complete Router Method Implementation

All four required router methods are fully implemented:

```python
def db_for_read(model, **hints) -> str | None:
    """Routes read queries to the appropriate database."""

def db_for_write(model, **hints) -> str | None:
    """Routes write queries to the appropriate database."""

def allow_relation(obj1, obj2, **hints) -> bool | None:
    """Controls whether relations are allowed between models."""

def allow_migrate(db, app_label, model_name, **hints) -> bool:
    """Controls whether migrations run for a model on a database."""
```

#### 3. Type Hints and Documentation

All methods include:
- Comprehensive docstrings with examples
- Type hints following PEP 484
- Clear parameter descriptions
- Return value explanations
- Usage examples

#### 4. Edge Case Handling

The router properly handles:
- **Cross-database relations**: Blocked to prevent runtime errors
- **Migration routing**: Auth apps → SQLite, Business apps → None (managed=False)
- **Unknown apps**: Returns None to let Django decide
- **Model instances vs classes**: Both handled correctly
- **Hints**: Checks for model hints in addition to direct model parameter

#### 5. Backward Compatibility

Includes legacy `allow_syncdb` method for Django < 1.7 compatibility.

## Configuration

### settings.py Changes

```python
# DATABASE_ROUTERS configuration
DATABASE_ROUTERS = ['sanfelipe.db_router.router_instance']
```

### Database Configuration

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db' / 'db.sqlite3'),
    },
    'business': env.db('DATABASE_URL'),
}
```

## Test Results

All tests passed successfully:

```
=== Testing Router Attributes ===
✓ All auth apps in AUTH_APPS
✓ All business apps in BUSINESS_APPS
✓ Database aliases correctly defined

=== Testing db_for_read Routing ===
✓ Auth models route to 'default' (SQLite)
✓ Business models route to 'business' (PostgreSQL)

=== Testing db_for_write Routing ===
✓ Auth models route to 'default' (SQLite)
✓ Business models route to 'business' (PostgreSQL)

=== Testing allow_relation ===
✓ Same-database relations allowed
✓ Cross-database relations blocked

=== Testing allow_migrate ===
✓ Auth apps migrate only on SQLite
✓ Business apps never migrate (managed=False)
```

## Usage Examples

### Reading Data

```python
# Automatically routed to SQLite (default)
users = User.objects.all()
permissions = Permission.objects.filter(codename='add_tramite')

# Automatically routed to PostgreSQL (business)
tramites = Tramite.objects.filter(estado='pendiente')
catalogos = CatActividad.objects.all()
```

### Writing Data

```python
# SQLite operations
user = User.objects.create_user(username='operador1')
user.save()

# PostgreSQL operations
tramite = Tramite.objects.create(
    cat_actividad_id=1,
    cat_estatus_id=1,
    fecha_inicio=timezone.now()
)
tramite.save()
```

### Relations

```python
# ✅ Allowed - same database (SQLite)
user.groups.add(group)

# ✅ Allowed - same database (PostgreSQL)
tramite.catalogo = catalogo

# ❌ NOT ALLOWED - cross-database
# Do NOT do: tramite.usuario = user (causes runtime error)
# Instead: tramite.usuario_id = user.pk
```

### Migrations

```bash
# Migrate auth apps to SQLite
python manage.py migrate

# Migrate specific database
python manage.py migrate --database=default

# Business apps won't migrate (managed=False)
python manage.py migrate --database=business  # No-op
```

## Best Practices

### 1. Avoid Cross-Database ForeignKeys

❌ **Don't do this:**
```python
class Tramite(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Cross-DB!
```

✅ **Do this instead:**
```python
class Tramite(models.Model):
    usuario_id = models.IntegerField(null=True)  # Integer FK
```

### 2. Use Explicit Database Aliases for Complex Queries

```python
from django.db import connections

with connections['default'].cursor() as cursor:
    cursor.execute("SELECT * FROM auth_user")
    users = cursor.fetchall()
```

### 3. Transaction Management

```python
from django.db import transaction

with transaction.atomic(using='default'):
    # SQLite operations
    user = User.objects.create_user(username='newuser')

with transaction.atomic(using='business'):
    # PostgreSQL operations
    tramite = Tramite.objects.create(...)
```

## Migration from Old Router

The new router is a drop-in replacement for the old `sanfelipe.routers.BusinessDatabaseRouter`:

**Before:**
```python
DATABASE_ROUTERS = ['sanfelipe.routers.BusinessDatabaseRouter']
```

**After:**
```python
DATABASE_ROUTERS = ['sanfelipe.db_router.router_instance']
```

No code changes required in models or views!

## Key Improvements Over Old Router

1. **More Comprehensive App Coverage**
   - Added `core` app to business apps
   - Added `messages`, `staticfiles`, `debug_toolbar` to auth apps

2. **Better Type Safety**
   - Full type hints for all methods
   - Explicit return types
   - Proper handling of Model vs type[Model]

3. **Enhanced Documentation**
   - Comprehensive docstrings with examples
   - Architecture diagrams
   - Usage examples
   - Troubleshooting guide

4. **Improved Edge Case Handling**
   - Better hint processing
   - Unknown app handling
   - Model instance vs class detection

5. **Test Coverage**
   - Complete test suite
   - All scenarios tested
   - Clear test output

6. **Performance Considerations**
   - Frozen sets for fast lookups
   - Minimal overhead
   - Efficient routing logic

## Django 6.x Compatibility

The router follows Django 6.x best practices and documentation:

- Uses modern type hints
- Follows PEP 8 style guide
- Implements all required router methods
- Properly handles hints parameter
- Returns None instead of raising exceptions for unknown cases

## Security Considerations

1. **Data Separation**: Auth data and business data are physically separated
2. **Privilege Separation**: Different database users can be configured
3. **Cross-DB Prevention**: Router prevents accidental cross-database operations
4. **Audit Trail**: Bitacora app maintains audit logs in PostgreSQL

## Performance Impact

- **Router Overhead**: Minimal (simple set lookups)
- **Connection Pooling**: Each database maintains its own pool
- **Query Optimization**: Router adds no query time overhead
- **Migration Speed**: Business apps skip migrations (faster deploys)

## Troubleshooting

### Issue: "no such table: auth_user"
**Solution:** Ensure `DATABASE_ROUTERS` is set in settings.py

### Issue: "Cannot create a relation between models on different databases"
**Solution:** Use integer fields instead of ForeignKeys for cross-database relations

### Issue: Migrations not running for business apps
**Solution:** This is intentional (managed=False). Ensure tables exist in PostgreSQL

## Next Steps

1. ✅ Router implemented and tested
2. ✅ Documentation created
3. ✅ Settings updated
4. ✅ Test suite passing

### Recommended Actions

1. **Review the documentation**: Read `DATABASE_ROUTER.md` for detailed usage
2. **Run the test suite**: Verify router functionality with `uv run python tests/test_db_router.py`
3. **Test in development**: Ensure all queries route to correct databases
4. **Audit models**: Check for any accidental cross-database ForeignKeys
5. **Update team**: Share this document with the development team

## Conclusion

The `MultiDatabaseRouter` provides a robust, Pythonic solution for multi-database routing in the Backoffice Trámites project. It follows Django best practices, includes comprehensive documentation, and has been thoroughly tested. The implementation successfully separates auth and business data while maintaining clean, maintainable code.
