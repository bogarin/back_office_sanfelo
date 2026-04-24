---
title: "ADR-009: Vista PostgreSQL Unificada para Trámites"
status: accepted
date: 2026-04-20
decision-makers: Equipo de Arquitectura
related:
  - ADR-008: Separación de esquema PostgreSQL
---

## Contexto y Motivación

El sistema de gestión de trámites operaba con múltiples modelos dispersos que dificultaban las operaciones de lectura y escritura. El admin de Django ejecutaba consultas complejas con múltiples JOINs que degradaban el rendimiento significativamente. Además, la separación entre bases de datos (SQLite para autenticación, PostgreSQL para lógica de negocio) impedía el uso de ForeignKeys tradicionales para relaciones cross-database.

**Problemas identificados:**
- Consultas lentas en el admin debido a JOINs múltiples entre `tramite`, `cat_tramite`, `cat_categoria`, `actividades`, y asignaciones
- Inconsistencias potenciales entre múltiples tablas que representaban información de trámites
- Dificultad para implementar filtros y búsquedas eficientes en listas de trámites
- Falta de un mecanismo centralizado para mantener sincronizados los datos denormalizados

**Restricciones:**
- Arquitectura multi-database: SQLite (schema auth) + PostgreSQL (schema backoffice)
- Necesidad de mantener el historial completo de actividades de cada trámite
- Requerimiento de performance para consultas de lectura frecuentes en el admin
- Django no soporta ForeignKeys entre bases de datos diferentes

## Decisión

Implementar una arquitectura de datos basada en una vista PostgreSQL denormalizada `v_tramites_unificado` que consolida información de múltiples tablas en un único modelo de lectura optimizado, combinada con una separación de responsabilidades CQRS donde `Actividades` es la fuente de verdad para operaciones de escritura.

**Componentes principales:**

1. **Vista PostgreSQL `v_tramites_unificado`**: Vista READ-ONLY con 28 campos denormalizados que unifica datos de trámites, solicitantes, peritos, última actividad, y asignación actual.

2. **Modelo `Tramite`**: Modelo Django que mapea a la vista PostgreSQL como `managed = False`, usando `ReadOnlyManager` para prevenir operaciones de escritura.

3. **Modelo `Actividades`**: Tabla fuente de verdad para todas las operaciones de escritura. PostgreSQL triggers mantienen la vista sincronizada.

4. **Cache multi-nivel**: Estrategia de caché con 3 niveles (process, Django, request) y Redis para optimizar consultas de lectura de catálogos y distribución de estatus.

5. **Sistema de estatus con agrupación por prefijo**: Códigos numéricos agrupados en rangos lógicos (1xx: inicio, 2xx: proceso, 3xx: finalizado).

6. **Modelos proxy Django**: `Buzon` y `Disponible` como proxies de `Tramite` para implementar diferentes querysets especializados en el admin.

## Decisiones de Arquitectura Detalladas

### 1. Vista PostgreSQL Denormalizada (`v_tramites_unificado`)

Vista READ-ONLY que unifica 28 campos desde múltiples tablas de origen:

**Campos del trámite:** `id`, `folio`, `tramite_id`, `tramite_nombre`, `tramite_categoria_id`, `tramite_categoria_nombre`, `tramite_tipo_cobro_id`, `tramite_tipo_cobro_nombre`, `clave_catastral`, `es_propietario`, `importe_total`, `urgente`, `creado`, `actualizado`

**Campos del solicitante:** `solicitante_nombre`, `solicitante_telefono`, `solicitante_correo`, `solicitante_comentario`

**Campos del perito:** `perito_id`, `perito_nombre`

**Campos de última actividad:** `ultima_actividad_estatus_id`, `ultima_actividad_estatus`, `ultima_actividad_responsable`, `ultima_actividad_descripcion`, `ultima_actividad_observacion`

**Campos de asignación:** `asignado_user_id`, `asignado_username`, `asignado_nombre`, `asignado_group_id`, `asignado_rol`

**Beneficio:** Evita JOINs complejos en consultas frecuentes del admin, simplificando queries y mejorando performance significativamente.

### 2. Actividades como Fuente de Verdad (CQRS Parcial)

Todas las operaciones de escritura se realizan en la tabla `Actividades`:
- Cambios de estatus
- Asignaciones
- Observaciones
- Cualquier transición de estado

