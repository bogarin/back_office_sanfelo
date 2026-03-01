# Backoffice de Trámites - Gobierno de San Felipe

Microservicio de gestión de trámites para las dependencias del gobierno de San Felipe.

---

## 🚀 Quick Start

### 👷 Operadores
**Empezar a usar el sistema**: [Tutorial: Crear tu primer trámite](docs/02-tutorials/operators/create-tramite.md)

### 👔 Administradores
**Configurar el sistema**: [Tutorial: Configurar usuarios](docs/02-tutorials/admins/setup-users.md)

### 💻 Desarrolladores
**Setup de desarrollo local**: [Tutorial: Setup de desarrollo](docs/02-tutorials/developers/local-dev-setup.md)

### 🔧 Sysadmins
**Despliegue en producción**: [Guía: Despliegue en producción](docs/03-guides/sysadmins/deploy-production.md)

---

## 📋 Overview

### ¿Qué es este proyecto?

Sistema de gestión de trámites con:
- 📝 Gestión completa de trámites con historial
- 🗃️ Catálogos configurables (tipos, estatus, requisitos, peritos)
- 💰 Sistema de costos calculado por UMA
- 📊 Auditoría completa (bitácora de cambios)
- 🔐 Sistema de permisos y roles

**Leer más**: [Overview completo](docs/01-onboarding/overview.md)

---

## 🏗️ Arquitectura

| Componente | Tecnología |
|------------|------------|
| **Backend** | Django 6.0.2 (Python 3.14) |
| **BD Auth** | SQLite (Django auth) |
| **BD Negocio** | PostgreSQL (business data) |
| **Cache** | Redis |
| **Interface** | Django Admin |
| **Deploy** | Docker + Gunicorn |

**Leer más**: [Arquitectura detallada](docs/01-onboarding/architecture-overview.md)

---

## 📚 Documentación

### Por Rol

| Rol | Documentación principal |
|-----|---------------------|
| 👷 **Operadores** | [Tutoriales operadores](docs/02-tutorials/operators/) |
| 👔 **Administradores** | [Tutoriales administradores](docs/02-tutorials/admins/) |
| 💻 **Desarrolladores** | [Tutoriales desarrolladores](docs/02-tutorials/developers/) |
| 🔧 **Sysadmins** | [Guías sysadmin](docs/03-guides/sysadmins/) |
| 🤖 **AI Agents** | [Documentación optimizada para LLMs](docs/08-ai-optimized/) |

### Por Tipo

| Tipo | Descripción |
|------|-------------|
| 📖 **Tutoriales** | Aprendizaje guiado paso a paso |
| 📋 **Guías** | Soluciones a problemas específicos |
| 🧠 **Conceptos** | Explicaciones teóricas del sistema |
| 📖 **Referencias** | Documentación técnica completa |
| 📋 **ADRs** | Decisiones de arquitectura |

**Ver mapa completo**: [Mapa de documentación](docs/README.md)

---

## 🔗 Enlaces Útiles

### Desarrollo
- [API Reference](docs/05-reference/api/endpoints.md)
- [Environment Variables](docs/05-reference/configuration/environment-vars.md)
- [Commands Reference](docs/05-reference/commands/index.md)
- [Model Reference](docs/05-reference/models/data-models.md)

### Operaciones
- [Troubleshooting](docs/03-guides/sysadmins/troubleshoot.md)
- [Backup & Restore](docs/03-guides/sysadmins/backup-restore.md)
- [Monitoring](docs/03-guides/sysadmins/monitoring.md)

### Arquitectura
- [Decisiones de Arquitectura (ADRs)](docs/06-decisions/README.md)
- [Dual Database Strategy](docs/04-concepts/dual-database.md)
- [Caching Strategy](docs/04-concepts/caching-strategy.md)

---

## 🛠️ Tecnologías

| Componente | Versión |
|------------|---------|
| Python | 3.14 |
| Django | 6.0.2 |
| uv | latest |
| PostgreSQL | - |
| Redis | - |
| Gunicorn | - |
| Docker | - |

---

## 📄 Licencia

Copyright © 2026 Gobierno de San Felipe. Todos los derechos reservados.
