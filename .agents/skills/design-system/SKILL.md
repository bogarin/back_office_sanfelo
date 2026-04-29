---
name: design-system
description: UX design system for Backoffice de Tramites (Django + Jazzmin)
---

# Design System para Backoffice de Tramites

## Resumen

Basado en **Jazzmin** (Bootstrap 5 + AdminLTE + Bootswatch "united") con personalizacion en `static/admin/css/backoffice.css`.

### Archivos Clave

| Archivo | Proposito |
|---------|-----------|
| `static/admin/css/backoffice.css` | CSS custom properties (light/dark), badges, quick actions |
| `sanfelipe/settings/jazzmin.py` | Configuracion Jazzmin: tema, sidebar, links, branding |
| `templates/admin/` | Templates personalizados que extienden Jazzmin (referencia para patrones) |

### Stack de UI

- **Framework CSS**: Bootstrap 5 (via Jazzmin)
- **Tema Base**: Bootswatch "united"
- **Layout**: AdminLTE (sidebar, navbar, cards)
- **Iconos**: Font Awesome (prefijo `fas`)
- **JS**: jQuery (Django admin) + Bootstrap JS + AdminLTE JS

## Paleta de Colores

### Colores Primarios
- **Primary (Rojo/Maroon):** `#9d2638`
- **Secondary (Gris Oscuro):** `#1a1a1a`
- **Accent (Naranja):** `#f59e0b`

### Colores de Botones
- **Primary Button:** `#1e3a8a`
- **Destructive Button:** `#9d2638`
- **Text/Button Hover:** Aclarar 10% en hover states

### Colores de Texto
- **Text Primary:** `#ffffff`
- **Text Secondary:** `#e5e7eb`
- **Text Muted:** `#9ca3af`

### Colores de Estado
- **Success:** `#10b981`
- **Warning:** `#f59e0b`
- **Error:** `#ef4444`
- **Info:** `#3b82f6`

## Variables CSS Custom Properties

Definidas en `backoffice.css`. Jazzmin controla el tema activo via `data-bs-theme` en `<html>`.

### Tema Claro (`:root`, `[data-bs-theme="light"]`)

| Variable | Valor |
|----------|-------|
| `--bs-primary` | `#9d2638` |
| `--bs-secondary` | `#1a1a1a` |
| `--bs-success` | `#10b981` |
| `--bs-danger` | `#ef4444` |
| `--bs-warning` | `#f59e0b` |
| `--bs-info` | `#3b82f6` |
| `--bs-dark` | `#1a1a1a` |
| `--bs-body-bg` | `#fff` |
| `--bs-body-color` | `#1a1a1a` |
| `--bs-link-color` | `#9d2638` |
| `--bs-link-hover-color` | `#7d1e2d` |
| `--bs-border-color` | `#dee2e6` |

### Variables de Botones (Tema Claro)

Definidas en `backoffice.css` como custom properties. Los colores de texto cumplen WCAG AA (ratio >= 4.5:1).

**Botones Solid**

| Boton | bg | color | hover-bg | active-bg |
|-------|----|-------|----------|-----------|
| primary | `#9d2638` | `#fff` | `#852030` | `#7e1e2d` |
| secondary | `#1a1a1a` | `#fff` | `#161616` | `#151515` |
| success | `#10b981` | `#000` | `#0e9d6e` | `#0d9467` |
| info | `#3b82f6` | `#000` | `#326ed1` | `#2f68c5` |
| warning | `#f59e0b` | `#000` | `#d08609` | `#c47e09` |
| danger | `#ef4444` | `#000` | `#cb3a3a` | `#bf3636` |
| light | `#e9ecef` | `#000` | `#c6c9cb` | `#babdbf` |
| dark | `#1a1a1a` | `#fff` | `#161616` | `#151515` |

**Botones Outline** (hover/active rellenan con el color base)