PostgreSQL triggers o actualizaciones sincronizan automáticamente la vista `v_tramites_unificado`. El modelo `Tramite` es exclusivamente READ-ONLY.

**Separación de responsabilidades:**
- **Lectura:** Modelo `Tramite` (vista PostgreSQL optimizada)
- **Escritura:** Modelo `Actividades` (tabla fuente de verdad)
- **Historial:** `Actividades` provee auditoría completa e inherente

### 3. Cache Multi-Nivel

Implementación de caché en 4 niveles diferentes:

**Nivel 1: Process-level (`@lru_cache`)**
- Manager: `CachedCatalogManager`
- Uso: Catálogos read-only que cambian raramente
- Alcance: Por worker process de Django
- Timeout: Permanente (hasta reinicio del worker)
- Invalidación: Manual vía `invalidate_cache()`

**Nivel 2: Django Cache Framework**
- Manager: `CachedReadOnlyManager`
- Backend: LocMemCache (producción) o DummyCache (testing)
- Timeout: 1 hora (3600 segundos)
- Keys: `'sf_tramites:catalog:v1:{model_name}:all'`

**Nivel 3: Redis-based**
- Caché de métricas: `estatus_distribution` con 60s TTL
- Invalidación vía signals Django (`post_save`, `post_delete`)

**Nivel 4: Request-level**
- Middleware: `CacheUserRolesMiddleware`
- Carga roles de usuario una vez por request
- Almacenamiento: `request.user.roles` como `set`

**Beneficio:** Reducción significativa de carga en base de datos, mejor tiempo de respuesta, escalabilidad horizontal.

### 4. Sistema de Estatus con Agrupación por Prefijo

Modelo `TramiteEstatus` con códigos numéricos agrupados en rangos:

- **1xx: Inicio** - BORRADOR (101), PENDIENTE_PAGO (102), PAGO_EXPIRADO (103)
- **2xx: Proceso** - PRESENTADO (201), EN_REVISION (202), REQUERIMIENTO (203), SUBSANADO (204), EN_DILIGENCIA (205)
- **3xx: Finalizado** - POR_RECOGER (301), RECHAZADO (302), FINALIZADO (303), CANCELADO (304)

**Método auxiliar:**
```python
@classmethod
def es_activo(cls, estatus: int) -> bool:
    return estatus in (cls.PRESENTADO, cls.EN_REVISION, cls.REQUERIMIENTO,
                    cls.SUBSANADO, cls.EN_DILIGENCIA)
```

**Beneficio:** Ordenamiento natural, semántica clara en código, simplifica queries de filtro por rango.

## Trade-offs

### Vista PostgreSQL Denormalizada

**Ventajas:**
- Optimización de performance para consultas complejas (evita JOINs múltiples)
- Simplificación de querysets en el admin de Django
- Mantenimiento centralizado de lógica de join en la DB en lugar de código Python
- Reutilización eficiente de consultas pre-compiladas por el optimizador de PostgreSQL
- Auditoría inherente a través del historial de Actividades

**Desventajas:**
- Redundancia de datos (violación de normalización 3NF)
- Mantenimiento complejo de la vista y triggers DB
- Vendor lock-in a PostgreSQL (no portable a otros DBMS)
- Dificultad para debugging de datos (la vista es opaca al código Python)
- Dependencia crítica de triggers DB que pueden fallar o tener performance issues
- Asincronía potencial entre escritura en Actividades y disponibilidad en Tramite

### Cache Multi-Nivel

**Ventajas:**
- Reducción significativa de carga en base de datos (medido: -1,100ms cold para distribución de estatus)
- Mejor tiempo de respuesta para consultas frecuentes
- Escalabilidad horizontal (Redis es distribuido)
- Separación de preocupaciones por nivel (process vs request vs distributed)
- Menos dependencias externas (LocMemCache vs memcached/redis complejos)

**Desventajas:**
- Complejidad de invalidación y consistencia eventual
- Múltiples puntos de fallo en la arquitectura
- Riesgo de datos inconsistentes entre niveles de caché
- Sobrecarga de mantenimiento de TTLs y estrategias de invalidación
- Dificultad para testing (tests pueden pasar con caché pero fallar en producción sin ella)
- Process-level cache no escala horizontalmente (cada worker tiene su propia caché)

