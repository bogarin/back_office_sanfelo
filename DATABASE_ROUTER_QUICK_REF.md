# Database Router Quick Reference

## Quick Start

The database router is already configured and working. Here's what you need to know:

## What Goes Where?

### SQLite (default)
- **Users, Groups, Permissions** (`auth`)
- **Admin interface** (`admin`)
- **Sessions** (`sessions`)
- **Debug tools** (`debug_toolbar`)

### PostgreSQL (business)
- **Trámites** (`tramites`)
- **Catalogs** (`catalogos`)
- **Costs** (`costos`)
- **Audit logs** (`bitacora`)
- **Core models** (`core`)

## Common Patterns

### Querying Data

```python
# SQLite - just query normally
from django.contrib.auth.models import User
users = User.objects.all()

# PostgreSQL - just query normally
from tramites.models import Tramite
tramites = Tramite.objects.filter(estado='pendiente')
```

### Cross-Database References

```python
# ❌ WRONG - don't use ForeignKey across databases
class Tramite(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

# ✅ RIGHT - use integer field
class Tramite(models.Model):
    usuario_id = models.IntegerField(null=True)
```

### Creating Related Records

```python
# Create a tramite with user reference
def create_tramite(user_id):
    tramite = Tramite.objects.create(
        usuario_id=user_id,  # Use integer, not User object
        cat_actividad_id=1,
        cat_estatus_id=1,
    )
    return tramite
```

### Transactions

```python
from django.db import transaction

# SQLite transaction
with transaction.atomic(using='default'):
    user = User.objects.create_user(username='newuser')

# PostgreSQL transaction
with transaction.atomic(using='business'):
    tramite = Tramite.objects.create(...)
```

## Testing

```bash
# Run router tests
uv run python tests/test_db_router.py

# Django check
uv run manage.py check
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `no such table: auth_user` | Check `DATABASE_ROUTERS` in settings.py |
| `Cannot create relation between models on different databases` | Use `usuario_id` instead of `usuario` FK |
| Migrations not running for business apps | This is intentional (managed=False) |

## Documentation

- Full guide: `DATABASE_ROUTER.md`
- Implementation details: `ROUTER_IMPLEMENTATION_SUMMARY.md`
- Router code: `sanfelipe/db_router.py`
- Tests: `tests/test_db_router.py`

## Configuration

```python
# sanfelipe/settings.py
DATABASE_ROUTERS = ['sanfelipe.db_router.router_instance']
```

No changes needed to your code - the router handles everything automatically!
