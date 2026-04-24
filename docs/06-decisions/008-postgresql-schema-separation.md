# 003: PostgreSQL Schema Separation for Multi-Database Architecture

**Date:** 2026-04-14
**Status:** Draft
**Supersedes:** 002-configuracion-multiples-bases-de-datos.md

## Context

The Backoffice Trámites project uses a PostgreSQL database with schema separation instead of previous dual-database architecture (SQLite + PostgreSQL). All database connections now use PostgreSQL, but are logically separated by schema:

- **backoffice schema** (formerly "default" database): Django auth, admin, sessions, and `AsignacionTramite` table
- **public schema** (formerly "backend" database): Business legacy tables (tramites, catalogos, costos, bitacora, actividades)

This separation provides:
- Single PostgreSQL server with logical data isolation
- Simplified backup and maintenance
- Cross-schema joins are still prevented to maintain data integrity
- Different access patterns: read-only legacy data vs. managed Django data

## Decision

### Database Schema Mapping

| Database Alias | Schema | Purpose | Access Pattern |
|---------------|---------|---------|----------------|
| `default` | `backoffice` | Django auth, admin, sessions, `AsignacionTramite` | Full read/write, migrations allowed |
| `backend` | `public` | Business legacy tables (tramites, catalogos, relaciones) | Mixed (see per-model rules below) |

### Access Patterns

The project defines three access patterns for database models:

- **FULL_ACCESS**: All CRUD operations permitted (Create, Read, Update, Delete). Used for managed Django data.
- **READ_ONLY**: Only read operations permitted. All writes (Create, Update, Delete) are forbidden. Used for reference catalog tables that should never be modified by the application.
- **APPEND_ONLY**: Read and Create operations permitted, but Update and Delete are forbidden. Used for append-only transaction logs where historical records must remain immutable (e.g., Actividades table).

### Per-Model Migration and Access Rules

#### 1. Actividades (`tramites/models/actividades.py`)
- **Database:** `backend` (public schema)
- **Access:** APPEND_ONLY (Read and Create permitted, Updates and Delete forbidden)
- **Migrations:** FORBIDDEN
- **Managed:** `False` (production), `True` (testing only)
- **Table:** `actividades`
- **Use Case:** Transactional logging for tramite status changes

#### 2. AsignacionTramite (`tramites/models/asignacion.py`)
- **Database:** `default` (backoffice schema)
- **Access:** Full read/write
- **Migrations:** ALLOWED
- **Managed:** `True`
- **Table:** `asignacion_tramite`
- **Use Case:** Manages analyst assignments, stores cross-schema references via IntegerField
- **Special Notes:** Only Django model in default schema besides auth tables

#### 3. Catalog Models (`tramites/models/catalogos.py`)
Includes: `TramiteCatalogo`, `TramiteEstatus`, `Perito`, `Actividad`, `Categoria`, `Requisito`, `Tipo`

- **Database:** `backend` (public schema)
- **Access:** STRICTLY READ-ONLY
- **Migrations:** FORBIDDEN
- **Managed:** `False` (production), `True` (testing only)
- **Tables:** `cat_tramite`, `cat_estatus`, `cat_perito`, `cat_actividad`, `cat_categoria`, `cat_requisito`, `cat_tipo`
- **Use Case:** Reference data managed externally, cached in process memory

#### 4. Relationship Models (`tramites/models/relaciones.py`)
Includes: `TramiteCatalogoCategoria`, `TramiteCatalogoRequisito`, `TramiteCatalogoTipoRequisito`, `TramiteCatalogoActividad`

- **Database:** `backend` (public schema)
- **Access:** STRICTLY READ-ONLY
- **Migrations:** FORBIDDEN
- **Managed:** `False` (production), `True` (testing only)
- **Tables:** `rel_tmt_categoria`, `rel_tmt_cate_req`, `rel_tmt_tipo_req`, `rel_tmt_actividad`
- **Use Case:** Many-to-many pivot tables for catalog relationships

#### 5. Tramite (`tramites/models/tramite.py`)
- **Database:** `backend` (public schema)
- **Access:** STRICTLY READ-ONLY (status derived from Actividades)
- **Migrations:** FORBIDDEN
- **Managed:** `False` (production), `True` (testing only)
- **Table:** `tramite`
- **Use Case:** Main business entity, status derived from latest `Actividades` record

#### 6. Django Built-in Apps
Includes: `auth`, `contenttypes`, `admin`, `sessions`, `messages`, `staticfiles`, `debug_toolbar`

- **Database:** `default` (backoffice schema)
- **Access:** Full read/write
- **Migrations:** ALLOWED
- **Managed:** `True`
- **Use Case:** Django framework tables, authentication, admin interface

### Routing and Access Control System

The project uses a model-based routing system that explicitly configures each model's database and access pattern through a `@register_model` decorator. The ModelBasedRouter routes queries based on this model configuration, not on app labels, allowing mixed models within the same Django app to be routed to different databases. The router also validates relationships to prevent foreign key constraints across schemas.

Custom managers enforce access patterns at the ORM level. ReadOnlyManager prevents all write operations and raises RuntimeError when any create, update, or delete is attempted. CreateOnlyManager allows record creation but blocks updates and deletions, also raising RuntimeError on forbidden operations. Models requiring full access use Django's default Manager without custom restrictions.

