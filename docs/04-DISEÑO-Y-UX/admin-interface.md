# Interfaz de Administración (Django Admin)

## Visión General

El Backoffice de Trámites **no utiliza vistas personalizadas** para las operaciones CRUD de trámites. Django Admin — extendido con el tema **Jazzmin 3.0.3** — es la única interfaz de usuario del sistema. Toda la gestión de trámites, asignaciones y usuarios se realiza a través de las vistas estándar de `ModelAdmin`, templates personalizados y acciones batch.

### Principios de diseño

- **Solo lectura por defecto**: Los trámites se originan en un sistema externo; el backoffice no crea ni elimina registros, solo gestiona el flujo de trabajo (asignación, revisión, cancelación).
- **Modelos proxy**: Se usan modelos proxy (`Buzon`, `Disponible`, `EnDiligencia`, `Cerrado`) sobre la vista `v_tramites_unificado` para crear vistas de admin separadas con querysets filtrados.
- **Permisos basados en roles**: `RoleCheckMixin` restringe cada vista de admin a los roles que deben acceder.
- **Templates personalizados**: Las vistas de detalle (`change_view`) usan templates custom que muestran timeline, documentos SFTP y acciones de workflow.

______________________________________________________________________

## Clases Admin Registradas

### Trámites

| Clase Admin | Modelo Proxy | Roles Permitidos | Propósito | Queryset |
|---|---|---|---|---|
| `BuzonTramitesAdmin` | `Buzon` | Analista, Coordinador, Administrador | Trámites asignados al usuario actual (excluye 205) | `.en_proceso().excluyendo_diligencia().asignados_a(user.id)` |
| `TramitesDisponiblesAdmin` | `Disponible` | Analista, Coordinador, Administrador | Trámites sin asignar disponibles para tomar (excluye 205) | `.en_proceso().excluyendo_diligencia().sin_asignar()` |
| `TramitesAdmin` | `Tramite` | Coordinador, Administrador | Todos los trámites activos en curso | `.en_proceso()` |
| `TramitesEnDiligenciaAdmin` | `EnDiligencia` | Coordinador, Administrador | Trámites en diligencia (205) para gestión de cancelación | `.en_diligencia()` |
| `TramitesCerradosAdmin` | `Cerrado` | Coordinador, Administrador | Trámites finalizados (solo lectura) | `.finalizados()` |

### Usuarios

| Clase Admin | Modelo | Roles Permitidos | Propósito |
|---|---|---|---|
| `BackofficeUserAdmin` | `User` | Administrador (via permiso `core.view_user`) | Gestión de usuarios con asignación de roles |

______________________________________________________________________

## TramiteBaseAdmin

Clase base abstracta de la que heredan las cinco vistas de admin de trámites. Define la configuración compartida de columnas, filtros, acciones y la vista de detalle.

**Archivo:** `tramites/admin.py`

### Configuración general

| Propiedad | Valor |
|---|---|
| `save_on_top` | `True` |
| `list_per_page` | `25` |
| `list_max_show_all` | `100` |
| `list_editable` | `()` (vacío) |
| `has_add_permission` | `False` — no se crean trámites |
| `has_delete_permission` | `False` — no se eliminan trámites |
| `has_change_permission` | `NotImplementedError` — debe sobrescribirse |
| `ordering` | `('-urgente', '-creado', '-actualizado')` |
| `Media.js` | `('admin/js/quick_actions.js',)` |

### list_display

| Columna | Método | Descripción |
|---|---|---|
| `folio` | Campo del modelo | Folio del trámite (enlace a detalle) |
| `tramite_nombre_display` | `@admin.display(ordering='tramite_nombre')` | Tipo de trámite (campo denormalizado) |
| `estatus_display` | `@admin.display(ordering='ultima_actividad_estatus_id')` | Badge de estatus (via `render_status_badge`) |
| `urgencia_display` | `@admin.display(ordering='urgente')` | Badge "Urgente" (danger) / "Normal" (success) |
| `asignado_display` | `@admin.display(ordering='asignado_username')` | Nombre del analista o "📦 Sin Asignar" |
| `creado_display` | `@admin.display(ordering='-creado')` | Timestamp formateado `YYYY-MM-DD HH:MM:SS` |
| `actualizado_display` | `@admin.display(ordering='-actualizado')` | Timestamp formateado `YYYY-MM-DD HH:MM:SS` |
| `acciones_disponibles` | `@admin.display` | Botones de acción rápida por fila |

