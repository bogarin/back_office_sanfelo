# Multi-Database Router Documentation

## Overview

The `MultiDatabaseRouter` class in `sanfelipe/db_router.py` provides intelligent routing of database operations between SQLite (for Django's built-in authentication system) and PostgreSQL (for business domain data).

## Architecture

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
│                      │           │  (legacy tables)     │
└──────────────────────┘           └──────────────────────┘
```

## Configuration

The router is configured in `sanfelipe/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db' / 'db.sqlite3'),
    },
    'business': env.db('DATABASE_URL'),
}

DATABASE_ROUTERS = ['sanfelipe.db_router.router_instance']
```

## Routing Logic

### Auth Apps → SQLite (default)
- `auth` - User, Group, Permission models
- `contenttypes` - ContentType framework
- `admin` - Django admin interface
- `sessions` - Session storage
- `messages` - Messages framework
- `staticfiles` - Static files management
- `debug_toolbar` - Debug tools

### Business Apps → PostgreSQL (business)
- `catalogos` - Catalog data (master tables)
- `costos` - Cost management
- `bitacora` - Audit logs/trails
- `tramites` - Business processes/tramites
- `core` - Core business models

## Router Methods

### `db_for_read(model, **hints)`

Suggests the database for read queries based on the model's app label.

**Example:**
```python
# These queries go to SQLite (default)
User.objects.all()
Permission.objects.filter(codename='add_tramite')

# These queries go to PostgreSQL (business)
Tramite.objects.filter(estado='pendiente')
Catalogo.objects.all()
```

### `db_for_write(model, **hints)`

Suggests the database for write queries (INSERT, UPDATE, DELETE).

**Example:**
```python
# Write to SQLite
user = User.objects.create_user(username='operador1')
user.save()

# Write to PostgreSQL
tramite = Tramite.objects.create(
    cat_actividad_id=1,
    cat_estatus_id=1,
    fecha_inicio=timezone.now()
)
tramite.save()
```

### `allow_relation(obj1, obj2, **hints)`

Controls whether relations (ForeignKeys, ManyToMany) are allowed between models.

**Rules:**
- ✅ Relations within auth apps (both in SQLite)
- ✅ Relations within business apps (both in PostgreSQL)
- ❌ Cross-database relations (e.g., User → Tramite)

**Example:**
```python
# ✅ Allowed - both in SQLite
user = User.objects.get(pk=1)
group = Group.objects.get(pk=1)
user.groups.add(group)  # Same database (SQLite)

# ✅ Allowed - both in PostgreSQL
tramite = Tramite.objects.get(pk=1)
catalogo = Catalogo.objects.get(pk=1)
tramite.catalogo = catalogo  # Same database (PostgreSQL)

# ❌ NOT ALLOWED - cross-database
user = User.objects.get(pk=1)  # SQLite
tramite = Tramite.objects.get(pk=1)  # PostgreSQL
# Do NOT create: tramite.usuario = user
# This would cause a database error at runtime
```

**Workaround for cross-database relations:**
```python
# Store user ID instead of user object
tramite = Tramite.objects.create(
    cat_actividad_id=1,
    cat_estatus_id=1,
    usuario_id=request.user.pk,  # Store FK as integer
)
```

### `allow_migrate(db, app_label, model_name, **hints)`

Controls whether migrations run for a particular app on a database.

**Rules:**
- Auth apps: migrations only on SQLite (`default`)
- Business apps: migrations never run (managed=False, external DB)

**Example:**
```bash
# Run migrations for auth apps
python manage.py migrate

# Run migrations for specific database
python manage.py migrate --database=default

