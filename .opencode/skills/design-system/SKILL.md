---
name: design-system
description: UX design system for Django Admin - Backoffice San Felipe
---

# 🎨 Design System para Django Admin - Backoffice San Felipe

## 📋 Resumen del Sistema

Este design system define las reglas de estilo y variables CSS para garantizar consistencia visual en el admin de Django utilizando Django 6.0 theming. Basado en la paleta DAU y soporte nativo de variables CSS de Django.

## 🎨 Paleta de Colores (Tema Claro)

### Colores Primarios
- **Primary (Rojo/Maroon):** `#9d2638` - Usado en header, botones primarios
- **Secondary (Gris Oscuro):** `#1a1a1a` - Fondo principal de contenido
- **Accent (Naranja):** `#f59e0b` - Títulos destacados y advertencias

### Colores de Botones
- **Primary Button:** `#1e3a8a` - Azul oscuro para acciones principales
- **Destructive Button:** `#ef4444` - Rojo para acciones destructivas
- **Button Hover:** Aclarar 10% en hover states

### Colores de Texto
- **Text Primary:** `#1a1a1a` - Texto principal oscuro
- **Text Secondary:** `#4b5563` - Gris medio para texto secundario
- **Text Muted:** `#6b7280` - Gris claro para texto auxiliar
- **Text Quiet:** `#6b7280` - Texto muy claro

### Colores de Estado
- **Success:** `#10b981` - Verde para estados de éxito
- **Warning:** `#f59e0b` - Naranja para advertencias
- **Error:** `#ef4444` - Rojo para errores
- **Info:** `#3b82f6` - Azul para información

## 🔧 Django 6.0 Variables CSS

### Variables Principales
```css
/* DAU Brand Colors */
--primary: #9d2638;
--secondary: #1a1a1a;
--accent: #f59e0b;
--primary-fg: #ffffff;
```

### Variables de Cuerpo
```css
/* Body Colors (Light Theme) */
--body-fg: #1a1a1a;
--body-bg: #ffffff;
--body-quiet-color: #6b7280;
--body-medium-color: #4b5563;
--body-loud-color: #111827;
```

### Variables de Enlaces
```css
/* Link Colors */
--link-fg: #417893;
--link-hover-color: #0b599b;
--link-selected-fg: #1a1a1a;
```

### Variables de Mensajes
```css
/* Message Colors */
--message-success-bg: #d1fae5;
--message-success-icon: url(../img/icon-yes.svg);
--message-warning-bg: #fef3c7;
--message-warning-icon: url(../img/icon-alert.svg);
--message-error-bg: #fee2e2;
--message-error-icon: url(../img/icon-no.svg);
--message-info-bg: #d1ecf1;
--message-info-icon: url(../img/icon-info.svg);
```

### Variables de Botones
```css
/* Button Colors */
--button-bg: #1e3a8a;
--button-hover-bg: #1e40af;
--delete-button-bg: #ef4444;
--delete-button-hover-bg: #dc2626;
```

### Variables de Header
```css
/* Header Colors */
--header-bg: var(--primary);
--header-link-color: #ffffff;
```

### Variables de Breadcrumbs
```css
/* Breadcrumbs */
--breadcrumbs-bg: var(--primary);
--breadcrumbs-link-fg: #ffffff;
--breadcrumbs-fg: #e0e7ff;
```

### Variables de Otros Elementos
```css
/* Object Tools */
--object-tools-bg: #6b7280;
--object-tools-hover-bg: #4b5563;

/* Selected Row */
--selected-row: #fef3c7;

/* Borders */
--hairline-color: #d5dbdb;
--border-color: #d5dbdb;

/* Error FG */
--error-fg: #991b1b;
```

## 📝 Tipografía

### Familias de Fuentes
```css
/* Django defaults - sistema de fuentes */
--font-family-primary:
    "Segoe UI",
    system-ui,
    Roboto,
    "Helvetica Neue",
    Arial,
    sans-serif;
--font-family-monospace:
    ui-monospace,
    Menlo,
    Monaco,
    "Cascadia Mono",
    "Segoe UI Mono",
    "Roboto Mono",
    "Oxygen Mono",
    "Ubuntu Monospace",
    "Source Code Pro",
    "Fira Mono",
    "Droid Sans Mono",
    "Courier New",
    monospace;
```

