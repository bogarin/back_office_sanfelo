# Guía: Instalación y Configuración en Producción

> **Para:** Sysadmins y equipo de operaciones
> **Última actualización:** 23 de abril de 2026

---

## Resumen

Esta guía describe cómo desplegar el Backoffice de Trámites en un servidor de producción usando Docker/Podman y Docker Compose. El sistema consiste en:

- **1 contenedor de aplicación** (Nginx + Gunicorn + Django)
- **1 contenedor de PostgreSQL 16** (con dos schemas)
- **1 servidor SFTP externo** (para archivos PDF)

---

## Requisitos Previos

### Servidor

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| **CPU** | 2 cores | 4 cores |
| **RAM** | 2 GB | 4 GB |
| **Disco** | 10 GB | 20 GB |
| **SO** | Linux (Debian/Ubuntu) | Debian 12+ |

### Software requerido

- **Docker** >= 20.x o **Podman** >= 3.x
- **Docker Compose** >= 2.x (o `podman-compose`)
- **Git** (para clonar el repositorio)
- Acceso al **servidor SFTP** donde se almacenan los PDFs

### Información necesaria antes de empezar

- URL de la base de datos PostgreSQL (o credenciales para crear una nueva)
- Credenciales del servidor SFTP (host, usuario, contraseña o llave SSH)
- Nombre de dominio o IP pública donde será accesible el sistema
- Certificado SSL (si se usará HTTPS)

---

## Paso 1: Preparar la Base de Datos

### Opción A: Usar el PostgreSQL de Docker Compose (recomendado para inicio)

El `docker-compose.yml` incluye un servicio PostgreSQL. Solo necesitas configurar las credenciales en el `.env`:

```bash
POSTGRES_DB=backoffice_tramites
POSTGRES_USER=postgres
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_PORT=5432
```

### Opción B: Usar un PostgreSQL externo

Si ya tienes un servidor PostgreSQL:

1. **Crear la base de datos:**
   ```sql
   CREATE DATABASE backoffice_tramites;
   CREATE USER backoffice_user WITH PASSWORD 'STRONG_PASSWORD';
   GRANT ALL PRIVILEGES ON DATABASE backoffice_tramites TO backoffice_user;
   ```

2. **Crear el schema `backoffice`:**
   ```sql
   \c backoffice_tramites
   CREATE SCHEMA IF NOT EXISTS backoffice AUTHORIZATION backoffice_user;
   ```

3. **Verificar que el schema `public` existe** (default en PostgreSQL).

4. **Configurar la URL en `.env`:**
   ```bash
   POSTGRESQL_DB_URL=postgres://backoffice_user:STRONG_PASSWORD@db-host:5432/backoffice_tramites
   ```

5. **Eliminar el servicio postgres del docker-compose.yml** y apuntar la URL al servidor externo.

### Verificar conectividad

```bash
psql postgres://backoffice_user:STRONG_PASSWORD@HOST:5432/backoffice_tramites -c "\dn"
```

Debes ver los schemas `backoffice` y `public`.

---

## Paso 2: Obtener el Código

```bash
# Clonar el repositorio
git clone <URL_DEL_REPOSITORIO> backoffice_tramites
cd backoffice_tramites
```

---

## Paso 3: Configurar Variables de Entorno

### 3.1 Crear el archivo `.env`

```bash
cp .env.example .env
```

### 3.2 Variables obligatorias para producción

Editar `.env` con los valores de producción:

```bash
# === DJANGO CORE ===
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=GENERAR_CON_EL_COMANDO_DE_ABAJO
DJANGO_ALLOWED_HOSTS=backoffice.sanfelipe.gob.mx

# === BASE DE DATOS ===
POSTGRESQL_DB_URL=postgres://backoffice_user:STRONG_PASSWORD@postgres:5432/backoffice_tramites
BACKOFFICE_DB_SCHEMA=backoffice
BACKEND_DB_SCHEMA=public

# === SEGURIDAD (con HTTPS) ===
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_CONTENT_TYPE_NOSNIFF=True
DJANGO_SECURE_BROWSER_XSS_FILTER=True
DJANGO_CSRF_TRUSTED_ORIGINS=https://backoffice.sanfelipe.gob.mx

# === LOGGING ===
DJANGO_LOG_LEVEL=INFO

# === POSTGRESQL (Docker Compose) ===
POSTGRES_DB=backoffice_tramites
POSTGRES_USER=postgres
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_PORT=5432

# === SFTP ===
SFTP_HOST=sftp.example.com
SFTP_PORT=22
SFTP_USERNAME=backoffice_user
SFTP_PASSWORD=SFTP_PASSWORD_HERE
SFTP_HOST_KEY=ssh-ed25519 AAAA...
SFTP_BASE_DIR=/data/tramites
SFTP_PDF_DIR=pdfs
SFTP_CACHE_DIR=/app/.sftp_cache
SFTP_CACHE_TTL=3600
SFTP_CACHE_MAX_SIZE_MB=500
```

