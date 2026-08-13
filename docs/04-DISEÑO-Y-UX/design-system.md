# Design System — Backoffice de Trámites

> Documentación de referencia del sistema de diseño visual y de componentes del Backoffice.
> Incluye paleta de colores, tipografía, modo oscuro, componentes reutilizables y convenciones CSS.

______________________________________________________________________

## Stack de UI

El Backoffice se construye sobre el ecosistema **Jazzmin**, que integra múltiples capas:

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| Framework CSS | **Bootstrap 5** (vía Jazzmin) | Grid, utilidades, componentes base |
| Tema base | **Bootswatch "united"** | Variables Bootstrap con fuente Ubuntu |
| Layout | **AdminLTE 3** | Sidebar, navbar, cards, widgets de dashboard |
| Iconos | **Font Awesome 5** | Íconos vectoriales (prefijo `fas`) |
| JS — Framework | **jQuery** | Incluido por Django Admin |
| JS — Componentes | **Bootstrap JS** | Dropdowns, modales, collapse |
| JS — Layout | **AdminLTE JS** | Control de sidebar, push menu |
| CSS personalizado | `static/admin/css/backoffice.css` | Design tokens, badges, timeline, overrides |
| JS personalizado | `static/admin/js/*.js` | Quick actions, tramite actions (event delegation) |

### Archivos clave del design system

| Archivo | Rol |
|---------|-----|
| `static/admin/css/backoffice.css` | CSS custom properties (light/dark), badges, buttons, timeline, error pages |
| `sanfelipe/settings/jazzmin.py` | Configuración Jazzmin: tema, sidebar, links, branding dinámico |
| `tramites/constants.py` | Mapeo de estatus → grupo → clase CSS de badge |
| `tramites/templatetags/admin_extras.py` | Filtros de template `status_badge_class` y `status_group` |
| `core/admin_utils.py` | Funciones `render_status_badge()`, `render_activo_badge()`, `render_quick_action()` |
| `templates/admin/` | Templates personalizados que extienden Jazzmin |

______________________________________________________________________

## Paleta de Colores

### Colores del tema

| Nombre | Hex | Variable CSS | Uso principal |
|--------|-----|-------------|---------------|
| **Primary (Granate)** | `#9d2638` | `--bs-primary` | Color institucional, enlaces, sidebar, botones principales |
| **Secondary (Negro suave)** | `#1a1a1a` | `--bs-secondary` | Botones secundarios, textos de énfasis máximo |
| **Accent (Ámbar)** | `#f59e0b` | `--bs-warning` / `--bs-orange` | Advertencias, icono de toggle de tema |
| **Success (Verde)** | `#10b981` | `--bs-success` | Estados positivos, badges "Activo", estatus Proceso |
| **Info (Azul)** | `#3b82f6` | `--bs-info` | Información, estatus Finalizado, badges info |
| **Danger (Rojo)** | `#ef4444` | `--bs-danger` | Errores, urgencia, botones destructivos |
| **Light (Gris claro)** | `#e9ecef` | `--bs-light` | Fondos secundarios, botones light |
| **Dark (Negro suave)** | `#1a1a1a` | `--bs-dark` | Mismo valor que secondary |

### Colores de fondo y texto

| Elemento | Light | Variable CSS |
|----------|-------|-------------|
| Fondo del body | `#fff` | `--bs-body-bg` |
| Texto del body | `#1a1a1a` | `--bs-body-color` |
| Fondo del header | `#5a1019` | `--header-bg` (custom prop en `staticfiles/`) |
| Fondo del sidebar | `#3f0f16` | Override directo, `shade(primary, 60%)` |
| Fondo breadcrumbs | `#420b12` | `--breadcrumbs-bg` (custom prop en `staticfiles/`) |
| Color de enlaces | `#9d2638` | `--bs-link-color` |
| Color de enlaces hover | `#7d1e2d` | `--bs-link-hover-color` |

### Escala de grises

| Variable | Hex | Uso |
|----------|-----|-----|
| `--bs-gray-100` | `#f8f9fa` | Fondos terciarios, celdas info-table |
| `--bs-gray-200` | `#e9ecef` | Bordes sutiles |
| `--bs-gray-300` | `#dee2e6` | Bordes por defecto |
| `--bs-gray-500` | `#aea79f` | Dots de timeline "inicio" |
| `--bs-gray-700` | `#495057` | Texto secundario oscuro |
| `--bs-gray-900` | `#212529` | Fondo dark mode |

