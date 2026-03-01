# Environment Variables Reference

Complete reference of all environment variables used in the Backoffice Trámites project.

## Quick Reference

| Category | Variable | Required | Default | Description |
|----------|------------|-----------|-------------|
| **Core** | `DJANGO_SECRET_KEY` | ✅ Yes | Cryptographic signing key |
| | `DJANGO_DEBUG` | No | `False` | Enable debug mode |
| | `DJANGO_ALLOWED_HOSTS` | No | `*` | Allowed hostnames |
| | `TESTING` | No | `False` | Enable test mode |
| **Database** | `DATABASE_URL` | ✅ Yes | PostgreSQL connection URL |
| | `DJANGO_SQLITE_DB_PATH` | No | `db.sqlite3` | SQLite database path |
| **Debug** | `DJANGO_INTERNAL_IPS` | No | `127.0.0.1,0.0.0.0` | Debug toolbar IPs |
| | `DJANGO_DEBUG_SQL` | No | `False` | Log SQL queries |
| | `DJANGO_LOG_LEVEL` | No | `INFO` | Logging level |
| **Security** | `DJANGO_SECURE_CONTENT_TYPE_NOSNIFF` | No | `True` | Security header |
| | `DJANGO_SECURE_BROWSER_XSS_FILTER` | No | `True` | XSS protection header |
| | `DJANGO_SECURE_SSL_REDIRECT` | No | `False` | Force HTTPS |
| | `DJANGO_SESSION_COOKIE_SECURE` | No | `False` | Secure session cookies |
| | `DJANGO_CSRF_COOKIE_SECURE` | No | `False` | Secure CSRF cookies |
| **CSRF** | `DJANGO_CSRF_TRUSTED_ORIGINS` | No | `http://localhost,...` | Trusted origins |
| **Session** | `DJANGO_SESSION_COOKIE_AGE` | No | `3600` | Session timeout (seconds) |
| **Pagination** | `DJANGO_DEFAULT_PAGE_SIZE` | No | `25` | Items per page |
| **Email** | `DJANGO_EMAIL_BACKEND` | No | `console.EmailBackend` | Email backend |
| | `DJANGO_EMAIL_HOST` | No | `localhost` | SMTP server |
| | `DJANGO_EMAIL_PORT` | No | `587` | SMTP port |
| | `DJANGO_EMAIL_USE_TLS` | No | `True` | Use TLS |
| | `DJANGO_EMAIL_HOST_USER` | No | `""` | SMTP username |
| | `DJANGO_EMAIL_HOST_PASSWORD` | No | `""` | SMTP password |
| | `DJANGO_DEFAULT_FROM_EMAIL` | No | `noreply@...` | From address |
| **Docker** | `HTTP_PORT` | No | `8090` | Exposed HTTP port |
| **PostgreSQL** | `POSTGRES_DB` | No | `backoffice_tramites` | Database name |
| | `POSTGRES_USER` | No | `postgres` | Database user |
| | `POSTGRES_PASSWORD` | No | `postgres` | Database password |
| | `POSTGRES_PORT` | No | `5432` | Database port |

---

## Core Django Configuration

### DJANGO_SECRET_KEY
**Required:** Yes (production)

**Description:** Secret key for cryptographic signing. Must be unique and kept secret.

**Generate securely:**
```bash
# Using Python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Using OpenSSL
openssl rand -base64 48

# Using uv-secrets (recommended)
uv pip install uv-secrets
uv-secrets generate
```

**Example:**
```bash
# Development
DJANGO_SECRET_KEY=django-insecure-dev-key-ONLY-FOR-LOCAL-DEV

# Production (use a strong, random key)
DJANGO_SECRET_KEY=django-insecure-7#8j$@v9k5*8%7hjx-9@y0q6q^k5wz3!l#m^1v8p%0
```

### DJANGO_DEBUG
**Required:** No (default: `False`)

**Description:** Enable debug mode for development. Always `False` in production.

**Development:**
```bash
DJANGO_DEBUG=True
```

**Production:**
```bash
DJANGO_DEBUG=False
```

**Side effects when `True`:**
- Django Debug Toolbar enabled
- Detailed error pages
- Static files served by Django
- Debug SQL logging enabled if `DJANGO_DEBUG_SQL=True`
- Security settings relaxed (SSL redirects disabled)

