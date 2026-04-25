# Mapa de Documentación — Backoffice de Trámites

> Índice completo de la documentación del proyecto.
> Última actualización: 23 de abril de 2026

---

## Rutas por Rol

| Rol | Punto de partida |
|-----|-----------------|
| **Desarrollador** | [Tutorial: Setup de desarrollo](02-tutorials/developers/local-dev-setup.md) |
| **Sysadmin** | [Guía: Despliegue en producción](03-guides/sysadmins/deploy-production.md) |

---

## Estructura de Documentación

```
docs/
├── 00-system-design/          # Requisitos y diseño del sistema
│   └── REQUERIMIENTOS_ALTO_NIVEL.md
├── 01-onboarding/             # Onboarding y visión general
│   ├── overview.md
│   ├── glossary.md
│   └── architecture-overview.md
├── 02-tutorials/              # Aprendizaje paso a paso
│   ├── developers/
│   │   └── local-dev-setup.md
│   └── admins/
│       ├── manage-catalogs.md
│       ├── manage-groups.md
│       ├── setup-users.md
│       └── seguridad-auditoria-produccion.md  # ← Checklist obligatorio antes de deploy
├── 03-guides/                 # Soluciones a problemas específicos
│   ├── sysadmins/
│   │   ├── deploy-production.md
│   │   └── sftp-setup.md
│   └── admins/
│       ├── configure-costs.md
│       ├── manage-workflow.md
│       ├── add-peritos.md
│       ├── change-status.md
│       └── manage-tramites.md
├── 05-reference/              # Referencia técnica (SSOT)
│   ├── commands.md
│   ├── environment-vars.md    # ← TODAS las variables de entorno
│   ├── models.md
│   ├── admin-setup.md
│   ├── sftp.md
│   ├── estados-tramites.md
│   └── rbac.md
├── 06-decisions/              # ADRs (Architecture Decision Records)
│   ├── README.md
│   ├── 001 a 013              # 13 ADRs
│   └── adr-template.md
├── COMANDOS_DJANGO.md         # Redirect → 05-reference/commands.md
└── _templates/                # Plantillas para nuevos documentos
```
docs/
├── 00-system-design/          # Requisitos y diseño del sistema
│   └── REQUERIMIENTOS_ALTO_NIVEL.md
├── 01-onboarding/             # Onboarding y visión general
│   ├── overview.md
│   ├── glossary.md
│   └── architecture-overview.md
├── 02-tutorials/              # Aprendizaje paso a paso
│   └── developers/
│       └── local-dev-setup.md
├── 03-guides/                 # Soluciones a problemas específicos
│   └── sysadmins/
│       ├── deploy-production.md
│       └── sftp-setup.md
├── 05-reference/              # Referencia técnica (SSOT)
│   ├── commands.md
│   ├── environment-vars.md    # ← TODAS las variables de entorno
│   ├── models.md
│   ├── admin-setup.md
│   ├── sftp.md
│   ├── estados-tramites.md
│   └── rbac.md
├── 06-decisions/              # ADRs (Architecture Decision Records)
│   ├── README.md
│   ├── 001 a 013              # 13 ADRs
│   └── adr-template.md
├── COMANDOS_DDJANGO.md         # Redirect → 05-reference/commands.md
└── _templates/                # Plantillas para nuevos documentos
```

---

## Por Categoría

### Onboarding (Conocer el sistema)

| Documento | Descripción |
|-----------|-------------|
| [Overview](01-onboarding/overview.md) | ¿Qué es este sistema? |
| [Arquitectura](01-onboarding/architecture-overview.md) | Cómo funciona por dentro |
| [Glosario](01-onboarding/glossary.md) | Términos de negocio y técnicos |

### Tutoriales (Aprender haciendo)

| Documento | Rol | Descripción |
|-----------|-----|-------------|
| [Setup de desarrollo](02-tutorials/developers/local-dev-setup.md) | Dev | Entorno local paso a paso |

### Guías (Resolver problemas)

| Documento | Rol | Descripción |
|-----------|-----|-------------|
| [Despliegue en producción](03-guides/sysadmins/deploy-production.md) | Sysadmin | Instalación completa en servidor |
| [Configuración SFTP](03-guides/sysadmins/sftp-setup.md) | Sysadmin | Host keys y conectividad SFTP |
| [Auditoría de Seguridad en Producción](02-tutorials/admins/seguridad-auditoria-produccion.md) | **Sysadmin / Admin** | **OBLIGATORIO** antes de primer deploy en producción. Checklist de validación de todas las correcciones de seguridad críticas y de alta prioridad implementadas en Fases 1-2. |

### Referencia (Detalles técnicos)

| Documento | Descripción |
|-----------|-------------|
| [Variables de entorno](05-reference/environment-vars.md) | **TODAS** las ~45 variables documentadas |
| [Comandos](05-reference/commands.md) | Management commands + justfile |
| [Modelos](05-reference/models.md) | Modelos Django → tablas PostgreSQL |
| [Admin setup](05-reference/admin-setup.md) | Configuración del Django Admin |
| [SFTP](05-reference/sftp.md) | Arquitectura de serving de PDFs |
| [Estados de trámites](05-reference/estados-tramites.md) | Códigos de estatus (1xx, 2xx, 3xx) |
| [RBAC](05-reference/rbac.md) | Roles y permisos detallados |

### Decisiones de Arquitectura (ADRs)

| # | Título | Estado |
|---|--------|--------|
| [001](06-decisions/001-seleccion-stack-base.md) | Stack base original | Superseded by 012 |
| [002](06-decisions/002-configuracion-multiples-bases-de-datos.md) | Multi-db original | Superseded by 008 |
| [003](06-decisions/003-estrategia-caching-rendimiento.md) | Caching | Current |
| [004](06-decisions/004-logging-monitoreo.md) | Logging | Current |
| [005](06-decisions/005-despliegue-docker-gunicorn.md) | Deploy Docker | Current |
| [006](06-decisions/006-permisos-admin-operador.md) | Permisos 2 roles | Superseded by 007 |
| [007](06-decisions/007-implementacion-rbac-django-60.md) | RBAC 2 roles | Superseded by 013 |
| [008](06-decisions/008-postgresql-schema-separation.md) | PostgreSQL schema separation | **Current** |
| [009](06-decisions/009-vista-postgresql-para-tramites.md) | Vista unificada | Current |
| [010](06-decisions/010-integracion-con-sftp.md) | Integración SFTP | Current |
| [011](06-decisions/011-docs-cleanup.md) | Cleanup de documentación | Current |
| [012](06-decisions/012-stack-base-actualizado.md) | Stack actualizado | **Current** |
| [013](06-decisions/013-rbac-tres-roles.md) | RBAC 3 roles | **Current** |

### Diseño del Sistema

| Documento | Descripción |
|-----------|-------------|
| [Requerimientos de alto nivel](00-system-design/REQUERIMIENTOS_ALTO_NIVEL.md) | Requisitos de negocio (los técnicos están desactualizados) |

---

## Convenciones

- **Idioma:** Toda la documentación está en español
- **SSOT:** Cada pieza de información vive en un solo lugar
- **Links relativos:** Los links entre documentos son relativos
- **ADRs:** Nunca se borran, solo se marcan como superseded
