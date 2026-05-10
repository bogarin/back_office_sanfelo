# 001: Selección de Stack Tecnológico Base

**Fecha:** 26 de febrero de 2026  
**Estado:** Aceptado

## Contexto

Este es un microservicio para administración de trámites gubernamentales, que funciona como backoffice para llevar el tracking de trámites de la entidad gubernamental. El microservicio no procesa pagos (responsabilidad de otros microservicios) ni crea trámites (tarea de otro microservicio que interactúa con la BD de postgres). Las operaciones principales son: cambio de estado de trámites, asignación a funcionarios y gestión del estado. Aunque Django lo permite, nada se debe eliminar de la base de datos postgres.

## Decision

Se ha decidido utilizar el siguiente stack tecnológico:

- **Python 3.14** (última versión estable en 2026)
- **Django 6.x** (última versión estable en 2026)
- **uv** para manejo de paquetes
- **justfile** para desarrolladores
- **django-environ** para configuraciones de archivos .env
- **psycopg-binary** para evitar problemas de compilación de drivers de postgres
- **2 Bases de datos:**
  - **SQLite** -- autenticación, permisos (RBAC) y Django Admin
  - **PostgreSQL** -- Base de datos legacy (migraciones desactivadas)

## Consequences

**Positivas:**
- Rapida entrega de producto funcional gracias a Django Admin
- Expertise del equipo en Python
- Simplificación del desarrollo con herramientas modernas (uv, justfile)

**Negativas:**
- Posibles limitaciones de rendimiento con múltiples bases de datos
- Complejidad en la gestión de configuraciones

## Risks and Mitigations

- **Python expertise**: Un miembro del equipo domina Python, minimizando el riesgo de problemas técnicos
- **Developer experience**: Usaremos uv y justfile para eliminar fricción en el onboarding de nuevos desarrolladores
- **Development tools**: Configuración de herramientas de calidad de código (ruff para linting, pyright para type checking) con grupos de dependencias separados (dev/prod)
- **Deployment**: Construiremos imágenes de Docker configurables mediante envvars, con settings necesarios configurables en runtime y guardados en SQLite si es necesario
- **Performance**: 
  - Baseline de rendimiento: 50 usuarios simultáneos
  - Optimizaremos parámetros de SQLite para mejorar rendimiento
  - Usaremos módulos de cacheo de Django (incluso Redis si es necesario)
  - Escalado horizontal mediante múltiples Docker containers con load balancing si la carga lo exige

## Development Tools and Quality Assurance

- **Package management**: uv para manejo de dependencias con lock file
- **Development commands**: justfile para automatizar tareas comunes (runserver, migrate, lint, tests)
- **Linting**: ruff para análisis de código estático con configuración personalizada
- **Type checking**: pyright para validación de tipos
- **Code formatting**: ruff format para mantener consistencia de código
- **Dependency groups**: Separación de dependencias (dev para desarrollo, prod para producción)

## Alternatives Considered

- **Java/NodeJS**: Descartados debido al expertise del equipo y el poco tiempo disponible para lograr un producto funcional
- **Laravel**: Considerado pero descartado por falta de expertise en el equipo

## Superseded by

**[ADR-012: Stack Tecnológico Actualizado](012-stack-base-actualizado.md)** — El stack evolucionó de SQLite+PostgreSQL a un solo PostgreSQL con separación de esquemas. El cache cambió de "posible Redis" a LocMemCache. Los roles evolucionaron de 2 a 3. Se añadió SFTP, Nginx, y Gunicorn.