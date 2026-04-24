# 012: Stack Tecnológico Actualizado

**Fecha:** 23 de abril de 2026
**Estado:** Accepted
**Supersedes:** [ADR-001: Selección de Stack Tecnológico Base](001-seleccion-stack-base.md)

## Contexto

El ADR-001 definía un stack con SQLite + PostgreSQL como bases de datos duales. El proyecto evolucionó significativamente desde febrero 2026:

- **ADR-008** unificó la base de datos a un solo PostgreSQL con separación de esquemas
- **ADR-009** consolidó los modelos de trámites en una vista PostgreSQL unificada
- El sistema de roles evolucionó de 2 roles (Operador/Administrador) a 3 roles (Administrador/Coordinador/Analista)
- Se integró SFTP para servir archivos PDF via Nginx X-Accel-Redirect
- No se construyó REST API — la interfaz es exclusivamente Django Admin

## Decisión

El stack tecnológico actual del proyecto es:

### Backend

| Componente | Tecnología | Versión |
|------------|------------|---------|
| **Lenguaje** | Python | 3.14 |
| **Framework** | Django | 6.0.2 |
| **Interfaz** | Django Admin (jazzmin) | 3.0.3 |
| **Base de datos** | PostgreSQL (dos schemas) | 16 |
| **Servidor WSGI** | Gunicorn | 25.1+ |
| **Proxy reverso** | Nginx | (distro) |
| **Cache** | LocMemCache | Django built-in |

### Infraestructura

| Componente | Tecnología |
|------------|------------|
| **Contenedores** | Docker / Podman |
| **Orquestación** | Docker Compose |
| **Package manager** | uv |
| **Task runner** | just |
| **Almacenamiento archivos** | SFTP (django-storages) |

### Herramientas de desarrollo

| Componente | Tecnología |
|------------|------------|
| **Linting** | ruff |
| **Type checking** | pyright |
| **Testing** | pytest + pytest-django + factory-boy |
| **Cobertura** | pytest-cov |

### Configuración

| Componente | Tecnología |
|------------|------------|
| **Variables de entorno** | django-environ |
| **Logging** | Django logging framework |
| **Seguridad** | Django CSP (6.0 native) |

### Arquitectura de Base de Datos

Un solo servidor PostgreSQL con dos esquemas:

| Schema | Propósito | Gestión |
|--------|-----------|---------|
| `backoffice` | Django auth, sessions, admin, AsignacionTramite | Django migrations |
| `public` | Trámites, catálogos, actividades, peritos | Externo (no migrations) |

**Routing:** `core.db_router.ModelBasedRouter` con decorador `@register_model()` y `AccessPattern` (FULL_ACCESS, READ_ONLY, APPEND_ONLY).

### Arquitectura de Despliegue

Contenedor único con Nginx + Gunicorn:
- Nginx escucha en puerto 8080 (externo)
- Gunicorn escucha en 127.0.0.1:8081 (interno)
- Archivos estáticos servidos directamente por Nginx
- PDFs servidos via X-Accel-Redirect desde cache SFTP

### Sistema RBAC

Tres roles definidos en `core/rbac/constants.py`:

| Rol | Acceso |
|-----|--------|
| **Administrador** | Acceso completo a auth + tramites |
| **Coordinador** | Puede asignar/reasignar, ve todos los trámites |
| **Analista** | Solo sus trámites asignados + disponibles |

## Cambios respecto a ADR-001

| Aspecto | ADR-001 | ADR-012 (actual) |
|---------|---------|-------------------|
| BD auth | SQLite | PostgreSQL (backoffice schema) |
| BD negocio | PostgreSQL | PostgreSQL (public schema) |
| Cache | "Incluso Redis si es necesario" | LocMemCache (Redis rechazado, ADR-003) |
| Interfaz | Django Admin | Django Admin + jazzmin |
| API | No mencionada | No existe (Django Admin only) |
| Roles | Operador/Administrador | Administrador/Coordinador/Analista |
| SFTP | No mencionado | Integrado para PDFs |
| Contenedor | Mencionado | Nginx + Gunicorn single container |

## Consecuencias

### Positivas

- **Simplificación operativa:** Un solo PostgreSQL vs SQLite + PostgreSQL
- **Consistencia de datos:** Transacciones ACID dentro del mismo servidor
- **Backup simplificado:** Un solo pg_dump vs dos estrategias
- **Performance:** LocMemCache es suficiente para la carga actual (50 usuarios simultáneos)
- **Mantenibilidad:** Menos componentes, menos puntos de fallo

### Negativas

- **Vendor lock-in PostgreSQL:** Vista `v_tramites_unificado` y triggers no son portables
- **Sin Redis:** Cache no distribuido entre workers (cada worker tiene su propia cache)
- **Django Admin como límite:** Sin API REST, no hay integración programática externa

## Alternativas Consideradas

Las alternativas originales (Java/NodeJS, Laravel) siguen descartadas por las mismas razones del ADR-001. Los cambios principales respecto a ADR-001 son:

1. **SQLite → PostgreSQL schema:** Simplifica operaciones, elimina dual-DB
2. **Redis rechazado:** LocMemCache suficiente para carga actual (ver ADR-003)
3. **No REST API:** Django Admin cumple los requisitos del sistema

## Referencias

- [ADR-001: Stack base original](001-seleccion-stack-base.md) (superseded por este)
- [ADR-003: Estrategia de caching](003-estrategia-caching-rendimiento.md)
- [ADR-005: Despliegue Docker + Gunicorn](005-despliegue-docker-gunicorn.md)
- [ADR-008: PostgreSQL Schema Separation](008-postgresql-schema-separation.md)
- [ADR-009: Vista PostgreSQL unificada](009-vista-postgresql-para-tramites.md)
- [ADR-013: RBAC tres roles](013-rbac-tres-roles.md)
