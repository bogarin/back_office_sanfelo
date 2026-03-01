# 005: Despliegue con Docker y gunicorn

**Fecha:** 26 de febrero de 2026  
**Estado:** Propuesto

## Contexto

El microservicio requiere un despliegue robusto y escalable en producción. Se necesita:
- Aislamiento del entorno de ejecución
- Configuración configurable via environment variables
- Rendimiento optimizado para 50 usuarios simultáneos
- Seguridad con usuario no-root
- Facilidad de despliegue y mantenimiento

## Decision

Se ha decidido utilizar la siguiente estrategia de despliegue:

1. **Docker multi-stage build**:
   - **Builder stage**: Instalación de dependencias con uv
   - **Runtime stage**: Solo el entorno de ejecución y código de aplicación

2. **Configuración de gunicorn**:
   - 4 workers con 2 threads cada uno
   - Timeout de 120 segundos
   - Binding dinámico al puerto configurado via envvar
   - Logging a stdout/stderr

3. **Configuración de entorno**:
   - Usuario no-root para seguridad
   - Variables de entorno configurables (puerto, settings module)
   - Colección de archivos estáticos

4. **Optimizaciones**:
   - Uso de uv para manejo de dependencias
   - Multi-stage build para reducir tamaño de imagen
   - Configuración de puerto dinámico

## Consequences

**Positivas:**
- Aislamiento completo del entorno
- Facilidad de despliegue y escalado
- Seguridad mejorada con usuario no-root
- Configuración adaptable a diferentes entornos

**Negativas:**
- Complejidad inicial en la configuración de Docker
- Overhead de contenedores
- Necesidad de gestión de volúmenes y redes

## Risks and Mitigations

- **Tamaño de imagen**: Uso de multi-stage build para minimizar tamaño
- **Rendimiento**: Configuración óptima de gunicorn (workers/threads)
- **Seguridad**: Usuario no-root y permisos adecuados
- **Configuración compleja**: Documentación clara y variables de entorno bien definidas

## Alternatives Considered

- **Despliegue directo en servidor**: Descartado por falta de aislamiento y难于管理
- **Otras soluciones de contenedores**: Descartado por preferencia por Docker
- **Serverless**: Descartado por complejidad y costos

## Superseded by

(ninguno)