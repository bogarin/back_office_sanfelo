# Referencia: Sistema RBAC (Roles y Permisos)

> **Fuente de verdad:** `core/rbac/constants.py`, `core/rbac/__init__.py`, `core/models.py`, `tramites/models/tramite.py`
> Última actualización: 9 de mayo de 2026

______________________________________________________________________

## Resumen

El sistema usa **RBAC (Role-Based Access Control)** con 3 roles implementados como grupos de Django. Los permisos custom controlan la visibilidad de secciones en el sidebar de Jazzmin. Un Custom User Model (`core.User`) expone properties de rol, y el modelo `Tramite` implementa permisos a nivel de objeto para controlar el acceso a trámites individuales.

______________________________________________________________________

## Roles

| Rol | Grupo Django | Descripción |
|-----|-------------|-------------|
| **Administrador** | `Administrador` | Acceso completo a auth + core + tramites |
| **Coordinador** | `Coordinador` | Ver todos los trámites, asignar/reasignar |
| **Analista** | `Analista` | Solo trámites propios + disponibles |

Definidos en `core/rbac/constants.py` como `BackOfficeRole(StrEnum)`.

______________________________________________________________________

## Custom User Model

`core.User` extiende `AbstractUser` y está configurado como `AUTH_USER_MODEL = 'core.User'`. No agrega campos a la base de datos — los roles se derivan de la membresía a grupos Django.

### Properties de rol

| Property | Retorna | Implementación |
|----------|---------|----------------|
| `user.is_administrador` | `bool` | `BackOfficeRole.ADMINISTRADOR in self._get_roles()` |
| `user.is_coordinador` | `bool` | `BackOfficeRole.COORDINADOR in self._get_roles()` |
| `user.is_analista` | `bool` | `BackOfficeRole.ANALISTA in self._get_roles()` |

Uso típico:

```python
if user.is_coordinador:
    # lógica específica del rol
    ...
```

### Resolución de roles (`_get_roles`)

Las properties delegan a `_get_roles()` que:

1. Retorna `user.roles` (cacheado por `CacheUserRolesMiddleware`) si está disponible
1. Si no, consulta la base de datos: `user.groups.values_list('name', flat=True)`

En práctica, `CacheUserRolesMiddleware` siempre pobla `user.roles`, por lo que el fallback a BD es solo una salvaguarda.

### Migración

La migración inicial del Custom User Model es `core/migrations/0001_custom_user_model.py`.

> **Referencia:** `core/models.py`

______________________________________________________________________

## Permisos por Rol

### Administrador

**Permisos estándar de Django:**

Acceso completo (add, change, delete, view) a todas las modelos de las apps `auth`, `core` y `tramites`:

```python
ADMINISTRADOR_APPS = ['auth', 'core', 'tramites']
```

**Permisos custom (sidebar Jazzmin):**

| Permiso | Sección visible |
|---------|----------------|
| `acceso_analista` | Mis trámites + Disponibles |
| `acceso_coordinador` | Trámites en curso + Finalizados |

### Coordinador

**Permisos estándar:** Ninguno (solo permisos custom).

**Permisos custom (sidebar Jazzmin):**

| Permiso | Sección visible |
|---------|----------------|
| `acceso_coordinador` | Trámites en curso + Finalizados |

### Analista

**Permisos estándar:** Ninguno (solo permisos custom).

**Permisos custom (sidebar Jazzmin):**

| Permiso | Sección visible |
|---------|----------------|
| `acceso_analista` | Mis trámites + Disponibles |

______________________________________________________________________

## Proxy Models por Rol

Cada rol ve trámites a través de un proxy model diferente:

| Proxy Model | Queryset | Roles |
|-------------|----------|-------|
| `Tramite` | Todos los trámites activos (estatus 201-205) | Administrador, Coordinador |
| `Buzon` | Trámites asignados al usuario actual | Analista |
| `Disponible` | Trámites sin asignar | Todos los roles |
| `Cerrado` | Trámites finalizados (estatus 301-304) | Coordinador |

> **Referencia:** `tramites/models/tramite.py`

______________________________________________________________________

## Transiciones del Workflow

El modelo `Tramite` define un dict `TRANSITIONS` que mapea todas las transiciones de estado válidas como `(from_status, to_status) → True`:

```
TRANSITIONS = {
    # Asignar: presentado → en revisión
    (201, 202): True,
    # Reasignar: en revisión → en revisión (cambio de analista)
    (202, 202): True,
    # Liberar: en revisión → presentado (volver al pool)
    (202, 201): True,
    # Requerir documentos: en revisión → requerimiento
    (202, 203): True,
    # Enviar a firma: en revisión → en diligencia
    (202, 205): True,
    # Cancelar desde estados activos → estados terminales
    (202, 301): True,  # por recoger
    (202, 302): True,  # rechazado
    (202, 304): True,  # cancelado
    (203, 301): True,  # por recoger
    (203, 302): True,  # rechazado
    (203, 304): True,  # cancelado
    (205, 301): True,  # por recoger
    (205, 302): True,  # rechazado
    (205, 304): True,  # cancelado
}
```

Cada método de acción (`requerir_documentos`, `enviar_a_firma`, `cancelar`) valida la transición vía `_validate_transition(to_status)`. La excepción es `_liberar()`: solo usa `_assert_activo()` porque la liberación es un "reset" que aplica a cualquier estado activo.

