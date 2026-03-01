# 006: Permisos de admin y operador

**Fecha:** 26 de febrero de 2026  
**Estado:** Propuesto

## Contexto

El microservicio requiere un sistema de permisos robusto para:
- Control de acceso basado en roles (RBAC)
- Auditoría de operaciones críticas
- Seguridad en la gestión de trámites gubernamentales
- Diferenciación entre administradores y operadores

Se necesita una configuración que:
- Defina claramente los roles y permisos
- Implemente auditoría automática
- Facilite la gestión de usuarios y permisos
- Sea escalable y mantenible

## Decision

Se ha decidido utilizar la siguiente estrategia de permisos:

1. **Configuración de Django Admin**:
   - Customización del site header y título
   - Reordenamiento de apps por prioridad (tramites primero)
   - Configuración de ModelAdmin base con funcionalidades comunes

2. **Roles y permisos**:
   - **Administradores**: Acceso completo al sistema
   - **Operadores**: Acceso limitado a operaciones de tramites (cambio de estado, asignación)
   - **Lectores**: Acceso solo de lectura a información

3. **Auditoría automática**:
   - Mixin de auditoría para registrar cambios en bitacora
   - Logging de operaciones críticas (CREATE, UPDATE, DELETE)
   - Información detallada de usuario, IP y timestamp

4. **Acciones personalizadas**:
   - Marcado de tramites como urgentes/no urgentes
   - Marcado de tramites como pagados/no pagados
   - Gestión de estado de catalogos

## Consequences

**Positivas:**
- Mejora significativa en la seguridad y control de acceso
- Trazabilidad completa de operaciones
- Facilidad en la gestión de permisos
- Auditoría automática sin esfuerzo adicional

**Negativas:**
- Complejidad inicial en la configuración de roles
- Overhead adicional en operaciones de escritura
- Necesidad de mantenimiento de la configuración de permisos

## Risks and Mitigations

- **Configuración compleja**: Documentación clara y configuración modular
- **Auditoría overhead**: Optimización de queries y gestión de bitacora
- **Seguridad**: Roles bien definidos y permisos mínimos necesarios
- **Mantenimiento**: Estrategia clara de gestión de usuarios y roles

## Alternatives Considered

- **Sistema de permisos simple**: Descartado por necesidad de auditoría y control granular
- **Sistemas externos de auth**: Descartado por complejidad y dependencias
- **No RBAC**: Descartado por requisitos de seguridad gubernamental

## Superseded by

(ninguno)