# Business apps will not create tables (managed=False)
python manage.py migrate --database=business  # No-op for business apps
```

## Best Practices

### 1. Avoid Cross-Database ForeignKeys

❌ **Don't do this:**
```python
# models.py in tramites app
class Tramite(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Cross-DB!
```

✅ **Do this instead:**
```python
# models.py in tramites app
class Tramite(models.Model):
    usuario_id = models.IntegerField(null=True, blank=True)  # Integer FK

# In your code
def create_tramite(user_id):
    tramite = Tramite.objects.create(
        usuario_id=user_id,
        cat_actividad_id=1,
        cat_estatus_id=1,
    )
    return tramite
```

### 2. Use Explicit Database Aliases for Complex Queries

When you need to be explicit about which database to use:

```python
from django.db import connections

# Query auth database explicitly
with connections['default'].cursor() as cursor:
    cursor.execute("SELECT * FROM auth_user")
    users = cursor.fetchall()

# Query business database explicitly
with connections['business'].cursor() as cursor:
    cursor.execute("SELECT * FROM tramite_tramite")
    tramites = cursor.fetchall()
```

### 3. Transaction Management

When working with multiple databases, use `transaction.atomic` with specific database:

```python
from django.db import transaction

with transaction.atomic(using='default'):
    # SQLite operations
    user = User.objects.create_user(username='newuser')
    group = Group.objects.create(name='newgroup')
    user.groups.add(group)

with transaction.atomic(using='business'):
    # PostgreSQL operations
    tramite = Tramite.objects.create(
        cat_actividad_id=1,
        cat_estatus_id=1,
    )
```

### 4. Testing

When writing tests, ensure you're testing with the correct database:

```python
from django.test import TestCase

class TramiteTestCase(TestCase):
    def test_create_tramite(self):
        # This will use 'business' database automatically
        tramite = Tramite.objects.create(
            cat_actividad_id=1,
            cat_estatus_id=1,
        )
        self.assertEqual(tramite.cat_estatus_id, 1)

class AuthTestCase(TestCase):
    def test_create_user(self):
        # This will use 'default' database automatically
        user = User.objects.create_user(username='testuser')
        self.assertEqual(user.username, 'testuser')
```

### 5. Logging Queries

To debug which database queries are going where:

```python
# settings.py
LOGGING = {
    # ...
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Enable SQL logging
            'propagate': False,
        },
    },
}
```

## Troubleshooting

### Issue: "no such table: auth_user"

**Cause:** Database router not configured or misconfigured.

**Solution:** Ensure `DATABASE_ROUTERS` is set in settings.py:
```python
DATABASE_ROUTERS = ['sanfelipe.db_router.router_instance']
```

### Issue: "Cannot create a relation between models on different databases"

**Cause:** Attempting to create a cross-database ForeignKey.

**Solution:** Store the foreign key as an integer field instead:
```python
usuario_id = models.IntegerField(null=True)  # Instead of ForeignKey(User)
```

### Issue: Migrations not running for business apps

**Cause:** Business apps use `managed=False` to prevent table creation.

**Solution:** This is intentional. Business tables are managed externally.
Ensure tables exist in PostgreSQL before using the app.

### Issue: Query routing to wrong database

**Cause:** App label not recognized or misclassified.

**Solution:** Check the `AUTH_APPS` and `BUSINESS_APPS` sets in `db_router.py`:
```python
AUTH_APPS = frozenset({'auth', 'contenttypes', ...})
BUSINESS_APPS = frozenset({'catalogos', 'costos', ...})
```

## Migration from Old Router

If migrating from the old `sanfelipe.routers.BusinessDatabaseRouter`, the new router is a drop-in replacement:

**Old settings.py:**
```python
DATABASE_ROUTERS = ['sanfelipe.routers.BusinessDatabaseRouter']
```

**New settings.py:**
```python
DATABASE_ROUTERS = ['sanfelipe.db_router.router_instance']
```

No code changes required in your models or views!

## Performance Considerations

1. **Connection Pooling:** Each database maintains its own connection pool. SQLite has minimal overhead; PostgreSQL connections are more expensive.

2. **Query Optimization:** The router adds minimal overhead. The primary performance cost comes from cross-database operations (avoid them).

3. **Migrations:** Business apps don't run migrations, which speeds up deploy times.

## Security Considerations

1. **Separation of Concerns:** Auth data (SQLite) and business data (PostgreSQL) are physically separated, providing an additional layer of security.

2. **Privilege Separation:** You can configure different database users for SQLite and PostgreSQL with appropriate permissions.

3. **Data Isolation:** A breach in the business database won't compromise user authentication data.

## References

- [Django Multiple Databases Documentation](https://docs.djangoproject.com/en/stable/topics/db/multi-db/)
- [Database Router API](https://docs.djangoproject.com/en/stable/topics/db/multi-db/#automatic-database-routing)
- [Django 6.x Release Notes](https://docs.djangoproject.com/en/stable/releases/6.0/)