### DJANGO_ALLOWED_HOSTS
**Required:** No (default: `*`)

**Description:** Comma-separated list of allowed hostnames.

**Development:**
```bash
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

**Production:**
```bash
DJANGO_ALLOWED_HOSTS=tramites.sanfelipe.gob.ar,localhost,127.0.0.1
```

### TESTING
**Required:** No (default: `False`)

**Description:** Enable test mode (disables cache, uses dummy cache).

**Usage:**
```bash
# Development
TESTING=False

# When running tests
TESTING=True
```

---

## Database Configuration

### DATABASE_URL
**Required:** Yes

**Description:** PostgreSQL connection string for business data (tramites, catalogos, costos, bitacora).

**Format:**
```
postgresql://[user[:password]@]host[:port][/database][?param=value]
```

**Development:**
```bash
DATABASE_URL=postgres://postgres:password@localhost:5432/business_db
```

**Docker:**
```bash
# In docker-compose.yml, constructed from envvars:
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
```

**Production:**
```bash
DATABASE_URL=postgresql://user:pass@prod-db.example.com:5432/backoffice
```

### DJANGO_SQLITE_DB_PATH
**Required:** No (default: `db.sqlite3`)

**Description:** Path to SQLite database file for Django auth, admin, sessions.

**Development:**
```bash
DJANGO_SQLITE_DB_PATH=db.sqlite3
```

**Docker:**
```bash
# Path inside container
DJANGO_SQLITE_DB_PATH=/app/db.sqlite3
```

**Production:**
```bash
# Absolute path
DJANGO_SQLITE_DB_PATH=/var/lib/django/db.sqlite3
```

---

## Debug & Development Settings

### DJANGO_INTERNAL_IPS
**Required:** No (default: `127.0.0.1,0.0.0.0`)

**Description:** Comma-separated list of IPs allowed to access Django Debug Toolbar.

**Only used when:** `DJANGO_DEBUG=True`

**Usage:**
```bash
# Local development only
DJANGO_INTERNAL_IPS=127.0.0.1,0.0.0.0

# Docker development
DJANGO_INTERNAL_IPS=172.18.0.1,172.18.0.2,172.18.0.3
```

### DJANGO_DEBUG_SQL
**Required:** No (default: `False`)

**Description:** Log SQL queries to console for debugging.

**Usage:**
```bash
# Enable SQL logging
DJANGO_DEBUG_SQL=True

# Disable (default)
DJANGO_DEBUG_SQL=False
```

**Output example:**
```
(0.001) SELECT "tramites_tramite"."id", "tramites_tramite"."folio" FROM "tramites_tramite" WHERE "tramites_tramite"."folio" = 'TRAM-2026-00001'
```

### DJANGO_LOG_LEVEL
**Required:** No (default: `INFO` if `DJANGO_DEBUG=False`, `DEBUG` if `DJANGO_DEBUG=True`)

**Description:** Logging level for application logs.

**Values:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Development:**
```bash
# Verbose logging
DJANGO_LOG_LEVEL=DEBUG

# Normal logging
DJANGO_LOG_LEVEL=INFO
```

**Production:**
```bash
# Only warnings and errors
DJANGO_LOG_LEVEL=WARNING

# Only errors
DJANGO_LOG_LEVEL=ERROR
```

---

## Security Settings (Production)

### DJANGO_SECURE_CONTENT_TYPE_NOSNIFF
**Required:** No (default: `True`)

**Description:** Add `X-Content-Type-Options: nosniff` header.

**Only used when:** `DJANGO_DEBUG=False`

### DJANGO_SECURE_BROWSER_XSS_FILTER
**Required:** No (default: `True`)

**Description:** Add `X-XSS-Protection` header.

**Only used when:** `DJANGO_DEBUG=False`

### DJANGO_SECURE_SSL_REDIRECT
**Required:** No (default: `False`)

**Description:** Redirect all non-HTTPS requests to HTTPS.

**Development:**
```bash
DJANGO_SECURE_SSL_REDIRECT=False  # No HTTPS in development
```

**Production:**
```bash
DJANGO_SECURE_SSL_REDIRECT=True  # Force HTTPS
```

**Only used when:** `DJANGO_DEBUG=False`

### DJANGO_SESSION_COOKIE_SECURE
**Required:** No (default: `False`)

**Description:** Mark session cookies as secure (HTTPS only).

**Development:**
```bash
DJANGO_SESSION_COOKIE_SECURE=False  # Allow HTTP in development
```

**Production:**
```bash
DJANGO_SESSION_COOKIE_SECURE=True  # Require HTTPS
```

**Only used when:** `DJANGO_DEBUG=False`

### DJANGO_CSRF_COOKIE_SECURE
**Required:** No (default: `False`)

**Description:** Mark CSRF cookies as secure (HTTPS only).

**Development:**
```bash
DJANGO_CSRF_COOKIE_SECURE=False
```

**Production:**
```bash
DJANGO_CSRF_COOKIE_SECURE=True
```

**Only used when:** `DJANGO_DEBUG=False`

---

## CSRF Configuration

### DJANGO_CSRF_TRUSTED_ORIGINS
**Required:** No (default: `http://localhost,http://127.0.0.1`)

