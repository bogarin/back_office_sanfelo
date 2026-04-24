# 011: Limpieza y Reestructuración de Documentación

**Fecha:** 23 de abril de 2026
**Estado:** Accepted
**Supersedes:** Ninguno

## Contexto

El proyecto experimentó cambios significativos desde su inicio. La documentación acumulada durante los primeros meses (~16,000 líneas en 53 archivos) fue generada en gran parte por agentes LLM basándose en requisitos técnicos de alto nivel (`REQUERIMIENTOS_ALTO_NIVEL.md`) que describían un stack tecnológico diferente (FastAPI, SQLAlchemy, Keycloak, Kong, Redis, REST API) al que finalmente se construyó (Django Admin, PostgreSQL schemas, LocMemCache, SFTP).

**Problemas identificados:**

- ~70% de la documentación describía una arquitectura que nunca se construyó
- Archivos de proceso/metodología (RESTRUCTURING_PLAN, TASKS, PROGRESO, etc.) ocupaban ~4,000 líneas sin valor técnico
- Redundancia: múltiples archivos documentando las mismas variables de entorno
- Referencias rotas: links a archivos y directorios que no existían
- Directorios vacíos creados por un plan de reestructuración que nunca se completó

**Decisión previa:** ADR-001 definía SQLite + PostgreSQL. ADR-008 migró a PostgreSQL con schema separation. La documentación nunca se actualizó para reflejar este cambio.

## Decisión

Ejecutar una limpieza completa con los siguientes criterios:

### Eliminados (archivos que describen sistema no construido o metadocumentación obsoleta)

| Archivo | Líneas | Razón |
|---------|--------|-------|
| `02-tutorials/developers/first-api-call.md` | 606 | No existe REST API |
| `RESTRUCTURING_PLAN.md` | 1,017 | Plan basado en arquitectura ficticia |
| `EXECUTIVE_SUMMARY.md` | 285 | Resumen de arquitectura ficticia |
| `PROGRESO.md` | 384 | Tracking de plan anterior |
| `TASKS.md` | 506 | Tareas de plan anterior |
| `METHODOLOGIES_QUICKREF.md` | 468 | Referencia arquitectura ficticia |
| `README_MAP.md` | 341 | Mapa de docs inexistentes |
| `QUICKSTART.md` | 425 | Proceso de dirs, no contenido útil |
| `VISUAL_DIAGRAM.md` | 312 | Diagramas de arquitectura ficticia |
| `SCRIPTS_REMOVAL.md` | 287 | Información integrada |
| `ENV_VARS_IMPLEMENTATION.md` | 282 | Consolidado en reference |
| `ENVIRONMENT_VARIABLES.md` | 51 | Redirect eliminado |

**Total eliminado: ~4,963 líneas**

### Directorios vacíos eliminados

- `04-concepts/`, `07-maintenance/`, `08-ai-optimized/`, `decisiones/`
- Subdirectorios vacíos: `03-guides/developers/`, `05-reference/api/`, `05-reference/models/`, `05-reference/components/`, `05-reference/commands/`

### Movidos y reorganizados

| Origen | Destino | Razón |
|--------|---------|-------|
| `REQUERIMIENTOS_ALTO_NIVEL.md` | `00-system-design/` | Reqs de negocio válidos, tech specs obsoletos |
| `DJANGO_ADMIN_SETUP.md` | `05-reference/admin-setup.md` | Referencia técnica |
| `MODEL_MAPPINGS.md` | `05-reference/models.md` | Referencia técnica |
| `ESTADOS-TRAMITES.md` | `05-reference/estados-tramites.md` | Referencia técnica |
| `SFTP-FILE-SERVING.md` | `05-reference/sftp.md` | Referencia técnica |
| `sftp-host-key.md` | `03-guides/sysadmins/sftp-setup.md` | Guía práctica |
| `05-reference/commands/index.md` | `05-reference/commands.md` | Aplanar estructura |

### Deprecados

- `SCHEMA_VALIDATOR.md` — El feature se depreca (fue diseñado para SQLite, ya no aplica)

### Actualizados (pedagogía preservada, contenido corregido)

- `01-onboarding/architecture-overview.md` — Arquitectura real
- `01-onboarding/overview.md` — Sistema real
- `01-onboarding/glossary.md` — Tecnología real
- `03-guides/sysadmins/deploy-production.md` — Despliegue real

### Nuevos ADRs creados

- **ADR-012**: Stack tecnológico actualizado (supersede ADR-001)
- **ADR-013**: RBAC de tres roles (supersede ADR-007)

## Consecuencias

### Positivas

- Documentación alineada con el código real
- ~5,000 líneas de ruido eliminadas
- Estructura plana y navegable
- ADRs reflejan decisiones actuales

### Negativas

- Pérdida de contexto histórico (mitigado: ADRs originales se conservan como superseded)
- Alguna información pedagógica en onboarding requiere reescritura completa

## Lecciones Aprendidas

1. **No generar documentación antes de que el código exista** — Los agentes LLM generaron miles de líneas describiendo un sistema planeado, no construido
2. **Los ADRs son la fuente de verdad** — Cuando el código cambia, los ADRs deben actualizarse primero
3. **Documentación de proceso es desechable** — TASKS, PROGRESO, PLANS son útiles durante la ejecución pero no como documentación permanente

## Referencias

- [ADR-001: Stack base original](001-seleccion-stack-base.md) (superseded)
- [ADR-007: RBAC original](007-implementacion-rbac-django-60.md) (superseded)
- [ADR-008: PostgreSQL Schema Separation](008-postgresql-schema-separation.md)
- [ADR-012: Stack actualizado](012-stack-base-actualizado.md)
- [ADR-013: RBAC tres roles](013-rbac-tres-roles.md)