### 3.3 Generar SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Pegar el resultado como valor de `DJANGO_SECRET_KEY`.

### 3.4 Obtener SFTP_HOST_KEY

```bash
ssh-keyscan -t rsa,ed25519 sftp.example.com
```

Copiar la línea que empieza con `ssh-ed25519` o `ssh-rsa` y pegarla como valor de `SFTP_HOST_KEY`.

> **Ver guía completa:** [Guía de configuración SFTP](sftp-setup.md)

### 3.5 Variables de branding (opcional)

```bash
BACKOFFICE_SITE_TITLE="Backoffice de Trámites"
BACKOFFICE_SITE_HEADER="San Felipe"
BACKOFFICE_SITE_BRAND="Ventanilla Urbana Digital"
BACKOFFICE_WELCOME_SIGN="Ventanilla Urbana Digital - Municipio de San Felipe"
BACKOFFICE_COPYRIGHT="Municipio de San Felipe - Todos los derechos reservados"
```

> **Referencia completa:** [Variables de Entorno](../../05-reference/environment-vars.md)

---

## Paso 4: Construir la Imagen Docker

```bash
# Con Docker
docker build -t backoffice-tramites:latest .

# Con Podman
podman build -t backoffice-tramites:latest .
```

El build:
1. Instala dependencias con `uv`
2. Instala nginx y libpq5
3. Crea usuario `appuser` (uid 1000)
4. Ejecuta `collectstatic`
5. Expone puerto 8080

---

## Paso 5: Desplegar con Docker Compose

```bash
# Iniciar servicios (PostgreSQL + aplicación)
docker compose up -d

# Ver logs
docker compose logs -f
```

### Verificar que los servicios están corriendo

```bash
# Ver contenedores activos
docker compose ps

# Verificar health check
curl http://localhost:8090/health/
```

La respuesta debe ser `200 OK`.

### Qué hace el entrypoint automáticamente

Cuando el contenedor inicia, el `entrypoint.sh` ejecuta:

1. **Verifica que no corre como root** (security)
2. **Ejecuta migraciones** (`manage.py migrate`) — Solo afecta el schema `backoffice`
3. **Recolecta archivos estáticos** (`manage.py collectstatic`)
4. **Inicia Nginx** en puerto 8080
5. **Inicia Gunicorn** en puerto 8081 (interno)
6. **Maneja señales** SIGTERM/SIGINT para apagado graceful

---

## Paso 6: Post-Instalación

### 6.1 Crear el superusuario

```bash
docker compose exec backoffice python manage.py createsuperuser
```

Sigue las instrucciones interactivas (username, email, password).

### 6.2 Configurar roles RBAC

```bash
docker compose exec backoffice python manage.py setup_roles
```

Esto crea los 3 grupos de Django:
- **Administrador** — Acceso completo
- **Coordinador** — Puede asignar/reasignar trámites
- **Analista** — Ve sus trámites asignados + disponibles

### 6.3 Asignar roles a usuarios

Desde el admin de Django (`https://DOMINIO/admin/`):

1. Ir a **Autenticación y Autorización → Usuarios**
2. Seleccionar un usuario
3. En la sección **Grupos**, agregar al grupo correspondiente:
   - `Administrador`, `Coordinador`, o `Analista`
4. Guardar

### 6.4 Verificar conectividad SFTP

```bash
docker compose exec backoffice python manage.py sftp ping
```

Debe responder sin errores.

---

## Paso 7: Configurar HTTPS (Recomendado)

### Opción A: Reverse proxy externo (recomendado)

Colocar un Nginx/Caddy/Traefik delante del contenedor:

```nginx
# /etc/nginx/sites-available/backoffice
server {
    listen 443 ssl http2;
    server_name backoffice.sanfelipe.gob.mx;

    ssl_certificate /etc/letsencrypt/live/backoffice.sanfelipe.gob.mx/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/backoffice.sanfelipe.gob.mx/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}

server {
    listen 80;
    server_name backoffice.sanfelipe.gob.mx;
    return 301 https://$host$request_uri;
}
```

