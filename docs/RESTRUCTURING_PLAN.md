# Plan de Reestructuración de Documentación

## Estado Actual: Diagnóstico

### Problemas Identificados

1. **README.md como "dumping ground"**: El archivo principal contiene 494 líneas mezclando información para 5 audiencias diferentes
2. **Duplicación masiva**: Los mismos ejemplos de código aparecen en README, COMANDOS_DJANGO.md, DJANGO_ADMIN_SETUP.md
3. **Sin estructura progresiva**: No hay rutas claras de aprendizaje; todo está en el mismo nivel
4. **Audiencias mezcladas**: Operadores no técnicos ven configuración de base de datos; desarrolladores ven configuración del admin
5. **Falta de navegación**: No hay mapas de contenido ni guías para diferentes roles
6. **AI/LLM no optimizado**: Aunque mencionan agentes LLM, la estructura no facilita el parsing semántico

### Métricas del Problema

- **Total de líneas de documentación**: ~5,300 líneas
- **README.md**: 494 líneas (9.3% del total, pero 80% de lo que la gente ve primero)
- **Archivos en docs/**: 10 archivos markdown + 6 ADRs
- **Niveles de audiencia**: 5 tipos de usuarios completamente distintos

---

## Metodologías Recomendadas

### 1. Progressive Disclosure (Divulgación Progresiva)

**Qué es**: Revelar información gradualmente según la necesidad y el nivel del usuario.

**Aplicación práctica**:
- Principio de "3 clicks": Ningún usuario debería necesitar más de 3 clics para encontrar información crítica
- Resumen → Detalle → Profundidad: Cada concepto tiene 3 niveles de explicación
- "Need-to-know" basis: Ocultar detalles técnicos de usuarios no técnicos

**Estructura propuesta**:
```
Usuario llega → Ver ruta según rol → Nivel básico → "Saber más?" → Nivel avanzado
```

### 2. Diátaxis Framework

**Qué es**: Estructurar documentación en 4 categorías distinta, según la metodología de Daniel Nathans.

**Las 4 categorías**:

1. **Tutorials (Tutoriales)**: Aprendizaje guiado paso a paso
   - Audiencia: Principiantes, nuevos miembros del equipo
   - Ejemplo: "Crear tu primer trámite en 5 minutos"
   - No exhaustivo; se enfoca en un flujo completo

2. **How-to Guides (Guías Prácticas)**: Soluciones a problemas específicos
   - Audiencia: Usuarios con experiencia buscando soluciones rápidas
   - Ejemplo: "Cómo cambiar el estado de un trámite"
   - Prescriptivo y directo

3. **Explanation (Explicaciones/Teoría)**: Conceptos y contexto
   - Audiencia: Usuarios que necesitan entender "por qué"
   - Ejemplo: "Por qué usamos dos bases de datos"
   - Contextual, no tutorial

4. **Reference (Referencia)**: Información técnica exhaustiva
   - Audiencia: Desarrolladores, Sysadmins
   - Ejemplo: "API Endpoints completa", "Variables de entorno"
   - Estructurada y completa

**Aplicación a tu proyecto**:

| Tipo | Ubicación | Ejemplo | Audiencia |
|------|-----------|---------|-----------|
| Tutorial | `docs/tutorials/` | "Primeros pasos: Crear un trámite" | Operadores, Admins |
| How-to | `docs/guides/` | "Deploy en producción" | Sysadmins |
| Explanation | `docs/concepts/` | "Arquitectura dual de BD" | Developers, Sysadmins |
| Reference | `docs/reference/` | API Endpoints, Models, Env Vars | Developers, AI Agents |

### 3. Information Architecture (Arquitectura de la Información)

**Qué es**: Organizar el contenido de forma que sea descubrible y navegable.

**Principios aplicados**:
- **Task-based navigation**: Organizar por tareas, no por tecnología
- **User-centered design**: Estructurar según roles de usuario
- **Search-first design**: Optimizar para búsqueda (especialmente para LLMs)
- **Semantic structure**: Usar headings H1-H4 jerárquicamente para mejor parsing

### 4. Single Source of Truth (SSOT)

**Qué es**: Cada pieza de información vive en un solo lugar; el resto son referencias.

**Ejemplo actual (PROBLEMA)**:
```bash
# Ejemplo duplicado en 3 lugares:
uv run python manage.py runserver
# Aparece en: README.md, COMANDOS_DJANGO.md, DJANGO_ADMIN_SETUP.md
```

**Solución futura**:
```bash
# Vive solo en: docs/reference/commands.md
# Referencias en otros archivos:
# - README.md: → "See: [Commands Reference](docs/reference/commands.md)"
# - DJANGO_ADMIN_SETUP.md: → → "See: [Commands Reference](docs/reference/commands.md)"
```

### 5. Document-Driven Design (DDD)

**Qué es**: Documentar antes/durante el desarrollo, no después.

**Aplicación**:
- Documentación como PRD (Product Requirements Document)
- ADRs antes de implementar cambios arquitectónicos
- Documentación de API antes de escribir el código

### 6. Andragogy (Andragogía)

**Qué es**: Aprendizaje adulto - principios de educación para adultos.

**Principios**:
- **Inmediatez**: El adulto quiere información cuando la necesita ahora
- **Relevancia**: ¿Por qué me importa esto? (WIIFM - What's In It For Me?)
- **Experiencia previa**: Aprovechar conocimientos que ya tienen (Django, Python)
- **Orientación a problema**: Resolver problemas reales, no teoría abstracta
- **Autonomía**: Permitir autoexploración sin secuencia forzada

**Aplicación**:
- Operadores administrativos: "Cómo registrar un trámite nuevo" (no les importa la BD)
- Desarrolladores: "Implementar nuevo endpoint API" (no les importa el admin)
- Sysadmins: "Configurar Docker para producción" (no les importa la lógica de negocio)

### 7. Minimal Documentation (Documentación Mínima)

**Qué es**: "Menos es más" - documentar solo lo necesario.

**Principios**:
- No documentar lo obvio (Python/Django ya están documentados)
- No reinventar la rueda: Link a documentación oficial de Django
- Enfocarse en lo específico del proyecto: decisiones de arquitectura, configuración especial

---

## Nueva Estructura Propuesta

### Estructura de Directorios

```
backoffice_tramites/
├── README.md                          # 🏠 Entry point + Quick Start
├── docs/                             # 📚 Toda la documentación
│   │
│   ├── README.md                     # 🗺️ Mapa de documentación
│   │
│   ├── 01-onboarding/                # 🚀 Nuevos miembros (todas las audiencias)
│   │   ├── overview.md               # Qué es este proyecto (5 min)
│   │   ├── glossary.md               # Términos clave (tramite, perito, UMA)
│   │   └── architecture-overview.md  # Arquitectura visual
│   │
│   ├── 02-tutorials/                 # 📖 Aprendizaje guiado (Diátaxis: Tutorials)
│   │   ├── operators/
│   │   │   ├── create-tramite.md     # Tutorial: Crear tu primer trámite
│   │   │   └── manage-workflow.md    # Tutorial: Flujo de trabajo diario
│   │   ├── admins/
│   │   │   ├── setup-users.md        # Tutorial: Configurar usuarios
│   │   │   └── manage-catalogs.md    # Tutorial: Gestionar catálogos
│   │   └── developers/
│   │       ├── first-api-call.md     # Tutorial: Primera llamada a la API
│   │       └── local-dev-setup.md    # Tutorial: Setup de desarrollo local
│   │
│   ├── 03-guides/                    # 📋 Soluciones a problemas (Diátaxis: How-to)
│   │   ├── operators/
│   │   │   ├── change-status.md      # Guía: Cambiar estado de trámite
│   │   │   ├── upload-docs.md        # Guía: Subir documentos
│   │   │   └── search-tramites.md    # Guía: Búsqueda avanzada
│   │   ├── admins/
│   │   │   ├── add-peritos.md        # Guía: Agregar peritos
│   │   │   ├── configure-costs.md    # Guía: Configurar costos por trámite
│   │   │   └── manage-groups.md      # Guía: Gestionar grupos de usuarios
│   │   ├── sysadmins/
│   │   │   ├── deploy-production.md  # Guía: Despliegue en producción
│   │   │   ├── docker-setup.md       # Guía: Configurar Docker
│   │   │   ├── backup-restore.md     # Guía: Backups y restauración
│   │   │   ├── monitoring.md         # Guía: Monitoreo y alertas
│   │   │   └── troubleshoot.md        # Guía: Troubleshooting común
│   │   └── developers/
│   │       ├── add-model.md          # Guía: Añadir nuevo modelo
│   │       ├── create-api-endpoint.md # Guía: Crear endpoint API
│   │       ├── run-tests.md          # Guía: Ejecutar y escribir tests
│   │       ├── debug-schema.md       # Guía: Debug schema validator
│   │       └── contribute.md          # Guía: Proceso de contribución
│   │
│   ├── 04-concepts/                  # 🧠 Teoría y contexto (Diátaxis: Explanation)
│   │   ├── dual-database.md          # Concepto: Por qué dos BD
│   │   ├── no-migrations.md         # Concepto: Estrategia sin migraciones
│   │   ├── denormalization.md        # Concepto: Por qué denormalizar
│   │   ├── caching-strategy.md       # Concepto: Estrategia de caché
│   │   ├── auth-system.md            # Concepto: Sistema de autenticación
│   │   └── audit-system.md           # Concepto: Sistema de auditoría
│   │
│   ├── 05-reference/                 # 📖 Referencia técnica (Diátaxis: Reference)
│   │   ├── api/                      # API completa
│   │   │   ├── endpoints.md          # Todos los endpoints
│   │   │   ├── authentication.md     # Auth headers, JWT
│   │   │   ├── error-codes.md        # Códigos de error
│   │   │   └── examples.md           # Ejemplos de requests/responses
│   │   ├── models/                   # Modelos de datos
│   │   │   ├── data-models.md        # Diagramas y descripciones
│   │   │   ├── sql-schema.md         # Esquema SQL
│   │   │   └── model-mappings.md     # Mapeo SQL ↔ Django
│   │   ├── commands/                 # Comandos Django
│   │   │   ├── index.md              # Índice de comandos
│   │   │   ├── database.md           # Comandos de BD
│   │   │   ├── development.md        # Comandos de desarrollo
│   │   │   └── testing.md            # Comandos de testing
│   │   ├── configuration/             # Configuración
│   │   │   ├── environment-vars.md   # Variables de entorno (SSOT)
│   │   │   ├── settings.md           # Django settings
│   │   │   └── docker.md             # Docker configuration
│   │   └── components/               # Componentes
│   │       ├── admin-interface.md    # Django Admin
│   │       ├── schema-validator.md  # Validador de esquema
│   │       └── cache-redis.md        # Caché Redis
│   │
│   ├── 06-decisions/                 # 📋 ADRs (Architecture Decision Records)
│   │   ├── README.md                 # Índice de decisiones
│   │   ├── 001-stack-base.md         # Stack tecnológico
│   │   ├── 002-dual-database.md      # BD dual
│   │   ├── 003-no-migrations.md      # Sin migraciones
│   │   ├── 004-denormalization.md    # Denormalización
│   │   ├── 005-caching.md            # Estrategia de caché
│   │   ├── 006-docker-gunicorn.md    # Deploy Docker
│   │   ├── 007-auth-permissions.md  # Permisos
│   │   └── template.md               # Template para nuevos ADRs
│   │
│   ├── 07-maintenance/               # 🔧 Operaciones y mantenimiento
│   │   ├── release-notes.md          # Notas de versión
│   │   ├── upgrade-guide.md          # Guía de actualización
│   │   ├── changelog.md              # Cambios recientes
│   │   └── security-advisories.md    # Avisos de seguridad
│   │
│   └── 08-ai-optimized/              # 🤖 Optimizado para LLMs
│       ├── context.md                # Contexto del proyecto para agentes
│       ├── architecture-summary.md   # Resumen arquitectónico (LLM-friendly)
│       ├── code-patterns.md          # Patrones de código
│       └── api-spec-json.md          # API spec en formato JSON
│
├── docker-compose.yml
├── sql/
├── tramites/
└── ...
```

---

## Perfiles de Usuario y Rutas de Aprendizaje

### 1. Desarrolladores (Developers)

**Conocimiento previo**: Python, Django (no garantizado pero asumido)

**Qué necesitan**:
- Guías técnicas de implementación
- Referencia API completa
- Entender arquitectura y decisiones
- Proceso de contribución

**Ruta recomendada**:

```
README.md
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

**Contenido crítico**:
- Dual database strategy
- Schema validator usage
- API endpoints
- Environment variables
- Testing strategy

### 2. AI/LLM Agents

**Características**: Procesan texto estructurado, prefieren formato semántico

**Qué necesitan**:
- Contexto estructurado del proyecto
- Especificación técnica en formato parsable
- Patrones de código y arquitectura
- ADRs para entender restricciones

**Ruta recomendada**:

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

**Optimizaciones para LLMs**:
- JSON schemas para API
- Summaries en formato estructurado
- Sin imágenes de texto (todo Markdown)
- Headings jerárquicos H1-H6 para better parsing

### 3. Sysadmins

**Conocimiento previo**: Linux, Docker, PostgreSQL, Redis

**Qué necesitan**:
- Despliegue y configuración
- Monitoreo y logging
- Troubleshooting
- Backups y restore

**Ruta recomendada**:

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
05-reference/configuration/* (referencia detallada)
```

**Contenido crítico**:
- Docker configuration
- Environment variables
- Database setup (dual schema)
- Health checks
- Logging configuration

### 4. Administradores (Administrators)

**Conocimiento previo**: Gestión de sistemas, NO técnico en desarrollo

**Qué necesitan**:
- Uso de Django Admin
- Gestión de usuarios y permisos
- Configuración de catálogos y costos
- Reportes y auditoría

**Ruta recomendada**:

```
README.md (sección "Administrators")
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

**Contenido crítico**:
- No necesitan saber Python/Django
- Solo necesitan conocer la interfaz de Admin
- Entender el modelo de permisos (admin vs operador)
- Cómo configurar costos por trámite

### 5. Operadores (Operators)

**Conocimiento previo**: Usuarios del sistema, NO técnico

**Qué necesitan**:
- Uso diario del sistema
- Creación y gestión de trámites
- Subida de documentos
- Búsqueda y filtrado

**Ruta recomendada**:

```
README.md (sección "Operadores")
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

**Contenido crítico**:
- NO necesitan saber de base de datos, Django, etc.
- Solo flujo de trabajo del día a día
- Entender estados de trámite
- Cómo adjuntar documentos

---

## Nuevo README.md (Propuesta)

```markdown
# Backoffice de Trámites - Gobierno de San Felipe

Microservicio de gestión de trámites para las dependencias del gobierno de San Felipe.

## 🚀 Quick Start

### Para Operadores
Empezar a usar el sistema: **[Tutorial: Crear tu primer trámite](docs/02-tutorials/operators/create-tramite.md)**

### Para Administradores
Configurar el sistema: **[Tutorial: Configurar usuarios](docs/02-tutorials/admins/setup-users.md)**

### Para Desarrolladores
Setup de desarrollo local: **[Tutorial: Setup de desarrollo](docs/02-tutorials/developers/local-dev-setup.md)**

### Para Sysadmins
Despliegue en producción: **[Guía: Despliegue en producción](docs/03-guides/sysadmins/deploy-production.md)**

---

## 📋 Overview

### ¿Qué es este proyecto?

Sistema de gestión de trámites con:
- 📝 Gestión completa de trámites con historial
- 🗃️ Catálogos configurables (tipos, estatus, requisitos, peritos)
- 💰 Sistema de costos calculado por UMA
- 📊 Auditoría completa (bitácora de cambios)
- 🔄 Arquitectura de microservicio con API REST

**Leer más**: [Overview completo](docs/01-onboarding/overview.md)

### Arquitectura

- **Backend**: Django 6.0.2 (Python 3.14)
- **Bases de datos**: SQLite (auth) + PostgreSQL (business data)
- **Cache**: Redis
- **Interface**: Django Admin
- **Deploy**: Docker + Gunicorn

**Leer más**: [Arquitectura detallada](docs/01-onboarding/architecture-overview.md)

---

## 📚 Documentación

### Por Rol

| Rol | Documentación principal |
|-----|-------------------------|
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
| 🔧 **Mantenimiento** | Notas de versión y actualizaciones |

**Ver todo**: [Mapa de documentación](docs/README.md)

---

## 🔗 Enlaces Útiles

### Desarrollo
- [API Reference](docs/05-reference/api/endpoints.md)
- [Environment Variables](docs/05-reference/configuration/environment-vars.md)
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

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Python | Python | 3.14 |
| Framework | Django | 6.0.2 |
| Package Manager | uv | latest |
| Database (Auth) | SQLite | - |
| Database (Business) | PostgreSQL | - |
| Cache | Redis | - |
| WSGI Server | Gunicorn | - |
| Container | Docker | - |

---

## 📄 Licencia

Copyright © 2026 Gobierno de San Felipe. Todos los derechos reservados.
```

---

## Estrategia de Migración

### Fase 1: Preparación (Semana 1)

1. **Crear estructura de directorios**
   ```bash
   mkdir -p docs/{01-onboarding,02-tutorials/{operators,admins,developers},03-guides/{operators,admins,sysadmins,developers},04-concepts,05-reference/{api,models,commands,configuration,components},06-decisions,07-maintenance,08-ai-optimized}
   ```

2. **Crear documentos guía**
   - `docs/README.md` - Mapa de navegación
   - `docs/01-onboarding/overview.md` - Overview del proyecto
   - `docs/01-onboarding/architecture-overview.md` - Arquitectura

3. **Preparar plantillas**
   - Tutorial template
   - Guide template
   - Concept template
   - Reference template

### Fase 2: Extracción y Reorganización (Semana 2-3)

**De README.md:**
- Extrar "Instalación" → `02-tutorials/developers/local-dev-setup.md`
- Extrar "Despliegue" → `03-guides/sysadmins/deploy-production.md`
- Extrar "Comandos" → `05-reference/commands/index.md` (referencias)
- Extrar "API" → `05-reference/api/endpoints.md`
- Extrar "Modelos" → `05-reference/models/data-models.md`
- Extrar "Troubleshooting" → `03-guides/sysadmins/troubleshoot.md`

**De COMANDOS_DJANGO.md:**
- Mover completo a `05-reference/commands/index.md`
- Crear referencias desde otros docs

**De ENVIRONMENT_VARIABLES.md:**
- Mover completo a `05-reference/configuration/environment-vars.md`
- Crear resumen (quick reference) en nuevo README

**De DJANGO_ADMIN_SETUP.md:**
- Tutorial básico → `02-tutorials/admins/setup-users.md`
- Guías específicas → `03-guides/admins/`
- Referencia técnica → `05-reference/components/admin-interface.md`

**De SCHEMA_VALIDATOR.md:**
- Concepto → `04-concepts/no-migrations.md`
- Guía de uso → `03-guides/developers/debug-schema.md`
- Referencia técnica → `05-reference/components/schema-validator.md`

### Fase 3: Creación de Contenido Nuevo (Semana 4-5)

**Para Operadores:**
- Tutorial: "Crear tu primer trámite"
- Tutorial: "Flujo de trabajo diario"
- Guía: "Cambiar estado de trámite"
- Guía: "Subir documentos"
- Guía: "Búsqueda avanzada"

**Para Administradores:**
- Tutorial: "Configurar usuarios"
- Tutorial: "Gestionar catálogos"
- Guía: "Agregar peritos"
- Guía: "Configurar costos"
- Guía: "Gestionar grupos"

**Para Sysadmins:**
- Guía: "Docker setup"
- Guía: "Backup & restore"
- Guía: "Monitoring"
- Referencia: "Logging configuration"

**Para Desarrolladores:**
- Tutorial: "Primera llamada a la API"
- Guía: "Crear nuevo endpoint API"
- Guía: "Ejecutar tests"
- Guía: "Contribución"

**Optimización para LLM:**
- `08-ai-optimized/context.md` - Contexto estructurado
- `08-ai-optimized/architecture-summary.md` - Resumen en formato parsable
- `08-ai-optimized/api-spec-json.md` - API spec en JSON

### Fase 4: Revisión y Refinamiento (Semana 6)

1. **Auditoría de duplicaciones**
   - Buscar contenido duplicado con `grep -r "uv run python manage.py" docs/`
   - Consolidar en SSOT

2. **Validación de rutas**
   - Verificar cada rol tiene path claro
   - Verificar todos los links funcionan

3. **Testing de navegación**
   - Usar herramienta de link checking
   - Simular journey de cada tipo de usuario

4. **Optimización SEO/LLM**
   - Verificar headings jerárquicos
   - Agregar meta descripciones
   - Crear sitemap.json para LLMs

### Fase 5: Lanzamiento y Feedback (Semana 7-8)

1. **Publicar estructura nueva**
   - Mantener viejo README como `README.old.md`
   - Desplegar nueva estructura

2. **Recopilar feedback**
   - Survey a cada tipo de usuario
   - Métricas de búsqueda (¿qué buscan y no encuentran?)

3. **Iteración continua**
   - Actualizar basado en feedback
   - Ajustar categorización si necesario

---

## Templates para Documentos

### Template para Tutorial

```markdown
---
Title: [Título del tutorial]
Role: [operator|admin|developer|sysadmin]
Time: [X minutos]
Level: [beginner|intermediate|advanced]
Prerequisites: [Lo que necesitan saber antes]
---

## Resumen

[Descripción breve de qué aprenderán y qué construirán en este tutorial. 2-3 oraciones.]

## Lo que aprenderás

- [Concepto 1]
- [Concepto 2]
- [Concepto 3]

## Requisitos previos

- [Requisito 1]
- [Requisito 2]

## Paso 1: [Título del paso]

[Explicación del paso]

**Instrucciones**:
```bash
comando
```

**Resultado esperado**: [Lo que deberían ver]

## Paso 2: [Título del paso]

...

## Resumen

[Recapitulación de lo aprendido]

## ¿Qué sigue?

- [Enlace al siguiente tutorial]
- [Enlace a guías relacionadas]
```

### Template para Guía How-to

```markdown
---
Title: [Cómo X]
Role: [operator|admin|developer|sysadmin]
Related: [enlaces a conceptos relacionados]
---

## Resumen

[Problema que esta guía resuelve. 1 oración.]

## Use Case

[Describe cuándo usar esta guía. Ejemplo: "Usa esta guía cuando necesites X".]

## Instrucciones

### Paso 1: [Descripción]

[Instrucciones prescriptivas]

**Comando**:
```bash
comando
```

**Nota**: [Consejo o advertencia importante]

### Paso 2: [Descripción]

...

## Solución de problemas

| Problema | Solución |
|----------|----------|
| Problema 1 | Solución 1 |
| Problema 2 | Solución 2 |

## Referencias

- [Enlace a documentación oficial]
- [Enlace a conceptos relacionados]
```

### Template para Concepto

```markdown
---
Title: [Concepto]
Category: [architecture|data|security|performance]
Related ADR: [ADR-XXX](../06-decisions/XXX.md)
---

## ¿Qué es [Concepto]?

[Definición clara y concisa. 1-2 oraciones.]

## ¿Por qué lo usamos?

[Contexto del problema que este concepto resuelve. 2-3 oraciones.]

## Cómo funciona

[Explicación técnica de la implementación. Usar diagramas si aplica.]

```mermaid
[diagram si aplica]
```

## Trade-offs

| Ventajas | Desventajas |
|----------|-------------|
| Ventaja 1 | Desventaja 1 |
| Ventaja 2 | Desventaja 2 |

## Referencias

- [ADR relacionado](../06-decisions/XXX.md)
- [Enlaces a documentación externa]
```

### Template para Referencia

```markdown
---
Title: [Referencia]
Component: [API|Model|Command|Configuration]
Version: [Versión]
Last Updated: [Fecha]
---

## Quick Reference

[Tabla rápida con parámetros principales]

## Descripción

[Descripción técnica detallada. No explicaciones teóricas, solo hechos.]

## Parámetros

| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| param1 | string | ✅ Yes | - | Descripción |
| param2 | int | ❌ No | 10 | Descripción |

## Ejemplos

### Ejemplo 1: [Descripción]

```bash
# Ejemplo de uso
comando param1=value1 param2=100
```

**Output**:
```
Resultado esperado
```

## Errores

| Código | Descripción | Solución |
|--------|-------------|----------|
| 400 | Bad request | Ver parámetros |
| 404 | Not found | Verificar ID |

## Véase también

- [Referencia relacionada 1]
- [Referencia relacionada 2]
```

---

## Principios de Escritura

### Para Operadores y Administradores (No técnicos)

- ✅ Usar lenguaje simple, sin jerga técnica
- ✅ Enfocarse en tareas y resultados, no en cómo funciona
- ✅ Incluir capturas de pantalla de la interfaz
- ✅ Proveer ejemplos con datos reales del negocio
- ✅ Usar analogías del dominio (ej: "tramite como expediente")
- ❌ NO mencionar Python, Django, base de datos
- ❌ NO incluir código SQL o Python

### Para Desarrolladores

- ✅ Usar jerga técnica apropiada
- ✅ Incluir ejemplos de código y comandos
- ✅ Link a documentación oficial de Django
- ✅ Enfatizar decisiones arquitectónicas (con links a ADRs)
- ✅ Incluir diagramas de flujo y arquitectura
- ✅ Proveer patrones y mejores prácticas
- ❌ NO explicar conceptos básicos de Python/Django (asumen conocimiento)

### Para Sysadmins

- ✅ Enfocarse en configuración y operaciones
- ✅ Incluir comandos completos (copy-paste ready)
- ✅ Proveer comandos de verificación (health checks)
- ✅ Incluir troubleshooting común
- ✅ Documentar configuración de logging y monitoreo
- ❌ NO explicar la lógica de negocio del sistema
- ❌ NO incluir código de la aplicación

### Para AI/LLM Agents

- ✅ Estructura semántica (headings H1-H6 jerárquicos)
- ✅ Sintaxis clara y no ambigua
- ✅ Incluir esquemas JSON donde sea posible
- ✅ Resúmenes al inicio de cada documento
- ✅ Relaciones explícitas entre documentos ("ver también")
- ✅ Sin metáforas, humor o sarcasmo
- ❌ EVITAR contenido no textual (imágenes de texto)
- ❌ EVITAR formato no parsable (tablas complejas sin descripción)

---

## Métricas de Éxito

### Métricas Cualitativas

1. **Time to First Value (TTFV)**
   - Operadores: ¿Cuánto tiempo tardan en crear su primer trámite?
   - Desarrolladores: ¿Cuánto tiempo en hacer un deploy local?
   - Sysadmins: ¿Cuánto tiempo en desplegar en producción?

2. **Search Success Rate**
   - ¿Qué tan a menudo encuentran lo que buscan?
   - Encuestas a usuarios después de búsqueda

3. **Reduction in Support Tickets**
   - ¿Cuántos tickets de soporte se reducen?
   - Métrica: Tickets por usuario/mes

### Métricas Cuantitativas

1. **Documentación Coverage**
   - % de archivos con documentación
   - % de endpoints documentados
   - % de modelos con descripción

2. **Link Integrity**
   - % de links rotos (objetivo: 0%)
   - Tiempo para auditar links

3. **Documentation Freshness**
   - Edad promedio de documentación
   - % de documentación actualizada en últimos 3 meses

4. **LLM Parsing Efficiency**
   - Número de tokens necesarios para entender arquitectura
   - Número de documentos para tener contexto completo

---

## Herramientas Recomendadas

### Para Creación y Mantenimiento

1. **Markdown Linting**
   - [markdownlint](https://github.com/igorshubovych/markdownlint-cli)
   - Asegura consistencia de formato

2. **Link Checking**
   - [markdown-link-check](https://github.com/tcort/markdown-link-check)
   - Detecta links rotos

3. **Diagramas**
   - [Mermaid](https://mermaid.js.org/) - Diagramas en Markdown
   - [PlantUML](https://plantuml.com/) - Diagramas UML

4. **Preview**
   - [vscode](https://code.visualstudio.com/) con extensiones de Markdown

### Para LLMs

1. **API Documentation**
   - OpenAPI/Swagger spec en YAML/JSON
   - Exportar a JSON para fácil parsing

2. **Context Summarization**
   - Herramientas para resumir documentos automáticamente
   - Crear "executive summaries" para LLMs

3. **Vector Search**
   - Considerar [Obsidian](https://obsidian.md/) o similar
   - Links bidireccionales para mejor contexto

---

## Próximos Pasos

### Inmediato (Esta semana)

1. ✅ Revisar este plan con el equipo
2. ✅ Obtener feedback de cada tipo de usuario
3. ✅ Crear estructura de directorios
4. ✅ Elegir 1-2 documentos piloto para probar templates

### Corto Plazo (2-4 semanas)

1. ✅ Migrar documentación crítica (README → nueva estructura)
2. ✅ Crear documentación faltante para operadores
3. ✅ Implementar templates y validar
4. ✅ Auditar y eliminar duplicaciones

### Medio Plazo (1-2 meses)

1. ✅ Completar migración de toda la documentación
2. ✅ Crear documentación optimizada para LLMs
3. ✅ Implementar automatización (linting, link checking)
4. ✅ Establecer proceso de mantenimiento continuo

### Largo Plazo (3-6 meses)

1. ✅ Medir éxito con métricas cualitativas y cuantitativas
2. ✅ Iterar basado en feedback
3. ✅ Documentar patrones y mejores prácticas para el equipo
4. ✅ Considerar herramienta de documentación dedicada (Sphinx, Docusaurus, etc.)

---

## Conclusión

Este plan de reestructuración implementa:

✅ **Diátaxis Framework** - 4 categorías claras de documentación
✅ **Progressive Disclosure** - Información revelada gradualmente por necesidad
✅ **Andragogía** - Orientada a adultos, relevante y práctica
✅ **Information Architecture** - Estructura navegable y descubrible
✅ **SSOT** - Una sola fuente de verdad para cada información
✅ **User-centered** - Rutas específicas para cada tipo de usuario
✅ **LLM-optimized** - Estructura semántica para agentes de IA

El resultado será una documentación:
- **Más mantenible** (sin duplicaciones)
- **Más escalable** (estructura clara para crecer)
- **Más efectiva** (cada usuario encuentra lo que necesita rápido)
- **Más moderna** (optimizada para humanos y para IA)

---

*Este plan es un documento vivo. Debe ser revisado y actualizado según el feedback del equipo.*