### list_filter (base)

| Filtro | Tipo | Descripción |
|---|---|---|
| `TramiteTipoFilter` | `SimpleListFilter` personalizado | Filtra por tipo de trámite (consulta `TramiteCatalogo`) |
| `TramiteEstatusFilter` | `SimpleListFilter` personalizado | Filtra por estatus de la última actividad |
| `TramiteUrgenteFilter` | `SimpleListFilter` personalizado | Urgente / Normal |
| `creado` | Filtro de fecha nativo | Rango de fecha de creación |
| `actualizado` | Filtro de fecha nativo | Rango de fecha de actualización |

Filtros adicionales por admin:

| Clase Admin | Filtro adicional |
|---|---|
| `TramitesAdmin` | `AsignadoUserFilter` — filtro por analista asignado (incluye "Sin Asignar", "Asignados a mí") |
| `TramitesCerradosAdmin` | `AsignadoUserFilter` — mismo filtro por analista |
| `BuzonTramitesAdmin` | Sin filtro de analista (columna `asignado` oculta) |
| `TramitesDisponiblesAdmin` | Sin filtro de analista (todos sin asignar) |

### Personalizaciones por admin

#### BuzonTramitesAdmin (`Buzon`)

- Oculta la columna `asignado_display` del `list_display` (todos son del usuario actual).
- Queryset: solo trámites activos asignados al usuario en sesión, excluyendo los que están en diligencia (205).

#### TramitesDisponiblesAdmin (`Disponible`)

- Oculta la columna `asignado_display` del `list_display` (todos sin asignar).
- Queryset: solo trámites activos sin asignar, excluyendo los que están en diligencia (205).
- Acción batch única: `tomar_asignacion`.
- `acciones_disponibles`: botón "📌 Tomar" por fila.
- `get_actions()` filtra para solo exponer `tomar_asignacion`.

#### TramitesAdmin (`Tramite`)

- Incluye `AsignadoUserFilter` como primer filtro.
- `acciones_disponibles`: botón "Modificar Asignación" por fila.

#### TramitesCerradosAdmin (`Cerrado`)

- Incluye `AsignadoUserFilter` como primer filtro.
- `acciones_disponibles`: botón "Modificar Asignación" por fila.
- Queryset: solo trámites finalizados (estatus ≥ 300).

______________________________________________________________________

## RoleCheckMixin

**Archivo:** `tramites/admin.py`

Mixin que restringe el acceso a vistas de admin basándose en las propiedades de rol del modelo `User`.

### Cómo funciona

1. La subclase define `allowed_roles` como una tupla de nombres de propiedades del modelo User (e.g. `('is_analista', 'is_coordinador')`).
1. Al importar, `__init_subclass__` valida que todos los roles estén en `VALID_ROLE_PROPERTIES` (`core/rbac/constants.py`). Si un rol es inválido, lanza `ImproperlyConfigured`.
1. `has_change_permission()` solo permite acceso cuando `obj is None` (vista de listado/acciones) y el usuario tiene al menos uno de los roles permitidos. Los superusuarios siempre tienen acceso.

### Propiedades de rol válidas

Definidas en `core/rbac/constants.py`:

| Propiedad | Rol |
|---|---|
| `is_administrador` | Administrador |
| `is_coordinador` | Coordinador |
| `is_analista` | Analista |

### Restricción de permisos

- `obj is not None` → **siempre** retorna `False` (no se permite editar objetos individuales).
- `obj is None` (changelist) → verifica roles.
- `request.user.is_superuser` → bypass total.

______________________________________________________________________

## Acciones de Admin (Batch Actions)

### Acciones sobre trámites

