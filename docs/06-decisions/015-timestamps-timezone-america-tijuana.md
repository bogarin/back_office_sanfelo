# 015: Estrategia Unificada de Timestamps y Zona Horaria (America/Tijuana)

**Date:** 2026-04-30
**Status:** Accepted
**Related:** 008-postgresql-schema-separation.md

## Contexto y Planteamiento del Problema

El sistema Backoffice Trámites es un microservicio Django que comparte la base de datos PostgreSQL (schema `public`) con aplicaciones Java legacy. Las tablas del backend (`actividades`, `tramite`, etc.) usan columnas `timestamp` **sin timezone** (`timestamp` en PostgreSQL, no `timestamptz`).

Se detectó que Django insertaba timestamps en UTC (ej: `07:47`) mientras que las aplicaciones Java insertaban en hora local de Tijuana (ej: `00:47`). Esto causaba:

- **Datos inconsistentes**: la misma columna contenía timestamps con 7 horas de diferencia según el origen
- **Ordenamiento roto**: `ORDER BY timestamp` mezclaba horas UTC y locales
- **Display incorrecto**: el admin mostraba UTC crudo; los templates convertían incorrectamente

## Opciones Consideradas

* **Opción A**: Dejar que PostgreSQL maneje los timestamps vía `DEFAULT CURRENT_TIMESTAMP`, configurando la sesión con `timezone=America/Tijuana`
* **Opción B**: Usar `default=timezone.localtime` en Django para enviar hora local explícitamente
* **Opción C**: Migrar las columnas PostgreSQL a `timestamptz` (con timezone)

## Resultado de la Decisión

Opción elegida: **"A — PostgreSQL DEFAULT CURRENT_TIMESTAMP con sesión en America/Tijuana"**, porque es consistente con las aplicaciones Java que ya usan este mecanismo, respeta el diseño original de las tablas, y no requiere migraciones en la base de datos.

### Configuración implementada

| Componente | Configuración | Propósito |
|---|---|---|
| Dockerfile (`TZ`) | `America/Tijuana` | Zona horaria del contenedor (logs, procesos SO) |
| Django (`TIME_ZONE`) | `env('DJANGO_TIME_ZONE', default='America/Tijuana')` | Zona horaria para Django templates/forms |
| Django (`USE_TZ`) | `True` | Django maneja datetimes con timezone awareness |
| PostgreSQL sesión (`default` DB) | `-c timezone=America/Tijuana` | CURRENT_TIMESTAMP devuelve hora local |
| PostgreSQL sesión (`backend` DB) | `-c timezone=America/Tijuana` | CURRENT_TIMESTAMP devuelve hora local (consistente con Java) |
| `.env.example` | `DJANGO_TIME_ZONE=America/Tijuana` | Variable de entorno documentada |

### Flujo de timestamps

```
INSERT sin timestamp explícito
    → Django NO envía campo timestamp (sin auto_now_add)
    → PostgreSQL ejecuta DEFAULT CURRENT_TIMESTAMP
    → CURRENT_TIMESTAMP = hora local America/Tijuana (por sesión timezone)
    → Resultado: 00:47 (igual que Java)
```

### Cambios en código

1. **`sanfelipe/settings/__init__.py`**:
   - Variable `tz` leída de `DJANGO_TIME_ZONE` antes de DATABASES
   - Ambas conexiones PostgreSQL incluyen `-c timezone={tz}`
   - `TIME_ZONE = tz` (reutiliza la misma variable)

2. **`tramites/models/actividades.py`**:
   - Campo `timestamp` sin `auto_now_add=True`
   - `editable=False, blank=True` — PostgreSQL maneja el default

3. **`tramites/admin.py`**:
   - `_display_timestamp()` usa `tz.localtime()` antes de `strftime()`

4. **`templates/admin/tramite_detail.html`**:
   - Timestamps usan `|localtime|date:"Y-m-d H:i:s"` — conversión explícita + formato unificado

### Consecuencias

* Bueno, porque los timestamps de Django y Java son consistentes en la misma tabla
* Bueno, porque respeta el diseño original de las tablas sin requerir migraciones SQL
* Bueno, porque la zona horaria es configurable via variable de entorno para futuras deployments
* Malo, porque Django pierde la capacidad de auto-llenar el campo timestamp (no se puede usar `auto_now_add`)
* Malo, porque las lecturas de timestamps desde la DB backend requieren `localtime()` explícito en el admin (los templates con `|date` ya convierten automáticamente con `USE_TZ=True`)

---
Formato basado en [MADR](https://adr.github.io/madr/)
