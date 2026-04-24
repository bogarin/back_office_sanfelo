# Backoffice de Trámites - Gobierno de San Felipe

Microservicio de gestión de trámites para las dependencias del gobierno de San Felipe. Interfaz basada en Django Admin con roles RBAC (Administrador, Coordinador, Analista).

---

## Quick Start

### Desarrolladores

```bash
# Requisitos: Python 3.14, uv, PostgreSQL
git clone <URL> && cd backoffice_tramites
cp .env.example .env          # Editar con tus valores
just install                   # uv sync
just migrate                   # Crear tablas en schema backoffice
just setup_roles               # Crear grupos RBAC
just createsuperuser           # Crear usuario admin
just run                       # Iniciar servidor en localhost:8000
```

**Tutorial completo:** [Setup de desarrollo](docs/02-tutorials/developers/local-dev-setup.md)

### Sysadmins (Producción)

```bash
cp .env.example .env          # Configurar TODAS las variables de producción
docker compose up -d           # Iniciar PostgreSQL + aplicación
docker compose exec backoffice python manage.py createsuperuser
docker compose exec backoffice python manage.py setup_roles
```

**Guía completa:** [Despliegue en producción](docs/03-guides/sysadmins/deploy-production.md)

---

## Arquitectura

| Componente | Tecnología | Detalle |
|------------|------------|---------|
| **Framework** | Django 6.0.2 | Python 3.14 |
| **Interface** | Django Admin | jazzmin (Bootstrap) |
| **Base de datos** | PostgreSQL 16 | 2 schemas: `backoffice` + `public` |
| **Cache** | LocMemCache | En memoria por proceso |
| **Servidor** | Nginx + Gunicorn | Contenedor único |
| **Archivos PDF** | SFTP | Servidos via Nginx X-Accel-Redirect |
| **Package manager** | uv | Con justfile |

### Roles

| Rol | Permisos |
|-----|----------|
| **Administrador** | Acceso completo (auth + trámites) |
| **Coordinador** | Asignar/reasignar, ver todos los trámites |
| **Analista** | Solo trámites propios + disponibles |

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [Arquitectura](docs/01-onboarding/architecture-overview.md) | Visión general del sistema |
| [Variables de entorno](docs/05-reference/environment-vars.md) | Referencia completa (~45 variables) |
| [Despliegue producción](docs/03-guides/sysadmins/deploy-production.md) | Guía paso a paso |
| [Setup desarrollo](docs/02-tutorials/developers/local-dev-setup.md) | Tutorial para desarrolladores |
| [Comandos](docs/05-reference/commands.md) | Management commands + justfile |
| [ADRs](docs/06-decisions/README.md) | Decisiones de arquitectura |
| [Mapa completo](docs/README.md) | Índice de toda la documentación |

---

## Comandos Útiles

```bash
just run              # Servidor de desarrollo
just test             # Ejecutar tests
just lint             # Linting con ruff
just typecheck        # Type checking con pyright
just check            # lint + typecheck
just shell            # Django shell
just setup_roles      # Crear grupos RBAC
```

---

## Licencia

Copyright © 2026 Gobierno de San Felipe. Todos los derechos reservados.