| Acción | Admin | Descripción | Template Intermedio |
|---|---|---|---|
| `modificar_asignacion` | Base, TramitesAdmin, CerradosAdmin | Asigna, reasigna o libera trámites seleccionados | `admin/modificar_asignacion.html` |
| `tomar_asignacion` | Disponibles | Autoasigna trámites al usuario actual (delega a `modificar_asignacion` con overrides) | Ninguno (ejecución directa) |
| `liberar_rapido` | Base (quick action) | Libera un trámite individual desde botón de fila | Ninguno (ejecución directa) |

### `modificar_asignacion` — flujo detallado

1. **Primera visita** (sin `analista` en POST): renderiza `admin/modificar_asignacion.html` con la lista de analistas y los trámites seleccionados.
1. **Envío del formulario**:
   - `analista_id == 'ninguno'` → **Liberar**: llama `tramite.asignar(analista=None, ...)` para cada trámite.
   - `analista_id != 'ninguno'` → **Asignar/Reasignar**: llama `tramite.asignar(analista=user, ...)` para cada trámite.
1. Cada error se captura individualmente; los éxitos y errores se reportan por separado via `messages`.

### `tomar_asignacion` — autoasignación

Delega a `modificar_asignacion` con parámetros explícitos:

```python
analista_override = str(request.user.id)
observacion_override = 'Autoasignado'
```

### `liberar_rapido` — liberación individual

Verifica `tramite.can_release(user)` antes de liberar. Solo disponible para Coordinadores/Admin.

### Acciones sobre usuarios (`BackofficeUserAdmin`)

| Acción | Descripción |
|---|---|
| `asignar_rol` | Redirige al template intermedio `admin/auth/user/asignar_rol.html` para seleccionar rol |
| `marcar_como_activo` | Marca usuarios seleccionados como `is_active=True` (excluye superusers si el usuario no es superuser) |
| `marcar_como_inactivo` | Marca usuarios seleccionados como `is_active=False` (soft delete) |

La acción `delete_selected` se elimina de la lista de acciones. `delete_model` y `delete_queryset` implementan soft delete (`is_active=False`).

______________________________________________________________________

## Templates Personalizados

### `templates/admin/tramite_detail.html`

Vista de detalle de trámite (reemplaza el `change_form` estándar).

**Layout:** Dos columnas (9-3).

**Columna principal (col-lg-9):**

| Sección | Contenido |
|---|---|
| Información del Trámite | Folio, tipo, categoría, tipo de cobro, clave catastral, propietario, urgencia |
| Estatus Actual | Estatus (badge), responsable, descripción, observaciones, asignado, fechas |
| Solicitante | Nombre, teléfono, correo, comentario |
| Perito (condicional) | Nombre del perito (solo si existe) |
| Historial del Trámite | Timeline vertical con actividades, documentos adjuntos (requisitos y archivos de actividad) |

**Columna lateral (col-lg-3):**

- Botón "Regresar a Listado"
- Panel "Acciones Disponibles" (condicional, basado en `available_actions`):
  - **Requerir Documentos** (btn-warning) — POST directo
  - **Enviar a Firma** (btn-info) — POST directo
  - **Cancelar Trámite** (btn-danger) — enlace a vista intermedia
- Campo de observación (para requerir y firma)

**Datos contextuales inyectados por `change_view`:**

| Variable | Descripción |
|---|---|
| `tramite` | Instancia del trámite |
| `timeline_entries` | Lista de entradas del timeline (actividades + archivos) |
| `form` | `TramiteDetailForm` con campo `observacion` |
| `available_actions` | Lista de acciones permitidas (requerir, firma, cancelar) |
| `has_change_permission` | Permiso de cambio (siempre False para objetos) |
| `has_view_permission` | Permiso de visualización |

**Archivos SFTP cargados:** `SFTPService._list_all_files_for_tramite()`, `SFTPService.fetch_requisito_files()`, `SFTPService.fetch_actividad_files()`.

**JavaScript:** `admin/js/tramite_actions.js` (maneja envío del formulario de acciones).

