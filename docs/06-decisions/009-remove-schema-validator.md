# 009: Remoción del Schema Validator

**Date:** 2026-04-23
**Status:** Accepted
**Supersedes:** N/A

## Context

El proyecto incluía un módulo `core.schema_validator` que validaba que los modelos Django estuvieran sincronizados con el esquema externo de PostgreSQL. Este módulo constaba de:

- `core/schema_validator.py` — Clase `SchemaValidator` que comparaba modelos Django contra columnas de PostgreSQL usando `information_schema`.
- `core/management/commands/validate_schema.py` — Management command `validate_schema` para ejecutar la validación desde CLI.
- `docs/SCHEMA_VALIDATOR.md` — Documentación completa del validador.

El validador fue diseñado durante la fase de prototipo del proyecto, cuando existía una arquitectura de doble base de datos (SQLite + PostgreSQL) y el riesgo de desincronización entre modelos y esquema SQL era alto.

## Decision

Eliminar completamente el schema validator del proyecto, incluyendo:

1. **Código fuente:** `core/schema_validator.py` y `core/management/commands/validate_schema.py`
2. **Documentación:** `docs/SCHEMA_VALIDATOR.md`
3. **Referencias en ADRs:** Actualizar ADR-008 para eliminar menciones al schema validator y actualizar la mitigación de "Schema drift" en la tabla de riesgos.
4. **Exports:** Actualizar `core/__main__.py` para remover `schema_validator` del `__all__`.

## Rationale

El schema validator perdió utilidad por las siguientes razones:

1. **Evolución del proyecto:** Fue útil durante el prototipo cuando el esquema cambiaba frecuentemente y no existía un proceso formal de sincronización.
2. **Arquitectura madura:** Con la migración a PostgreSQL con separación de esquemas (ADR-008), el esquema es más estable y los cambios se coordinan manualmente.
3. **Validación limitada:** El validador solo comparaba tipos y nullability, pero no detectaba problemas semánticos ni problemas en vistas materializadas como `v_tramites_unificado`.
4. **Sin integración CI/CD:** Nunca se integró en un pipeline automatizado, por lo que solo se ejecutaba manualmente y de forma esporádica.

La sincronización modelo-esquema se realiza ahora mediante:

- Revisión manual cuando se reciben cambios de esquema del equipo externo
- Code review en los PRs que afectan modelos
- Pruebas de integración que validan que los queries funcionan contra la base de datos real

## Consequences

### Positivas

- **Código más limpio:** Eliminación de ~320 líneas de código no utilizado
- **Menos mantenimiento:** No hay que actualizar el validador cuando cambian los modelos
- **Documentación más precisa:** Los docs ya no referencian una herramienta que no se usaba

### Negativas

- **Sin validación automática:** No existe un mecanismo automático para detectar desincronización modelo-esquema
- **Riesgo de drift:** Cambios en el esquema PostgreSQL podrían pasar desapercibidos hasta producción

### Mitigación

El riesgo de desincronización se mitiga mediante:

- Pruebas de integración que ejecutan queries contra la base de datos real
- Proceso manual de revisión cuando se reciben cambios de esquema
- Monitoreo en producción que detecta errores de query

## Archivos Eliminados

| Archivo | Descripción |
|---------|-------------|
| `core/schema_validator.py` | Clase `SchemaValidator` (301 líneas) |
| `core/management/commands/validate_schema.py` | Management command (16 líneas) |
| `docs/SCHEMA_VALIDATOR.md` | Documentación del validador (305 líneas) |

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `core/__main__.py` | Removido `schema_validator` de `__all__` |
| `docs/06-decisions/008-postgresql-schema-separation.md` | Eliminadas menciones al schema validator (sección, referencia en risks, paso de migración, link) |
| `docs/06-decisions/002-configuracion-multiples-bases-de-datos.md` | Agregada nota en "Superseded by" referenciando este ADR |

## Related Documentation

- [ADR-002: Configuración de múltiples bases de datos](002-configuracion-multiples-bases-de-datos.md) — Contiene la sección histórica del schema validator
- [ADR-008: PostgreSQL Schema Separation](008-postgresql-schema-separation.md) — Arquitectura actual de base de datos