### Colores semánticos de formulario

| Estado | Color | Variable CSS |
|--------|-------|-------------|
| Válido (light) | `#0c875e` | `--bs-form-valid-color` |
| Inválido (light) | `#d73d3d` | `--bs-form-invalid-color` |
| Válido (dark) | `#70d5b3` | `--bs-form-valid-color` |
| Inválido (dark) | `#f58f8f` | `--bs-form-invalid-color` |

______________________________________________________________________

## Tipografía

### Familia tipográfica

| Uso | Familia | Variable CSS |
|-----|---------|-------------|
| Cuerpo de texto | **Ubuntu**, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif | `--bs-font-sans-serif` |
| Código | SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace | `--bs-font-monospace` |

> La fuente **Ubuntu** proviene del tema Bootswatch "united". Si no está disponible localmente, se usan los fallbacks del sistema.

### Tamaños y pesos

| Elemento | Tamaño | Peso | Contexto |
|----------|--------|------|----------|
| Body base | `1rem` (16px) | `400` | `--bs-body-font-size`, `--bs-body-font-weight` |
| Línea base | `1.5` | — | `--bs-body-line-height` |
| H2 (card headers) | ~`1.25rem` | `600–700` | Títulos de sección en cards |
| H5 (sub-headers) | ~`1.1rem` | `600` | Headers dentro de cards de detalle |
| Badges | `75%` del padre | `600` | `.badge` font-size y font-weight |
| Texto pequeño | `0.875rem` | Normal | `.small`, `.form-text`, `.text-muted` |
| Código de error | `6rem` | `800` | `.error-page .error-code` |

______________________________________________________________________

## Modo Oscuro

### Cómo funciona

El sistema soporta dos modos de tema: **light** (por defecto) y **dark**.

1. **Jazzmin** controla el tema activo mediante el atributo `data-bs-theme` en el elemento `<html>`.
1. La preferencia del usuario se persiste en `localStorage` bajo la clave `jazzmin-theme-mode`.
1. El tema por defecto se configura en `JAZZMIN_UI_TWEAKS["default_theme_mode"]` (valor actual: `"light"`).

### CSS Custom Properties por tema

Las variables CSS se definen en dos bloques en `backoffice.css`:

| Selector | Tema |
|----------|------|
| `:root, [data-bs-theme="light"]` | Tema claro (líneas 1–157) |
| `[data-bs-theme="dark"]` | Tema oscuro (líneas 159–212) |

### Variables que cambian en modo oscuro

| Variable | Light | Dark | Fórmula |
|----------|-------|------|---------|
| `--bs-body-bg` | `#fff` | `#212529` | Bootstrap default |
| `--bs-body-color` | `#1a1a1a` | `#dee2e6` | Bootstrap default |
| `--bs-link-color` | `#9d2638` | `#c47d88` | `tint(primary, 40%)` |
| `--bs-link-hover-color` | `#7d1e2d` | `#ba6774` | `tint(primary, 30%)` |
| `--bs-border-color` | `#dee2e6` | `#495057` | Bootstrap default |
| `--bs-emphasis-color` | `#000` | `#fff` | Inverso |
| `--bs-primary-bg-subtle` | `#ebd4d7` | `#1f080b` | `shade(primary, 85%)` |
| `--bs-success-bg-subtle` | `#cff1e6` | `#03251a` | `shade(success, 85%)` |
| `--bs-danger-bg-subtle` | `#fcdada` | `#300e0e` | `shade(danger, 85%)` |

### Sidebar: forzado a dark

Jazzmin fuerza `data-bs-theme="dark"` y la clase `sidebar-dark-primary` en `#jazzy-sidebar`. El override en `backoffice.css` cambia el fondo a `#3f0f16` (solo en tema light del body):

```css
[data-bs-theme="light"] #jazzy-sidebar,
#jazzy-sidebar.sidebar-dark-primary {
    background-color: #3f0f16 !important;
}
```

### Regla de compatibilidad