| Boton | color | hover-color |
|-------|-------|-------------|
| outline-primary | `#9d2638` | `#fff` |
| outline-secondary | `#1a1a1a` | `#fff` |
| outline-success | `#10b981` | `#000` |
| outline-info | `#3b82f6` | `#000` |
| outline-warning | `#f59e0b` | `#000` |
| outline-danger | `#ef4444` | `#000` |
| outline-light | `#e9ecef` | `#000` |
| outline-dark | `#1a1a1a` | `#fff` |

**Regla WCAG AA**: Los botones con fondo claro (success, info, warning, danger, light) usan texto `#000`. Los botones con fondo oscuro (primary, secondary, dark) usan texto `#fff`.

### Tema Obscuro (`[data-bs-theme="dark"]`)

Jazzmin fuerza `data-bs-theme="dark"` en el sidebar. Valores derivados con `tint(base, 40%)` / `shade(base, 80%)` / `shade(base, 60%)`.

| Variable | Valor | Formula |
|----------|-------|---------|
| `--bs-body-bg` | `#212529` | Bootstrap default |
| `--bs-body-color` | `#dee2e6` | Bootstrap default |
| `--bs-link-color` | `#c47d88` | tint(primary, 40%) |
| `--bs-link-hover-color` | `#ba6774` | tint(primary, 30%) |
| `--bs-border-color` | `#495057` | Bootstrap default |
| `--bs-form-valid-color` | `#70d5b3` | tint(success, 40%) |
| `--bs-form-invalid-color` | `#f58f8f` | tint(danger, 40%) |

### Badges (Design System - Pastel + Pill)

Estilo: fondo suave tintado (bg-subtle) + texto oscuro (text-emphasis) + border-radius pill (`50rem`). Visualmente diferenciados de botones.

**Regla**: Badges = solo lectura, no interactivos. Si necesita interaccion, usar `.btn-sm` o `.quick-action`.

| Clase | bg (tint 80%) | color (shade 60%) | border |
|-------|---------------|-------------------|--------|
| `badge-primary` | `#ebd4d7` | `#3f0f16` |
| `badge-secondary` | `#d1d1d1` | `#0a0a0a` |
| `badge-success` | `#cff1e6` | `#064a34` |
| `badge-info` | `#d8e6fd` | `#183462` |
| `badge-warning` | `#fdecce` | `#623f04` |
| `badge-danger` | `#fcdada` | `#601b1b` |
| `badge-light` | `#fcfcfd` | `#495057` |
| `badge-dark` | `#d1d1d1` | `#0a0a0a` |
| `badge-inicio` | `#d1d1d1` | `#0a0a0a` | `#080808`
| `badge-inicio-101` | `#e4e4e4` | `#0a0a0a` | `#080808` | BORRADOR
| `badge-inicio-102` | `#cdcdcd` | `#0a0a0a` | `#080808` | PENDIENTE_PAGO
| `badge-inicio-103` | `#b6b6b6` | `#0a0a0a` | `#080808` | PAGO_EXPIRADO
| `badge-proceso` | `#cff1e6` | `#064a34` | `#053827`
| `badge-proceso-201` | `#ecf9f5` | `#064a34` | `#053827` | PRESENTADO
| `badge-proceso-202` | `#d9f4eb` | `#064a34` | `#053827` | EN_REVISION
| `badge-proceso-203` | `#c6eee1` | `#064a34` | `#053827` | REQUERIMIENTO
| `badge-proceso-204` | `#b3e9d7` | `#064a34` | `#053827` | SUBSANADO
| `badge-proceso-205` | `#9fe3cd` | `#064a34` | `#053827` | EN_DILIGENCIA
| `badge-finalizado` | `#d8e6fd` | `#183462` | `#12274a`
| `badge-finalizado-301` | `#e7f0fe` | `#183462` | `#12274a` | POR_RECOGER
| `badge-finalizado-302` | `#d8e6fd` | `#183462` | `#12274a` | RECHAZADO
| `badge-finalizado-303` | `#c8dcfc` | `#183462` | `#12274a` | FINALIZADO
| `badge-finalizado-304` | `#b8d2fc` | `#183462` | `#12274a` | CANCELADO
| `badge-otro` | `#d1d1d1` | `#0a0a0a` | `#080808`
| `badge-activo` | `#cff1e6` | `#064a34` | `#053827`
| `badge-inactivo` | `#d1d1d1` | `#0a0a0a` | `#080808` |

