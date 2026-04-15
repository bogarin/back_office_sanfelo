# 002: Configuración de múltiples bases de datos y routers

**Fecha:** 26 de febrero de 2026
**Estado:** Superseded
**Superseded by:** [ADR-008: PostgreSQL Schema Separation for Multi-Database Architecture](003-postgresql-schema-separation.md)

## Contexto

El microservicio requiere manejar dos bases de datos distintas:
- **SQLite**: Para autenticación, permisos (RBAC) y Django Admin
- **PostgreSQL**: Para datos de negocio (tramites, catalogos, costos, bitacora) que son parte de una base de datos legacy

La configuración debe asegurar:
- Que las aplicaciones de negocio usen PostgreSQL
- Que Django admin y auth usen SQLite  
- Que no se ejecuten migraciones en PostgreSQL (datos managed externamente)
- Que se permitan relaciones dentro de cada BD pero no entre ellas

## Decision

Se ha decidido utilizar una configuración de múltiples bases de datos con routers personalizados:

1. **Configuración de DATABASES** en settings.py con dos conexiones:
   - `default`: SQLite para auth/admin
   - `business`: PostgreSQL para datos de negocio

2. **BusinessDatabaseRouter** para enrutar aplicaciones de negocio a PostgreSQL:
   - Apps: tramites, catalogos, costos, bitacora
   - Migraciones desactivadas para estas apps (`managed=False`)

3. **Permisos de relación**:
   - Relaciones permitidas dentro de PostgreSQL (apps de negocio)
   - Relaciones permitidas dentro de SQLite (apps de auth)
   - No se permiten relaciones cruzadas entre BDs

## Consequences

**Positivas:**
- Aislamiento lógico entre datos de sistema y negocio
- Mantenimiento de la base de datos legacy sin modificaciones
- Configuración clara de enrutamiento

**Negativas:**
- Complejidad en consultas que involucran múltiples BDs
- Necesidad de manejar dos conexiones de base de datos
- Posibles problemas de consistencia transaccional

## Schema Validation

Dado que PostgreSQL usa esquema externo gestionado por terceros, **es crítico mantener sincronizados los modelos Django con el esquema SQL**.

**Herramienta de validación:**
- **`core/schema_validator.py`**: Valida que los modelos Django coincidan con PostgreSQL
- Documentación completa: [docs/SCHEMA_VALIDATOR.md](../SCHEMA_VALIDATOR.md)

**Cuándo ejecutar:**
- Antes de cada commit que afecte modelos de negocio
- Después de recibir scripts SQL actualizados del equipo externo
- En pipeline de CI/CD para prevenir desincronización en producción

**Comando:**
```bash
uv run python -m core.schema_validator
```

**Ejemplo de salida:**
```
============================================================
SCHEMA VALIDATION REPORT
============================================================
⚠️  Warnings (1):
  - Max length mismatch for CatTramite.nombre: Django=255, SQL=100

❌ Errors (0):
✅ All models are synchronized with database schema!
```

## Risks and Mitigations

- **Consultas cruzadas**: No se permiten relaciones entre BDs, reduciendo complejidad
- **Migraciones en PostgreSQL**: Desactivadas explícitamente para evitar modificaciones
- **Configuración compleja**: Documentación clara en settings.py y routers.py
- **Rendimiento**: Uso de índices optimizados en PostgreSQL para consultas de negocio

## Alternatives Considered

- **Single database with schema separation**: Descartado por complejidad de manejo y riesgos de modificación de schema legacy
- **Separate microservices**: Descartado por overhead de comunicación y complejidad

## Superseded by

(ninguno)