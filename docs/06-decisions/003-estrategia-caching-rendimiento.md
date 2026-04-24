# 003: Estrategia de caching y rendimiento

**Fecha:** 26 de febrero de 2026
**Estado:** Parcialmente superseded
**Última actualización:** 23 de abril de 2026

## Contexto

El microservicio necesita manejar un baseline de 50 usuarios simultáneos con buen rendimiento. Las operaciones principales son:
- Lecturas frecuentes de catálogos y tramites (PostgreSQL)
- Consultas de autenticación y permisos (SQLite)
- Operaciones de administración (Django Admin)

Se requiere una estrategia de caching que:
- Mejore el rendimiento de lecturas frecuentes
- Sea configurable por entorno (desarrollo vs producción)
- No añada complejidad innecesaria
- Permita escalado horizontal si es necesario

## Decision

Se ha decidido utilizar la siguiente estrategia de caching:

1. **Caching por entorno**:
   - **Desarrollo y Testing**: `DummyCache` (sin almacenamiento, rápido para desarrollo)
   - **Producción**: `LocMemCache` (caching en memoria local, sin dependencias externas)

2. **Optimización de SQLite**:
   - Configuración de parámetros de rendimiento para producción
   - Uso de índices optimizados en modelos
   - Mantener consultas simples en SQLite

3. **Caching de Django**:
   - Uso de cache para consultas frecuentes a catálogos
   - Posibilidad de integrar Redis en el futuro si es necesario

4. **Escalado horizontal**:
   - Uso de múltiples contenedores Docker con balanceo de carga
   - Configuración de gunicorn con múltiples workers y threads

## Consequences

**Positivas:**
- Mejora significativa del rendimiento para lecturas frecuentes
- Simplificación del despliegue (sin dependencias de caching externas inicialmente)
- Configuración adaptable a diferentes entornos

**Negativas:**
- Limitaciones de escalabilidad del caching en memoria local
- Posible necesidad de migrar a Redis en el futuro
- Complejidad en la invalidación de cache

## Risks and Mitigations

- **Rendimiento de SQLite**: Optimización de parámetros de configuración y uso de índices
- **Escalabilidad del caching**: Posibilidad de migrar a Redis si el volumen de datos lo requiere
- **Invalidación de cache**: Estrategia clara de timeout y invalidación manual cuando sea necesario
- **Complejidad**: Mantener la configuración simple inicialmente, agregar complejidad solo cuando sea necesario

## Alternatives Considered

- **Redis Cache**: Descartado inicialmente por complejidad y dependencias adicionales
- **Database-level caching**: Descartado por riesgos de consistencia y complejidad
- **No caching**: Descartado por impacto en rendimiento con 50 usuarios simultáneos

## Superseded by

Este ADR ha sido **parcialmente superseded** por [ADR-009: Vista PostgreSQL Unificada para Trámites](009-vista-postgresql-para-tramites.md).

**Estatus:** Parcialmente superseded
**Fecha de actualización:** 2026-04-23

**Detalles de la supersección parcial:**

### Componentes que permanecen válidos:
- **Caching por entorno:** Configuración de DummyCache (desarrollo/testing) y LocMemCache (producción) sigue siendo el fundamento de la arquitectura
- **Optimización de SQLite:** Aunque ADR-008 migró a PostgreSQL con esquemas, los principios de optimización de base de datos siguen aplicando
- **Escalado horizontal:** Estrategia de múltiples contenedores Docker y configuración de gunicorn permanece válida

### Componentes expandidos en ADR-009:

**Arquitectura de cache expandida de 1 nivel a 4 niveles:**

1. **Process-level cache (`@lru_cache`)** - Nuevo en ADR-009
   - Manager: `CachedCatalogManager`
   - Uso: Catálogos read-only que cambian raramente
   - Alcance: Por worker process de Django
   - Timeout: Permanente (hasta reinicio del worker)

2. **Django Cache Framework** - Expandido desde ADR-003
   - Manager: `CachedReadOnlyManager` (nuevo)
   - Backend: LocMemCache (mantiene configuración de ADR-003)
   - Timeout: 1 hora (3600 segundos) - más específico que ADR-003
   - Keys: `'sf_tramites:catalog:v1:{model_name}:all'`

3. **Redis-based cache** - Nuevo en ADR-009
   - Caché de métricas: `estatus_distribution` con 60s TTL
   - Invalidación vía signals Django (`post_save`, `post_delete`)
   - Implementa la "posibilidad de integrar Redis" mencionada en ADR-003

4. **Request-level cache** - Nuevo en ADR-009
   - Middleware: `CacheUserRolesMiddleware`
   - Carga roles de usuario una vez por request
   - Almacenamiento: `request.user.roles` como `set`

### Impacto en decisiones:

- **Riesgo "Escalabilidad del caching"** en ADR-003 fue mitigado mediante implementación de Redis en ADR-009
- **Riesgo "Invalidación de cache"** en ADR-003 fue abordado con signals de invalidación consistentes en ADR-009
- **Trade-off "Limitaciones de escalabilidad del caching en memoria local"** en ADR-003 fue resuelto con Redis en ADR-009

### Recomendación:
Para detalles completos de la implementación actual de cache, referirse a [ADR-009](009-vista-postgresql-para-tramites.md). Este documento se mantiene como referencia histórica de la arquitectura inicial de caching del proyecto.