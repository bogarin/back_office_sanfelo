# Referencia de Variables de Entorno

> **Fuente única de verdad** para todas las variables de entorno del proyecto.
> Última actualización: 23 de abril de 2026

---

## Resumen Rápido

| Categoría | Variables | Requeridas |
|-----------|-----------|------------|
| [Django Core](#django-core) | 4 | Sí |
| [Debug & Dev](#debug--desarrollo) | 3 | No |
| [Base de Datos](#base-de-datos) | 3 | Sí |
| [Seguridad](#seguridad-producción) | 6 | En producción |
| [CSP](#content-security-policy) | 1 | No |
| [CSRF](#csrf) | 1 | En producción |
| [Sesión](#sesión) | 1 | No |
| [Paginación](#paginación) | 1 | No |
| [Email](#email) | 7 | En producción |
| [Docker](#dockerdeployment) | 1 | No |
| [PostgreSQL (Docker Compose)](#postgresql-service-docker-compose) | 4 | Solo Docker |
| [Tenancy](#tenancymulti-departamento) | 6 | No |
| [SFTP](#sftp-storage) | 13 | En producción |
| [Gunicorn](#gunicorn-contenedor) | 4 | No |

---

## Django Core

Variables esenciales que el proyecto necesita para funcionar.

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `DJANGO_SECRET_KEY` | string | — | **Sí** |
| `DJANGO_DEBUG` | bool | `True` | Sí |
| `DJANGO_ALLOWED_HOSTS` | lista coma | `localhost,127.0.0.1,0.0.0.0` | Sí |
| `TESTING` | bool | `False` | No |

### `DJANGO_SECRET_KEY`

Clave criptográfica para Django. Usada para firmar cookies CSRF, sesiones, y mensajes.

- **Desarrollo:** Cualquier string aleatorio funciona
- **Producción:** Debe ser un string aleatorio largo y único. Generar con:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(50))"
  ```
- **Dockerfile:** Usa `dummy-build-time-secret` durante el build (se reemplaza en runtime)

### `DJANGO_DEBUG`

Activa el modo debug de Django. Habilita Debug Toolbar, mensajes de error detallados, y SQL logging.

- **Desarrollo:** `True`
- **Producción:** `False` — **NUNCA usar True en producción**

### `DJANGO_ALLOWED_HOSTS`

Lista de hosts/válidos separados por coma. Previene ataques de host header.

- **Desarrollo:** `localhost,127.0.0.1,0.0.0.0`
- **Producción:** Dominio(s) del sitio, ej: `backoffice.sanfelipe.gob.mx`

### `TESTING`

Indica si se están ejecutando tests. Cuando es `True`:
- Deshabilita Debug Toolbar
- Usa DummyCache (sin cache real)
- Carga la app `tests` con modelos de prueba
- Cambia `managed=False` a `True` en modelos de negocio

---

## Debug & Desarrollo

Solo tienen efecto cuando `DJANGO_DEBUG=True`.

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `DJANGO_INTERNAL_IPS` | lista coma | `127.0.0.1,0.0.0.0` | No |
| `DJANGO_DEBUG_SQL` | bool | `False` | No |
| `DJANGO_LOG_LEVEL` | string | `DEBUG` (dev) / `INFO` (prod) | No |

### `DJANGO_INTERNAL_IPS`

IPs que ven el Debug Toolbar. Separadas por coma.

### `DJANGO_DEBUG_SQL`

Cuando es `True`, loguea todas las queries SQL a la consola. Útil para debugging de performance.

### `DJANGO_LOG_LEVEL`

Nivel de logging. Valores: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

- **Desarrollo:** `DEBUG` (ver todo)
- **Producción:** `INFO` (solo importantes y errores)

---

## Base de Datos

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `POSTGRESQL_DB_URL` | DB URL | — | **Sí** |
| `BACKOFFICE_DB_SCHEMA` | string | `backoffice` | No |
| `BACKEND_DB_SCHEMA` | string | `public` | No |

### `POSTGRESQL_DB_URL`

URL de conexión PostgreSQL. **Una sola conexión** que se usa para ambos esquemas.

Formato: `postgres://USUARIO:PASSWORD@HOST:PUERTO/BASE_DE_DATOS`

Ejemplos:
```bash
# Desarrollo local
POSTGRESQL_DB_URL=postgres://postgres:mipassword@localhost:5432/backoffice_tramites

# Docker Compose (interno)
POSTGRESQL_DB_URL=postgres://postgres:mipassword@postgres:5432/backoffice_tramites

# Producción
POSTGRESQL_DB_URL=postgres://backoffice_user:STRONG_PASSWORD@db.prod.internal:5432/backoffice_tramites
```

El proyecto crea dos conexiones lógicas con `search_path`:
- `default` → `search_path={BACKOFFICE_DB_SCHEMA}` (auth, admin, AsignacionTramite)
- `backend` → `search_path={BACKEND_DB_SCHEMA}` (catálogos, trámites, actividades)

Ver [ADR-008: PostgreSQL Schema Separation](../06-decisions/008-postgresql-schema-separation.md).

### `BACKOFFICE_DB_SCHEMA`

Nombre del schema PostgreSQL para datos de Django (auth, sessions, admin).

- Default: `backoffice`
- Debe existir en la base de datos antes de ejecutar migraciones

### `BACKEND_DB_SCHEMA`

Nombre del schema PostgreSQL para datos de negocio (catálogos, trámites, actividades).

- Default: `public`
- Las tablas son gestionadas externamente (no por Django migrations)

---

## Seguridad (Producción)

Solo tienen efecto cuando `DJANGO_DEBUG=False`.

| Variable | Tipo | Default Producción | Requerida |
|----------|------|-------------------|-----------|
| `DJANGO_SECURE_CONTENT_TYPE_NOSNIFF` | bool | `True` | Recomendada |
| `DJANGO_SECURE_BROWSER_XSS_FILTER` | bool | `True` | Recomendada |
| `DJANGO_SECURE_SSL_REDIRECT` | bool | `False` | Si hay HTTPS |
| `DJANGO_SESSION_COOKIE_SECURE` | bool | `False` | Si hay HTTPS |
| `DJANGO_CSRF_COOKIE_SECURE` | bool | `False` | Si hay HTTPS |
| `DJANGO_CSP_REPORT_ONLY` | bool | `False` | No |

### Checklist de Producción con HTTPS

```bash
DJANGO_SECURE_SSL_REDIRECT=True       # Redirigir HTTP → HTTPS
DJANGO_SESSION_COOKIE_SECURE=True      # Cookies de sesión solo por HTTPS
DJANGO_CSRF_COOKIE_SECURE=True         # Cookies CSRF solo por HTTPS
DJANGO_SECURE_CONTENT_TYPE_NOSNIFF=True  # Prevenir MIME sniffing
DJANGO_SECURE_BROWSER_XSS_FILTER=True    # Activar filtro XSS del navegador
```

### `DJANGO_CSP_REPORT_ONLY`

- `False` (default): CSP se **ejecuta** — bloquea violaciones
- `True`: CSP solo **reporta** violaciones sin bloquear — útil para diagnóstico inicial

---

## CSRF

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `DJANGO_CSRF_TRUSTED_ORIGINS` | lista coma | `http://localhost,http://127.0.0.1` | En producción |

### `DJANGO_CSRF_TRUSTED_ORIGINS`

Orígenes confiables para protección CSRF. Incluir protocolo (`http://` o `https://`).

- **Desarrollo:** `http://localhost,http://127.0.0.1`
- **Producción:** `https://backoffice.sanfelipe.gob.mx`

---

## Sesión

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `DJANGO_SESSION_COOKIE_AGE` | int (seg) | `3600` | No |

### `DJANGO_SESSION_COOKIE_AGE`

Tiempo de vida de la cookie de sesión en segundos.

- `3600` = 1 hora (default, recomendado para producción)
- `86400` = 24 horas
- `7200` = 2 horas

El proyecto usa `signed_cookies` como backend de sesión (no hay almacenamiento server-side).

---

## Paginación

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `DJANGO_DEFAULT_PAGE_SIZE` | int | `25` | No |

### `DJANGO_DEFAULT_PAGE_SIZE`

Cantidad de elementos por página en las vistas de lista del admin.

---

## Email

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `DJANGO_EMAIL_BACKEND` | string | `django.core.mail.backends.console.EmailBackend` | No |
| `DJANGO_EMAIL_HOST` | string | `localhost` | Si usa SMTP |
| `DJANGO_EMAIL_PORT` | int | `587` | Si usa SMTP |
| `DJANGO_EMAIL_USE_TLS` | bool | `True` | No |
| `DJANGO_EMAIL_HOST_USER` | string | (vacío) | Si usa SMTP |
| `DJANGO_EMAIL_HOST_PASSWORD` | string | (vacío) | Si usa SMTP |
| `DJANGO_DEFAULT_FROM_EMAIL` | string | `noreply@sanfelipe.gob.ar` | No |

### Backends disponibles

- **Desarrollo:** `django.core.mail.backends.console.EmailBackend` — imprime emails en consola
- **Producción:** `django.core.mail.backends.smtp.EmailBackend` — envía via SMTP

### Ejemplo de configuración SMTP en producción

```bash
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_EMAIL_HOST=smtp.gmail.com
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_USE_TLS=True
DJANGO_EMAIL_HOST_USER=noreply@sanfelipe.gob.mx
DJANGO_EMAIL_HOST_PASSWORD=APP_PASSWORD
DJANGO_DEFAULT_FROM_EMAIL=noreply@sanfelipe.gob.mx
```

---

## Docker/Deployment

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `HTTP_PORT` | int | `8090` | No |

### `HTTP_PORT`

Puerto externo del host que se mapea al puerto 8080 del contenedor (nginx).

```bash
# En docker-compose.yml
ports:
  - "${HTTP_PORT:-8090}:8080"
```

---

## PostgreSQL Service (Docker Compose)

Estas variables configuran el **contenedor de PostgreSQL** en Docker Compose. No son usadas directamente por Django.

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `POSTGRES_DB` | string | `backoffice_tramites` | Solo Docker |
| `POSTGRES_USER` | string | `postgres` | Solo Docker |
| `POSTGRES_PASSWORD` | string | `postgres` | **Sí en prod** |
| `POSTGRES_PORT` | int | `5432` | No |

### ⚠️ Nota importante

`POSTGRESQL_DB_URL` (usada por Django) y `POSTGRES_*` (usada por el contenedor) están relacionadas pero son diferentes:

```bash
# Contenedor PostgreSQL
POSTGRES_DB=backoffice_tramites
POSTGRES_USER=postgres
POSTGRES_PASSWORD=STRONG_PASSWORD

# Django (debe coincidir con el contenedor)
POSTGRESQL_DB_URL=postgres://postgres:STRONG_PASSWORD@postgres:5432/backoffice_tramites
```

---

## Tenancy/Multi-Departamento

Estas variables permiten que una misma imagen Docker sirva a múltiples departamentos con diferente branding.

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `BACKOFFICE_SITE_TITLE` | string | `Ventanilla Urbana Digital` | No |
| `BACKOFFICE_SITE_HEADER` | string | `San Felipe` | No |
| `BACKOFFICE_SITE_BRAND` | string | `Ventanilla Urbana Digital` | No |
| `BACKOFFICE_SITE_LOGO` | string | (vacío) | No |
| `BACKOFFICE_WELCOME_SIGN` | string | `Ventanilla Urbana Digital - Municipio...` | No |
| `BACKOFFICE_COPYRIGHT` | string | `Municipio de San Felipe...` | No |

### Ejemplo para otro departamento

```bash
BACKOFFICE_SITE_TITLE="Backoffice Trámites"
BACKOFFICE_SITE_HEADER="Municipio X"
BACKOFFICE_SITE_BRAND="Backoffice Municipal"
BACKOFFICE_WELCOME_SIGN="Sistema de Gestión - Municipio X"
BACKOFFICE_COPYRIGHT="Municipio X - Todos los derechos reservados"
BACKOFFICE_SITE_LOGO=logo_municipio.png
```

---

## SFTP Storage

Configuración para acceder a archivos PDF almacenados en un servidor SFTP remoto.

### Conexión

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `SFTP_HOST` | string | (vacío) | **Sí en prod** |
| `SFTP_PORT` | int | `22` | No |
| `SFTP_USERNAME` | string | (vacío) | **Sí en prod** |
| `SFTP_PASSWORD` | string | (vacío) | Una de las dos |
| `SFTP_PRIVATE_KEY_PATH` | string | (vacío) | Una de las dos |
| `SFTP_PRIVATE_KEY_PASSPHRASE` | string | (vacío) | Si la key tiene passphrase |
| `SFTP_TIMEOUT` | int | None (~30s paramiko) | No |
| `SFTP_HOST_KEY` | string | (vacío) | **Recomendada en prod** |

### Autenticación

Dos métodos, usar **uno solo**:

1. **Password:**
   ```bash
   SFTP_USERNAME=backoffice_user
   SFTP_PASSWORD=STRONG_PASSWORD
   ```

2. **Llave SSH:**
   ```bash
   SFTP_USERNAME=backoffice_user
   SFTP_PRIVATE_KEY_PATH=~/.ssh/id_rsa
   SFTP_PRIVATE_KEY_PASSPHRASE=passphrase_if_any
   ```

### `SFTP_HOST_KEY`

Clave SSH del servidor para verificar identidad y prevenir ataques MITM.

- **Requerida en producción** (`DEBUG=False`). Si no está configurada, usa `WarningPolicy` (acepta cualquier key).
- **Obtener la key:**
  ```bash
  ssh-keyscan -t rsa,ed25519 sftp.example.com
  ```
- **Formato:** `"ssh-rsa AAAAB3Nza..."` o `"ssh-ed25519 AAAA..."`
- **Ver guía:** [Guía de configuración SFTP](../03-guides/sysadmins/sftp-setup.md)

### Directorios

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `SFTP_BASE_DIR` | string | (vacío) | **Sí en prod** |
| `SFTP_PDF_DIR` | string | `pdfs` | No |

- `SFTP_BASE_DIR`: Directorio base en el servidor SFTP donde se almacenan los archivos
- `SFTP_PDF_DIR`: Subdirectorio para PDFs (relativo a `SFTP_BASE_DIR`)

### Cache Local

Los PDFs se descargan a un cache local antes de servirlos via Nginx X-Accel-Redirect.

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `SFTP_CACHE_DIR` | string | `.sftp_cache` | No |
| `SFTP_CACHE_TTL` | int (seg) | `3600` (1 hora) | No |
| `SFTP_CACHE_MAX_SIZE_MB` | int (MB) | `500` | No |

- **Desarrollo:** `.sftp_cache` (relativo al proyecto)
- **Docker:** `/app/.sftp_cache` (configurado en Dockerfile)

### Probar conectividad SFTP

```bash
just shell  # o uv run manage.py shell
>>> from core.management.commands.sftp import Command
>>> # O usar el comando directamente:
uv run manage.py sftp ping
uv run manage.py sftp list FOLIO-123456
```

---

## Gunicorn (Contenedor)

Estas variables se usan dentro del contenedor Docker. Configuran el servidor de aplicación.

| Variable | Tipo | Default | Requerida |
|----------|------|---------|-----------|
| `GUNICORN_PORT` | int | `8081` | No |
| `GUNICORN_WORKERS` | int | `4` | No |
| `GUNICORN_TIMEOUT` | int (seg) | `60` | No |
| `GUNICORN_MAX_REQUESTS` | int | `1000` | No |
| `GUNICORN_MAX_REQUESTS_JITTER` | int | `50` | No |

### Configuración recomendada por entorno

| Entorno | Workers | Timeout | Max Requests |
|---------|---------|---------|-------------|
| Desarrollo | 2 | 120 | 0 (sin límite) |
| Producción (pequeño) | 4 | 60 | 1000 |
| Producción (medio) | 8 | 60 | 1000 |

**Regla general:** `workers = (2 × CPUs) + 1`

---

## Variables del Dockerfile (build-time)

Estas variables se configuran automáticamente en el Dockerfile y **no necesitan ser configuradas manualmente**:

| Variable | Valor | Propósito |
|----------|-------|-----------|
| `PYTHONUNBUFFERED` | `1` | Output directo a terminal |
| `PYTHONDONTWRITEBYTECODE` | `1` | No crear archivos `.pyc` |
| `DJANGO_SETTINGS_MODULE` | `sanfelipe.settings` | Módulo de settings |
| `DJANGO_SECRET_KEY` | `dummy-build-time-secret` | Solo para `collectstatic` |
| `BACKEND_DB_URL` | `postgresql://user:pass@localhost/db` | Solo para `collectstatic` |

---

## Checklist de Producción

Variables **obligatorias** para desplegar en producción:

```bash
# === OBLIGATORIAS ===
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<generar-con-secrets-token-urlsafe-50>
DJANGO_ALLOWED_HOSTS=backoffice.sanfelipe.gob.mx
POSTGRESQL_DB_URL=postgres://USER:PASSWORD@HOST:5432/DATABASE

# === SEGURIDAD (con HTTPS) ===
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_CSRF_TRUSTED_ORIGINS=https://backoffice.sanfelipe.gob.mx

# === SFTP ===
SFTP_HOST=sftp.example.com
SFTP_USERNAME=backoffice
SFTP_PASSWORD=STRONG_PASSWORD
SFTP_HOST_KEY=ssh-ed25519 AAAA...
SFTP_BASE_DIR=/data/tramites

# === RECOMENDADAS ===
DJANGO_LOG_LEVEL=INFO
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
POSTGRES_PASSWORD=STRONG_DB_PASSWORD
HTTP_PORT=8090
```

---

## Ver también

- [Guía de despliegue en producción](../03-guides/sysadmins/deploy-production.md)
- [ADR-008: PostgreSQL Schema Separation](../06-decisions/008-postgresql-schema-separation.md)
- [Referencia de SFTP](sftp.md)
- [Guía de setup SFTP](../03-guides/sysadmins/sftp-setup.md)
- [`.env.example`](../../.env.example) — Template con todos los valores default