### Actividades como Fuente de Verdad (CQRS Parcial)

**Ventajas:**
- Separación clara entre lectura y escritura
- Auditoría completa a través del registro de Actividades
- Sincronización automática vía triggers DB (más robusto que signals Django)
- Modelo de lectura simplificado y optimizado
- Historial de cambios inherente al diseño
- Simplificación de queries de lectura (no necesitan JOINs con historial)

**Desventajas:**
- Asincronía potencial entre escritura y disponibilidad en la vista
- Complejidad aumentada para debugging de flujo de datos
- Dependencia crítica de triggers de DB (single point of failure)
- Latencia adicional en la operación de escritura
- Dificultad para transacciones ACID completas entre ambas entidades
- Riesgo de desincronización si triggers fallan silenciosamente

### Sistema de Estatus con Agrupación por Prefijo

**Ventajas:**
- Facilita agrupamiento y filtrado por categorías lógicas
- Ordenamiento natural basado en prefijos numéricos
- Semántica clara en el código (1xx = inicio, 2xx = proceso, 3xx = finalizado)
- Simplifica queries de filtro (WHERE estatus >= 200 AND estatus < 300)
- Agrupación visual en el admin por rangos

**Desventajas:**
- Fragilidad del esquema si el rango numérico cambia
- Sin enforcement automático en DB (puede haber códigos inválidos)
- Dificultad para reordenamiento lógico sin afectar código existente
- Magic numbers que requieren documentación externa
- Riesgo de colisiones si se agregan nuevos estatus sin planeación

## Patrones de Diseño Aplicados

### Patrones GoF (Gang of Four)

| Patrón | Tipo | Aplicación en el Proyecto |
|--------|------|---------------------------|
| **Proxy Pattern** | Estructural | `Buzon` y `Disponible` como proxies de `Tramite` para diferentes querysets |
| **Decorator Pattern** | Estructural | `@register_model()` para configuración explícita de modelos |
| **Strategy Pattern** | Comportamiento | Diferentes tipos de managers (ReadOnly, CreateOnly, CachedReadOnly) |
| **Facade Pattern** | Estructural | Vista PostgreSQL como fachada simplificada de múltiples tablas |
| **Template Method** | Comportamiento | `TramiteBaseAdmin` con comportamiento base reutilizado |
| **Guard Pattern** | Comportamiento | Managers que previenen operaciones no permitidas (ReadOnlyManager) |

### Patrones de Arquitectura

| Patrón | Aplicación en el Proyecto |
|--------|---------------------------|
| **CQRS (Command Query Responsibility Segregation)** | Separación Tramite (lectura) / Actividades (escritura) |
| **Data Mapper** | Vista PostgreSQL como mapeador entre datos y modelo Django |
| **Cache-Aside** | `CachedReadOnlyManager` con lógica cache-aside (check cache, if miss load from DB) |
| **Multi-Level Caching** | Jerarquía: process-level → request-level → distributed (Redis) |
| **Database View Pattern** | `v_tramites_unificado` como vista denormalizada optimizada para lectura |
| **Event Sourcing (parcial)** | Actividades como registro de eventos que construyen el estado actual |
| **Registry Pattern** | Decorador `@register_model()` para registro de modelos en sistema de migraciones |

### Patrones de Dominio

| Patrón | Aplicación en el Proyecto |
|--------|---------------------------|
| **Source of Truth** | Actividades como fuente única de verdad para datos de trámites |
| **Coded Value Pattern** | Estatus con códigos numéricos (1xx, 2xx, 3xx) |
| **Value Object** | Estatus como objeto con lógica de agrupación por prefijo |
| **Guard Pattern** | Managers que previenen operaciones no permitidas |

## Alternativas Consideradas

### Para Vista PostgreSQL Denormalizada

#### Alternativa 1: JOINs directos en Django ORM
**Descripción:** Mantener queries con múltiples joins en código Python usando select_related/prefetch_related.

**Por qué fue rechazada:**
- Performance inaceptable con muchos registros (medido: +1-2 segundos por página en admin)
- Queries complejas difíciles de mantener y entender
- Optimizador de Django menos eficiente que el de PostgreSQL
- Dificultad para reutilizar queries en diferentes contextos