> **Todos los colores en CSS personalizado deben usar `var(--bs-*)`** para que funcionen en ambos temas. Nunca hardcodear valores que ya existen como variables Bootstrap.

______________________________________________________________________

## Componentes

### Badges (Estatus de Trámite)

Los badges son **solo lectura** — nunca interactivos. Si se necesita interacción, usar `.btn-sm` o `.quick-action`.

#### Estilo visual

- **Forma**: Pill (`border-radius: 50rem`)
- **Fondo**: Pastel tintado (`--bs-*-bg-subtle`)
- **Texto**: Oscuro (`--bs-*-text-emphasis`) — cumple WCAG AA (ratio >= 4.5:1)
- **Borde**: `1px solid shade(base, 70%)` para contorno visual
- **Peso**: `font-weight: 600`

#### Badges estándar (Bootstrap)

| Clase | Color texto | Color fondo | Borde |
|-------|------------|-------------|-------|
| `.badge-primary` | `#3f0f16` | `#ebd4d7` | `#2f0b11` |
| `.badge-secondary` | `#0a0a0a` | `#d1d1d1` | `#080808` |
| `.badge-success` | `#064a34` | `#cff1e6` | `#053827` |
| `.badge-info` | `#183462` | `#d8e6fd` | `#12274a` |
| `.badge-warning` | `#623f04` | `#fdecce` | `#4a2f03` |
| `.badge-danger` | `#601b1b` | `#fcdada` | `#481414` |
| `.badge-light` | `#495057` | `#fcfcfd` | `#4a4b4b` |
| `.badge-dark` | `#0a0a0a` | `#d1d1d1` | `#080808` |

#### Badges de estatus de trámite

Los estatus de trámite se organizan en **familias** por rango de ID. Cada familia tiene un color base y sub-variantes con gradiente de intensidad (más oscuro = más avanzado el estado).

| Familia | Rango de IDs | Color base | Sub-variantes |
|---------|-------------|------------|---------------|
| **Inicio** (gris) | 100–199 | `.badge-inicio` | `.badge-inicio-101` → `.badge-inicio-103` |
| **Proceso** (verde) | 200–299 | `.badge-proceso` | `.badge-proceso-201` → `.badge-proceso-205` |
| **Finalizado** (azul) | 300–399 | `.badge-finalizado` | `.badge-finalizado-301` → `.badge-finalizado-304` |
| **Otro** (gris) | resto | `.badge-otro` | — |

**Detalle de sub-variantes:**

| Clase CSS | Estatus | Fondo | Estatus nombre |
|-----------|---------|-------|---------------|
| `.badge-inicio-101` | 101 | `#e4e4e4` | BORRADOR |
| `.badge-inicio-102` | 102 | `#cdcdcd` | PENDIENTE_PAGO |
| `.badge-inicio-103` | 103 | `#b6b6b6` | PAGO_EXPIRADO |
| `.badge-proceso-201` | 201 | `#ecf9f5` | PRESENTADO |
| `.badge-proceso-202` | 202 | `#d9f4eb` | EN_REVISION |
| `.badge-proceso-203` | 203 | `#c6eee1` | REQUERIMIENTO |
| `.badge-proceso-204` | 204 | `#b3e9d7` | SUBSANADO |
| `.badge-proceso-205` | 205 | `#9fe3cd` | EN_DILIGENCIA |
| `.badge-finalizado-301` | 301 | `#e7f0fe` | POR_RECOGER |
| `.badge-finalizado-302` | 302 | `#d8e6fd` | RECHAZADO |
| `.badge-finalizado-303` | 303 | `#c8dcfc` | FINALIZADO |
| `.badge-finalizado-304` | 304 | `#b8d2fc` | CANCELADO |

#### Badges de estado de usuario

| Clase | Uso | Color texto | Color fondo |
|-------|-----|------------|-------------|
| `.badge-activo` | Usuario activo | `#064a34` | `#cff1e6` |
| `.badge-inactivo` | Usuario inactivo | `#0a0a0a` | `#d1d1d1` |

#### Lógica de resolución de clase

```python
# tramites/constants.py
get_status_badge_class(estatus_id) → "inicio-{id}" | "proceso-{id}" | "finalizado-{id}" | "otro"
get_status_group(estatus_id)       → "inicio" | "proceso" | "finalizado" | "otro"
```

