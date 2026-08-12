# Custom User Model, Workflow Refactoring y Permission Methods

## Contexto y Planteamiento del Problema

El sistema backoffice acumulaba tres problemas interrelacionados:

1. **Sin Custom User Model**: El proyecto usaba `auth.User` por defecto de Django, lo que impedía agregar properties de rol (`is_administrador`, `is_coordinador`, `is_analista`) directamente en el modelo. Los chequeos de rol estaban dispersos como `BackOfficeRole.COORDINADOR in getattr(user, 'roles', set())` a lo largo de admin, views y templates.

1. **Workflow sin estructura**: Las transiciones de estado del trámite estaban codificadas como condicionales dispersos en cada método (`requerir_documentos`, `en_diligencia`, `finalizar`). Cada método repetía la validación `if self.ultima_actividad_estatus_id != TramiteEstatus.Estatus.EN_REVISION: raise ...`. Esto violaba DRY y hacía difícil agregar nuevas transiciones.

1. **Permisos sin encapsulación**: La autorización de descargas (`_check_download_permission` en `views.py`) duplicaba la lógica de roles que ya existía en admin. El `change_view` del admin no tenía protección IDOR — cualquier usuario staff podía ver cualquier trámite. El template mostraba botones de acción sin validar si el usuario/estatus los permitía.

## Opciones Consideradas

### Para el User Model:

- **A)** `AbstractUser` con properties de rol → los roles se derivan de grupos Django
- **B)** Campos `is_administrador`, `is_coordinador`, `is_analista` como `BooleanField` en la BD
- **C)** Proxy models por rol

### Para el Workflow:

- **A)** Dict `TRANSITIONS` + método `_validate_transition()` centralizado
- **B)** Librería externa (django-fsm, django-viewflow)
- **C)** Tabla de transiciones en BD

### Para los Permisos:

- **A)** Métodos en el modelo `Tramite` (`can_view`, `can_download`, `available_actions`)
- **B)** Service layer separada (`TramitePermissionService`)
- **C)** Mixins de admin con permisos

## Resultado de la Decisión

**User Model — Opción A**: `AbstractUser` con properties que delegan a `_get_roles()` (cache→DB fallback). Sin campos extra en BD, sin migraciones de datos. Las properties son `@property` que leen de `user.roles` (poblado por `CacheUserRolesMiddleware`) con fallback a query de grupos.

**Workflow — Opción A**: Dict `TRANSITIONS: dict[tuple[int, int], bool]` a nivel módulo que mapea `(from_status, to_status) → True`. Cada método de acción (`requerir_documentos`, `en_diligencia`, `finalizar`) delega a `_validate_transition(to_status)`. `_liberar()` es la excepción: solo usa `_assert_activo()` porque liberación es un "reset" que aplica a cualquier estado activo.

**Permisos — Opción A**: Seis métodos en `Tramite`: `can_view()`, `can_download()`, `can_assign()`, `can_release()`, `can_execute_action()`, `available_actions()`. Fat Models: la lógica vive en el modelo, los consumidores (admin, views, template) delegan al modelo.

### Consecuencias

- Bueno, porque los chequeos de rol están centralizados en `User.is_*` y `Tramite.can_*()` — un solo lugar para cambiar
- Bueno, porque el `change_view` ahora tiene protección IDOR via `tramite.can_view(user)`
- Bueno, porque el template renderiza botones condicionalmente según `available_actions`
- Bueno, porque agregar una transición nueva es agregar una línea al dict `TRANSITIONS`
- Malo, porque `_get_roles()` hace fallback a query de BD si `CacheUserRolesMiddleware` no pobló `user.roles` — pero en práctica siempre está poblado
- Malo, porque el modelo `Tramite` creció en complejidad — pero es complejidad necesaria que antes estaba dispersa

## Detalles de Implementación

### Custom User Model (`core/models.py`)

```python
class User(AbstractUser):
    @property
    def is_administrador(self) -> bool:
        return BackOfficeRole.ADMINISTRADOR in self._get_roles()
    # is_coordinador, is_analista similares
```