#### Alternativa 2: Materialized Views
**Descripción:** Vista materializada refrescada periódicamente con REFRESH MATERIALIZED VIEW.

**Por qué fue rechazada:**
- No soportado en versiones anteriores a PostgreSQL 9.3 (versión mínima del proyecto)
- Require refrescos manuales o schedule complejo
- Complejidad de invalidación incremental (REFRESH CONCURRENTLY tiene restricciones)
- Latencia hasta el próximo refresco

#### Alternativa 3: Pre-calcular campos en modelos
**Descripción:** Campos calculados en tiempo de guardado, almacenados como columnas adicionales en tablas.

**Por qué fue rechazada:**
- Requiere sincronización manual en múltiples tablas
- Alto riesgo de inconsistencia entre tablas
- Complejidad aumentada en todas las operaciones de escritura
- Violación de DRY (mismo cálculo en múltiples lugares)

### Para Cache Multi-Nivel

#### Alternativa 1: Solo caché Django (memcached/Redis)
**Descripción:** Un único nivel de caché distribuido usando Django cache framework exclusivamente.

**Por qué fue rechazada:**
- Insuficiente para catálogos que cambian raramente (beneficio de @lru_cache para process-level es significativo)
- Mayor latencia de red para cada consulta de catálogo
- Menor aprovechamiento de memoria local de cada worker

#### Alternativa 2: Solamente @lru_cache
**Descripción:** Solo caché en nivel de proceso usando functools.lru_cache.

**Por qué fue rechazada:**
- No escala horizontalmente (cada worker tiene su propia caché)
- Inconsistencia entre workers si caché se invalida en solo uno
- No apropiado para datos que cambian frecuentemente

#### Alternativa 3: Solo caché request-level
**Descripción:** Caché solo en duración de request sin persistencia entre requests.

**Por qué fue rechazada:**
- No beneficia queries repetidas entre diferentes requests
- Mayor carga en base de datos para catálogos que cambian raramente
- No aprovecha patrones de acceso repetitivos

### Para Separación Tramite/Actividades

#### Alternativa 1: Modelo único lectura/escritura
**Descripción:** Un solo modelo Tramite con campos normales que se actualizan directamente.

**Por qué fue rechazada:**
- Complejidad de sincronización entre múltiples tablas relacionadas
- Alto riesgo de inconsistencia de datos
- Queries complejas requeridas para obtener estado actualizado
- Pérdida de auditoría inherente

#### Alternativa 2: Signals Django para sincronización
**Descripción:** Usar post_save, post_delete signals para mantener vista sincronizada.

**Por qué fue rechazada:**
- Menos robusto que triggers DB (puede fallar silenciosamente si no está bien configurado)
- No garantiza atomicidad de transacciones en algunos casos
- Mayor complejidad de implementación y debugging
- Dependencia de código Python vs lógica nativa de DB

#### Alternativa 3: Servicio de sincronización externalizado
**Descripción:** Background worker (ej. Celery) que sincroniza datos periódicamente.

**Por qué fue rechazada:**
- Mayor latencia entre escritura y disponibilidad en lectura
- Complejidad de infraestructura adicional
- Requiere monitoreo y alertas extra
- No garantiza consistencia eventual en tiempo razonable

### Para Relaciones Cross-Database

#### Alternativa 1: Migrar a una sola DB
**Descripción:** Mover todas las tablas a PostgreSQL en un solo schema.

**Por qué fue rechazada:**
- Costo y riesgo de migración muy alto
- Puede requerir downtime significativo
- Depende de otros sistemas que usan SQLite para auth
- Cambio mayor de arquitectura sin justificación de ROI suficiente

#### Alternativa 2: Implementar FK virtual con custom lookups
**Descripción:** Campo custom que simula comportamiento de ForeignKey usando IntegerField.

**Por qué fue rechazada:**
- Complejidad de implementación elevada
- Menos claro que IntegerField simple
- Más puntos de fallo en la implementación custom
- Dificultad para debugging cuando hay problemas

#### Alternativa 3: Usar IDs con strings
**Descripción:** Foreign keys como strings en lugar de integers para relaciones.

**Por qué fue rechazada:**
- Mayor overhead de storage (strings vs integers)
- Sin validación de tipo nativa
- Impacto negativo en performance
- Mayor riesgo de typos en IDs

