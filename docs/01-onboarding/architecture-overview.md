# Arquitectura del Backoffice de Trámites

> **Vista arquitectónica completa del sistema**
> Última actualización: 23 de abril de 2026

---

## Resumen

El Backoffice de Trámites es una aplicación web basada en **Django Admin** que permite a los funcionarios del Gobierno de San Felipe gestionar trámites municipales. Corre en un **contenedor único** con Nginx + Gunicorn, conectado a una base de datos **PostgreSQL** con separación de esquemas.

---

## Diagrama General

```
┌─────────────────────────────────────────────────────────┐
│                    NAVEGADOR WEB                         │
│            (Administrador / Coordinador / Analista)      │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   CONTENEDOR DOCKER                       │
│                                                          │
│  ┌──────────────┐     ┌──────────────────────────────┐  │
│  │    Nginx     │────▶│        Gunicorn               │  │
│  │   (:8080)    │     │  (:8081 interno, 4 workers)   │  │
│  │              │     └──────────────┬───────────────┘  │
│  │ - /static/   │                    │                   │
│  │ - /media/    │                    ▼                   │
│  │ - /admin/ ───┤           ┌──────────────┐            │
│  │ - /sftp-cache│           │    Django     │            │
│  │ - /healthz   │           │   Admin +     │            │
│  └──────────────┘           │   jazzmin     │            │
│                             └──────┬───────┘            │
└────────────────────────────────────┼─────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                                 ▼
        ┌───────────────────┐             ┌──────────────────┐
        │   PostgreSQL      │             │  Servidor SFTP   │
        │                   │             │  (PDFs remotos)  │
        │ Schema: backoffice│             │                  │
        │  - auth, sessions │             │  /data/tramites/ │
        │  - AsignacionTramite│           │    /pdfs/*.pdf   │
        │                   │             └──────────────────┘
        │ Schema: public    │
        │  - v_tramites_unificado (vista)
        │  - actividades    │
        │  - cat_tramite    │
        │  - cat_estatus    │
        │  - cat_perito     │
        │  - (etc.)         │
        └───────────────────┘
```

---

## Componentes Principales

### 1. Interfaz: Django Admin (jazzmin)

La interfaz de usuario es exclusivamente **Django Admin** con el tema **jazzmin** (Bootstrap). No hay API REST ni SPA.

- **3 vistas de trámites** según el rol del usuario:
  - **Todos** → Administradores y Coordinadores ven todos los trámites activos
  - **Buzón (Mis Trámites)** → Analistas ven solo sus trámites asignados
  - **Disponibles** → Todos ven los trámites sin asignar

- **Acciones rápidas:** Tomar trámite, liberar trámite
- **Acciones en lote:** Asignar/reasignar múltiples trámites
- **Filtros:** Por estatus, tipo, urgencia, asignado

### 2. Base de Datos: PostgreSQL con Schema Separation

Un solo servidor PostgreSQL con **dos esquemas lógicos**:

| Schema | Propósito | Gestión | Ejemplos |
|--------|-----------|---------|----------|
| `backoffice` | Datos propios de Django | Django migrations | auth_user, django_session, asignacion_tramite |
| `public` | Datos de negocio (legacy) | Externo (no Django) | v_tramites_unificado, actividades, cat_tramite, cat_estatus |

**Routing:** `core.db_router.ModelBasedRouter` con decorador `@register_model()` determina a qué schema va cada modelo.

### 3. Access Patterns (Patrones de Acceso)

Cada modelo tiene un patrón de acceso definido:

| Patrón | Permite | Usado por |
|--------|---------|-----------|
| **FULL_ACCESS** | Create, Read, Update, Delete | AsignacionTramite, Django auth |
| **READ_ONLY** | Solo Read | Tramite, catálogos (cat_tramite, cat_estatus, etc.) |
| **APPEND_ONLY** | Create + Read | Actividades (auditoría, nunca se modifica/borra) |

**Custom Managers** enforce estos patrones a nivel ORM:
- `ReadOnlyManager` — Bloquea create/update/delete
- `CreateOnlyManager` — Permite create, bloquea update/delete
- `CachedCatalogManager` — Solo lectura + cache en memoria

