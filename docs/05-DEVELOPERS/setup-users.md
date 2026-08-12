# Configurar Usuarios y Roles

Guía paso a paso para crear usuarios y asignar roles en el Backoffice de Trámites.

## Resumen del sistema de roles

El sistema utiliza **tres roles** implementados como Django Groups. Cada usuario pertenece a exactamente un grupo, lo que determina qué secciones ve en el sidebar y qué acciones puede ejecutar sobre los trámites.

| Rol | Grupo (Django) | Perfil |
|-----|----------------|--------|
| **Administrador** | `Administrador` | Acceso completo a usuarios, grupos, catálogos y todos los trámites |
| **Coordinador** | `Coordinador` | Ve todos los trámites activos y finalizados; puede asignar/reasignar/liberar |
| **Analista** | `Analista` | Solo ve sus propios trámites y los disponibles para autoasignación |

> **Referencia técnica:** Los roles están definidos en `core/rbac/constants.py` como el enum `BackOfficeRole`. Las decisiones de diseño se documentan en [ADR-013](../02-DECISIONES/013-rbac-tres-roles.md) y [ADR-014](../02-DECISIONES/014-custom-user-workflow-permissions.md).

______________________________________________________________________

## Paso 1 — Ejecutar `setup_roles`

Antes de crear usuarios, los grupos y permisos deben existir en la base de datos.

### 1.1 Ejecutar el comando

```bash
python manage.py setup_roles
```

Salida esperada:

```
Starting role setup...
  - Administrador: N permissions (apps: auth, core, tramites + custom Jazzmin permissions)
  - Coordinador: 1 custom Jazzmin permissions (acceso_coordinador)
  - Analista: 1 custom Jazzmin permissions (acceso_analista)
  No is_staff inconsistencies found.
Role setup completed successfully
```

### 1.2 ¿Qué hace este comando?

1. **Crea los tres grupos** (`Administrador`, `Coordinador`, `Analista`) si no existen.
1. **Asigna permisos estándar de Django:**
   - **Administrador**: todos los permisos (`add`, `change`, `delete`, `view`) sobre las apps `auth`, `core` y `tramites`.
   - **Coordinador**: sin permisos estándar (solo permisos personalizados).
   - **Analista**: sin permisos estándar (solo permisos personalizados).
1. **Crea y asigna permisos personalizados** que controlan la visibilidad del sidebar:
   - `acceso_analista` → secciones "Mis trámites" + "Disponibles" (Analista y Administrador).
   - `acceso_coordinador` → secciones "Trámites en curso" + "Finalizados" (Coordinador y Administrador).
1. **Repara inconsistencias de `is_staff`**: si un usuario pertenece a un grupo de rol pero tiene `is_staff=False`, lo corrige automáticamente.

### 1.3 Ejecución automática

El comando se ejecuta automáticamente después de cada `python manage.py migrate` gracias a la señal `post_migrate` definida en `core/signals.py`. No necesitas ejecutarlo manualmente a menos que:

- Estés configurando una base de datos desde cero sin correr migraciones.
- Sospeches que los permisos están desincronizados.

El comando es **idempotente**: puedes ejecutarlo cuantas veces quieras sin duplicar datos.

______________________________________________________________________

## Paso 2 — Crear un usuario en Django Admin

### 2.1 Acceder al formulario

1. Inicia sesión en `/admin/` con un usuario Administrador o superusuario.
1. En el sidebar, ve a **Usuarios** (dentro de la sección "Core").
1. Haz clic en **Añadir usuario** (esquina superior derecha).

### 2.2 Completar el formulario

El formulario de alta (`CustomUserAddForm`) presenta los siguientes campos:

| Campo | Requerido | Notas |
|-------|-----------|-------|
| **Nombre de usuario** | Sí | Formato sugerido: `nombre.apellido`. No se puede cambiar después. |
| **Nombre** y **Apellido** | Recomendado | Se muestran en la interfaz y en las actividades de trámites. |
| **Correo electrónico** | Sí | Debe ser único en el sistema. |
| **Contraseña** / **Confirmación** | Sí | Mínimo 8 caracteres con complejidad. |
| **Rol** | Sí | Selector desplegable con los tres roles. Por defecto: `Analista`. |

### 2.3 Qué ocurre al guardar

El método `BackofficeUserAdmin.save_model()` ejecuta automáticamente:

1. **`is_staff = True`** → Todo usuario con un rol válido puede acceder al admin.
1. **`is_active = True`** → Los usuarios nuevos siempre se crean activos.
1. **Asignación al grupo** → Se elimina cualquier grupo de rol previo y se agrega al grupo seleccionado.
1. Todo se ejecuta dentro de una transacción atómica (si algo falla, no se crea el usuario).

> **Nota:** Los campos `is_staff`, `is_superuser` y `is_active` no aparecen en el formulario porque se gestionan automáticamente. El campo `is_staff` se muestra como deshabilitado con una nota que indica que se controla por el rol.

______________________________________________________________________

## Paso 3 — Asignar o cambiar el rol de un usuario

### 3.1 Desde el formulario de edición

1. Ve a **Usuarios** y haz clic en el nombre del usuario.
1. El formulario de edición (`CustomUserChangeForm`) muestra el campo **Rol** con el rol actual preseleccionado.
1. Cambia el valor del selector y guarda.

El sistema automáticamente:

- Remueve al usuario del grupo de rol anterior.
- Lo agrega al nuevo grupo.
- Mantiene `is_staff = True` mientras tenga un rol válido.
- Si seleccionas "Sin rol", el usuario pierde acceso al admin (`is_staff = False`).

### 3.2 Desde la acción masiva "Asignar rol"

1. En la lista de usuarios, selecciona uno o varios usuarios con los checkboxes.
1. En el menú desplegable de acciones, selecciona **"Asignar rol"**.
1. Serás redirigido a un formulario donde podrás elegir el nuevo rol para todos los seleccionados.

> **Protección:** Los usuarios que no son superusuarios no pueden editar ni cambiar la contraseña de un superusuario.

______________________________________________________________________

## Paso 4 — Qué ve cada rol

Las secciones del sidebar de Jazzmin se controlan mediante los permisos personalizados `acceso_analista` y `acceso_coordinador`.

### Administrador

Ve **todas** las secciones del sidebar:

| Sección | Modelo proxy | Contenido |
|---------|-------------|-----------|
| Mis trámites | `Buzon` | Trámites asignados al usuario (si tiene alguno) |
| Disponibles | `Disponible` | Trámites sin asignar y activos |
| Trámites en curso | `Tramite` | Todos los trámites activos con filtros de asignación |
| Finalizados | `Cerrado` | Todos los trámites en estatus terminal |
| Usuarios | `core.User` | Gestión completa de usuarios |
| Catálogos | Varios | TramiteCatalogo, TramiteEstatus, etc. |

Además, tiene permisos completos (`add`, `change`, `delete`, `view`) sobre las apps `auth`, `core` y `tramites`.

### Coordinador

Ve las secciones de coordinación:

| Sección | Modelo proxy | Contenido |
|---------|-------------|-----------|
| Trámites en curso | `Tramite` | Todos los trámites activos. Puede asignar/reasignar/liberar. |
| Finalizados | `Cerrado` | Todos los trámites cerrados (por recoger, rechazados, cancelados). |

No ve: gestión de usuarios, catálogos, ni el buzón personal.

### Analista

Ve las secciones operativas:

| Sección | Modelo proxy | Contenido |
|---------|-------------|-----------|
| Mis trámites | `Buzon` | Solo trámites asignados a él (`asignado_user_id = user.id`) que estén en proceso |
| Disponibles | `Disponible` | Trámites sin asignar y activos. Puede autoasignarse ("Tomar Asignación"). |