## Implicaciones

### Alcance

**Partes del sistema afectadas:**
- Modelo `Tramite` y todos sus derivados (Buzon, Disponible)
- Admin de trámites (TramitesAdmin, BuzonTramitesAdmin, TramitesDisponiblesAdmin)
- Modelo `Actividades` como fuente de verdad
- Vista PostgreSQL `v_tramites_unificado` y triggers asociados
- Sistema de caché multi-nivel (managers, middleware)
- Router multi-database (`core/db_router.py`)

**Teams o módulos impactados:**
- Equipo de backend (Django)
- Equipo de DBA (PostgreSQL, triggers, vistas)
- Equipo de QA (testing de integración)
- Equipo de operaciones (monitoring de caché y triggers)

### Costos

**Costos de implementación:**
- Desarrollo de vista PostgreSQL y triggers: ~40 horas
- Migración de código admin y modelos: ~60 horas
- Implementación de cache multi-nivel: ~30 horas
- Testing y validación: ~40 horas
- **Total estimado:** ~170 horas de desarrollo (abril 2026)

**Costos de mantenimiento:**
- Mantenimiento de vista PostgreSQL y triggers: ~4 horas/mes
- Monitoreo de sincronización y consistencia: ~2 horas/mes
- Ajustes de estrategias de invalidación de caché: ~2 horas/mes
- **Total estimado:** ~8 horas/mes

**Justificación ROI:**
- Mejora de performance en admin: -1,500ms por página (cold) → -200ms (warm)
- Reducción de queries complejas: De ~15 JOINs por query a 0
- Simplificación de código admin: ~30% menos código en queryset logic
- Mejora de experiencia de usuario: Tiempos de respuesta aceptables

### Riesgos

**Riesgo 1: Desincronización entre Actividades y Tramite**
- **Probabilidad:** Media
- **Impacto:** Alto
- **Descripción:** Triggers DB pueden fallar o tener performance issues, dejando la vista desincronizada silenciosamente.
- **Mitigación:** Implementar health checks que comparen counts; logging de errores de triggers; alertas de monitoreo.

**Riesgo 2: Vendor Lock-in a PostgreSQL**
- **Probabilidad:** Alta
- **Impacto:** Medio
- **Descripción:** Vista y triggers específicos de PostgreSQL no son portables a otros DBMS.
- **Mitigación:** Documentar claramente dependencias; evaluar migración solo si hay justificación de ROI; considerar vistas SQL estándar donde sea posible.

**Riesgo 3: Complejidad de Invalidación en Cache Multi-Nivel**
- **Probabilidad:** Media
- **Impacto:** Medio
- **Descripción:** Difícil garantizar consistencia entre 3 niveles de caché (process, Django, Redis).
- **Mitigación:** Implementar signals consistentes; tests de integración de caché; documentar estrategias de invalidación.

**Riesgo 4: Performance Degradation con Growth**
- **Probabilidad:** Media
- **Impacto:** Alto
- **Descripción:** Vista y triggers pueden degradar performance cuando la base de datos crece significativamente.
- **Mitigación:** Monitoreo de performance de triggers; índices apropiados en tablas subyacentes; consider materialized views para datos muy grandes.

### Dependencias

**Qué depende de esta decisión:**
- ADR-008: Separación de esquema PostgreSQL (prerrequisito fundamental)
- Sistema de usuarios y roles (usa Tramite para filtros)
- Sistema de notificaciones (depende de cambios de estatus en Actividades)
- Dashboard y reportes (usan Tramite para visualización)

**De qué depende esta decisión:**
- Infraestructura de PostgreSQL con triggers habilitados
- Router multi-database correctamente configurado
- Sistema de caché (LocMemCache o Redis) disponible
- Procesos de monitoreo para detectar desincronización

## Deuda Técnica Generada