### `templates/admin/tramite_cancelar.html`

Vista intermedia para cancelar un trámite (accedida via URL `tramites:cancelar-tramite`).

**Contenido:**

- Header con información del trámite (folio, tipo, solicitante, estatus actual)
- Alerta de advertencia: "Esta acción es irreversible"
- Formulario:
  - Selector de `estatus_cierre` (Por Recoger, Rechazado, Cancelado)
  - Campo `observacion` obligatorio (motivo de cancelación)
  - Botones: Cancelar / Confirmar Cancelación

### `templates/admin/modificar_asignacion.html`

Vista intermedia para la acción batch `modificar_asignacion`.

**Layout:** Dos columnas (6-6).

- **Izquierda:** Lista de trámites seleccionados (folio, urgencia, estado de asignación, tipo).
- **Derecha:** Formulario con selector de analista (dropdown con todos los usuarios del grupo "Analista" + opción "Ninguno (Liberar)") y campo de observación opcional.

### `templates/admin/auth/user/asignar_rol.html`

Vista intermedia para la acción batch `asignar_rol` sobre usuarios.

**Contenido:**

- Tabla de usuarios seleccionados (nombre, email)
- Formulario con radio buttons para seleccionar rol (`Administrador`, `Coordinador`, `Analista`)
- Botones: Asignar Rol / Cancelar

### `templates/admin/includes/dashboard_cards.html`

Componente reutilizable para el dashboard del índice de admin.

**Contenido:** Grid de tarjetas (col-md-6 col-lg-4) con:

- Ícono FontAwesome e indicador de color
- Contador de trámites
- Título y descripción
- Enlace "Ver listado"

______________________________________________________________________

## BackofficeUserAdmin (Gestión de Usuarios)

**Archivo:** `core/admin.py`

Configuración del admin para el modelo `User` personalizado.

### list_display

| Columna | Método | Descripción |
|---|---|---|
| `usuario` | Propiedad | Nombre completo o username |
| `rol` | Propiedad | Badge de rol (Superusuario, Administrador, Coordinador, Analista, Sin rol) |
| `usuario_estatus` | Propiedad | Badge Activo/Inactivo |
| `acciones` | Propiedad | Botón "🔑 Cambiar contraseña" (oculto para superusers si el usuario actual no es superuser) |

### fieldsets

```python
fieldsets = (
    (None, {
        'fields': (
            'username',
            ('first_name', 'last_name'),  #misma fila
            'password',
            'email',
            'role',
        )
    }),
)
```

### add_fieldsets

```python
add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': (
            'username',
            ('first_name', 'last_name'),
            'email',
            'password1',
            'password2',
            'role',
        ),
    }),
)
```

### Protección de superusuarios

| Método | Regla |
|---|---|
| `has_change_permission` | No-superusers no pueden editar superusers |
| `has_delete_permission` | No-superusers no pueden eliminar superusers |
| `get_readonly_fields` | Todos los campos readonly al ver un superuser sin serlo |
| `user_change_password` | No-superusers no pueden cambiar contraseña de superusers |

### save_model

Gestión atómica de usuarios:

1. Establece `is_staff=True` si el rol es válido, `False` si no.
1. Nuevos usuarios siempre `is_active=True`.
1. Dentro de `transaction.atomic()`: remueve grupos de roles anteriores y agrega el nuevo grupo.
1. Validación de defensa en profundidad: no-superusers no pueden modificar superusers.

### Formularios

| Contexto | Formulario |
|---|---|
| Crear usuario (`obj is None`) | `CustomUserAddForm` |
| Editar usuario (`obj is not None`) | `CustomUserChangeForm` |

______________________________________________________________________

## Configuración Jazzmin

**Archivo:** `sanfelipe/settings/jazzmin.py`

La configuración de Jazzmin se genera dinámicamente via `configure_jazzmin(tenancy_settings)` para permitir branding por departamento.

### Parámetros de branding (desde tenancy)

