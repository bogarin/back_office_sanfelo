# 017: Migraciones Django Prohibidas en Producción

**Date:** 9 de mayo de 2026
**Status:** Accepted
**Partially supersedes:** [008-postgresql-schema-separation.md](008-postgresql-schema-separation.md) (sección "Per-Model Migration and Access Rules", modelos del schema `backoffice`)
**Related:** [ADR-001 multi-departamento](../../../esquemas_de_dau/docs/adr/ADR-001-multi-departamento.md)

## Contexto y Planteamiento del Problema

ADR-008 establece que las tablas del schema `backoffice` (auth, admin, `core_user`, `asignacion_tramite`) tienen "Migrations: ALLOWED" y se gestionan vía `manage.py migrate`. Esto funciona para DAU (único departamento existente).

Con la expansión multi-departamento (ADR-001), cada departamento tiene su propia instancia backoffice conectada a su propia DB (`dau_db`, `sec_db`, `tes_db`). El cliente (Coordinación Municipal) requiere que **en producción no se ejecuten migraciones Django** — todo cambio de schema debe hacerse mediante scripts SQL versionados en `esquemas_de_dau/migrations/`.

El motivo es operativo: el equipo de sistemas del municipio no tiene experiencia con Django y prefiere manejar cambios de schema vía SQL scripts (Flyway-style) que pueden auditar, revertir y ejecutar sin dependencias de Python.

## Opciones Consideradas

* **Opción A:** Mantener `manage.py migrate` en producción (status quo de ADR-008)
* **Opción B:** Prohibir `manage.py migrate` en producción; todo cambio via DDL en `esquemas_de_dau/`
* **Opción C:** Híbrida: `manage.py migrate` solo para DAU, DDL para SEC/TES

## Resultado de la Decisión

Opción elegida: **"B — DDL exclusivo en producción"**, porque el cliente lo requiere como restricción operativa y unifica el procedimiento para todos los departamentos.

### Reglas

1. **En producción:** `managed=False` para TODOS los modelos, incluidos los del schema `backoffice` (`core_user`, `asignacion_tramite`, tablas Django built-in).
2. **Cambios de schema:** Cualquier alteración a tablas del schema `backoffice` se realiza mediante scripts SQL de migración (V/D) en `esquemas_de_dau/migrations/`, siguiendo la convención Flyway existente.
3. **Bootstrap de nuevo depto:** Las tablas del schema `backoffice` se crean con un migration SQL (ej: `V1.4.0-SEC__backoffice_schema.sql`), no con `manage.py migrate`.
4. **En desarrollo/testing:** Se mantiene `managed=True` condicional (`TESTING=True`) para que los tests funcionen con SQLite en memoria. No hay cambios aquí.
5. **`manage.py migrate` en staging:** Se puede usar como herramienta de verificación (comparar DDL generado por Django vs DDL en `esquemas_de_dau/`), pero el schema ya debe estar creado por los scripts SQL.

### Qué cambia vs ADR-008

| Aspecto | ADR-008 (antes) | Este ADR (ahora) |
|---|---|---|
| Django built-in (auth, admin, etc.) | Migrations: ALLOWED | Migrations: FORBIDDEN en producción |
| `core_user` (custom User) | Migrations: ALLOWED | Migrations: FORBIDDEN en producción |
| `asignacion_tramite` | Migrations: ALLOWED | Migrations: FORBIDDEN en producción |
| Tablas `public` schema | Migrations: FORBIDDEN | Sin cambio |
| Desarrollo/testing | managed=True condicional | Sin cambio |

### Procedimiento para cambios de schema backoffice

1. Identificar el cambio necesario en el modelo Django.
2. Generar el SQL equivalente manualmente o con `manage.py sqlmigrate` como referencia.
3. Crear migration script en `esquemas_de_dau/migrations/` con versión bump (V/D).
4. Probar en staging contra la DB correspondiente.
5. Aplicar en producción ejecutando el script SQL directamente.

## Consecuencias

* **Bueno, porque** unifica el mecanismo de cambios de schema para todos los componentes (backend Spring Boot, backoffice Django, catálogos) bajo un solo sistema de versionado SQL.
* **Bueno, porque** el equipo de sistemas del municipio puede auditar y revertir cambios sin entender Django.
* **Bueno, porque** elimina la dependencia de `manage.py migrate` en producción, reduciendo la superficie de error.
* **Malo, porque** requiere mantener el DDL manualmente sincronizado con los modelos Django. Si un modelo cambia, el SQL debe actualizarse manualmente.
* **Malo, porque** el bootstrap de un nuevo departamento requiere un DDL exacto que coincida con lo que Django espera (tablas `core_user`, `auth_group`, etc.).

### Mitigación del riesgo de drift

- Comparar el DDL generado por `manage.py sqlmigrate` con los scripts en `esquemas_de_dau/` como paso de CI/review.
- El router Django (`core/db_router.ModelBasedRouter`) ya bloquea `allow_migrate` para modelos con `allow_migrations=False`.

---

## Ver también

* [ADR-008: PostgreSQL Schema Separation](008-postgresql-schema-separation.md) — Partially superseded por este ADR
* [ADR-018: Backoffice multi-departamento](018-backoffice-multi-departamento.md) — Arquitectura multi-instancia
* [ADR-001 multi-departamento](../../../esquemas_de_dau/docs/adr/ADR-001-multi-departamento.md) — Decisión general de plataforma