### Tamaños de Texto (Django defaults)
- **Base:** 0.875rem (14px)
- **H1 (títulos principales):** 1.25rem (20px)
- **H2 (subtítulos):** 1rem (16px)
- **H3 (secciones):** 0.875rem (14px)
- **Small (texto pequeño):** 0.75rem (12px)
- **Caption (texto muy pequeño):** 0.625rem (10px)

### Espaciado de Texto
- **Line-height:** 1.5 para mejor legibilidad
- **Letter-spacing:** Normal para body text, 0.5px para títulos

## 📏 Espaciado y Layout

### Espaciado Base
- **Padding estándar:** 16px en contenedores principales
- **Margin vertical:** 24px entre secciones
- **Gap en grids:** 16px entre elementos
- **Border radius:** 4px (Django default)

### Máximos de Contenido
- **Min-width container:** 980px (Django default)
- **Padding horizontal:** Responsive (auto con breakpoints)

### Responsive Design
- **Breakpoints:** Django admin maneja responsividad nativamente
- **Touch targets:** Mínimo 44x44px para accesibilidad móvil

## 🎯 Django Admin Customization

### Template Override Base

Crear `templates/admin/base.html` para override de variables CSS:

```django
{% extends "admin/base.html" %}
{% load static %}

{% block extrastyle %}
{{ block.super }}
<style>
  :root {
    /* DAU Brand Colors */
    --primary: #9d2638;
    --secondary: #1a1a1a;
    --accent: #f59e0b;
    --primary-fg: #ffffff;
    
    /* Body Colors (Light Theme) */
    --body-fg: #1a1a1a;
    --body-bg: #ffffff;
    --body-quiet-color: #6b7280;
    --body-medium-color: #4b5563;
    --body-loud-color: #111827;
    
    /* Link Colors */
    --link-fg: #417893;
    --link-hover-color: #0b599b;
    --link-selected-fg: #1a1a1a;
    
    /* Message Colors */
    --message-success-bg: #d1fae5;
    --message-success-icon: url(../img/icon-yes.svg);
    --message-warning-bg: #fef3c7;
    --message-warning-icon: url(../img/icon-alert.svg);
    --message-error-bg: #fee2e2;
    --message-error-icon: url(../img/icon-no.svg);
    --message-info-bg: #d1ecf1;
    --message-info-icon: url(../img/icon-info.svg);
    
    /* Button Colors */
    --button-bg: #1e3a8a;
    --button-hover-bg: #1e40af;
    --delete-button-bg: #ef4444;
    --delete-button-hover-bg: #dc2626;
    
    /* Header Colors */
    --header-bg: var(--primary);
    --header-link-color: #ffffff;
    
    /* Breadcrumbs */
    --breadcrumbs-bg: var(--primary);
    --breadcrumbs-link-fg: #ffffff;
    --breadcrumbs-fg: #e0e7ff;
    
    /* Object Tools */
    --object-tools-bg: #6b7280;
    --object-tools-hover-bg: #4b5563;
    
    /* Selected Row */
    --selected-row: #fef3c7;
    
    /* Borders */
    --hairline-color: #d5dbdb;
    --border-color: #d5dbdb;
    
    /* Error FG */
    --error-fg: #991b1b;
  }
</style>
{% endblock %}
```

### Logo Override (CSS-only)

```css
/* Logo Override */
#branding h1 {
  display: flex;
  align-items: center;
}

#branding h1 a {
  background-image: url({% static 'admin/img/logo.png' %});
  background-repeat: no-repeat;
  background-size: contain;
  background-position: center;
  display: inline-block;
  width: 40px;
  height: 40px;
  text-indent: -9999px;
  overflow: hidden;
}

#branding h1 a::before {
  display: none;
}
```

**Nota:** Actualizar path y agregar imagen de logo a `static/admin/img/` cuando esté disponible.

### Admin.py Styling

Para badges y estilos inline en admin.py, usar `format_html()` con colores del design system:

```python
from django.utils.html import format_html

def badge_status(self, obj):
    """Display status badge with design system colors."""
    colors = {
        'inicio': '#6b7280',      # gray-500
        'proceso': '#3b82f6',     # blue-500
        'finalizado': '#10b981',  # green-500
        'error': '#ef4444',        # red-500
    }
    color = colors.get(obj.estatus, '#6b7280')
    return format_html(
        '<span style="background-color: {}; color: white; '
        'padding: 2px 8px; border-radius: 4px;">{}</span>',
        color,
        obj.estatus
    )
badge_status.short_description = 'Estatus'
```

## 🎯 Principios de Diseño para Aplicaciones Gubernamentales

### Valores Fundamentales
1. **Claridad sobre complejidad:** Los usuarios nunca deben preguntarse qué hace algo
2. **Confianza a través de consistencia:** Patrones predecibles en todas las interfaces
3. **Accesibilidad por defecto:** Diseñar para todos, incluyendo usuarios de tecnología asistiva
4. **Apariencia profesional:** Limpio, moderno, no demasiado estilizado
5. **Eficiencia:** Minimizar clics, simplificar flujos, reducir carga cognitiva

### Jerarquía Visual
- **Acciones primarias:** Alto contraste, ubicación prominente (alineado a la derecha para formularios)
- **Acciones secundarias:** Estilos sutiles, clara diferenciación de las primarias
- **Advertencias críticas:** Rojo/naranja con alerts apropiados
- **Estados de éxito:** Verde con mensajes de confirmación
- **Jerarquía de información:** Usar tamaño, peso y espaciado, no solo color

