# 003: Estrategia de caching y rendimiento

**Fecha:** 26 de febrero de 2026  
**Estado:** Propuesto

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

(ninguno)