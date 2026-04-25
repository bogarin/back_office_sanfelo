# Guía: Despliegue en Producción con Docker

> **Para:** Sysadmins y equipo de operaciones
> **Última actualización:** 25 de abril de 2026

---

## Resumen

Esta guía describe cómo desplegar el Backoffice de Trámites en un servidor de producción usando Docker/Podman. El sistema consiste en:

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
- **zstd** (para descomprimir la imagen exportada)
- Acceso al **servidor SFTP** donde se almacenan los PDFs

### Información necesaria antes de empezar

- URL de la base de datos PostgreSQL (o credenciales para crear una nueva)
- Credenciales del servidor SFTP (host, usuario, llave SSH)
- Nombre de dominio o IP pública donde será accesible el sistema
- Certificado SSL (si se usará HTTPS)
- Llave SSH privada para conectarse al servidor SFTP

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

1. **Crear la base de datos y el schema `backoffice`:**
   ```sql
   CREATE DATABASE backoffice_tramites;
   CREATE USER backoffice_user WITH PASSWORD 'STRONG_PASSWORD';
   GRANT ALL PRIVILEGES ON DATABASE backoffice_tramites TO backoffice_user;

   \c backoffice_tramites
   CREATE SCHEMA IF NOT EXISTS backoffice AUTHORIZATION backoffice_user;
   ```

2. **Verificar que el schema `public` existe** (default en PostgreSQL).

3. **Configurar la URL en `.env`:**
   ```bash
   POSTGRESQL_DB_URL=postgres://backoffice_user:STRONG_PASSWORD@db-host:5432/backoffice_tramites
   ```

4. **Eliminar el servicio postgres del docker-compose.yml** y apuntar la URL al servidor externo.

### Verificar conectividad

```bash
psql postgres://backoffice_user:STRONG_PASSWORD@HOST:5432/backoffice_tramites -c "\dn"
```

Debes ver los schemas `backoffice` y `public`.

---

## Paso 2: Transferir la Imagen al Servidor

La imagen se construye en la máquina de desarrollo y se transfiere al servidor.

### 2.1 Construir la imagen

```bash
just container-build
```

Esto genera un archivo comprimido en `.docker-images/`.

### 2.2 Transferir al servidor

```bash
just container-push
```

Este comando:
1. Copia la imagen comprimida via `scp` al servidor
2. La carga en Docker (`docker load`)
3. Re-taggea a `sanfelipe-backoffice:latest` (sin prefijo de registry)
4. Elimina el archivo temporal

> **Nota:** El servidor destino (`sanfelo.stage`) debe estar configurado en `~/.ssh/config` o ser accesible directamente.

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

# === GUNICORN ===
GUNICORN_PORT=8081
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=60

# === SEGURIDAD (con HTTPS) ===
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_CONTENT_TYPE_NOSNIFF=True
DJANGO_SECURE_BROWSER_XSS_FILTER=True
DJANGO_CSRF_TRUSTED_ORIGINS=https://backoffice.sanfelipe.gob.mx

# === LOGGING ===
DJANGO_LOG_LEVEL=INFO

# === SFTP ===
SFTP_HOST=sftp.example.com
SFTP_PORT=22
SFTP_USERNAME=backoffice_user
SFTP_SSH_KEY_PATH=/home/appuser/.ssh/id_ed25519_sf_demo
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

Pegar el resultado como valor de `DJANGO_SECRET_KEY`. No usar el prefijo `django-insecure-`.

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

## Paso 4: Configurar Volúmenes y Archivos Montados

El contenedor expone configuración via volúmenes montados. Esto permite customizar sin reconstruir la imagen.

### 4.1 Llave SSH para SFTP

Montar la llave SSH privada que Django usa para conectarse al servidor SFTP:

```yaml
services:
  backoffice:
    volumes:
      - ./secrets/id_ed25519_sf_demo:/home/appuser/.ssh/id_ed25519_sf_demo:ro
```

**Requisitos**:
- El archivo debe ser legible por `appuser` (uid 1000)
- El modo `:ro` (read-only) es obligatorio por seguridad
- El path en el contenedor debe coincidir con `SFTP_SSH_KEY_PATH` en el `.env`

**Permisos correctos**:
```bash
chmod 600 secrets/id_ed25519_sf_demo
chown 1000:1000 secrets/id_ed25519_sf_demo
```

### 4.2 Configuración de Nginx (opcional)

La imagen incluye una configuración nginx funcional por defecto (catch-all, rate limiting, security headers). Para customizar (hostname, timeouts, etc.):

```yaml
services:
  backoffice:
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
```

**Cuándo montar una config custom**:
- Necesitas restringir el `server_name` a un dominio específico
- Quieres ajustar rate limits o timeouts
- Agregar ubicaciones adicionales (monitoring, etc.)

> La config por defecto usa `server_name _;` (catch-all) y es suficiente para la mayoría de despliegues.

### 4.3 docker-compose.yml de referencia