| Parámetro | Descripción |
|---|---|
| `site_title` | Título de la ventana del navegador |
| `site_header` | Título en pantalla de login |
| `site_brand` | Título en la marca (sidebar) |
| `welcome_sign` | Texto de bienvenida en login |
| `copyright` | Texto de copyright en footer |

### Assets estáticos

| Asset | Ruta |
|---|---|
| Logo sidebar (dark) | `logo_dark.svg` |
| Logo login | `logo.svg` |
| CSS personalizado | `admin/css/backoffice.css` |

### Aplicaciones ocultas

```python
'hide_apps': ['contenttypes', 'sessions', 'admin', 'tramites', 'core']
```

Todas las apps de trámites se ocultan del sidebar por defecto; el acceso se controla exclusivamente via `custom_links` con permisos.

### Modelos ocultos

```python
'hide_models': ['auth.group']
```

### Enlaces personalizados del sidebar

Grupo **"Administración"** (requiere `core.view_user`):

| Nombre | URL | Ícono | Permiso |
|---|---|---|---|
| Usuarios | `admin:core_user_changelist` | `fas fa-users` | `core.view_user` |

Grupo **"Trámites"**:

| Nombre | URL | Ícono | Permiso | Roles que lo ven |
|---|---|---|---|---|
| Mis trámites | `admin:tramites_buzon_changelist` | `fas fa-user` | `tramites.acceso_analista` | Analista, Administrador |
| Disponibles | `admin:tramites_disponible_changelist` | `fas fa-inbox` | `tramites.acceso_analista` | Analista, Administrador |
| Trámites en curso | `admin:tramites_tramite_changelist` | `fas fa-inbox` | `tramites.acceso_coordinador` | Coordinador, Administrador |
| En diligencia | `admin:tramites_endiligencia_changelist` | `fas fa-hard-hat` | `tramites.acceso_coordinador` | Coordinador, Administrador |
| Trámites finalizados | `admin:tramites_cerrado_changelist` | `fas fa-flag-checkered` | `tramites.acceso_coordinador` | Coordinador, Administrador |

### UI Tweaks

| Parámetro | Valor |
|---|---|
| `theme` | `united` |
| `default_theme_mode` | `light` |
| `footer_small_text` | `True` |
| `brand_small_text` | `True` |
| `sidebar_nav_flat_style` | `True` |
| `brand_colour` | `green` |
| `show_sidebar` | `True` |
| `navigation_expanded` | `True` |
| `related_modal_active` | `True` |

______________________________________________________________________

## CSS Personalizado

**Archivo:** `static/admin/css/backoffice.css`

### Design System — Variables CSS

El archivo define un sistema de diseño completo usando CSS custom properties (`:root` y `[data-bs-theme="light"]` / `[data-bs-theme="dark"]`).

#### Paleta de colores principal

| Variable | Light | Uso |
|---|---|---|
| `--bs-primary` | `#9d2638` (granate) | Color primario institucional |
| `--bs-secondary` | `#1a1a1a` (negro suave) | Color secundario |
| `--bs-success` | `#10b981` (verde) | Estados positivos |
| `--bs-info` | `#3b82f6` (azul) | Información / estatus finalizado |
| `--bs-warning` | `#f59e0b` (ámbar) | Advertencias |
| `--bs-danger` | `#ef4444` (rojo) | Errores / urgencia |
| `--bs-link-color` | `#9d2638` | Enlaces |

#### Tipografía

Familia principal: **Ubuntu**, con fallbacks a system fonts.

### Componentes badge

#### Badges estándar (pastel + pill)

Estilo: fondo tintado suave (`bg-subtle`) + texto oscuro (`text-emphasis`) + `border-radius: 50rem`.

| Clase | Texto | Fondo | Borde |
|---|---|---|---|
| `.badge-primary` | `#3f0f16` | `#ebd4d7` | `#2f0b11` |
| `.badge-secondary` | `#0a0a0a` | `#d1d1d1` | `#080808` |
| `.badge-success` | `#064a34` | `#cff1e6` | `#053827` |
| `.badge-info` | `#183462` | `#d8e6fd` | `#12274a` |
| `.badge-warning` | `#623f04` | `#fdecce` | `#4a2f03` |
| `.badge-danger` | `#601b1b` | `#fcdada` | `#481414` |