**Description:** Comma-separated list of trusted origins for CSRF (without protocol).

**Format:** `http://localhost,http://127.0.0.1,http://example.com`

**Development:**
```bash
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1,http://dev.example:3000
```

**Production:**
```bash
DJANGO_CSRF_TRUSTED_ORIGINS=https://tramites.sanfelipe.gob.ar,https://api.sanfelipe.gob.ar
```

---

## Session Configuration

### DJANGO_SESSION_COOKIE_AGE
**Required:** No (default: `3600`)

**Description:** Session cookie age in seconds.

**Common values:**
```bash
# 1 hour
DJANGO_SESSION_COOKIE_AGE=3600

# 8 hours (work day)
DJANGO_SESSION_COOKIE_AGE=28800

# 24 hours
DJANGO_SESSION_COOKIE_AGE=86400

# 1 week
DJANGO_SESSION_COOKIE_AGE=604800
```

---

## Pagination Configuration

### DJANGO_DEFAULT_PAGE_SIZE
**Required:** No (default: `25`)

**Description:** Default number of items per page in list views.

**Usage:**
```bash
# Small pages
DJANGO_DEFAULT_PAGE_SIZE=10

# Medium pages (default)
DJANGO_DEFAULT_PAGE_SIZE=25

# Large pages
DJANGO_DEFAULT_PAGE_SIZE=50
# DJANGO_DEFAULT_PAGE_SIZE=100
```

---

## Email Configuration

### DJANGO_EMAIL_BACKEND
**Required:** No (default: `django.core.mail.backends.console.EmailBackend`)

**Description:** Email backend to use.

**Development:**
```bash
# Console backend (prints to stdout)
DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Production (SMTP):**
```bash
# SMTP backend
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

### DJANGO_EMAIL_HOST
**Required:** No (default: `localhost`)

**Description:** SMTP server hostname.

**Example:**
```bash
# Gmail (use app password)
DJANGO_EMAIL_HOST=smtp.gmail.com

# SendGrid
DJANGO_EMAIL_HOST=smtp.sendgrid.net

# Custom SMTP server
DJANGO_EMAIL_HOST=mail.sanfelipe.gob.ar
```

### DJANGO_EMAIL_PORT
**Required:** No (default: `587`)

**Description:** SMTP server port.

**Common ports:**
```bash
# SMTP with TLS
DJANGO_EMAIL_PORT=587

# SMTPS (implicit TLS)
DJANGO_EMAIL_PORT=465

# SMTP (no encryption, not recommended)
# DJANGO_EMAIL_PORT=25
```

### DJANGO_EMAIL_USE_TLS
**Required:** No (default: `True`)

**Description:** Use TLS when connecting to SMTP server.

**Usage:**
```bash
# Use TLS (recommended)
DJANGO_EMAIL_USE_TLS=True

# No TLS (not recommended)
# DJANGO_EMAIL_USE_TLS=False
```

### DJANGO_EMAIL_HOST_USER
**Required:** No (default: `""`)

**Description:** SMTP username (leave empty for console backend).

**Example:**
```bash
DJANGO_EMAIL_HOST_USER=noreply@sanfelipe.gob.ar
DJANGO_EMAIL_HOST_USER=apikey
```

### DJANGO_EMAIL_HOST_PASSWORD
**Required:** No (default: `""`)