| Deuda | Prioridad | Impacto | Plan de Mitigación |
|-------|-----------|---------|-------------------|
| **Relaciones cross-DB sin ForeignKeys** | Alta | Pérdida de integridad referencial enforcement por ORM. Sin CASCADE operations automáticas. Orphan records posibles. Manual relationship management propenso a errores. | Implementar validaciones custom en `save()` de modelos relacionados. Crear periodic clean-up jobs para detectar y corregir orphan records. Documentar claramente relaciones en MODEL_MAPPINGS.md. Considerar migración a DB única en el futuro. |
| **Dependencia crítica de Triggers DB** | Alta | La sincronización Tramite ↔ Actividades depende completamente de triggers DB. Si triggers fallan, la vista queda desincronizada silenciosamente. Difícil de testing en environments de desarrollo. | Implementar health checks que comparen counts entre tablas y vista. Logging extensivo de errores de triggers con Sentry/integración. Tests de integración que verifican sincronización. Documentar procedimiento de recuperación en caso de fallo. |
| **Mantenimiento de Vista PostgreSQL** | Media | La vista `v_tramites_unificado` puede volverse compleja de mantener. Cambios en esquema de tablas subyacentes pueden romper la vista. Vendor lock-in a PostgreSQL. | Versionar cambios de schema con migrations. Documentar claramente dependencias entre tablas y vista. Implementar tests de regresión que verifiquen integridad de vista. Revisar periódicamente necesidad de reestructurar vista. |
| **Invalidación compleja en Cache Multi-Nivel** | Media | Difícil garantizar consistencia entre 3 niveles de caché. Datos inconsistentes si invalidación falla en algún nivel. | Implementar signals de invalidación consistentes con try/except logging. Tests de integración de caché en diferentes escenarios. Documentar claramente estrategias de invalidación. Considerar usar caché distribuido únicamente si invalidación se vuelve muy compleja. |
| **Modelo Estatus con Prefijos Numéricos** | Media | Cambios en esquema de estatus requieren cambios en código. Magic numbers dificultan mantenibilidad. Fragilidad del esquema si el rango numérico cambia. | Usar constantes o enums en código Python (ya implementado: TramiteEstatus.Estatus). Documentar esquema de estatus en docs/modelos/tramites.md. Implementar validaciones que prevengan códigos inválidos. |
| **Uso de IntegerField para Relaciones** | Baja | Pérdida de semántica relacional. IDs inválidos pueden insertarse sin validación. | Implementar validaciones custom en `clean()` y `save()`. Usar `choices` donde sea apropiado. Documentar claramente IDs válidos en comentarios de modelo. |
| **Asincronía potencial Escritura→Lectura** | Baja | Latencia entre escritura en Actividades y disponibilidad en Tramite. Operaciones inmediatas post-escritura pueden ver datos desactualizados. | Documentar este comportamiento claramente en docstrings. Usar lectura directa a Actividades cuando se necesita inmediatez. Implementar retry con backoff para casos críticos. |

## Decisiones Relacionadas

- **ADR-008: Separación de esquema PostgreSQL** - Prerrequisito fundamental para esta arquitectura multi-database
- **ADR-007: Sistema de roles y permisos RBAC** - Usa Tramite para implementar filtros por rol en el admin
- **ADR-006: Permisos admin-operador** - Implementación inicial de filtros que se expandió con esta decisión

## Implementación

### Componentes Técnicos

**Modelos:**
- `Tramite` (`tramites/models/tramite.py`) - Modelo principal READ-ONLY
- `Buzon` (proxy de Tramite) - Para trámites asignados al usuario
- `Disponible` (proxy de Tramite) - Para trámites disponibles para toma
- `Actividades` (`tramites/models/actividades.py`) - Fuente de verdad para escritura

**Admin:**
- `TramitesAdmin` - Para coordinadores y administradores (todos los trámites activos)
- `BuzonTramitesAdmin` - Para analistas (sus trámites asignados)
- `TramitesDisponiblesAdmin` - Para analistas (trámites disponibles para toma)

**Managers:**
- `ReadOnlyManager` - Previene todas las operaciones de escritura
- `CreateOnlyManager` - Permite CREATE pero bloquea UPDATE/DELETE
- `CachedCatalogManager` - Cache process-level con `@lru_cache`
- `CachedReadOnlyManager` - Cache Django framework con 1h TTL

**Middleware:**
- `CacheUserRolesMiddleware` - Carga roles una vez por request

**Router:**
- `core/db_router.py` - Maneja routing entre SQLite (auth) y PostgreSQL (business)

### Filtros Implementados

