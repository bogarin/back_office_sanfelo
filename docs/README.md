# Mapa de Documentación

> **📚 Bienvenido a la documentación del Backoffice de Trámites**

Este mapa te ayudará a encontrar la información que necesitas según tu rol y tus objetivos.

---

## 🗺️ Mapa Rápido

### ¿Quién eres?

| Tu rol | ¿Qué necesitas? | Empieza aquí |
|--------|-----------------|--------------|
| 👷 **Operador** | Usar el sistema diariamente | [Tutoriales Operadores](02-tutorials/operators/) |
| 👔 **Administrador** | Configurar usuarios y catálogos | [Tutoriales Administradores](02-tutorials/admins/) |
| 💻 **Desarrollador** | Desarrollar y mantener el sistema | [Tutoriales Desarrolladores](02-tutorials/developers/) |
| 🔧 **Sysadmin** | Desplegar y operar el sistema | [Guías Sysadmin](03-guides/sysadmins/) |
| 🤖 **Agente IA** | Entender el proyecto para LLM | [Documentación para IA](08-ai-optimized/) |

### ¿Qué necesitas hacer?

| Tarea | Documentación |
|-------|---------------|
| Crear tu primer trámite | [Tutorial: Crear Trámite](02-tutorials/operators/create-tramite.md) |
| Setup de desarrollo local | [Tutorial: Setup Local](02-tutorials/developers/local-dev-setup.md) |
| Desplegar en producción | [Guía: Deploy Producción](03-guides/sysadmins/deploy-production.md) |
| Configurar usuarios | [Tutorial: Configurar Usuarios](02-tutorials/admins/setup-users.md) |
| Entender la arquitectura | [Overview Arquitectura](01-onboarding/architecture-overview.md) |
| Consultar la API | [Referencia: API Endpoints](05-reference/api/endpoints.md) |

---

## 📂 Estructura de Directorios

```
docs/
│
├── 🏠 README.md (este archivo)
│
├── 01-onboarding/          # 🚀 Para nuevos miembros (todas las audiencias)
│   ├── overview.md         # ¿Qué es este proyecto?
│   ├── glossary.md         # Términos clave
│   └── architecture-overview.md  # Arquitectura visual
│
├── 02-tutorials/           # 📖 Aprendizaje guiado paso a paso
│   ├── operators/         # 👷 Operadores
│   ├── admins/            # 👔 Administradores
│   └── developers/        # 💻 Desarrolladores
│
├── 03-guides/             # 📋 Soluciones a problemas específicos
│   ├── operators/         # 👷 Operadores
│   ├── admins/            # 👔 Administradores
│   ├── sysadmins/         # 🔧 Sysadmins
│   └── developers/        # 💻 Desarrolladores
│
├── 04-concepts/           # 🧠 Explicaciones teóricas
│   ├── dual-database.md
│   ├── no-migrations.md
│   ├── denormalization.md
│   ├── caching-strategy.md
│   ├── auth-system.md
│   └── audit-system.md
│
├── 05-reference/          # 📖 Referencia técnica completa
│   ├── api/               # API endpoints, auth, errores
│   ├── models/            # Modelos de datos, SQL schema
│   ├── commands/          # Comandos Django
│   ├── configuration/     # Variables de entorno, settings
│   └── components/        # Admin, validator, caché
│
├── 06-decisions/          # 📋 ADRs (Decisiones de Arquitectura)
│   ├── README.md          # Índice de decisiones
│   ├── 001-stack-base.md
│   ├── 002-dual-database.md
│   ├── ...
│
├── 07-maintenance/        # 🔧 Mantenimiento
│   ├── release-notes.md
│   ├── upgrade-guide.md
│   ├── changelog.md
│   └── security-advisories.md
│
├── 08-ai-optimized/       # 🤖 Optimizado para LLMs
│   ├── context.md
│   ├── architecture-summary.md
│   ├── code-patterns.md
│   └── api-spec-json.md
│
└── _templates/           # 📝 Plantillas de documentos
    ├── tutorial-template.md
    ├── guide-template.md
    ├── concept-template.md
    └── reference-template.md
```