### Uso de Colores
- **Primary:** Usar colores definidos en paleta (#9d2638 para DAU)
- **Success:** Verde para estados positivos (#10b981)
- **Warning/Error:** Rojo para errores (#ef4444), naranja para advertencias (#f59e0b)
- **Neutral:** Grises para texto, bordes, fondos
- **IMPORTANTE:** Nunca usar color solo para transmitir significado

## ♿ Accesibilidad

### Requisitos WCAG 2.1 AA
- **Contraste mínimo:** 4.5:1 para texto normal, 3:1 para texto grande
- **Focus management:** Elementos focusables con borde visible
- **ARIA labels:** Todas las acciones y componentes accesibles
- **Keyboard navigation:** Todas las funcionalidades accesibles por teclado
- **Responsive design:** Funcional en dispositivos móviles y desktop

### Patrones de Accesibilidad
- **Buttons:** ARIA labels claros, focus visible
- **Forms:** Labels asociados a inputs, validación accesible
- **Alerts:** ARIA live regions para mensajes críticos
- **Icons:** Texto alternativo o descripción accesible

## 🔐 Seguridad en Django Admin

### 1. Auto-escaping de Django

Django auto-escapa todos los templates por defecto para prevenir XSS:

```django
<!-- ✅ SEGURO - Django auto-escapa -->
{{ variable }}

<!-- ❌ PELIGROSO - Solo usar mark_safe con contenido confiable -->
{{ unsafe_variable|safe }}
```

### 2. Uso de format_html() para HTML seguro

```python
from django.utils.html import format_html

# ✅ SEGURO - format_html() valida y escapa el contenido
return format_html(
    '<span style="color: {};">{}</span>',
    '#10b981',
    user_input
)

# ❌ PELIGROSO - Evitar concatenación directa de strings HTML
return f'<span style="color: #10b981;">{user_input}</span>'
```

### 3. Protección CSRF

Django incluye protección CSRF automática en formularios:

```django
<!-- ✅ Django agrega token CSRF automáticamente -->
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

### Reglas de Seguridad

- ✅ **Siempre** usar `format_html()` para HTML dinámico en admin.py
- ✅ **Nunca** usar `|safe` filter con input de usuario
- ✅ **Siempre** incluir `{% csrf_token %}` en formularios
- ✅ **Validar** y sanitizar input de usuario en formularios
- ✅ **Nunca** confiar en input de usuario sin validación

## 🎨 Futuro: Tema Obscuro

Django 6.0 soporta modo obscuro vía `prefers-color-scheme` media query. Para implementar en el futuro:

```django
{% block extrastyle %}
{{ block.super }}
<style>
  @media (prefers-color-scheme: dark) {
    :root {
      /* DAU Colors */
      --primary: #9d2638;
      
      /* Body Colors (Dark Theme) */
      --body-fg: #ffffff;
      --body-bg: #1a1a1a;
      --body-quiet-color: #9ca3af;
      --body-medium-color: #e5e7eb;
      --body-loud-color: #ffffff;
      
      /* Links */
      --link-fg: #81d4fa;
      --link-hover-color: #4ac1f7;
      
      /* Borders */
      --hairline-color: #272727;
      --border-color: #353535;
      
      /* Selected Row */
      --selected-row: #00363a;
      
      /* Backgrounds */
      --darkened-bg: #212121;
      --selected-bg: #1b1b1b;
    }
  }
</style>
{% endblock %}
```

## 📊 Tabla de Mapeo de Colores

| DAU Design System | Django Variable | Uso |
|------------------|----------------|--------|
| #9d2638 (Primary Red) | `--primary` | Header, botones primarios |
| #1a1a1a (Dark Gray) | `--secondary` | Sidebar, navegación |
| #f59e0b (Orange Accent) | `--accent` | Highlights, advertencias |
| #10b981 (Green) | `--message-success-bg` | Mensajes de éxito |
| #f59e0b (Orange) | `--message-warning-bg` | Mensajes de advertencia |
| #ef4444 (Red) | `--message-error-bg` | Mensajes de error |
| #3b82f6 (Blue) | `--message-info-bg` | Mensajes de información |
| #1e3a8a (Dark Blue) | `--button-bg` | Botones primarios |
| #ef4444 (Red) | `--delete-button-bg` | Acciones destructivas |
| #6b7280 (Gray) | Badges "inicio" | Estado inicial |
| #3b82f6 (Blue) | Badges "proceso" | Estado en proceso |
| #10b981 (Green) | Badges "finalizado" | Estado finalizado |

## 🚀 Mantenimiento del Design System

### Proceso de Actualización
1. **Identificar cambios** en paleta de colores o estilos
2. **Actualizar variables** en `templates/admin/base.html`
3. **Actualizar colores** en admin.py si es necesario
4. **Validar** consistencia visual en todo el admin

### Mantenimiento
- **Documentación:** Actualizar cuando se añadan nuevos colores o componentes
- **Tests:** Verificar funcionalidad del admin después de cambios
- **Versionado:** Documentar cambios mayores en README o AGENTS.md
- **Revisión:** Revisión periódica de consistencia visual

## ✅ Checklist para Customization del Admin

Antes de finalizar customización del admin, verificar:

### Template Override
- [ ] `templates/admin/base.html` creado con variables CSS
- [ ] Variables de color coinciden con paleta DAU
- [ ] Logo override agregado (si aplica)

### Estilos y Temas
- [ ] Header usa color `--primary: #9d2638`
- [ ] Botones primarios usan color `--button-bg: #1e3a8a`
- [ ] Mensajes de estado usan colores correctos
- [ ] Badges en admin.py usan `format_html()` con colores del design system

### Admin.py Styling
- [ ] Inline colors coinciden con paleta DAU
- [ ] `format_html()` usado para HTML dinámico
- [ ] No hay referencias a colores antiguos (#667eea, #764ba2, etc.)
- [ ] Badges de estado usan colores correctos

### Accesibilidad
- [ ] **Contraste** mínimo WCAG 2.1 AA verificado
- [ ] **Focus management** con bordes visibles
- [ ] **ARIA labels** en componentes interactivos
- [ ] **Keyboard navigation** funcional
- [ ] Touch targets mínimos 44x44px

### Seguridad
- [ ] **Auto-escaping** de Django funcionando
- [ ] **format_html()** usado para HTML dinámico
- [ ] **No uso de `|safe`** con input de usuario
- [ ] **CSRF tokens** incluidos en formularios
- [ ] **Validación de input** implementada

### Funcionalidad
- [ ] Admin carga sin errores en `/admin/`
- [ ] Header, botones y mensajes tienen colores correctos
- [ ] List views y change views funcionan correctamente
- [ ] Responsive design funciona en móviles y desktop
- [ ] Dark mode (si implementado) funciona correctamente

---

*Nota: Este design system utiliza Django 6.0 nativo theming con CSS variables. Actualizar según necesidades del proyecto.*