```django
{# En templates #}
{% load admin_extras %}
<span class="badge badge-{{ tramite.ultima_actividad_estatus_id|status_badge_class }}">
    {{ tramite.ultima_actividad_estatus }}
</span>
```

Función auxiliar en Python (`core/admin_utils.py`):

```python
render_status_badge(estatus_id, estatus_text) → HTML <span class="badge ...">
render_activo_badge(is_activo)               → HTML <span class="badge badge-activo|badge-inactivo">
```

______________________________________________________________________

### Cards

Las cards son el contenedor principal de contenido. Se usan en el dashboard y en las vistas de detalle.

#### Dashboard Cards (`dashboard_cards.html`)

Grid de tarjetas resumen: `col-md-6 col-lg-4` (3 por fila en desktop).

```html
<div class="card tramites-card" style="border-left: 4px solid {{ card.color }};">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <i class="fas {{ card.icono }} fa-3x" style="color: {{ card.color }};"></i>
            <div class="text-end">
                <h2 class="mb-0 fw-bold">{{ card.count }}</h2>
                <small class="text-muted">trámites</small>
            </div>
        </div>
        <h5 class="card-title mb-2">{{ card.titulo }}</h5>
        <p class="card-text text-muted mb-3">{{ card.descripcion }}</p>
        <a href="{{ card.url }}" class="btn w-100" style="background-color: {{ card.color }}; color: white;">
            Ver listado →
        </a>
    </div>
</div>
```

#### Cards de detalle (vistas de trámite, asignación, cancelación)

Estructura estándar para cards de contenido:

```html
<section class="card shadow-sm mb-4">
    <div class="card-header bg-secondary text-white">
        <h5 class="mb-0">
            <i class="fas fa-icon px-2"></i>Título de la Sección
        </h5>
    </div>
    <div class="card-body">
        <!-- Contenido -->
    </div>
</section>
```

Variantes de header usadas:

| Clase del header | Uso |
|------------------|-----|
| `bg-secondary text-white` | Secciones de información (general) |
| `bg-primary text-white` | Panel de acciones disponibles |
| `bg-danger text-white` | Acciones destructivas (cancelar trámite) |

______________________________________________________________________

### Sidebar

La sidebar es controlada por Jazzmin/AdminLTE con personalizaciones en `backoffice.css`.

#### Estructura

- **Brand**: Logo `logo_dark.svg` + nombre del sitio
- **User panel**: Nombre del usuario autenticado
- **Navegación**: Grupos de enlaces con permisos basados en roles

#### Enlaces personalizados (definidos en `jazzmin.py`)

**Grupo "Administración"** (requiere permiso `core.view_user`):

| Nombre | URL Admin | Ícono | Permiso |
|--------|-----------|-------|---------|
| Usuarios | `admin:core_user_changelist` | `fas fa-users` | `core.view_user` |

**Grupo "Trámites"**:

| Nombre | URL Admin | Ícono | Permiso | Roles que lo ven |
|--------|-----------|-------|---------|-----------------|
| Mis trámites | `admin:tramites_buzon_changelist` | `fas fa-user` | `tramites.acceso_analista` | Analista |
| Disponibles | `admin:tramites_disponible_changelist` | `fas fa-inbox` | `tramites.acceso_analista` | Analista |
| Trámites en curso | `admin:tramites_tramite_changelist` | `fas fa-inbox` | `tramites.acceso_coordinador` | Coordinador |
| Trámites finalizados | `admin:tramites_cerrado_changelist` | `fas fa-flag-checkered` | `tramites.acceso_coordinador` | Coordinador |

#### Estilos del sidebar

- **Fondo (tema light)**: `#3f0f16` (shade del primary al 60%)
- **Texto de links inactivos**: `rgb(194, 199, 208)` (dark theme default de AdminLTE)
- **Link activo**: Texto blanco con highlight sutil
- **Brand text**: Usa `--bs-link-color` del dark theme (`#c47d88`)
- **Configuración Jazzmin**: `sidebar_nav_flat_style: True`, `navigation_expanded: True`

#### Aplicaciones ocultas

