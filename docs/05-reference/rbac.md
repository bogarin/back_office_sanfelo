# Referencia: Sistema RBAC (Roles y Permisos)

> **Fuente de verdad:** `core/rbac/constants.py` y `core/rbac/__init__.py`
> Última actualización: 23 de abril de 2026

---

## Resumen

El sistema usa **RBAC (Role-Based Access Control)** con 3 roles implementados como grupos de Django. Los permisos custom controlan la visibilidad de secciones en el sidebar de jazzmin.

---

## Roles

| Rol | Grupo Django | Descripción |
|-----|-------------|-------------|
| **Administrador** | `Administrador` | Acceso completo a auth + tramites |
| **Coordinador** | `Coordinador` | Ver todos los trámites, asignar/reasignar |
| **Analista** | `Analista` | Solo trámites propios + disponibles |

Definidos en `core/rbac/constants.py` como `BackOfficeRole(StrEnum)`.

---

## Permisos por Rol

### Administrador

**Permisos estándar de Django:**
- Acceso completo (add, change, delete, view) a todas las modelos de las apps `auth` y `tramites`

**Permisos custom (sidebar):**

| Permiso | Sección visible |
|---------|----------------|
| `view_mis_tramites` | Tramites → Mis Tramites |
| `view_todos` | Tramites → Todos |
| `view_disponibles` | Tramites → Disponibles |
| `view_asignados` | Tramites → Asignados |
| `view_finalizados` | Tramites → Finalizados |

### Coordinador

**Permisos estándar:** Ninguno (solo permisos custom)

**Permisos custom (sidebar):**

| Permiso | Sección visible |
|---------|----------------|
| `view_todos` | Tramites → Todos |
| `view_disponibles` | Tramites → Disponibles |
| `view_asignados` | Tramites → Asignados |
| `view_finalizados` | Tramites → Finalizados |

### Analista

**Permisos estándar:** Ninguno (solo permisos custom)

**Permisos custom (sidebar):**

| Permiso | Sección visible |
|---------|----------------|
| `view_mis_tramites` | Tramites → Mis Tramites |
| `view_disponibles` | Tramites → Disponibles |

---

## Proxy Models por Rol

Cada rol ve trámites a través de un proxy model diferente:

| Proxy Model | Queryset | Roles |
|-------------|----------|-------|
| `Tramite` | Todos los trámites activos (estatus 201-205) | Administrador, Coordinador |
| `Buzon` | Trámites asignados al usuario actual | Analista |
| `Disponible` | Trámites sin asignar | Todos los roles |

---

## Comando `setup_roles`

Crea los grupos y asigna permisos:

```bash
python manage.py setup_roles
```

**Qué hace:**
1. Crea 3 grupos: Administrador, Coordinador, Analista
2. Crea 5 permisos custom en la BD
3. Limpia permisos existentes de cada grupo
4. Asigna permisos estándar + custom según la configuración

**Idempotente:** Se puede ejecutar múltiples veces sin efectos secundarios.

---

## Asignar Roles a Usuarios

Desde Django Admin:

1. Ir a **Autenticación y Autorización → Usuarios**
2. Seleccionar un usuario
3. En **Grupos**, agregar: `Administrador`, `Coordinador`, o `Analista`
4. Guardar

> **Nota:** Un usuario puede tener múltiples grupos, pero la interfaz está diseñada para un rol principal.

---

## Middleware: CacheUserRolesMiddleware

`core/middleware.py` — Carga los roles del usuario una vez por request:

```python
# Disponible en views y templates:
request.user.roles  # set[str], ej: {'Administrador'}
```

Los roles se cachean por request, no por sesión. Si cambias el grupo de un usuario, el cambio se refleja en el próximo request.

---

## Ver también

- [ADR-013: RBAC Tres Roles](../06-decisions/013-rbac-tres-roles.md)
- [ADR-007: RBAC original (superseded)](../06-decisions/007-implementacion-rbac-django-60.md)
- [Referencia de Comandos](commands.md) — `setup_roles`
- [Código fuente](../../core/rbac/constants.py) — Fuente autoritativa