#### Badges de estatus de trámite

Gradientes de intensidad dentro de cada familia:

| Familia | Rango de IDs | Clase base | Sub-variantes |
|---|---|---|---|
| Inicio | 100–199 | `.badge-inicio` | `.badge-inicio-{id}` (gris degradado) |
| Proceso | 200–299 | `.badge-proceso` | `.badge-proceso-{id}` (verde degradado) |
| Finalizado | 300–399 | `.badge-finalizado` | `.badge-finalizado-{id}` (azul degradado) |
| Otro | resto | `.badge-otro` | — |

#### Badges de estado de usuario

| Clase | Uso |
|---|---|
| `.badge-activo` | Usuario activo (verde pastel) |
| `.badge-inactivo` | Usuario inactivo (gris pastel) |

### Sidebar

Override del fondo del sidebar Jazzmin (`#jazzy-sidebar`) al color primario oscuro (`#3f0f16`) para tema light.

### Botones

Sobrescritura completa de variables `--bs-btn-*` para `.btn-primary`, `.btn-secondary`, `.btn-success`, `.btn-info`, `.btn-warning`, `.btn-danger`, `.btn-light`, `.btn-dark` y todas sus variantes `outline-*`. Valores calculados con `shade()`/`tint()` para cumplir WCAG AA.

### Timeline (Historial del Trámite)

Componente CSS puro para el historial de actividades:

- Línea vertical con `border-left` + dots circulares (`::before`)
- Color de dot por familia de estatus: `inicio` (gris), `proceso` (verde), `finalizado` (azul)
- Hover: dot escala 1.25x + borde cambia a primario
- Primer item: dot sólido primario
- Archivos adjuntos: panel con fondo `tertiary-bg` y bordes
- Panel scrollable: `.scroll-panel` con `max-height: 400px`

### Páginas de error

Layout centrado minimalista para 403, CSRF, 404, 500 con código grande, ícono FontAwesome, título, mensaje y botón de acción.

### Folio Link

Efecto hover en los enlaces de folio: ícono FontAwesome de flecha (`\f061`) aparece con transición de opacidad y margen.

### Quick Actions

Clase `.quick-action` con `margin-right: 4px` para espaciado entre botones.

______________________________________________________________________

## URLs Personalizadas de Admin

**Archivo:** `tramites/urls.py`

Las URLs de trámites se montan bajo el prefijo `admin/tramites/` via `get_urls()` en las clases admin o como rutas independientes:

| URL | Nombre | Vista | Descripción |
|---|---|---|---|
| `tramite/<int:pk>/cancelar/` | `tramites:cancelar-tramite` | `views.cancelar_tramite_view` | Vista intermedia para cancelar trámite |
| `tramite/<int:pk>/download/<str:filename>/` | `tramites:download-pdf` | `views.download_pdf` | Descarga de documentos PDF desde SFTP |
| `sin_asignar/` | `tramites:sin-asignar` | `RedirectView` → changelist con filtro | Redirect legacy |
| `<id>/password/` | `core_user_password_change` | `BackofficeUserAdmin.user_change_password` | Cambio de contraseña (registrada via `get_urls()`) |

______________________________________________________________________

## Funciones Auxiliares de Renderizado

**Archivo:** `core/admin_utils.py`

| Función | Parámetros | Retorna | Uso |
|---|---|---|---|
| `render_badge(text, badge_class)` | Texto, clase CSS | `<span class="badge ...">texto</span>` | Badge genérico |
| `render_status_badge(estatus_id, estatus_text)` | ID de estatus, texto | Badge con clase específica por ID o familia | Estatus de trámite |
| `render_activo_badge(is_activo)` | Booleano | Badge "Activo" (verde) o "Inactivo" (gris) | Estado de usuario |
| `render_quick_action(label, attrs, target)` | Etiqueta, data attrs, URL | `<button>` o `<a>` con estilo `btn-outline-primary` | Acciones rápidas por fila |