```python
'hide_apps': ['contenttypes', 'sessions', 'admin', 'tramites', 'core']
'hide_models': ['auth.group']
```

Toda la navegación se controla exclusivamente via `custom_links` con permisos. Ningún modelo se registra directamente en el sidebar.

______________________________________________________________________

### Timeline (Historial del Trámite)

Componente CSS puro que muestra el historial de actividades de un trámite en la vista de detalle (`tramite_detail.html`).

#### Estructura HTML

```html
<div class="timeline-item" data-status="proceso">
    <!-- Badge de estatus + timestamp -->
    <div class="d-flex align-items-center mb-1">
        <span class="badge badge-proceso-202 me-2">EN_REVISION</span>
        <small class="text-muted">2026-04-30 14:30:00</small>
    </div>
    <!-- Usuario -->
    <div class="mb-1"><i class="fas fa-user px-1"></i>Juan Pérez</div>
    <!-- Observación -->
    <div class="text-muted mb-2">Observación del analista</div>
    <!-- Archivos adjuntos -->
    <div class="timeline-files mb-2">
        <small class="text-muted"><i class="fas fa-paperclip"></i> Documentos (2)</small>
        <div class="file-item">
            <a href="..."><i class="fas fa-file-pdf"></i> archivo.pdf</a>
            <small>(1.23 MB)</small>
        </div>
    </div>
</div>
```

#### Estilos CSS

| Elemento | Implementación |
|----------|---------------|
| Línea vertical | `border-left: 3px solid var(--bs-border-color)` |
| Dot (círculo) | `::before` pseudo-elemento: 11×11px, `border-radius: 50%` |
| Dot por familia | `data-status="inicio"` → gris (`--bs-gray-500`), `"proceso"` → verde (`--bs-success`), `"finalizado"` → azul (`--bs-info`) |
| Primer item | Dot sólido: `background: var(--bs-primary)` |
| Hover | Dot escala a `1.25x`, borde cambia a `--bs-primary`, línea cambia a `--bs-primary` |
| Último item | Línea transparente, sin padding inferior |
| Panel de archivos | `.timeline-files`: fondo `--bs-tertiary-bg`, borde `--bs-border-color`, `border-radius` |
| Scroll | `.scroll-panel`: `max-height: 400px`, `overflow-y: auto` |

> El timeline usa **exclusivamente** `var(--bs-*)` para compatibilidad con ambos temas (light/dark).

______________________________________________________________________

### Quick Actions (Botones de Acción Rápida)

Botones individuales por fila en las listas de trámites (changelist) que ejecutan acciones sin necesidad de seleccionar checkboxes.

#### CSS

```css
.quick-action {
    margin-right: 4px;
}
```

#### JavaScript (`static/admin/js/quick_actions.js`)

Usa **event delegation** sobre `#changelist-form` para capturar clicks en elementos `.quick-action`:

1. Previene la acción por defecto.
1. Establece el valor del dropdown `<select name="action">` con `data-action` del botón.
1. Crea un `<input type="hidden" name="_selected_action">` con `data-pk`.
1. Envía el formulario.

> **CSP-safe**: Sin inline handlers. Servido como archivo estático (`script-src 'self'`).

#### Generación desde Python (`core/admin_utils.py`)

```python
render_quick_action(label, attrs, target)
# Retorna: <button> o <a> con clase btn-outline-primary + btn-sm
```

______________________________________________________________________

## Iconografía

El sistema utiliza **Font Awesome 5** (incluido por Jazzmin). Todos los íconos usan el prefijo **`fas`** (Font Awesome Solid).

### Convenciones

- **Prefijo**: Siempre `fas` + clase de ícono (ej: `fas fa-user`)
- **Spacing**: Acompañar con clases de utilidad Bootstrap: `px-2`, `px-1`, `mr-1`, `me-1`, `me-2`
- **Tamaño**: Por defecto hereda `font-size` del padre. Usar `fa-3x` solo en dashboard cards

### Íconos usados en el proyecto