No ve: trámites de otros analistas, finalizados, gestión de usuarios, catálogos.

> **Detalle técnico:** La visibilidad del sidebar se controla con los permisos `acceso_analista` y `acceso_coordinador` configurados en el archivo `settings.py` bajo `JAZZMIN_SETTINGS['custom_links']`. Cada link verifica si el usuario tiene el permiso correspondiente.

______________________________________________________________________

## Paso 5 — Propiedades del modelo User

El modelo personalizado `core.User` (definido en `core/models.py`) extiende `AbstractUser` y expone tres propiedades de conveniencia que delegan a la pertenencia al grupo:

```python
# Equivalente a: BackOfficeRole.ADMINISTRADOR in user.roles
user.is_administrador  # → bool

# Equivalente a: BackOfficeRole.COORDINADOR in user.roles
user.is_coordinador    # → bool

# Equivalente a: BackOfficeRole.ANALISTA in user.roles
user.is_analista       # → bool
```

### ¿Cómo funcionan internamente?

1. **`CacheUserRolesMiddleware`** (`core/middleware.py`) se ejecuta en cada request y pobla `request.user.roles` con un `set[str]` de nombres de grupos en una sola consulta.

1. Las propiedades usan `user._get_roles()`, que devuelve el set cacheado si existe, o consulta la base de datos como fallback:

   ```python
   def _get_roles(self) -> set[str]:
       roles = getattr(self, 'roles', None)
       if roles is not None:
           return roles  # cacheado por el middleware
       return set(self.groups.values_list('name', flat=True))  # fallback a DB
   ```

1. Para usuarios anónimos, el middleware asigna `user.roles = set()`, por lo que todas las propiedades devuelven `False` de forma segura.

### Uso en permisos de trámite

El modelo `Tramite` define métodos de permiso a nivel de objeto que usan estas propiedades:

| Método | Administrador | Coordinador | Analista |
|--------|:---:|:---:|:---:|
| `can_view(user)` | Siempre | Siempre | Solo si está asignado |
| `can_download(user)` | Siempre | Siempre | Asignados + disponibles activos |
| `can_assign(user)` | Sí | Sí | No |
| `can_release(user)` | Sí | Sí | No |
| `can_execute_action(user)` | Siempre | Siempre | Solo si está asignado |

______________________________________________________________________

## Paso 6 — Modelos proxy y vistas de trámite

El sistema usa modelos proxy (subclases de `Tramite` en `tramites/models/tramite.py`) para ofrecer vistas diferentes según el rol. Cada proxy tiene su propio `ModelAdmin` con `allowed_roles` que controla el acceso:

| Proxy | Admin | `allowed_roles` | QuerySet | Acciones |
|-------|-------|-----------------|----------|----------|
| `Buzon` | `BuzonTramitesAdmin` | analista, coordinador, administrador | Trámites en proceso asignados al usuario | Modificar asignación |
| `Disponible` | `TramitesDisponiblesAdmin` | analista, coordinador, administrador | Trámites en proceso sin asignar | Tomar asignación |
| `Tramite` | `TramitesAdmin` | coordinador, administrador | Todos los trámites en proceso | Modificar asignación, liberar rápido |
| `Cerrado` | `TramitesCerradosAdmin` | coordinador, administrador | Todos los trámites finalizados | Solo lectura |

El acceso está controlado por `RoleCheckMixin` (en `tramites/admin.py`), que valida `allowed_roles` contra las propiedades del usuario:

```python
class RoleCheckMixin:
    allowed_roles: tuple[str, ...] = ()

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return False  # nunca se edita directamente
        user = request.user
        if user.is_superuser:
            return True
        return any(getattr(user, role, False) for role in self.allowed_roles)
```

> **Seguridad:** Solo se aceptan nombres de propiedades válidos (definidos en `VALID_ROLE_PROPERTIES` en `core/rbac/constants.py`). Si un admin declara un `allowed_role` inválido, se lanza `ImproperlyConfigured` al importar.