**Description:** SMTP password (leave empty for console backend).

**Example:**
```bash
DJANGO_EMAIL_HOST_PASSWORD=your-password-here
DJANGO_EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxx.xxxxxxx
```

### DJANGO_DEFAULT_FROM_EMAIL
**Required:** No (default: `noreply@sanfelipe.gob.ar`)

**Description:** Default "From" email address.

**Example:**
```bash
DJANGO_DEFAULT_FROM_EMAIL=noreply@sanfelipe.gob.ar
DJANGO_DEFAULT_FROM_EMAIL=tramites@sanfelipe.gob.ar
```

---

## Docker Configuration

### HTTP_PORT
**Required:** No (default: `8090`)

**Description:** Port to expose the HTTP server on host.

**Usage:**
```bash
# Default port
HTTP_PORT=8090

# Custom port
HTTP_PORT=8000
```

**Docker:**
```bash
# Maps to container port 8080
HTTP_PORT=8090  # localhost:8090 → container:8080
```

---

## PostgreSQL Service Configuration

### POSTGRES_DB
**Required:** No (default: `backoffice_tramites`)

**Description:** PostgreSQL database name.

### POSTGRES_USER
**Required:** No (default: `postgres`)

**Description:** PostgreSQL user.

### POSTGRES_PASSWORD
**Required:** No (default: `postgres`)

**Description:** PostgreSQL password.

**Security:** Use strong passwords in production!

### POSTGRES_PORT
**Required:** No (default: `5432`)

**Description:** PostgreSQL port exposed on host.

---

## Configuration Examples

### Development Environment
```bash
# .env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=dev-only-key-change-in-prod
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://postgres:password@localhost:5432/business_db
DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production Environment
```bash
# .env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-strong-secret-key-here
DJANGO_ALLOWED_HOSTS=tramites.sanfelipe.gob.ar
DATABASE_URL=postgresql://user:pass@prod-db:5432/business_db
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_EMAIL_HOST=mail.sanfelipe.gob.ar
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_USE_TLS=True
DJANGO_EMAIL_HOST_USER=noreply@sanfelipe.gob.ar
DJANGO_EMAIL_HOST_PASSWORD=your-smtp-password
```

### Docker Environment
```bash
# docker-compose.yml + .env
POSTGRES_DB=backoffice_tramites
POSTGRES_USER=postgres
POSTGRES_PASSWORD=strong-password-here
DATABASE_URL=postgresql://postgres:strong-password-here@postgres:5432/backoffice_tramites
HTTP_PORT=8090
```

---

## Troubleshooting

### "Secret key not configured"

**Error:** `django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty.`

**Solution:**
```bash
# Generate a new key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Add to .env
DJANGO_SECRET_KEY=your-generated-secret-key
```

### "DisallowedHost at /"

**Error:** Request from host not in `DJANGO_ALLOWED_HOSTS`.

**Solution:**
```bash
# Add your host to allowed hosts
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,your-hostname.com
```

### "Connection refused" (PostgreSQL)

**Error:** Cannot connect to PostgreSQL database.

**Solution:**
```bash
# Check DATABASE_URL format
DATABASE_URL=postgres://user:pass@host:port/database

# Verify PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres
```

### "Permission denied" (SQLite)

**Error:** Cannot write to SQLite database file.

**Solution:**
```bash
# Check file permissions
chmod 644 db.sqlite3
chown user:group db.sqlite3

# Or use absolute path with writable location
DJANGO_SQLITE_DB_PATH=/tmp/db.sqlite3
```

### Email not sending in production

**Error:** Emails not delivered in production.

**Solution:**
```bash
# Change from console to SMTP backend
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Verify SMTP credentials
DJANGO_EMAIL_HOST=your-smtp-server.com
DJANGO_EMAIL_HOST_USER=your-username
DJANGO_EMAIL_HOST_PASSWORD=your-password

# Test email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

---

## Related Documentation

- [Schema Validator](SCHEMA_VALIDATOR.md) - Validating models against PostgreSQL
- [ADR-002: Multiple Databases](decisiones/002-configuracion-multiples-bases-de-datos.md) - Dual database architecture
- [Docker Configuration](../README.md#docker) - Docker deployment guide
- [Django Settings Reference](https://docs.djangoproject.com/en/stable/ref/settings/)