| Ícono | Clase | Contexto de uso |
|-------|-------|----------------|
| 👤 Usuario | `fas fa-user` | Solicitante, analista asignado, sidebar "Mis trámites" |
| 👥 Usuarios | `fas fa-users` | Sidebar "Usuarios", gestión de usuarios |
| 📥 Bandeja | `fas fa-inbox` | Sidebar "Disponibles", "Trámites en curso" |
| 🏁 Meta | `fas fa-flag-checkered` | Sidebar "Trámites finalizados" |
| 📄 Documento | `fas fa-file-alt` | Información del trámite, "Requerir Documentos" |
| ℹ️ Información | `fas fa-info-circle` | Sección "Estatus Actual" |
| 👨‍💼 Perito | `fas fa-user-tie` | Sección "Perito" |
| 🕐 Historial | `fas fa-history` | Sección "Historial del Trámite" |
| 📎 Adjunto | `fas fa-paperclip` | Documentos adjuntos en timeline |
| 📕 PDF | `fas fa-file-pdf` | Enlaces a descarga de PDF |
| ✏️ Editar | `fas fa-edit` | "Modificar Asignación" |
| 📋 Lista | `fas fa-list-alt` | Lista de trámites seleccionados |
| 📦 Caja | `fas fa-box` | Trámite sin asignar |
| ✅ Check | `fas fa-check` | Confirmar acciones |
| ❌ Cancelar | `fas fa-times` | Cancelar acciones |
| ⬅️ Regresar | `fas fa-arrow-left` | Botón "Regresar a Listado" |
| ⚠️ Advertencia | `fas fa-exclamation-triangle` | Cancelación de trámite, error 500 |
| ℹ️ Alerta | `fas fa-exclamation-circle` | Advertencias inline |
| 🔒 Bloqueado | `fas fa-lock` | Error 403 |
| 🛡️ CSRF | `fas fa-shield-alt` | Error CSRF |
| 🔍 Buscar | `fas fa-search` | Error 404 |
| 🏠 Inicio | `fas fa-home` | Botón "Volver al inicio" en páginas de error |
| 🔄 Reintentar | `fas fa-redo` | Botón en error CSRF |
| 📋 Portapapeles | `fas fa-clipboard-check` | Sección "Selecciona el motivo de cancelación" |
| 🚩 Bandera | `fas fa-flag` | "Estatus de cierre" |
| 💬 Comentario | `fas fa-comment` | Campos de observación |
| 🕐 Reloj | `fas fa-clock` | "Enviar a Firma" |
| ❌ Cerrar círculo | `fas fa-times-circle` | "Cancelar Trámite", "Confirmar Cancelación" |
| 📋 Tareas | `fas fa-tasks` | "Acciones Disponibles" |
| 👁️ Vista | `fas fa-eye` | Preview en debug |

______________________________________________________________________

## Templates Personalizados

Todos los templates extienden `admin/base_site.html`, que a su vez extiende el layout de Jazzmin (`admin/base.html`).

### Mapa de templates

| Template | Extiende | Propósito | Layout |
|----------|----------|-----------|--------|
| `admin/base_site.html` | `admin/base.html` | Footer con versión de la app (desde `pyproject.toml`) y copyright | Full layout |
| `admin/tramite_detail.html` | `admin/base_site.html` | Vista de detalle de trámite con timeline | 2 columnas (9-3) |
| `admin/tramite_cancelar.html` | `admin/base_site.html` | Formulario de cancelación de trámite | 1 columna centrada (8) |
| `admin/modificar_asignacion.html` | `admin/base_site.html` | Asignación/reasignación de trámites | 2 columnas (6-6) |
| `admin/buzon_asignacion_changelist.html` | `admin/change_list.html` | Balance de carga en listado de buzón | Full width |
| `admin/auth/user/asignar_rol.html` | `admin/base_site.html` | Asignación de roles a usuarios | 1 columna |
| `admin/includes/dashboard_cards.html` | — (include) | Tarjetas del dashboard (grid) | Grid `col-md-6 col-lg-4` |
| `403.html`, `403_csrf.html`, `404.html`, `500.html` | Login box layout | Páginas de error minimalistas | Centrado |

### Patrones de template

#### Cards de sección (vista de detalle)

```html
<section class="card shadow-sm mb-4">
    <div class="card-header bg-secondary text-white">
        <h5 class="mb-0"><i class="fas fa-icon px-2"></i>Título</h5>
    </div>
    <div class="card-body">
        <table class="table table-bordered info-table">
            <!-- Filas de datos -->
        </table>
    </div>
</section>
```