**Agregar una transición nueva** = agregar una línea al dict. No se necesita modificar lógica en los métodos.

> **Referencia:** `tramites/models/tramite.py` (constante `TRANSITIONS`)

______________________________________________________________________

## Permisos a Nivel de Objeto

El modelo `Tramite` implementa permisos a nivel de objeto (object-level permissions) mediante métodos que evalúan el rol del usuario y el estado del trámite. Esto centraliza la autorización en el modelo (patrón "Fat Models") y evita dispersar lógica de permisos en admin, views y templates.

### Métodos de permisos

| Método | Retorna | Descripción |
|--------|---------|-------------|
| `can_view(user)` | `bool` | ¿Puede ver el detalle del trámite? |
| `can_download(user)` | `bool` | ¿Puede descargar documentos del trámite? |
| `can_assign(user)` | `bool` | ¿Puede asignar/reasignar el trámite? |
| `can_release(user)` | `bool` | ¿Puede liberar el trámite al pool? |
| `can_execute_action(user)` | `bool` | ¿Puede ejecutar acciones de workflow? |
| `available_actions(user)` | `list[str]` | Lista de acciones disponibles según rol + estatus |

### Reglas por rol

#### `can_view(user)`

| Rol | Condición |
|-----|-----------|
| Superuser / Administrador / Coordinador | Siempre `True` |
| Analista | Solo si `tramite.asignado_user_id == user.id` |

#### `can_download(user)`

| Rol | Condición |
|-----|-----------|
| Superuser / Administrador / Coordinador | Siempre `True` |
| Analista | Si está asignado al trámite, **o** si el trámite no tiene asignado y está activo |

#### `can_assign(user)` / `can_release(user)`

| Rol | Condición |
|-----|-----------|
| Superuser / Administrador / Coordinador | `True` |
| Analista | `False` |

#### `can_execute_action(user)`

| Rol | Condición |
|-----|-----------|
| Superuser / Administrador / Coordinador | Siempre `True` |
| Analista | Solo si está asignado al trámite |

#### `available_actions(user)`

Retorna una lista de nombres de acción que el usuario puede ejecutar en el estatus actual. Si `can_execute_action()` es `False`, retorna `[]`.

| Estatus actual | Acciones disponibles |
|----------------|---------------------|
| EN_REVISION (202) | `['requerir_documentos', 'enviar_a_firma', 'cancelar']` |
| REQUERIMIENTO (203) | `['cancelar']` |
| EN_DILIGENCIA (205) | `['cancelar']` |
| Otro estatus | `[]` |

### Consumidores

Estos métodos son consumidos por:

| Consumidor | Uso |
|------------|-----|
| `tramites/admin.py` (change_view) | `can_view()` para protección IDOR; `available_actions()` para POST y template |
| `tramites/views.py` (download_requisito_pdf) | `can_download()` — reemplaza la antigua `_check_download_permission` |
| `templates/admin/tramite_detail.html` | `{% if 'accion' in available_actions %}` para botones condicionales |
| `tramites/admin.py` (acciones_disponible, liberar_rapido) | `can_release()` para validar permisos |

> **Referencia:** `tramites/models/tramite.py` (métodos `can_*` y `available_actions`)

______________________________________________________________________

## Comando `setup_roles`

Crea los grupos y asigna permisos:

```bash
python manage.py setup_roles
```

**Qué hace:**

1. Crea 3 grupos: Administrador, Coordinador, Analista
1. Crea 2 permisos custom en la BD (`acceso_analista`, `acceso_coordinador`)
1. Limpia permisos existentes de cada grupo
1. Asigna permisos estándar + custom según la configuración

**Idempotente:** Se puede ejecutar múltiples veces sin efectos secundarios.

______________________________________________________________________

## Asignar Roles a Usuarios

Desde Django Admin:

1. Ir a **Autenticación y Autorización → Usuarios**
1. Seleccionar un usuario
1. En **Grupos**, agregar: `Administrador`, `Coordinador`, o `Analista`
1. Guardar

> **Nota:** Un usuario puede tener múltiples grupos, pero la interfaz está diseñada para un rol principal.

______________________________________________________________________

## Middleware: CacheUserRolesMiddleware

`core/middleware.py` — Carga los roles del usuario una vez por request:

```python
# Disponible en views y templates:
request.user.roles  # set[str], ej: {'Administrador'}
```

Los roles se cachean por request, no por sesión. Si cambias el grupo de un usuario, el cambio se refleja en el próximo request.

Para usuarios anónimos, `request.user.roles` es un `set()` vacío.

______________________________________________________________________

## Ver también

- [ADR-014: Custom User Model, Workflow Refactoring, Permission Methods](../02-DECISIONES/014-custom-user-workflow-permissions.md)
- [ADR-013: RBAC Tres Roles](../02-DECISIONES/013-rbac-tres-roles.md)
- [ADR-007: RBAC original (superseded)](../02-DECISIONES/007-implementacion-rbac-django-60.md)
- [Referencia de Comandos](commands.md) — `setup_roles`
- [Código fuente RBAC](../../core/rbac/constants.py) — Fuente autoritativa de roles y permisos
- [Código fuente User Model](../../core/models.py) — Custom User con properties de rol
- [Código fuente Tramite](../../tramites/models/tramite.py) — Permisos a nivel de objeto y TRANSITIONS
