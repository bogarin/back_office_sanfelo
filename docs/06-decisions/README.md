# Registro de Decisiones de Arquitectura (ADR)

> "Escuchen bien. Si no documentan sus decisiones de arquitectura, están construyendo un castillo de naipes sobre arenas movedizas. He visto demasiados proyectos colapsar porque nadie recordaba *por qué* demonios elegimos una tecnología sobre otra o por qué desacoplamos ese servicio hace dos años. Un ADR no es burocracia, es su póliza de seguro." — Pietro

## ¿Qué es un ADR y por qué nos importa?

Un **ADR (Architecture Decision Record)** es un documento corto que captura una decisión de arquitectura importante, junto con su contexto y sus consecuencias.

**Beneficios para el Equipo:**
- **Memoria Institucional:** Evita que tengamos las mismas discusiones una y otra vez. "Ya decidimos esto, mira el ADR-005".
- **Onboarding:** Los nuevos desarrolladores pueden entender la evolución del sistema leyendo la historia de las decisiones.

**Beneficios para Agentes LLM:**
- **Contexto Crítico:** Cuando me pidan (o a cualquier otro agente) refactorizar o añadir features, los ADRs nos dicen qué restricciones existen y por qué. Sin esto, podríamos sugerir cambios que violen principios fundamentales que ustedes ya establecieron.

## Índice de ADRs

| Número ADR | Descripción |
|------------|-------------|
| [ADR-001](001-seleccion-stack-base.md) | Selección de Stack Tecnológico Base *(Superseded by ADR-012)* |
| [ADR-002](002-configuracion-multiples-bases-de-datos.md) | Configuración de múltiples bases de datos y routers *(Superseded by ADR-008)* |
| [ADR-003](003-estrategia-caching-rendimiento.md) | Estrategia de caching y rendimiento |
| [ADR-004](004-logging-monitoreo.md) | Logging y monitoreo |
| [ADR-005](005-despliegue-docker-gunicorn.md) | Despliegue con Docker y gunicorn |
| [ADR-006](006-permisos-admin-operador.md) | Permisos de admin y operador *(Superseded by ADR-007)* |
| [ADR-007](007-implementacion-rbac-django-60.md) | Implementación de RBAC para Django 6.0 *(Superseded by ADR-013)* |
| [ADR-008](008-postgresql-schema-separation.md) | PostgreSQL Schema Separation |
| [ADR-009](009-vista-postgresql-para-tramites.md) | Vista PostgreSQL unificada para trámites |
| [ADR-010](010-integracion-con-sftp.md) | Integración con servicio SFTP para requisitos |
| [ADR-011](011-docs-cleanup.md) | Limpieza y reestructuración de documentación |
| [ADR-012](012-stack-base-actualizado.md) | Stack tecnológico actualizado *(Supersedes ADR-001)* |
| [ADR-013](013-rbac-tres-roles.md) | Sistema RBAC con tres roles *(Supersedes ADR-007)* |

## Cómo crear un nuevo ADR

El proceso es simple, no hay excusas:

1. **Copiar** el archivo `adr-template.md` a un nuevo archivo con el formato `NNN-titulo-de-la-decision.md` dentro de este directorio (`docs/decisiones`).
   - `NNN` es el número consecutivo (ej. 001, 002).
   - `titulo-de-la-decision` es una descripción corta en kebab-case.
2. **Rellenar** los campos del documento explicando el contexto, las opciones y la decisión final.

## Cómo sustituir una decisión (Superseding)

La arquitectura evoluciona. Si una decisión anterior ya no es válida:

1. **Crear el Nuevo ADR** (ej. `010-nueva-bd.md`).
   - En la sección de contexto o cabecera, añadir: "Sustituye a: [ADR-005](005-vieja-bd.md)".
2. **Actualizar el Viejo ADR** (ej. `005-vieja-bd.md`).
   - Cambiar su estado a **Sustituido** (Superseded).
   - Añadir al principio: "Sustituido por: [ADR-010](010-nueva-bd.md)".

**Regla de oro:** Nunca borren un ADR antiguo. Solo márquenlo como obsoleto. Necesitamos saber qué errores cometimos para no repetirlos.

---
*Mantengan este directorio limpio y ordenado. Un sistema sin documentación de decisiones es un crimen esperando suceder.*