#### Tabla de información (`info-table`)

```css
.info-table td:first-child {
    font-weight: bold;
    width: 30%;
    background-color: #f8f9fa;
}
```

> **Nota**: Los estilos `info-table` se definen inline en `{% block extrastyle %}` de `tramite_detail.html`. Considerar mover a `backoffice.css`.

#### Formularios de acción

```html
<form method="post" id="accion-form">
    {% csrf_token %}
    <input type="hidden" name="action" id="action-input">
    <div class="d-grid gap-2">
        <button type="submit" class="btn btn-warning" data-action="requerir_documentos">
            <i class="fas fa-file-alt px-2"></i>Requerir Documentos
        </button>
    </div>
</form>
<!-- JS externo con event delegation -->
{% block extrajs %}
<script src="{% static 'admin/js/tramite_actions.js' %}" defer></script>
{% endblock %}
```

______________________________________________________________________

## Reglas de Diseño

### Convenciones CSS

| Regla | Descripción |
|-------|-------------|
| **Sin colores hardcodeados** | Usar `var(--bs-*)` para compatibilidad light/dark. Excepción: valores calculados con `shade()`/`tint()` que ya incorporan los tokens |
| **Sin estilos inline** | Todo CSS debe ir en `static/admin/css/backoffice.css`. Excepción actual: `dashboard_cards.html` usa inline styles para colores dinámicos por tarjeta |
| **Sin scripts inline** | Todo JS debe ser archivos estáticos con event delegation (CSP compliance). Prohibido `onclick`, `onchange`, `<script>` inline |
| **Bootstrap first** | Usar clases de Bootstrap antes de CSS custom. Ej: preferir `d-grid gap-2` sobre CSS custom para layout de botones |
| **`defer` en scripts** | Siempre agregar `defer` al cargar archivos JS desde templates |

### Patrones de nomenclatura

| Elemento | Patrón | Ejemplo |
|----------|--------|---------|
| Variables CSS de tema | `--bs-{componente}-{propiedad}` | `--bs-primary`, `--bs-body-bg` |
| Variables CSS custom | `--{nombre-descriptivo}` | `--header-bg`, `--breadcrumbs-bg` |
| Clases de badge por estatus | `.badge-{grupo}-{id}` | `.badge-proceso-202` |
| Clases de badge genéricas | `.badge-{color}` | `.badge-success`, `.badge-danger` |
| Templates admin | `admin/{modelo}_{vista}.html` | `admin/tramite_detail.html` |
| Templates includes | `admin/includes/{componente}.html` | `admin/includes/dashboard_cards.html` |
| JS estáticos | `admin/js/{funcionalidad}.js` | `admin/js/quick_actions.js` |

### Breakpoints responsive

| Breakpoint | Ancho | Variable CSS | Uso principal |
|------------|-------|-------------|---------------|
| XS | 0+ | `--bs-breakpoint-xs` | Móvil |
| SM | 576px+ | `--bs-breakpoint-sm` | Móvil horizontal |
| MD | 768px+ | `--bs-breakpoint-md` | Tablet (dashboard cards: 2 por fila) |
| LG | 992px+ | `--bs-breakpoint-lg` | Desktop (detalle: 2 columnas, dashboard: 3 por fila) |
| XL | 1200px+ | `--bs-breakpoint-xl` | Desktop grande |
| XXL | 1400px+ | `--bs-breakpoint-xxl` | Monitor externo |

### Accesibilidad (WCAG AA)

- **Contraste de texto**: Todos los badges y botones cumplen WCAG AA (ratio >= 4.5:1)
- **Texto sobre fondo claro** (success, info, warning, danger, light): usa texto oscuro (`#000` o `text-emphasis`)
- **Texto sobre fondo oscuro** (primary, secondary, dark): usa texto blanco (`#fff`)
- **Focus ring**: `rgba(157, 38, 56, 0.25)` — visible en ambos temas

### Regla para nuevos componentes

> **Antes de crear un template nuevo**, leer un template existente en `templates/admin/` como referencia. Seguir los patrones de: sección card → header con ícono + título → body con tabla/formulario → buttons con íconos + spacing.
