# 018: Backoffice Multi-Departamento

**Date:** 9 de mayo de 2026
**Status:** Accepted
**Related:** [ADR-001 multi-departamento](../../../esquemas_de_dau/docs/adr/ADR-001-multi-departamento.md), [ADR-017 migraciones prohibidas](017-migraciones-django-prohibidas-produccion.md)

## Contexto y Planteamiento del Problema

El backoffice (`backoffice_tramites`) fue construido para DAU. Con la expansión multi-departamento (ADR-001), SEC y TES necesitan su propio backoffice. El backoffice se conecta a una DB PostgreSQL con dos schemas:

- `backoffice` — Django auth, admin, `core_user`, `asignacion_tramite`
- `public` — datos de negocio: `tramite`, `actividades`, catálogos, vista `v_tramites_unificado`

Cada departamento tiene tablas de negocio diferentes en su schema `public` (SEC no tiene `cat_perito`, `cat_categoria`, `cat_tipo`; TES tendrá `datos_extra JSONB`). Pero el schema `backoffice` (Django) es idéntico en estructura para todos.

## Opciones Consideradas

- **Opción A:** Un solo backoffice multi-tenant (un Django, Router por depto)
- **Opción B:** Instancias independientes por depto (mismo codebase, diferente `.env`, diferente DB)

## Resultado de la Decisión

Opción elegida: **"B — Instancias independientes"**, porque requiere ~3h de setup vs ~20h para multi-tenant (sin refactor de routers, sin auth compartida, sin middleware de tenancy).

### Arquitectura

```
┌──────────────────────────────────────────────────┐
│  MISMA IMAGEN Docker (backoffice-tramites:latest) │
├──────────────┬──────────────┬────────────────────┤
│  .env.dau    │  .env.sec    │  .env.tes          │
│  POSTGRESQL_ │  POSTGRESQL_ │  POSTGRESQL_       │
│  DB_URL=...  │  DB_URL=...  │  DB_URL=...        │
│  DB=dau_db   │  DB=sec_db   │  DB=tes_db         │
├──────────────┼──────────────┼────────────────────┤
│  :8090       │  :8091       │  :8092             │
└──────────────┴──────────────┴────────────────────┘
```

### Diferencias entre departamentos

Cada instancia se diferencia **únicamente** por su archivo `.env`:

| Aspecto | Mecanismo | Configuración |
|---|---|---|
| DB destino | `POSTGRESQL_DB_URL` | Apunta a `dau_db` / `sec_db` / `tes_db` |
| Branding | `BACKOFFICE_SITE_*` (tenancy.py) | Título, header, logo por depto |
| Transiciones deshabilitadas | `BACKOFFICE_DISABLED_TRANSITIONS` (nueva env var) | Lista de IDs a excluir del dict TRANSITIONS |
| Vista de trámites | Diferente SQL por DB | `v_tramites_unificado` adaptada en cada DB |
| Folio prefix | GUC `app.depto_prefix` | `ALTER DATABASE sec_db SET app.depto_prefix = 'SEC';` |

### Lo que NO cambia

- **Mismo código** — cero `if depto == X` en el codebase
- **Mismos modelos Django** — los campos DAU-specific que no existen en SEC reciben NULL (ya son `null=True, blank=True`) excepto `es_propietario` donde la vista SEC retorna `FALSE`
- **Mismo SFTP regex** — `FOLIO_REGEX = ^[A-Z]+-\d{6}-[A-Z]{4}-[A-Z]$` ya matchea SEC/TES
- **Mismos tests** — los tests usan SQLite con `managed=True`

### `BACKOFFICE_DISABLED_TRANSITIONS`

Nueva variable de entorno que filtra el dict `TRANSITIONS` en `tramite.py`.

- Los IDs listados se eliminan de las transiciones permitidas al momento de validar, por lo que las acciones correspondientes no aparecen en la UI ni son ejecutables vía API.
- Los valores se convierten de `str` a `int` al cargar settings para comparación correcta con las llaves de `TRANSITIONS`.
- La verificación se hace en tiempo de llamada (no muta el dict `TRANSITIONS`), permitiendo tests aislados con `@override_settings`.
- SEC deshabilita EN_DILIGENCIA (estatus 205). DAU tiene todas las habilitadas (default).

Ver `PLAN.md` Fase 1 para los detalles de implementación.

### Vista `v_tramites_unificado` por depto

Cada DB tiene su propia versión de la vista en `backoffice.v_tramites_unificado`:

- **DAU:** Versión actual V1.3.0 — JOINs a `cat_perito`, `cat_categoria`, `cat_tipo`; integer cast en `tramite.tipo`
- **SEC:** Sin JOINs a `cat_perito`/`cat_categoria`/`cat_tipo`; `tramite.tipo` como VARCHAR directo; NULLs cast para columnas DAU-specific (`clave_catastral`, etc.); `FALSE` para `es_propietario` (campo no nullable)
- **TES:** Pendiente de definición

Todas devuelven las mismas columnas (mismos nombres, mismos tipos) para que el modelo `Tramite` de Django funcione sin cambios.

### Bootstrap de nuevo departamento

Ver [ADR-017](017-migraciones-django-prohibidas-produccion.md). Las tablas del schema `backoffice` se crean vía migration SQL (no `manage.py migrate`). Procedimiento:

1. Crear la DB con el schema `public` (tablas de negocio + seed data).
1. Aplicar migration SQL que crea el schema `backoffice` con todas las tablas Django.
1. Aplicar migration SQL que crea la vista `v_tramites_unificado` adaptada.
1. Crear `.env.depto` con `POSTGRESQL_DB_URL` apuntando a la nueva DB.
1. Levantar la instancia Docker con el `.env.depto`.
1. Crear superuser y roles vía `manage.py createsuperuser` + `setup_roles`.

## Consecuencias

- **Bueno, porque** cada departamento opera 100% independiente (sin shared state).
- **Bueno, porque** levantar un nuevo depto es copiar `.env` + aplicar 3-4 scripts SQL.
- **Bueno, porque** no hay refactor de código — solo configuración.
- **Bueno, porque** el aislamiento de datos es físico (DBs separadas).
- **Malo, porque** cada instancia consume memoria independiente (Gunicorn workers × 3).
- **Malo, porque** bug fixes deben desplegarse en N instancias (misma imagen, distinto deploy).
- **Malo, porque** reportes consolidados municipio requieren ETL externo.

______________________________________________________________________

## Ver también

- [ADR-001 multi-departamento](../../../esquemas_de_dau/docs/adr/ADR-001-multi-departamento.md) — Decisión general de plataforma
- [ADR-017 migraciones prohibidas](017-migraciones-django-prohibidas-produccion.md) — Sin migrate en producción
- [ADR-008 PostgreSQL schema separation](008-postgresql-schema-separation.md) — Separación backoffice/public
- [Variables de entorno](../05-DEVELOPERS/environment-vars.md) — Referencia completa de env vars
