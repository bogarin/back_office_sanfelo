# Tutorial: Configurar Entorno de Desarrollo Local

> **Para:** Desarrolladores nuevos en el proyecto
> **Tiempo estimado:** 30 minutos
> **Última actualización:** 23 de abril de 2026

---

## Resumen

Este tutorial te guía paso a paso para levantar el Backoffice de Trámites en tu máquina local para desarrollo.

---

## Prerequisitos

Antes de empezar necesitas:

| Requisito | Versión | Cómo verificar |
|-----------|---------|----------------|
| **Python** | 3.14+ | `python --version` |
| **uv** | latest | `uv --version` |
| **PostgreSQL** | 16+ | `psql --version` |
| **just** | latest | `just --version` |
| **Git** | any | `git --version` |

### Instalar prerequisitos

```bash
# uv (package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# just (task runner)
cargo install just
# o en Ubuntu/Debian:
sudo apt install just

# PostgreSQL (si no lo tienes)
sudo apt install postgresql-16
```

---

## Paso 1: Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO> backoffice_tramites
cd backoffice_tramites
```

---

## Paso 2: Instalar dependencias

```bash
just install
```

Esto ejecuta `uv sync` que instala todas las dependencias del proyecto (Django, psycopg2, gunicorn, etc.) y crea el entorno virtual.

---

## Paso 3: Crear la base de datos

```bash
# Conectarse a PostgreSQL
sudo -u postgres psql

# Crear la base de datos y usuario
CREATE DATABASE backoffice_tramites;
CREATE USER backoffice_user WITH PASSWORD 'backoffice_pass';
GRANT ALL PRIVILEGES ON DATABASE backoffice_tramites TO backoffice_user;

# Crear el schema backoffice
\c backoffice_tramites
CREATE SCHEMA IF NOT EXISTS backoffice AUTHORIZATION backoffice_user;

# Salir
\q
```

---

## Paso 4: Configurar variables de entorno

```bash
# Copiar el template
cp .env.example .env
```

Editar `.env` con los valores mínimos para desarrollo:

```bash
# === MÍNIMO PARA DESARROLLO ===
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=dev-secret-key-change-in-production-abc123
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
POSTGRESQL_DB_URL=postgres://backoffice_user:backoffice_pass@localhost:5432/backoffice_tramites
BACKOFFICE_DB_SCHEMA=backoffice
BACKEND_DB_SCHEMA=public
```

> **Referencia completa:** [Variables de Entorno](../../05-reference/environment-vars.md)

---

## Paso 5: Cargar datos de negocio (fixtures)

Los catálogos y datos de negocio están en fixtures:

```bash
uv run manage.py loaddata backend.json
```

Esto carga los catálogos (tipos de trámite, estatus, peritos, etc.) en el schema `public`.

---

## Paso 6: Ejecutar migraciones

```bash
just migrate
```

Esto crea las tablas de Django (auth, sessions, admin, AsignacionTramite) en el schema `backoffice`.

---

## Paso 7: Crear superusuario

```bash
just createsuperuser
```

Sigue las instrucciones interactivas para crear tu usuario admin.

---

## Paso 8: Configurar roles RBAC

```bash
just setup_roles
```

Esto crea los 3 grupos: Administrador, Coordinador, Analista.

---

## Paso 9: Iniciar el servidor

```bash
just run
```

Abrir en el navegador: **http://localhost:8000/admin/**

Deberías ver la pantalla de login de Django Admin con el tema jazzmin.

---

## Verificar que todo funciona

1. **Login:** Inicia sesión con el superusuario que creaste
2. **Sidebar:** Deberías ver las secciones de Trámites y Autenticación
3. **Trámites:** Navega a Tramites → Disponibles — deberías ver trámites si cargaste fixtures
4. **Roles:** Ve a Autenticación → Grupos — deberías ver los 3 grupos

---

## Comandos útiles para desarrollo

```bash
just run              # Servidor de desarrollo (puerto 8000)
just shell            # Django shell interactivo
just test             # Ejecutar todos los tests
just test-app core    # Tests de una app específica
just lint             # Linting con ruff
just typecheck        # Type checking con pyright
just check            # lint + typecheck
just format           # Formatear código
just migrate-status   # Ver estado de migraciones
```

Ver: [Referencia de Comandos](../../05-reference/commands.md)

---

## Datos de prueba

Para simular pagos y generar trámites con estatus "Presentado":

```bash
uv run manage.py simular_pago
```

---

## Estructura del proyecto

```
backoffice_tramites/
├── core/                    # Infraestructura (RBAC, middleware, db router)
│   ├── rbac/               # Roles y permisos
│   ├── management/commands/ # Comandos personalizados
│   ├── middleware.py        # CacheUserRolesMiddleware
│   └── db_router.py        # ModelBasedRouter
├── tramites/                # App principal
│   ├── models/             # Modelos (Tramite, Actividades, Catálogos)
│   ├── admin.py            # Configuración del Django Admin
│   └── managers.py         # Custom managers
├── sanfelipe/               # Configuración del proyecto
│   ├── settings/           # Settings separados por tema
│   ├── urls.py
│   └── wsgi.py
├── tests/                   # Tests
├── nginx/                   # Config de Nginx (solo para Docker)
├── docker/                  # Entrypoint (solo para Docker)
├── docs/                    # Documentación
├── justfile                 # Comandos de desarrollo
├── Dockerfile               # Build de imagen Docker
└── docker-compose.yml       # Orquestación local
```

---

## Problemas comunes

### "No module named 'psycopg2'"

```bash
just install  # Reinstalar dependencias
```

### Error de conexión a PostgreSQL

Verificar que PostgreSQL está corriendo y las credenciales en `.env` son correctas:

```bash
psql postgres://backoffice_user:backoffice_pass@localhost:5432/backoffice_tramites -c "\dn"
```

### Error de migraciones

```bash
just migrate-status    # Ver qué migraciones faltan
just migrate           # Aplicar migraciones pendientes
```

### "Column does not exist" en schema public

El schema `public` es gestionado externamente. Asegúrate de haber cargado los fixtures:

```bash
uv run manage.py loaddata backend.json
```

---

## Siguiente paso

Ahora que tienes el entorno funcionando, lee:

- [Arquitectura del sistema](../../01-onboarding/architecture-overview.md) — Entender cómo funciona
- [Glosario](../../01-onboarding/glossary.md) — Términos del dominio
- [Referencia RBAC](../../05-reference/rbac.md) — Sistema de roles