### Opción B: Let's Encrypt con Certbot

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d backoffice.sanfelipe.gob.mx
```

---

## Verificación Final

### Checklist

- [ ] Contenedores corriendo (`docker compose ps`)
- [ ] Health check responde (`curl http://localhost:8090/health/`)
- [ ] Admin accesible (`https://DOMINIO/admin/`)
- [ ] Login funciona con el superusuario
- [ ] Roles creados (`setup_roles` ejecutado)
- [ ] SFTP conectividad verificada (`sftp ping`)
- [ ] HTTPS configurado (si aplica)
- [ ] Headers de seguridad activos (verificar con `curl -I`)
- [ ] Logs visibles (`docker compose logs -f`)
- [ ] Backup de base de datos configurado

### Verificar headers de seguridad

```bash
curl -I https://backoffice.sanfelipe.gob.mx/admin/
```

Debes ver:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

---

## Operaciones Comunes

### Ver logs

```bash
# Todos los servicios
docker compose logs -f

# Solo la aplicación
docker compose logs -f backoffice

# Solo PostgreSQL
docker compose logs -f postgres
```

### Reiniciar servicios

```bash
docker compose restart backoffice
```

### Actualizar la aplicación

```bash
git pull
docker compose build backoffice
docker compose up -d backoffice
```

### Backup de base de datos

```bash
docker compose exec postgres pg_dump -U postgres backoffice_tramites > backup_$(date +%Y%m%d).sql
```

### Restaurar backup

```bash
cat backup_20260423.sql | docker compose exec -T postgres psql -U postgres backoffice_tramites
```

### Escalar workers de Gunicorn

Editar `.env`:
```bash
GUNICORN_WORKERS=8
```

Luego reiniciar: `docker compose restart backoffice`

---

## Troubleshooting

### El contenedor no inicia

```bash
# Ver logs del contenedor
docker compose logs backoffice

# Verificar que .env existe y tiene las variables obligatorias
grep -c 'DJANGO_SECRET_KEY\|POSTGRESQL_DB_URL\|DJANGO_DEBUG' .env
```

### Error de conexión a PostgreSQL

```bash
# Verificar que PostgreSQL está healthy
docker compose ps postgres

# Probar conexión manual
docker compose exec backoffice python -c "
import psycopg2
conn = psycopg2.connect('postgres://postgres:PASSWORD@postgres:5432/backoffice_tramites')
print('Conexión OK')
conn.close()
"
```

### Error de migraciones

```bash
# Ver estado de migraciones
docker compose exec backoffice python manage.py showmigrations

# Ejecutar migraciones manualmente
docker compose exec backoffice python manage.py migrate --no-input
```

### Nginx no sirve archivos estáticos

```bash
# Recollect static
docker compose exec backoffice python manage.py collectstatic --no-input --clear

# Verificar que los archivos existen
docker compose exec backoffice ls -la /app/staticfiles/
```

### SFTP no conecta

```bash
# Probar conectividad
docker compose exec backoffice python manage.py sftp ping

# Ver configuración SFTP
docker compose exec backoffice python -c "
from django.conf import settings
print(f'Host: {settings.SFTP_HOST}')
print(f'Port: {settings.SFTP_PORT}')
print(f'User: {settings.SFTP_USERNAME}')
"
```

---

## Estructura del Contenedor

```
Contenedor (appuser, uid 1000)
├── Nginx (:8080 externo)
│   ├── /static/     → /app/static/ (archivos estáticos)
│   ├── /media/      → /app/media/ (archivos subidos)
│   ├── /admin/      → proxy a Gunicorn (:8081)
│   ├── /sftp-cache/ → X-Accel-Redirect (PDFs desde cache)
│   └── /healthz     → 200 OK (health check)
└── Gunicorn (:8081 interno)
    └── Django WSGI application
```

---

## Ver también

- [Referencia de Variables de Entorno](../../05-reference/environment-vars.md)
- [Referencia de SFTP](../../05-reference/sftp.md)
- [Guía de configuración SFTP](sftp-setup.md)
- [ADR-005: Despliegue Docker + Gunicorn](../../06-decisions/005-despliegue-docker-gunicorn.md)
- [ADR-008: PostgreSQL Schema Separation](../../06-decisions/008-postgresql-schema-separation.md)
- [ADR-010: Integración SFTP](../../06-decisions/010-integracion-con-sftp.md)
