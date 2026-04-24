# 010: Remoción del Modelo AsignacionTramite

**Date:** 2026-04-24
**Status:** Accepted

## Context

El proyecto incluía un modelo `AsignacionTramite` en `tramites/models/asignacion.py` que gestionaba las asignaciones de trámites a analistas. Este modelo fue diseñado durante la fase inicial del proyecto cuando existía una arquitectura de doble base de datos (SQLite + PostgreSQL) y era necesario almacenar las asignaciones en SQLite (`default`) mientras los trámites residían en PostgreSQL (`backend`).

El modelo incluía:
- Campos `tramite_id` (IntegerField), `analista` (FK a User), `asignado_por` (FK a User)
- Métodos `asignar()` y `liberar()` con raw SQL y savepoints
- UniqueConstraint para garantizar una sola asignación por trámite
- Migración `0003_asignaciontramite.py`

## Decision

Eliminar completamente el modelo `AsignacionTramite` y todas sus referencias, incluyendo:

1. **Código fuente:** `tramites/models/asignacion.py` (286 líneas)
2. **Migración:** `tramites/migrations/0003_asignaciontramite.py`
3. **Imports:** En `tramites/admin.py` y `tramites/models/__init__.py`
4. **Tests:** Referencias en `tests/sanfelipe/test_db_router.py`

## Rationale

El modelo `AsignacionTramite` es redundante porque la asignación de trámites ya se maneja completamente por el modelo `Tramite`:

1. **Campos denormalizados:** La vista `v_tramites_unificado` ya expone `asignado_user_id`, `asignado_username` y `asignado_nombre` directamente en el modelo `Tramite`.
2. **Método `Tramite.asignar()`:** Crea un registro en la tabla `Actividades` (estatus EN_REVISION) que actualiza automáticamente la vista materializada. No necesita una tabla intermedia.
3. **Método `Tramite.liberar()`:** Igualmente opera vía `Actividades` (estatus PRESENTADO).
4. **Arquitectura simplificada:** Con la migración a PostgreSQL con separación de esquemas (ADR-008), ya no hay necesidad de una tabla separada en SQLite para las asignaciones.

### Flujo actual (sin AsignacionTramite)

```
Tramite.asignar(analista, asignado_por, observacion)
  → Tramite.registrar_actividad(EN_REVISION, analista_id, observacion)
    → INSERT INTO actividades (tramite_id, estatus_id, backoffice_user_id, observacion)
      → v_tramites_unificado se actualiza automáticamente
        → Tramite.asignado_user_id apunta al analista
```

### AsignacionTramite nunca se usaba en runtime

Las llamadas en `tramites/admin.py` usan `tramite.asignar()` (método del modelo Tramite), no `AsignacionTramite.asignar()`. El modelo estaba importado pero nunca invocado.

## Consequences

### Positivas

- **Código más limpio:** Eliminación de ~300 líneas de código duplicado
- **Modelo de datos simplificado:** Una sola fuente de verdad para asignaciones (Actividades + vista)
- **Menos migraciones:** Se elimina la migración de una tabla que ya no se usa
- **Tests más simples:** El test de db_router ya no necesita verificar routing para un modelo eliminado

### Negativas

- **Ninguna:** El modelo no tenía uso en runtime, solo existía como código muerto

## Archivos Eliminados

| Archivo | Descripción |
|---------|-------------|
| `tramites/models/asignacion.py` | Modelo `AsignacionTramite` (286 líneas) |
| `tramites/migrations/0003_asignaciontramite.py` | Migración de la tabla |

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `tramites/models/__init__.py` | Removido import y export de `AsignacionTramite` |
| `tramites/admin.py` | Removido import de `AsignacionTramite` |
| `tests/sanfelipe/test_db_router.py` | Eliminadas referencias a `AsignacionTramite` en 4 métodos de test |

## Related Documentation

- [ADR-008: PostgreSQL Schema Separation](008-postgresql-schema-separation.md) — Arquitectura actual de base de datos
- [ADR-009: Remoción del Schema Validator](009-remove-schema-validator.md) — Otra limpieza de código legacy del prototipo