### Configuracion de Tema en Jazzmin

En `sanfelipe/settings/jazzmin.py`, `JAZZMIN_UI_TWEAKS`:
- `"theme"`: Bootswatch theme name (ej: `"united"`)
- `"default_theme_mode"`: `"light"` o `"dark"`
- Jazzmin persiste la preferencia en `localStorage` (`jazzmin-theme-mode`)

### Sidebar (Tema Light)

Jazzmin fuerza `data-bs-theme="dark"` y clase `sidebar-dark-primary` en `#jazzy-sidebar`. Sobrescrito en `backoffice.css`:
- **Background**: `#3f0f16` (shade(primary, 60%))
- **Links inactivos**: `rgb(194, 199, 208)` (dark theme default)
- **Link activo**: texto blanco con highlight sutil
- **Brand link**: usa `--bs-link-color` del dark theme (`#c47d88`)

**Regla**: Siempre usar `var(--bs-*)` en CSS custom. Nunca hardcodear valores que ya existen como variables Bootstrap.

## Clases CSS Disponibles

### Badges

Clases Bootstrap: `badge-primary`, `badge-success`, `badge-danger`, `badge-warning`, `badge-info`, `badge-secondary`, `badge-light`, `badge-dark`

Clases custom de estatus (grupo): `badge-inicio`, `badge-proceso`, `badge-finalizado`, `badge-otro`

Clases custom de estatus (específico, gradiente por intensidad):
- Inicio: `badge-inicio-101`..`badge-inicio-103` (gris, tint 88%→68%)
- Proceso: `badge-proceso-201`..`badge-proceso-205` (verde, tint 92%→60%)
- Finalizado: `badge-finalizado-301`..`badge-finalizado-304` (azul, tint 88%→64%)

Todos los badges custom incluyen `border: 1px solid shade(base, 70%)` para mejorar contorno visual.

Clases custom de estado: `badge-activo`, `badge-inactivo`

Template tag asociado: `status_badge_class` → retorna `inicio-{id}` / `proceso-{id}` / `finalizado-{id}` / `otro`
Función admin: `render_status_badge()` → usa `badge-{status_badge_class(estatus_id)}`

Colores y reglas WCAG AA documentados en la tabla de Badges arriba.

### Quick Actions

Clase: `quick-action` (definida en `backoffice.css`, JS en `static/admin/js/quick_actions.js`)

### Componentes Bootstrap en uso

Cards, tablas, formularios, badges, buttons, grid, alerts. Referencia: `templates/admin/` para ver los patrones usados.

### Iconos Font Awesome en uso

Prefijo `fas`. Referencia: buscar `fas fa-` en `templates/admin/` para los iconos especificos del proyecto.

## Reglas de Estilo

1. **No hardcoded colors**: Usar `var(--bs-*)` para compatibilidad con ambos temas
2. **No inline styles**: Todo CSS debe ir en `backoffice.css`
3. **No inline scripts**: Todo JS debe ser archivos estaticos con event delegation
4. **Bootstrap classes first**: Usar clases de Bootstrap antes de CSS custom
5. **Font Awesome icons**: Siempre con prefijo `fas` y clase de spacing (`px-2`, `mr-1`, etc.)
6. **CSP compliance**: No usar `onclick`, `onchange` ni `<script>` inline. Crear `.js` estaticos con event delegation
7. **Para nuevos templates**: Siempre leer un template existente en `templates/admin/` como referencia antes de crear