A migration guard overrides the standard `makemigrations` command to check each model's configuration before generating migrations. Models configured as READ_ONLY or APPEND_ONLY trigger a RuntimeError with a descriptive message labeled "Read-Only Constraint Violation," preventing accidental migration generation for protected legacy tables.

### Database Router Rules

The `core.db_router.ModelBasedRouter` enforces these rules:

1. **Read operations:** Routes to configured database via `@register_model` decorator
2. **Write operations:** Routes to same database as read operations (consistency)
3. **Migration permissions:** Controlled by ModelConfig.allow_migrations flag
4. **Relation permissions:** Relations allowed only within same schema (same db_alias)

### Cross-Schema References

**AsignacionTramite pattern:**
- Stores `tramite_id` as `IntegerField` (no Django FK to Tramite)
- Stores `analista` and `asignado_por` as real Django FKs to User (same database)
- Allows safe cross-schema lookups without FK constraints
- Application code must explicitly use `.using('backend')` for cross-database queries

### Cache Configuration

**Production:**
- **Backend:** LocMemCache (in-memory cache)
- **Catalog data:** ReadOnlyManager enforces access, data loaded from fixtures in tests

**Testing:**
- **Backend:** In-memory SQLite for all tests
- **Fixture loading:** `catalog_fixtures` fixture loads test data from `fixtures/backend.json`

### Schema Validation

Schema validation is critical for maintaining synchronization between Django models and PostgreSQL schema. The `core.schema_validator` module should be run before commits and after receiving SQL schema changes.

## Consequences

### Positive

- **Simplified architecture:** Single PostgreSQL server instead of multiple database types
- **Logical separation:** Clear data isolation via schemas
- **Backward compatibility:** Existing queries using `.using('backend')` continue to work
- **Easier operations:** Single backup strategy, single connection pool
- **Clear access patterns:** Explicit rules prevent accidental modifications to legacy data
- **Model-based routing:** Fine-grained control per model, not per app

### Negative

- **Complex migrations:** AsignacionTramite is the only business model with migrations, but is in different schema
- **Cross-schema limitations:** Cannot use Django FK joins between `AsignacionTramite` and Tramite
- **Schema awareness:** Developers must understand schema separation and use correct `.using()` calls
- **Testing complexity:** Test database must create both schemas or use in-memory SQLite
- **Explicit configuration required:** All models must be registered with `@register_model` decorator

### Risks and Mitigations

| Risk | Mitigation |
|-------|------------|
| Accidental writes to legacy tables | Strict enforcement of read-only rules via custom managers and code reviews |
| Schema drift between models and PostgreSQL | Mandatory schema validation in CI/CD and before commits |
| Cross-schema relation attempts | Database router prevents cross-schema FK relations, code must use IntegerField pattern |
| Cache invalidation issues | Proper signal-based cache invalidation on Tramite and Actividades changes |
| Accidental migration generation | Migration guard raises "Read-Only Constraint Violation" for protected models |

## Migration Strategy from Dual-Database Architecture

### Phase 1: Code Updates
1. Update `managed` attributes in catalog models to `False` (production)
2. Update `managed` attributes in relationship models to `False` (production)
3. Verify `managed` in Actividades is conditionally `True` (testing) / `False` (production)
4. Verify `managed` in Tramite is conditionally `True` (testing) / `False` (production)
5. Update all code comments and documentation to reflect PostgreSQL schema separation

### Phase 2: Configuration Updates
1. Update `.env.example` with PostgreSQL URLs and schema parameters
2. Update `.env` with actual PostgreSQL server URLs
3. Update cache configuration to use LocMemCache instead of DatabaseCache
4. Delete deprecated `db/db.sqlite3` file

### Phase 3: Database Migration
1. Export existing auth/admin data from SQLite (if any exists)
2. Create backoffice schema in PostgreSQL (if not exists)
3. Import auth/admin data to backoffice schema
4. Validate schema with `core.schema_validator`
5. Run migrations on default database only (backoffice schema)

### Phase 4: Documentation Updates
1. Update README.md architecture table
2. Update ADR-002 to reference this new architecture
3. Update environment variables documentation
4. Update all code comments and docstrings

## Alternatives Considered

### Alternative 1: Separate PostgreSQL Databases (Rejected)
- **Description:** Use two separate PostgreSQL databases instead of schemas
- **Rejected because:** Adds complexity to backups, connection pooling, and maintenance
- **Current approach:** Schema separation is cleaner and maintains same benefits

### Alternative 2: Single Schema (Rejected)
- **Description:** Put all tables in single schema, use Django for all migrations
- **Rejected because:** Legacy tables must remain externally managed, cannot risk accidental modifications
- **Current approach:** Schema separation with `managed=False` provides necessary protection

### Alternative 3: Foreign Keys Across Schemas (Rejected)
- **Description:** Allow real Django FKs between AsignacionTramite and Tramite
- **Rejected because:** Django doesn't support cross-database FK joins, would cause runtime errors
- **Current approach:** IntegerField pattern with explicit `.using()` calls is safe and documented

## Related Documentation

- [ADR-002: Configuración de múltiples bases de datos](002-configuracion-multiples-bases-de-datos.md) - Superseded by this ADR
- [Schema Validator Guide](../SCHEMA_VALIDATOR.md) - Critical for maintaining model synchronization
- [Database Router Implementation](../../core/db_router.py) - Enforces these rules
- [Environment Variables Reference](../05-reference/configuration/environment-vars.md) - Database URL configuration