---

## 🔄 Tipos de Documentación

### Tutoriales (Tutorials) 📖

**Qué son**: Aprendizaje guiado paso a paso
**¿Para quién?**: Principiantes y nuevos miembros del equipo
**Ejemplos**:
- "Crear tu primer trámite en 5 minutos"
- "Setup de desarrollo local"
- "Configurar tus primeros usuarios"

**Ubicación**: [`02-tutorials/`](02-tutorials/)

---

### Guías (Guides) 📋

**Qué son**: Soluciones a problemas específicos
**¿Para quién?**: Usuarios con experiencia buscando soluciones rápidas
**Ejemplos**:
- "Cómo cambiar el estado de un trámite"
- "Cómo desplegar en producción"
- "Cómo debug el schema validator"

**Ubicación**: [`03-guides/`](03-guides/)

---

### Conceptos (Concepts) 🧠

**Qué son**: Explicaciones teóricas y contexto
**¿Para quién?**: Usuarios que necesitan entender "por qué"
**Ejemplos**:
- "Por qué usamos dos bases de datos"
- "Por qué denormalizamos datos"
- "Cómo funciona el sistema de caché"

**Ubicación**: [`04-concepts/`](04-concepts/)

---

### Referencia (Reference) 📖

**Qué son**: Documentación técnica exhaustiva y completa
**¿Para quién?**: Desarrolladores y Sysadmins
**Ejemplos**:
- "API Endpoints completos"
- "Variables de entorno"
- "Modelos de datos"

**Ubicación**: [`05-reference/`](05-reference/)

---

## 🎯 Rutas Recomendadas

### Ruta para Operadores 👷

```
README.md (Quick Start)
  ↓
02-tutorials/operators/create-tramite.md
  ↓
02-tutorials/operators/manage-workflow.md
  ↓
03-guides/operators/change-status.md
  ↓
03-guides/operators/upload-docs.md
  ↓
03-guides/operators/search-tramites.md
```

**Objetivo**: Usar el sistema diariamente para gestionar trámites

---

### Ruta para Administradores 👔

```
README.md (Quick Start - Administrators)
  ↓
02-tutorials/admins/setup-users.md
  ↓
02-tutorials/admins/manage-catalogs.md
  ↓
03-guides/admins/add-peritos.md
  ↓
03-guides/admins/configure-costs.md
  ↓
03-guides/admins/manage-groups.md
```

**Objetivo**: Configurar y administrar el sistema

---

### Ruta para Desarrolladores 💻

```
README.md (Quick Start - Developers)
  ↓
01-onboarding/architecture-overview.md
  ↓
02-tutorials/developers/local-dev-setup.md
  ↓
02-tutorials/developers/first-api-call.md
  ↓
04-concepts/* (leer según necesidad)
  ↓
03-guides/developers/* (consultar según tarea)
  ↓
05-reference/* (consultar según necesidad)
  ↓
06-decisions/* (cuando necesiten entender por qué)
```

**Objetivo**: Desarrollar, mantener y contribuir al sistema

---

### Ruta para Sysadmins 🔧

```
README.md (Quick Start - Production)
  ↓
03-guides/sysadmins/deploy-production.md
  ↓
03-guides/sysadmins/docker-setup.md
  ↓
03-guides/sysadmins/backup-restore.md
  ↓
03-guides/sysadmins/monitoring.md
  ↓
03-guides/sysadmins/troubleshoot.md
  ↓
05-reference/configuration/*
```

**Objetivo**: Desplegar, monitorear y mantener el sistema en producción

---

### Ruta para Agentes IA 🤖

```
08-ai-optimized/context.md (principal)
  ↓
08-ai-optimized/architecture-summary.md
  ↓
05-reference/api/endpoints.md
  ↓
05-reference/api/api-spec-json.md (JSON para parsing)
  ↓
06-decisions/* (restricciones arquitectónicas)
  ↓
04-concepts/* (entender dominio)
```