______________________________________________________________________

## Troubleshooting

### El usuario no puede iniciar sesión en `/admin/`

**Causas posibles:**

- El usuario no tiene un rol asignado (no pertenece a ningún grupo de `BackOfficeRole`).
- El campo `is_staff` es `False`.

**Solución:**

1. Verifica que el usuario tenga un rol en la lista de usuarios (columna "Rol").
1. Si muestra "Sin rol", edítalo y asígnale un rol.
1. Ejecuta `python manage.py setup_roles` para reparar `is_staff` automáticamente.

______________________________________________________________________

### El usuario no ve una sección del sidebar

| Sección ausente | Permiso requerido | Roles que lo tienen |
|----------------|-------------------|---------------------|
| Mis trámites / Disponibles | `acceso_analista` | Analista, Administrador |
| Trámites en curso / Finalizados | `acceso_coordinador` | Coordinador, Administrador |

**Solución:**

1. Edita el usuario y verifica que su rol sea el correcto.

1. Ejecuta `python manage.py setup_roles` para re-sincronizar permisos.

1. Si el problema persiste, verifica en la base de datos que el grupo tenga el permiso:

   ```bash
   python manage.py shell -c "
   from django.contrib.auth.models import Group, Permission
   g = Group.objects.get(name='Analista')
   print(list(g.permissions.values_list('codename', flat=True)))
   "
   ```

   Debe incluir `acceso_analista`.

______________________________________________________________________

### Un analista ve trámites que no son suyos

**Causa:** El usuario también pertenece al grupo `Coordinador` o `Administrador`.

**Solución:** Un usuario solo debe pertenecer a un grupo de rol a la vez. Edita el usuario y asígnale exclusivamente el rol `Analista`. El sistema elimina automáticamente otros grupos de rol al guardar.

______________________________________________________________________

### Los grupos no existen después de desplegar

**Causa:** Las migraciones no se ejecutaron o la señal `post_migrate` falló silenciosamente.

**Solución:** Ejecuta manualmente:

```bash
python manage.py setup_roles
```

Verifica la salida para confirmar que los tres grupos se crearon correctamente.

______________________________________________________________________

### Error: "Usuario no encontrado" al asignar rol masivamente

**Causa:** Los IDs de usuario almacenados en la sesión expiraron o son inválidos.

**Solución:** Regresa a la lista de usuarios, selecciona los usuarios nuevamente y ejecuta la acción "Asignar rol".

______________________________________________________________________

## Referencias

| Archivo | Descripción |
|---------|-------------|
| `core/rbac/constants.py` | Enum `BackOfficeRole`, permisos personalizados, mapeo de permisos por rol |
| `core/rbac/__init__.py` | Funciones `setup_all_roles()`, `setup_administrador()`, etc. |
| `core/management/commands/setup_roles.py` | Comando de management que crea grupos y repara `is_staff` |
| `core/signals.py` | Señal `post_migrate` que ejecuta `setup_roles` automáticamente |
| `core/middleware.py` | `CacheUserRolesMiddleware` que cachea roles por request |
| `core/models.py` | Modelo `User` con propiedades `is_administrador`, `is_coordinador`, `is_analista` |
| `core/admin.py` | `BackofficeUserAdmin` con formulario personalizado y gestión de roles |
| `core/forms.py` | `CustomUserAddForm` y `CustomUserChangeForm` con selector de rol |
| `tramites/models/tramite.py` | Modelos proxy (`Buzon`, `Disponible`, `Cerrado`) y métodos de permiso |
| `tramites/admin.py` | `RoleCheckMixin` y `ModelAdmin` para cada vista de trámite |
| [ADR-013](../02-DECISIONES/013-rbac-tres-roles.md) | Decisión de diseño: sistema RBAC de tres roles |
| [ADR-014](../02-DECISIONES/014-custom-user-workflow-permissions.md) | Custom User Model, permisos a nivel de objeto, workflow |