```yaml
services:
  backoffice:
    image: sanfelipe-backoffice:latest
    ports:
      - "8090:8080"
    env_file:
      - .env
    volumes:
      # Llave SSH para SFTP (obligatorio para documentos PDF)
      - ./secrets/id_ed25519_sf_demo:/home/appuser/.ssh/id_ed25519_sf_demo:ro
      # Nginx config custom (opcional, la imagen tiene una por defecto)
      # - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  pgdata:
```

---

## Paso 5: Desplegar

```bash
# Iniciar servicios
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

1. **Activa el virtualenv** (`. /app/.venv/bin/activate`)
2. **Recolecta archivos estáticos** (`manage.py collectstatic --no-input --clear`)
3. **Corrige permisos** de directorios generados en runtime (`chown appuser:appuser`)
4. **Inicia Nginx** en puerto 8080 (corre como root para bind)
5. **Inicia Gunicorn** en puerto 8081 como `appuser` (no-root)
6. **Maneja señales** TERM/INT para apagado graceful de ambos servicios

> **Las migraciones NO se ejecutan automáticamente.** Ver Paso 6 para ejecutarlas manualmente.

---

## Paso 6: Post-Instalación

### 6.1 Ejecutar migraciones

```bash
docker compose exec backoffice python manage.py migrate --no-input
```

Esto solo afecta el schema `backoffice`. El schema `public` (datos de negocio) se gestiona externamente.

### 6.2 Crear el superusuario

```bash
docker compose exec backoffice python manage.py createsuperuser
```

Sigue las instrucciones interactivas (username, email, password).

### 6.3 Configurar roles RBAC

```bash
docker compose exec backoffice python manage.py setup_roles
```

Esto crea los grupos de Django:
- **Administrador** — Acceso completo
- **Coordinador** — Puede asignar/reasignar trámites
- **Analista** — Ve sus trámites asignados + disponibles

### 6.4 Asignar roles a usuarios

Desde el admin de Django (`https://DOMINIO/admin/`):

1. Ir a **Autenticación y Autorización → Usuarios**
2. Seleccionar un usuario
3. En la sección **Grupos**, agregar al grupo correspondiente
4. Guardar

### 6.5 Verificar conectividad SFTP

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
- [ ] Migraciones ejecutadas (`manage.py migrate`)
- [ ] Admin accesible (`https://DOMINIO/admin/`)
- [ ] Login funciona con el superusuario
- [ ] Roles creados (`setup_roles` ejecutado)
- [ ] Llave SSH montada y SFTP conectividad verificada (`sftp ping`)
- [ ] Estilos CSS cargan correctamente en el admin
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

En la máquina de desarrollo:
```bash
just container-build
just container-push
```

En el servidor:
```bash
docker compose up -d backoffice
```

### Ejecutar migraciones

```bash
docker compose exec backoffice python manage.py migrate --no-input
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

| Problema | Solución |
|----------|----------|
| El contenedor no inicia | `docker compose logs backoffice` para ver el error |
| Error de conexión a PostgreSQL | Verificar `POSTGRESQL_DB_URL` y que PostgreSQL esté healthy |
| Nginx no sirve archivos estáticos | `docker compose exec backoffice ls /app/staticfiles/` — si está vacío, reiniciar el contenedor (collectstatic corre en el entrypoint) |
| SFTP no conecta | Verificar llave SSH montada, permisos (uid 1000), y `SFTP_HOST_KEY` |
| Error "No module named 'debug_toolbar'" | Verificar que `DJANGO_DEBUG=False` en producción, o que `debug_toolbar` esté instalado si `DEBUG=True` |
| CSS del admin no carga | Verificar que nginx apunta a `/app/staticfiles/` (no `/app/static/`) |
| Warning "INSECURE SECRET_KEY" | Generar una SECRET_KEY real sin el prefijo `django-insecure-` |

---

## Estructura del Contenedor

```
Contenedor (root para nginx, appuser para gunicorn)
├── Nginx (:8080 externo)
│   ├── /static/        → /app/staticfiles/ (archivos estáticos)
│   ├── /media/         → /app/media/ (no usado actualmente)
│   ├── /admin/         → proxy a Gunicorn (:8081)
│   ├── /sftp-cache/    → X-Accel-Redirect (PDFs desde cache)
│   └── /healthz        → 200 OK (health check nginx)
└── Gunicorn (:8081 interno, corre como appuser)
    └── Django WSGI application
```

### Archivos y directorios importantes

| Path | Propietario | Descripción |
|------|-------------|-------------|
| `/app/.venv/` | root | Virtualenv con dependencias Python |
| `/app/staticfiles/` | appuser | Archivos estáticos (generado por collectstatic) |
| `/app/static/` | root | Archivos estáticos fuente (CSS/JS custom) |
| `/app/logs/` | appuser | Logs de Django |
| `/app/.sftp_cache/` | appuser | Cache de PDFs descargados via SFTP |
| `/etc/nginx/nginx.conf` | root | Config Nginx (montable via volumen) |
| `/home/appuser/.ssh/` | — | Llaves SSH (montable via volumen) |

---

## Ver también

- [Referencia de Variables de Entorno](../../05-reference/environment-vars.md)
- [Referencia de SFTP](../../05-reference/sftp.md)
- [Guía de configuración SFTP](sftp-setup.md)