### 4. Modelo de Datos: Vista Denormalizada

El modelo central `Tramite` mapea a la vista PostgreSQL `v_tramites_unificado`, que consolida datos de múltiples tablas en una sola lectura optimizada (28 campos).

```
┌─────────────────────┐     ┌──────────────────────┐
│  v_tramites_unificado│     │    actividades       │
│  (Vista READ_ONLY)   │     │  (APPEND_ONLY)       │
│                      │     │                      │
│  - datos del trámite │◀────│  - fuente de verdad  │
│  - datos solicitante │     │  - cada cambio =     │
│  - datos perito      │     │    nueva actividad   │
│  - última actividad  │     │  - auditoría         │
│  - datos asignación  │     │    automática        │
└─────────────────────┘     └──────────────────────┘
         ▲                              │
         │    PostgreSQL triggers       │
         └──────────────────────────────┘
```

**Flujo de escritura:**
1. Usuario cambia estatus → Django crea registro en `actividades`
2. PostgreSQL trigger actualiza la vista `v_tramites_unificado`
3. La siguiente lectura refleja el cambio

Ver [ADR-009: Vista PostgreSQL Unificada](../06-decisions/009-vista-postgresql-para-tramites.md).

### 5. Sistema de Archivos: SFTP

Los PDFs de requisitos de trámites se almacenan en un **servidor SFTP externo**. El flujo de descarga:

```
Usuario solicita PDF → Django descarga de SFTP a cache local
                     → Nginx sirve via X-Accel-Redirect
                     → Cache se limpia automáticamente
```

Ver [Referencia SFTP](../05-reference/sftp.md) y [Guía SFTP](../03-guides/sysadmins/sftp-setup.md).

### 6. Cache: LocMemCache

El sistema usa **LocMemCache** (memoria por proceso) — no Redis. Tres niveles:

| Nivel | Mecanismo | Uso |
|-------|-----------|-----|
| **Process** | `@lru_cache` | Catálogos que casi nunca cambian |
| **Django Cache** | LocMemCache | Estadísticas de trámites (5 min TTL) |
| **Request** | `CacheUserRolesMiddleware` | Roles del usuario (por request) |

Ver [ADR-003: Estrategia de Caching](../06-decisions/003-estrategia-caching-rendimiento.md).

### 7. RBAC: Roles y Permisos

Tres roles definidos en `core/rbac/constants.py`:

| Rol | Ve | Puede hacer |
|-----|-----|-------------|
| **Administrador** | Todo | CRUD completo + gestión usuarios |
| **Coordinador** | Todos los trámites | Asignar/reasignar trámites |
| **Analista** | Solo sus trámites + disponibles | Tomar trámites, cambiar estatus |

Ver [ADR-013: RBAC Tres Roles](../06-decisions/013-rbac-tres-roles.md).

---

## Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Lenguaje | Python | 3.14 |
| Framework | Django | 6.0.2 |
| Admin UI | jazzmin | 3.0.3 |
| Base de datos | PostgreSQL | 16 |
| Servidor WSGI | Gunicorn | 25.1+ |
| Proxy reverso | Nginx | (distro) |
| Contenedores | Docker/Podman | - |
| Package manager | uv | latest |
| Task runner | just | - |
| Linting | ruff | - |
| Type checking | pyright | - |
| Testing | pytest + pytest-django | - |

---

## Apps Django

| App | Propósito |
|-----|-----------|
| `core` | Infraestructura: RBAC, middleware, db router, management commands |
| `tramites` | Modelos de negocio: Tramite, Actividades, Catálogos, Admin config |
| `jazzmin` | Tema Bootstrap para Django Admin |
| `django.contrib.*` | Auth, sessions, admin, messages, staticfiles |

---

## Ver también

- [¿Qué es el Backoffice?](overview.md)
- [Glosario](glossary.md)
- [ADR-008: PostgreSQL Schema Separation](../06-decisions/008-postgresql-schema-separation.md)
- [ADR-009: Vista PostgreSQL Unificada](../06-decisions/009-vista-postgresql-para-tramites.md)
- [ADR-012: Stack Tecnológico Actualizado](../06-decisions/012-stack-base-actualizado.md)
