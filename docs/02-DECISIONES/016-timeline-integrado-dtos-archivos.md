# 016: Timeline Integrado con DTOs y Doble Schema de Archivos PDF

**Date:** 2026-04-30
**Status:** Accepted
**Related:** 010-integracion-con-sftp.md, 015-timestamps-timezone-america-tijuana.md

## Contexto y Planteamiento del Problema

El detalle de trámite (`change_view` en `BuzonAdmin`) mostraba tres secciones separadas: (1) historial de actividades como tabla, (2) archivos de actividades (ACT-*.pdf), y (3) documentos del ciudadano (DAU-*.pdf). Esto generaba:

- **Experiencia fragmentada**: el usuario debía cruzar mentalmente la tabla de historial con las secciones de archivos
- **Redundancia visual**: los archivos aparecían separados de la actividad que los generó
- **Duplicación de lógica**: los DTOs (`RequisitoFile`, `ActividadFile`) estaban definidos en `catalogos.py` junto con modelos de catálogo

El sistema maneja dos schemas de archivos PDF con nombres distintos:

| Schema | Ejemplo | Origen | Asociado a |
|--------|---------|--------|------------|
| `DAU-{folio}-{requisito_id}.pdf` | `DAU-260420-AAAE-B-19.pdf` | Ciudadano (upload externo) | Primera actividad PENDIENTE_PAGO (102) |
| `ACT-{actividad_id}-{timestamp}.pdf` | `ACT-145-2026-04-30T02-54-49.pdf` | Sistema (generación automática) | Actividades en REQUERIMIENTO (203) o SUBSANADO (204) |

## Opciones Consideradas

* **Opción A**: Mantener las tres secciones separadas con mejoras visuales menores
* **Opción B**: Timeline vertical integrado que une actividades + archivos asociados, usando DTOs reubicados
* **Opción C**: Vista tipo "chat" con actividades como mensajes y archivos como adjuntos

## Resultado de la Decisión

Opción elegida: **"B — Timeline integrado con DTOs reubicados"**, porque unifica la experiencia visual sin cambiar el modelo mental del usuario (el historial ya existía como tabla), y la reubicación de DTOs elimina la dependencia circular con `catalogos.py`.

### Arquitectura de DTOs

Las dataclasses se movieron de `catalogos.py` a `actividades.py`:

```
tramites/models/actividades.py
├── RequisitoFile       # DAU-*.pdf metadata + catálogo
├── ActividadFile       # ACT-*.pdf metadata + registro actividades
├── TimelineEntry       # Actividad + archivos + usuario
└── Actividades (Model) # Sin cambios
```

`TimelineEntry` es el DTO central que une:
- Una `Actividades` del historial
- `list[ActividadFile]` — archivos ACT adjuntos (solo para REQUERIMIENTO/SUBSANADO)
- `list[RequisitoFile]` — documentos del ciudadano (solo para la primera PENDIENTE_PAGO)
- `User | None` — usuario backoffice resuelto vía batch lookup

### Reglas de negocio del timeline

| Regla | Estatus | Archivos asociados |
|-------|---------|-------------------|
| Documentos del ciudadano | Primero PENDIENTE_PAGO (102) | DAU-*.pdf (requisitos) |
| Archivos de actividad | REQUERIMIENTO (203) | ACT-{id}-*.pdf |
| Archivos de actividad | SUBSANADO (204) | ACT-{id}-*.pdf |
| Sin archivos | Todos los demás estatus | `[]` |

### Doble schema de validación

`validate_filename()` acepta ambos patterns:

```python
FILENAME_REGEX      = r'^[A-Z]+-\d{6}-[A-Z]{4}-[A-Z]-(?P<requisito_id>\d+)\.pdf$'
ACTIVIDAD_FILENAME_REGEX = r'^ACT-(?P<actividad_id>\d+)-(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})\.pdf$'
```

Ambos están anclados (`^...$`) y comparten las mismas defensas contra path traversal.

### Cambios en código

1. **`tramites/models/actividades.py`**: `RequisitoFile`, `ActividadFile`, `TimelineEntry` dataclasses
2. **`tramites/models/catalogos.py`**: DTOs eliminados (dead code), `from dataclasses` removido
3. **`tramites/models/__init__.py`**: Imports desde `.actividades`
4. **`tramites/sftp.py`**: `fetch_actividad_files()` classmethod + `_list_actividad_files()` interno
5. **`tramites/constants.py`**: `ACTIVIDAD_FILENAME_REGEX` añadido
6. **`tramites/admin.py`**: `change_view` construye `timeline_entries` con lógica de agrupamiento
7. **`templates/admin/tramite_detail.html`**: Timeline vertical reemplaza 3 secciones
8. **`static/admin/css/backoffice.css`**: Estilos de timeline con dots coloreados por grupo de estatus
9. **`tramites/templatetags/admin_extras.py`**: `status_group` filter para coloring CSS

### Tests

70 tests nuevos en `tests/tramites/test_timeline.py`:

| Categoría | Tests | Qué cubre |
|-----------|-------|-----------|
| validate_filename ACT-*.pdf | 12 | Path traversal, formato inválido, ambos schemas |
| ACTIVIDAD_FILENAME_REGEX | 6 | Parsing y rechazo |
| fetch_actividad_files() | 6 | SFTP listing, errores, sorting |
| ActividadFile dataclass | 2 | Creación básica y campos opcionales |
| RequisitoFile dataclass | 2 | Creación con/sin nombre de catálogo |
| TimelineEntry dataclass | 4 | Actividades, archivos, usuarios |
| status_group filter | 15 | Rangos 100-399, None, fuera de rango |
| status_badge_class filter | 7 | Formato group-id, None |
| Template filter integration | 2 | Renderizado en template Django |
| Timeline context building | 8 | Lógica de agrupamiento del admin |

### Consecuencias

* Bueno, porque la experiencia es una sola línea temporal — el usuario ve actividad y archivos juntos
* Bueno, porque los DTOs están junto al modelo `Actividades` donde pertenecen lógicamente
* Bueno, porque `validate_filename()` soporta ambos schemas sin bifurcación de código
* Bueno, porque las reglas de negocio están testeadas unitariamente (70 tests)
* Malo, porque el template es más complejo — `{% for entry in timeline_entries %}` con sub-condicionales
* Malo, porque la resolución de usuarios requiere un batch lookup a la DB (`User.objects.filter`)

---
Formato basado en [MADR](https://adr.github.io/madr/)
