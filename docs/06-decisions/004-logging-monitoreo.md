# 004: Logging y monitoreo

**Fecha:** 26 de febrero de 2026  
**Estado:** Propuesto

## Contexto

El microservicio requiere un sistema de logging robusto para:
- Trazabilidad de operaciones críticas
- Depuración de errores en producción
- Monitoreo del rendimiento y comportamiento
- Auditoría de cambios en datos sensibles

Se necesita una configuración que:
- Proporcione logs detallados sin overhead excesivo
- Sea configurable por entorno (desarrollo vs producción)
- Permita rotación de logs para gestión de espacio
- Incluya logs específicos por aplicación

## Decision

Se ha decidido utilizar la siguiente configuración de logging:

1. **Configuración de LOGGING** en settings.py con:
   - Formatters para logs detallados y simples
   - Handlers para consola y archivo con rotación
   - Loggers específicos por aplicación (tramites, catalogos, costos, bitacora, core)

2. **Niveles de logging configurables**:
   - `DEBUG` en desarrollo para depuración detallada
   - `INFO` o `WARNING` en producción para logs esenciales
   - `ERROR` para errores críticos

3. **Rotación de logs**:
   - Archivos de log rotativos con tamaño máximo (10MB)
   - Retención de 10 archivos de backup
   - Formato de timestamp y metadata

4. **Logs por aplicación**:
   - Separación lógica de logs por módulo funcional
   - Configuración individual de niveles por aplicación

## Consequences

**Positivas:**
- Mejora significativa en la depuración y monitoreo
- Trazabilidad completa de operaciones
- Gestión eficiente del espacio de logs
- Aislamiento de logs por aplicación

**Negativas:**
- Overhead adicional en producción
- Complejidad en la configuración inicial
- Necesidad de gestión de logs externa

## Risks and Mitigations

- **Overhead de logging**: Configuración de niveles apropiados por entorno
- **Gestión de logs**: Implementación de rotación automática y retención
- **Rendimiento**: Uso de formateadores eficientes y handlers optimizados
- **Configuración compleja**: Documentación clara y configuración modular

## Alternatives Considered

- **Simple print logging**: Descartado por falta de estructura y难以管理
- **External logging services**: Descartado inicialmente por complejidad y dependencias
- **No logging**: Descartado por necesidad crítica de trazabilidad y depuración

## Superseded by

(ninguno)