Configurado con `AUTH_USER_MODEL = 'core.User'` en settings. Migración inicial `core/migrations/0001_custom_user_model.py`.

### TRANSITIONS dict (`tramites/models/tramite.py`)

```python
TRANSITIONS: dict[tuple[int, int], bool] = {
    (PRESENTADO, EN_REVISION): True,       # asignar
    (EN_REVISION, EN_REVISION): True,       # reasignar
    (EN_REVISION, PRESENTADO): True,        # liberar
    (EN_REVISION, REQUERIMIENTO): True,     # requerir
    (EN_REVISION, EN_DILIGENCIA): True,     # diligencia
    (EN_REVISION, FINALIZADO): True,        # finalizar
    (REQUERIMIENTO, FINALIZADO): True,      # finalizar
    (EN_DILIGENCIA, FINALIZADO): True,      # finalizar
}
```

### Permission Methods en Tramite

| Método | Retorna | Lógica |
|--------|---------|--------|
| `can_view(user)` | `bool` | Admin/Coord: siempre. Analista: solo si asignado |
| `can_download(user)` | `bool` | Admin/Coord: siempre. Analista: asignado o disponible activo |
| `can_assign(user)` | `bool` | Coord/Admin |
| `can_release(user)` | `bool` | Coord/Admin |
| `can_execute_action(user)` | `bool` | Admin/Coord: siempre. Analista: solo si asignado |
| `available_actions(user)` | `list[str]` | Dependiente de estatus + rol |

### Consumidores actualizados

- `tramites/admin.py`: `change_view` usa `can_view()` (IDOR) y `available_actions()` (POST + template)
- `tramites/views.py`: `download_requisito_pdf` usa `can_download()` — eliminada `_check_download_permission`
- `templates/admin/tramite_detail.html`: botones condicionales con `{% if 'accion' in available_actions %}`
- `tramites/admin.py`: `acciones_disponibles` y `liberar_rapido` usan `can_release()`

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `core/models.py` | CREADO — Custom User model |
| `core/admin.py` | CREADO — BackofficeUserAdmin (reemplaza core/admin/ directory) |
| `core/views.py` | MODIFICADO — `asignar_rol` con is_staff consistente con save_model |
| `core/rbac/constants.py` | MODIFICADO — Permisos `acceso_analista`, `acceso_coordinador` + `core` en ADMINISTRADOR_APPS |
| `core/management/commands/setup_roles.py` | MODIFICADO — Auto-reparación de is_staff inconsistencies |
| `sanfelipe/settings/jazzmin.py` | MODIFICADO — `core.view_user` en vez de `auth.view_user` |
| `core/migrations/0001_custom_user_model.py` | CREADO — migración inicial |
| `tramites/models/tramite.py` | TRANSITIONS dict + \_validate_transition + permission methods |
| `tramites/admin.py` | IDOR protection + acción validation + elimina BackOfficeRole import |
| `tramites/views.py` | Elimina `_check_download_permission`, usa `tramite.can_download()` |
| `templates/admin/tramite_detail.html` | Botones de acción condicionales |
| `tests/tramites/test_models.py` | Actualizado para TRANSITIONS + renamed methods |
| `tests/tramites/test_sftp.py` | Refactorizado para usar `Tramite.can_download()` |

## Archivos Eliminados

| Archivo | Razón |
|---------|-------|
| `core/admin/__init__.py` | Aplanado a `core/admin.py` |
| `core/admin/base.py` | Eliminado — `BackofficeAdminSite` ya no se usa |
| `core/admin/mixins.py` | Eliminado — `ActionableReadOnlyMixin` ya no se usa |
| `core/admin/site.py` | Eliminado — `BackofficeAdminSite` ya no se usa |
| `core/admin/user_admin.py` | Movido a `core/admin.py` |
| `tests/core/test_admin.py` | Eliminado — testeaba `BackofficeAdminSite` |
| `tests/core/test_permissions.py` | Eliminado — testeaba `RoleBasedAccessMixin` |

______________________________________________________________________

Formato basado en [MADR](https://adr.github.io/madr/)