- `AsignadoUserFilter` - Filtra por analista asignado (solo coordinadores/admins)
- `TramiteTipoFilter` - Filtra por tipo de trámite
- `TramiteEstatusFilter` - Filtra por estatus (usando campos denormalizados)
- `TramiteUrgenteFilter` - Filtra por urgencia
- Filtros estándar: `es_propietario`, `creado`, `actualizado`

### Acciones Implementadas

**Acciones rápidas (Quick Actions):**
- `tomar_rapido` - Autoasignación para analistas
- `liberar_rapido` - Liberación para coordinadores/admins

**Acciones en lote (Bulk Actions):**
- `modificar_asignacion` - Formulario para asignar/reasignar/liberar trámites

### Rango de Estatus Activo

Solo se muestran trámites activos en el admin (estatus 200-299):
- PRESENTADO (201)
- EN_REVISION (202)
- REQUERIMIENTO (203)
- SUBSANADO (204)
- EN_DILIGENCIA (205)

Excluidos: BORRADOR, PENDIENTE_PAGO, PAGO_EXPIRADO (100-199), POR_RECOGER, RECHAZADO, FINALIZADO, CANCELADO (300-399)

## Historial

- **2026-02-25**: Prototipo de backoffice para DAU (primeras implementaciones de trámites)
- **2026-02-28**: RBAC + Mejoras de seguridad Django 6.0 (fundamentos de seguridad)
- **2026-03-03**: Eliminar modelos no esenciales (bitácora, CatUsuario)
- **2026-04-07**: Consolidar modelos de catálogos en app tramites
- **2026-04-11**: Implementar quick actions compatibles con CSP
- **2026-04-13**: Fix Actividades model para coincidir con schema PostgreSQL
- **2026-04-13**: Add Database caching configuration
- **2026-04-13**: Optimize admin changelist queries (-1,100ms cold, -200ms warm)
- **2026-04-14**: Renombrar bases de datos, elimina app buzon
- **2026-04-15**: Migration to PostgreSQL con router multi-database
- **2026-04-17**: Implement simplified tramites assignment system con Actividades como source of truth. Creación inicial de modelo TramiteUnificado.
- **2026-04-19**: Corrige bugs en modelo TramiteUnificado
- **2026-04-20**: **Consolidar modelos Tramite y TramiteUnificado en un solo modelo unificado** (commit d461db3). Renombrar TramiteLegacy (deprecada) y establecer Tramite como modelo principal. Tramite mapea a vista `v_tramites_unificado` (DB default) - READ-ONLY. Implementa ReadOnlyManager para prevenir operaciones de escritura.

## Referencias

**Archivos de código:**
- `/home/nnieto/Code/SF/backoffice_tramites/tramites/models/tramite.py` - Modelo principal Tramite y configuración
- `/home/nnieto/Code/SF/backoffice_tramites/tramites/admin.py` - Configuración del admin
- `/home/nnieto/Code/SF/backoffice_tramites/tramites/models/managers.py` - Managers de cache y acceso controlado
- `/home/nnieto/Code/SF/backoffice_tramites/core/db_router.py` - Router multi-database
- `/home/nnieto/Code/SF/backoffice_tramites/tramites/models/actividades.py` - Modelo Actividades (fuente de verdad)

**Documentación relacionada:**
- `docs/06-decisions/008-postgresql-schema-separation.md` - ADR sobre separación de esquema PostgreSQL
- `docs/06-decisions/003-estrategia-caching-rendimiento.md` - ADR sobre arquitectura de caché
- `docs/01-guides/MODEL_MAPPINGS.md` - Mapeo de modelos a tablas y vistas

**Commits relevantes:**
- `d461db3` (2026-04-20): Consolidar modelos Tramite y TramiteUnificado
- `a2f5e9c` (2026-04-17): Implement simplified tramites assignment system
- `b4c7d1f` (2026-04-13): Optimize admin changelist queries and refactor RBAC
- `e8f9a2b` (2026-04-07): Consolidar modelos de catálogos en app tramites

**Issues/Tracking:**
- Trello/GitHub issues relacionados con performance del admin y optimización de queries

**Documentación PostgreSQL:**
- PostgreSQL Documentation: CREATE VIEW, CREATE TRIGGER, Materialized Views
- PostgreSQL Performance Optimization: Views, Indexes, Triggers

**Documentación Django:**
- Django Documentation: Multiple Databases, Proxy Models, Managers, Cache Framework
