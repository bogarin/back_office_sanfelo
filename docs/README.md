# Mapa de Documentación — Backoffice de Trámites

> Índice completo de la documentación del proyecto.
> Última actualización: 9 de mayo de 2026

---

## Estructura

```
docs/
├── 01-ARQUITECTURA/         # Requisitos, arquitectura, modelo de datos
│   ├── 00-REQUERIMIENTOS.md
│   ├── 01-ARQUITECTURA.md
│   ├── 02-HISTORIAS-USUARIO.md
│   ├── 03-MODELO-DE-DATOS.md
│   └── glosario.md
├── 02-DECISIONES/            # ADRs (Architecture Decision Records)
│   ├── README.md
│   ├── 001 a 016             # 18 ADRs
│   └── adr-template.md
├── 03-AUDITORIAS/            # Auditorías técnicas
│   ├── README.md
│   ├── 001 a 003             # 3 auditorías
│   └── audit-template.md
├── 04-DISEÑO-Y-UX/           # Design system e interfaz admin
│   ├── design-system.md
│   └── admin-interface.md
├── 05-DEVELOPERS/            # Guías y referencia para desarrolladores
│   ├── local-dev-setup.md
│   ├── deploy-production.md
│   ├── setup-users.md
│   ├── workflow.md
│   ├── environment-vars.md
│   ├── commands.md
│   ├── models.md
│   ├── rbac.md
│   ├── sftp.md
│   ├── sftp-setup.md
│   └── seguridad-pre-release.md
└── _templates/               # Plantillas para nuevos documentos
```

---

## Por Sección

### 01-ARQUITECTURA — Qué es el sistema

| Documento | Descripción |
|-----------|-------------|
| [Requerimientos](01-ARQUITECTURA/00-REQUERIMIENTOS.md) | Requerimientos de negocio (PRD) |
| [Arquitectura](01-ARQUITECTURA/01-ARQUITECTURA.md) | Arquitectura técnica de alto nivel |
| [Historias de Usuario](01-ARQUITECTURA/02-HISTORIAS-USUARIO.md) | 28 HUs por rol |
| [Modelo de Datos](01-ARQUITECTURA/03-MODELO-DE-DATOS.md) | Modelo de datos con diagramas ERD |
| [Glosario](01-ARQUITECTURA/glosario.md) | Términos de negocio y técnicos |

### 02-DECISIONES — Por qué decidimos lo que decidimos

| # | Título | Estado |
|---|--------|--------|
| [001](02-DECISIONES/001-seleccion-stack-base.md) | Stack base original | Superseded by 012 |
| [002](02-DECISIONES/002-configuracion-multiples-bases-de-datos.md) | Multi-db original | Superseded by 008 |
| [003](02-DECISIONES/003-estrategia-caching-rendimiento.md) | Caching | Current |
| [004](02-DECISIONES/004-logging-monitoreo.md) | Logging | Current |
| [005](02-DECISIONES/005-despliegue-docker-gunicorn.md) | Deploy Docker | Current |
| [006](02-DECISIONES/006-permisos-admin-operador.md) | Permisos 2 roles | Superseded by 007 |
| [007](02-DECISIONES/007-implementacion-rbac-django-60.md) | RBAC 2 roles | Superseded by 013 |
| [008](02-DECISIONES/008-postgresql-schema-separation.md) | PostgreSQL schema separation | **Current** |
| [009](02-DECISIONES/009-vista-postgresql-para-tramites.md) | Vista unificada | Current |
| [009b](02-DECISIONES/009-remove-schema-validator.md) | Remover schema validator | Accepted |
| [010](02-DECISIONES/010-integracion-con-sftp.md) | Integración SFTP | Current |
| [010b](02-DECISIONES/010-remove-asignacion-tramite.md) | Remover AsignacionTramite | Accepted |
| [011](02-DECISIONES/011-docs-cleanup.md) | Cleanup de documentación | Current |
| [012](02-DECISIONES/012-stack-base-actualizado.md) | Stack actualizado | **Current** |
| [013](02-DECISIONES/013-rbac-tres-roles.md) | RBAC 3 roles | Superseded by 014 |
| [014](02-DECISIONES/014-custom-user-workflow-permissions.md) | Custom User + Workflow | **Current** |
| [015](02-DECISIONES/015-timestamps-timezone-america-tijuana.md) | Timestamps y timezone | Current |
| [016](02-DECISIONES/016-timeline-integrado-dtos-archivos.md) | Timeline integrado | Current |

### 03-AUDITORIAS — Cómo está el sistema

| Fecha | Auditoría | Tipo | Resumen |
|-------|-----------|------|---------|
| 2026-05-05 | [AUDIT-003](03-AUDITORIAS/003-seguridad-pre-release.md) | Seguridad | 9 hallazgos, 6 resueltos, 30 tests de regresión |
| 2026-05-04 | [AUDIT-002](03-AUDITORIAS/002-limpieza-de-codigo.md) | Calidad | 50 hallazgos, 4 críticos, 8 altos |
| 2026-05-04 | [AUDIT-001](03-AUDITORIAS/001-calidad-de-pruebas.md) | Calidad | 12 hallazgos, 344 tests, 100% pass rate |

### 04-DISEÑO-Y-UX — Cómo se ve y cómo se usa

| Documento | Descripción |
|-----------|-------------|
| [Design System](04-DISEÑO-Y-UX/design-system.md) | Paleta, tipografía, componentes, modo oscuro |
| [Interfaz Admin](04-DISEÑO-Y-UX/admin-interface.md) | Clases Admin, acciones, templates, Jazzmin |

### 05-DEVELOPERS — Cómo construirlo y operarlo

| Documento | Descripción |
|-----------|-------------|
| [Setup desarrollo](05-DEVELOPERS/local-dev-setup.md) | Entorno local paso a paso |
| [Deploy producción](05-DEVELOPERS/deploy-production.md) | Instalación completa en servidor |
| [Seguridad pre-release](05-DEVELOPERS/seguridad-pre-release.md) | Checklist obligatorio antes de deploy |
| [Configurar usuarios](05-DEVELOPERS/setup-users.md) | Crear usuarios y asignar roles |
| [Workflow de trámites](05-DEVELOPERS/workflow.md) | Estados, transiciones y permisos |
| [Variables de entorno](05-DEVELOPERS/environment-vars.md) | Todas las variables documentadas |
| [Comandos](05-DEVELOPERS/commands.md) | Management commands y justfile |
| [Modelos](05-DEVELOPERS/models.md) | Modelos Django → tablas PostgreSQL |
| [RBAC](05-DEVELOPERS/rbac.md) | Roles, permisos y Custom User Model |
| [SFTP](05-DEVELOPERS/sftp.md) | Arquitectura de serving de PDFs |

---

## Convenciones

- **Idioma:** Toda la documentación está en español
- **SSOT:** Cada pieza de información vive en un solo lugar
- **Links relativos:** Los links entre documentos son relativos
- **ADRs:** Nunca se borran, solo se marcan como superseded
- **Métricas siempre:** Toda auditoría incluye al menos una métrica cuantitativa