**Objetivo**: Entender el proyecto para tareas automatizadas con LLMs

---

## 📊 Matriz de Documentación por Rol y Tipo

| Tipo / Rol | Operador | Administrador | Desarrollador | Sysadmin | Agente IA |
|------------|----------|---------------|---------------|----------|------------|
| **Tutoriales** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Guías** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Conceptos** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Referencia** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **ADRs** | ❌ | ❌ | ✅ | ❌ | ✅ |
| **Optimizada para IA** | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 🔍 Búsqueda Rápida

### ¿Necesitas...?

| Buscar | Documentación |
|--------|---------------|
| Instalar el proyecto | [Tutorial: Setup Local](02-tutorials/developers/local-dev-setup.md) |
| Entender las bases de datos | [Concepto: Dual Database](04-concepts/dual-database.md) |
| Ver todos los endpoints API | [Referencia: API Endpoints](05-reference/api/endpoints.md) |
| Desplegar en Docker | [Guía: Docker Setup](03-guides/sysadmins/docker-setup.md) |
| Agregar un perito | [Guía: Add Peritos](03-guides/admins/add-peritos.md) |
| Ejecutar tests | [Guía: Run Tests](03-guides/developers/run-tests.md) |
| Debug schema validator | [Guía: Debug Schema](03-guides/developers/debug-schema.md) |
| Ver variables de entorno | [Referencia: Environment Vars](05-reference/configuration/environment-vars.md) |
| Entender por qué no migraciones | [Concepto: No Migrations](04-concepts/no-migrations.md) |
| Ver decisiones arquitectónicas | [ADRs: Índice](06-decisions/README.md) |

---

## 📚 Documentación Relacionada

### Para Proyectos de Django
- [Documentación oficial de Django](https://docs.djangoproject.com/)
- [Documentación de Django Admin](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)

### Para Despliegue
- [Documentación de Docker](https://docs.docker.com/)
- [Documentación de Gunicorn](https://docs.gunicorn.org/)

### Para Arquitectura
- [Plantilla de ADR](06-decisions/template.md)
- [Framework Diátaxis](https://diataxis.fr/) - Metodología de documentación

---

## 🤝 Contribuir a la Documentación

### ¿Cómo añadir documentación nueva?

1. **Identifica el tipo**: Tutorial, Guía, Concepto, o Referencia
2. **Usa la plantilla apropiada**: Ver plantillas en [`_templates/`](./_templates/)
3. **Ubica en el directorio correcto**: Según la estructura
4. **Agrega al mapa**: Actualiza este README.md
5. **Evita duplicación**: Verifica si ya existe contenido similar

### Principios clave

- ✅ **SSOT**: Una sola fuente de verdad para cada información
- ✅ **Divulgación progresiva**: Revelar información gradualmente
- ✅ **Centrado en el usuario**: Pensar en la audiencia objetivo
- ✅ **Andragogía**: Relevante, práctico, inmediato
- ✅ **Sin duplicación**: Usar referencias en lugar de repetir

---

## 🔗 Enlaces Importantes

- [Plan de Reestructuración](../RESTRUCTURING_PLAN.md) - Plan completo de documentación
- [README del Proyecto](../README.md) - Overview del proyecto
- [Lista de Tareas](./TASKS.md) - Tareas del proyecto
- [Resumen Ejecutivo](./EXECUTIVE_SUMMARY.md) - Resumen para stakeholders
- [Guía Rápida de Metodologías](./METHODOLOGIES_QUICKREF.md) - Referencia rápida

---

## 📅 Última Actualización

**Fecha**: 26 de Febrero de 2026

**Versión**: 1.0 (Propuesta)

**Estado**: Pendiente de aprobación e implementación

---

## 📊 Progreso

```
✅ Estructura de directorios creada
✅ Plantillas preparadas
⏳ Documentación por crear...
```

---

*¿Tienes dudas o sugerencias sobre la documentación? Abre un issue o PR en el repositorio.*
