# 013: Sistema RBAC con Tres Roles

**Fecha:** 23 de abril de 2026
**Estado:** Accepted
**Supersedes:** [ADR-007: Implementación de RBAC para Django 6.0](007-implementacion-rbac-django-60.md)

## Contexto

El ADR-007 definía un sistema RBAC con dos roles (Operador/Administrador) usando SQLite para auth, e incluía auditoría asíncrona con "Background Tasks" y un sistema de bitácora. El sistema evolucionó a tres roles, eliminó la bitácora como tabla separada (las Actividades sirven como auditoría), y migró a PostgreSQL con schema separation (ADR-008).

**Problemas con ADR-007:**

- Solo definía 2 roles (Operador, Administrador); el sistema ahora tiene 3 (Administrador, Coordinador, Analista)
- Referenciaba SQLite para auth, pero ahora todo es PostgreSQL (ADR-008)
- Mencionaba "AuditTrailMixin", "Async Audit Logging" y "Bitacora" que no existen en el código actual
- Afirmaba "10-40x más rápido" y "1,612+ líneas de documentación" sin base verificable
- El sistema de permisos es más simple de lo que describía (no hay auditoría automática, no hay bitácora separada)

## Decisión

### Roles Definidos

Tres roles implementados en `core/rbac/constants.py` como `BackOfficeRole(StrEnum)`:

| Rol | Nombre | Grupo Django | Descripción |
|-----|--------|-------------|-------------|
| `ADMINISTRADOR` | "Administrador" | `Group(name="Administrador")` | Acceso completo a auth + tramites |
| `COORDINADOR` | "Coordinador" | `Group(name="Coordinador")` | Asignar/reasignar, ver todos los trámites |
| `ANALISTA` | "Analista" | `Group(name="Analista")` | Solo trámites propios + disponibles |

### Permisos por Rol

#### Administrador

**Apps con acceso completo** (`ADMINISTRADOR_APPS`): `auth`, `tramites`
- Recibe TODOS los permisos (add, change, delete, view) para todas las modelos de estas apps
- Permisos custom: `view_mis_tramites`, `view_todos`, `view_disponibles`, `view_asignados`, `view_finalizados`

#### Coordinador

- Permisos custom únicamente: `view_todos`, `view_disponibles`, `view_asignados`, `view_finalizados`
- Sin permisos estándar de Django (no puede agregar/modificar/eliminar modelos directamente)
- Control de visibilidad via sidebar de Jazzmin

#### Analista

- Permisos custom únicamente: `view_mis_tramites`, `view_disponibles`
- Sin permisos estándar de Django
- Ve solo trámites asignados a sí mismo y trámites disponibles

### Permisos Custom (TramitePermission)

Los permisos custom controlan la visibilidad de links en el sidebar de Jazzmin:

| Permiso | Link en Sidebar | Roles |
|---------|----------------|-------|
| `view_mis_tramites` | Tramites / Mis Tramites | Analista, Administrador |
| `view_todos` | Tramites / Todos | Administrador, Coordinador |
| `view_disponibles` | Tramites / Disponibles / Sin asignar | Todos los roles |
| `view_asignados` | Tramites / Asignados | Administrador, Coordinador |
| `view_finalizados` | Tramites / Finalizados | Administrador, Coordinador |

### Implementación

**Archivo central:** `core/rbac/constants.py` — Fuente autoritativa de roles y permisos
**Módulo:** `core/rbac/__init__.py` — Funciones de setup
**Comando:** `manage.py setup_roles` — Crea grupos y asigna permisos

**Flujo de setup:**

1. `setup_all_roles()` llama a `setup_administrador()`, `setup_coordinador()`, `setup_analista()`
2. Cada función crea el `Group` via `get_or_create_group()`
3. Limpia permisos existentes (`group.permissions.clear()`)
4. Administrador: asigna todos los permisos estándar de `ADMINISTRADOR_APPS` + permisos custom
5. Coordinador/Analista: solo asigna permisos custom para sidebar

**Middleware:** `CacheUserRolesMiddleware` — Carga roles del usuario una vez por request en `request.user.roles` (set[str])

**Proxy Models por rol:**

| Proxy Model | Queryset | Visible para |
|-------------|----------|-------------|
| `Tramite` | Todos los trámites activos | Administrador, Coordinador |
| `Buzon` | Trámites asignados al usuario | Analista |
| `Disponible` | Trámites sin asignar | Todos los roles |

### Auditoría

La auditoría NO se implementa con una tabla de bitácora separada. En su lugar:

- **Tabla `actividades`** es la fuente de verdad (APPEND_ONLY)
- Cada cambio de estatus, asignación, u observación se registra como una nueva entrada en `actividades`
- PostgreSQL triggers mantienen la vista `v_tramites_unificado` sincronizada
- El modelo `Tramite` es READ_ONLY — las escrituras van siempre a `Actividades`

## Consecuencias

### Positivas

- **Simplicidad:** 3 roles bien definidos vs sistema genérico de permisos
- **Sin dependencias externas:** No usa django-guardian ni otros paquetes
- **Código centralizado:** Todo RBAC en `core/rbac/`, una sola fuente de verdad
- **Sidebar controlado:** Permisos custom controlan exactamente qué ve cada rol
- **Auditoría inherente:** Actividades como APPEND_ONLY proporcionan historial completo

### Negativas

- **Sin control a nivel de objeto:** Los permisos son por modelo, no por instancia individual
- **Coordinador sin permisos estándar:** No puede hacer CRUD directo, solo ver y asignar via acciones custom
- **Middleware de cache:** Los roles se cachean por request — cambios de grupo requieren nuevo login

## Diferencias con ADR-007

| Aspecto | ADR-007 | ADR-013 (actual) |
|---------|---------|-------------------|
| Roles | 2 (Operador, Administrador) | 3 (Administrador, Coordinador, Analista) |
| BD Auth | SQLite | PostgreSQL (backoffice schema) |
| Auditoría | Bitacora + AuditTrailMixin + Async | Actividades (APPEND_ONLY) |
| Permisos | Descripción genérica | Permisos custom para Jazzmin sidebar |
| Terceros | No pero los consideró | No, confirmado |
| Proxy Models | No mencionados | Buzon, Disponible |
| Middleware | No mencionado | CacheUserRolesMiddleware |

## Referencias

- [ADR-007: RBAC original](007-implementacion-rbac-django-60.md) (superseded por este)
- [ADR-006: Permisos admin-operador](006-permisos-admin-operador.md) (superseded por ADR-007)
- [ADR-008: PostgreSQL Schema Separation](008-postgresql-schema-separation.md)
- [ADR-009: Vista PostgreSQL unificada](009-vista-postgresql-para-tramites.md)
- `core/rbac/constants.py` — Definiciones autoritativas de roles y permisos
- `core/rbac/__init__.py` — Funciones de setup de roles
- `core/middleware.py` — CacheUserRolesMiddleware
