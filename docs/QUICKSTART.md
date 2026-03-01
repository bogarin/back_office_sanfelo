# Guía de Inicio Rápido - Qué Trabajar Hoy

> **Empieza a hacer progreso AHORA con estas victorias rápidas**
> Última actualización: 26 de Febrero de 2026

---

## 🚀 Acciones Inmediatas (Próximos 1-2 Horas)

### Opción 1: Para Desarrolladores (Configuración Técnica)

**Tiempo**: 1 hora
**Impacto**: Cimientos para todo el trabajo futuro

```bash
# 1. Crear nueva estructura de directorios
mkdir -p docs/01-onboarding
mkdir -p docs/02-tutorials/{operators,admins,developers}
mkdir -p docs/03-guides/{operators,admins,sysadmins,developers}
mkdir -p docs/04-concepts
mkdir -p docs/05-reference/{api,models,commands,configuration,components}
mkdir -p docs/06-decisions
mkdir -p docs/07-maintenance
mkdir -p docs/08-ai-optimized
mkdir -p docs/05-reference/api
mkdir -p docs/05-reference/models
mkdir -p docs/05-reference/commands
mkdir -p docs/05-reference/configuration
mkdir -p docs/05-reference/components

# 2. Mover ADRs existentes a nueva ubicación
mv docs/decisiones/* docs/06-decisions/
mv docs/adr/* docs/06-decisions/

# 3. Verificar estructura
tree docs -L 2
```

✅ **Tarea completada**: "Crear nueva estructura de directorios"

---

### Opción 2: Para Redactores Técnicos (Plantillas)

**Tiempo**: 2 horas
**Impacto**: Habilita creación de contenido consistente

Crear el primer archivo de plantilla:

```bash
# Crear directorio de plantillas
mkdir -p docs/_templates

# Crear Plantilla de Tutorial
cat > docs/_templates/tutorial-template.md << 'EOF'
---
Title: [Título del Tutorial]
Role: [operator|admin|developer|sysadmin]
Time: [X minutos]
Level: [beginner|intermediate|advanced]
Prerequisites: [Lo que necesitan saber antes]
---

## Resumen

[Descripción breve de qué aprenderán. 2-3 oraciones.]

## Lo que aprenderás

- [Concepto 1]
- [Concepto 2]

## Requisitos previos

- [Requisito 1]

## Paso 1: [Título]

[Instrucciones]

**Comando**:
```bash
comando
```

**Resultado esperado**: [Lo que deberían ver]

## Paso 2: [Título]

...

## ¿Qué sigue?

- [Siguiente tutorial]
- [Guías relacionadas]
EOF
```

✅ **Tarea completada**: "Documentar plantilla para documentos de Tutorial"

---

### Opción 3: Para Gestores de Proyecto (Feedback)

**Tiempo**: 4 horas
**Impacto**: Entender las necesidades de los usuarios

Crear y distribuir esta encuesta:

```markdown
# Encuesta de Documentación - Backoffice Trámites

**Tu rol**: [Operador/Admin/Desarrollador/Sysadmin]
**Fecha**: [Fecha]

## 1. Uso Actual

- ¿Con qué frecuencia usas la documentación actual?
  - [ ] Diariamente
  - [ ] Semanalmente
  - [ ] Mensualmente
  - [ ] Casi nunca

- ¿Qué sección de la documentación usas más?
  - [ ] README.md
  - [ ] COMANDOS_DJANGO.md
  - [ ] DJANGO_ADMIN_SETUP.md
  - [ ] ENVIRONMENT_VARIABLES.md
  - [ ] Otro: ______

## 2. Problemas Actuales

- ¿Cuál es el problema más grande con la documentación actual?
  - [ ] No encuentro lo que busco
  - [ ] Está mezclado (veo cosas que no necesito)
  - [ ] Está desactualizada
  - [ ] Es muy técnica/complicada
  - [ ] Otro: ______

- Describe una situación reciente donde la documentación te falló:
  _________________________________________________________________________

## 3. Tareas Comunes

- ¿Qué tareas haces más frecuentemente?
  1. ________________________
  2. ________________________
  3. ________________________

- Para estas tareas, ¿qué información necesitas?
  1. ________________________
  2. ________________________
  3. ________________________

## 4. Mejoras Deseadas

- Si pudieras cambiar una cosa de la documentación, ¿qué sería?
  _________________________________________________________________________

- ¿Qué tipo de documentación te ayudaría más?
  - [ ] Tutoriales paso a paso
  - [ ] Guías de solución de problemas
  - [ ] Referencia técnica
  - [ ] Explicaciones de cómo funciona el sistema
  - [ ] Otro: ______

## 5. Formato Preferido

- ¿Qué formato prefieres para aprender?
  - [ ] Texto con ejemplos
  - [ ] Capturas de pantalla
  - [ ] Videos
  - [ ] Diagramas
  - [ ] Otro: ______

- ¿Tienes alguna otra sugerencia?
  _________________________________________________________________________

¡Gracias por tu feedback!
```

✅ **Tarea completada**: "Crear encuesta de feedback para cada tipo de usuario"

---

## 📋 Esta Semana (3-4 Horas Cada Una)

### Prioridad 1: Establecer SSOT (Única Fuente de Verdad)

**Por qué es importante**: Elimina duplicación y hace el mantenimiento más fácil

**Tarea 1**: Mover documentación de comandos
```bash
# Mover a nueva ubicación SSOT
mv docs/COMANDOS_DJANGO.md docs/05-reference/commands/index.md
```

**Tarea 2**: Mover variables de entorno
```bash
# Mover a nueva ubicación SSOT
mv docs/ENVIRONMENT_VARIABLES.md docs/05-reference/configuration/environment-vars.md
```

**Tarea 3**: Crear redirecciones (para mantener enlaces viejos)
```bash
# Crear archivos viejos que apuntan a nueva ubicación
echo "# Referencia de Comandos

> ⚠️ **Este archivo se ha movido**
>
> Ver: [Referencia de Comandos](05-reference/commands/index.md)

Todos los comandos de gestión de Django están ahora documentados en la sección de referencia.
" > docs/COMANDOS_DJANGO.md
```

---

### Prioridad 2: Crear Materiales de Onboarding

**Por qué es importante**: Nuevos miembros del equipo pueden empezar independientemente

**Tarea**: Escribir overview del proyecto

Crear `docs/01-onboarding/overview.md`:

```markdown
# ¿Qué es el Backoffice de Trámites?

## Resumen

El Backoffice de Trámites es un microservicio de gestión de expedientes para las dependencias del gobierno de San Felipe, desplegado en intranet.

## Para quién es

Este sistema es utilizado por:
- **Operadores**: Gestionan trámites diarios
- **Administradores**: Configuran el sistema
- **Desarrolladores**: Mantienen y desarrollan el sistema
- **Sysadmins**: Despliegan y operan el sistema

## Qué hace

- 📝 Gestión completa de trámites con historial
- 🗃️ Catálogos configurables (tipos, estatus, requisitos)
- 💰 Sistema de costos calculado por UMA
- 📊 Auditoría completa (bitácora de cambios)
- 🔐 Sistema de permisos y roles

## Arquitectura Técnica

- **Backend**: Django 6.0.2 (Python 3.14)
- **Bases de datos**: SQLite (auth) + PostgreSQL (business)
- **Cache**: Redis
- **Interface**: Django Admin
- **Deploy**: Docker + Gunicorn

## Comenzar

- **Eres Operador**: [Tutorial: Crear tu primer trámite](../02-tutorials/operators/create-tramite.md)
- **Eres Administrador**: [Tutorial: Configurar usuarios](../02-tutorials/admins/setup-users.md)
- **Eres Desarrollador**: [Tutorial: Setup de desarrollo](../02-tutorials/developers/local-dev-setup.md)
- **Eres Sysadmin**: [Guía: Despliegue en producción](../03-guides/sysadmins/deploy-production.md)

## Leer más

- [Arquitectura detallada](architecture-overview.md)
- [Glosario de términos](glossary.md)
- [Documentación completa](../README_MAP.md)
```

---

### Prioridad 3: Extraer de README

**Por qué es importante**: Reducir README de 494 a ~150 líneas

**Tarea**: Extraer sección de instalación

Tomar este contenido de README.md y mover a `docs/02-tutorials/developers/local-dev-setup.md`:

```markdown
# Instalación y Setup de Desarrollo Local

## Resumen

Esta guía te muestra cómo configurar un entorno de desarrollo local para el Backoffice de Trámites.

**Tiempo estimado**: 30 minutos

## Requisitos previos

- Python 3.14
- uv (gestor de paquetes)
- PostgreSQL
- Redis

## Paso 1: Clonar el proyecto

\`\`\`bash
git clone <repo-url>
cd backoffice_tramites
\`\`\`

## Paso 2: Instalar dependencias

\`\`\`bash
uv sync
\`\`\`

## Paso 3: Configurar base de datos

\`\`\`bash
# Aplicar esquema inicial
psql -U postgres -d sanfelipe_tramites -f sql/migrations/001_init_schema.sql

# Cargar datos iniciales
psql -U postgres -d sanfelipe_tramites -f sql/data/001_tipos_tramites.sql
\`\`\`

## Paso 4: Crear superusuario

\`\`\`bash
uv run python manage.py createsuperuser
\`\`\`

## Paso 5: Iniciar servidor

\`\`\`bash
uv run python manage.py runserver
\`\`\`

## Verificar

1. Abre http://localhost:8000
2. Deberías ver la página de inicio
3. Accede a /admin/ con el superusuario creado

## Problemas comunes

| Error | Solución |
|-------|----------|
| "Table doesn't exist" | Ejecuta los scripts SQL |
| "uv command not found" | Instala uv: https://docs.astral.sh/uv/ |
| "PostgreSQL connection failed" | Verifica que PostgreSQL esté corriendo |

## ¿Qué sigue?

- [Tutorial: Primera llamada a la API](../02-tutorials/developers/first-api-call.md)
- [Guía: Crear nuevo endpoint](../03-guides/developers/create-api-endpoint.md)
- [Referencia: Comandos Django](../05-reference/commands/index.md)
```

---

## 🎯 Elige Tu Ruta

### Si tienes 1 hora → Opción 1 o 2 arriba
### Si tienes 4 horas → Prioridad 1 o 2 arriba
### Si tienes 8+ horas → Todo lo anterior

---

## 📊 Seguimiento de Progreso

Después de completar tareas, actualizar estado:

1. Abrir `docs/TASKS.md`
2. Encontrar número de tarea
3. Cambiar `⏳ Pendiente` a `✅ Completada`
4. Actualizar barra de progreso al inicio

---

## 💡 Consejos Pro

### Para Desarrolladores
- Empieza con la estructura de directorios - es fácil y proporciona valor inmediato
- Mueve archivos existentes primero antes de crear contenido nuevo
- Prueba que los enlaces viejos sigan funcionando después de mover archivos

### Para Redactores Técnicos
- Empieza con plantillas - aseguran consistencia
- Escribe el overview primero - es fundamental
- Obtén feedback de usuarios reales antes de escribir tutoriales

### Para Gestores de Proyecto
- Envía encuestas hoy - el feedback toma tiempo en recopilarse
- Habla con 1-2 personas de cada rol informalmente
- Enfócate en "puntos de dolor" - qué les frustra más

---

## 🆘 ¿Necesitas Ayuda?

### ¿Preguntas sobre metodología?
Ver: [METHODOLOGIES_QUICKREF.md](./METHODOLOGIES_QUICKREF.md)

### ¿Preguntas sobre tareas?
Ver: [TASKS.md](./TASKS.md)

### ¿Preguntas sobre el plan general?
Ver: [RESTRUCTURING_PLAN.md](./RESTRUCTURING_PLAN.md)

---

## ✅ Criterios de Éxito de Hoy

Al final de hoy, deberías tener:

- [ ] Creada nueva estructura de directorios O
- [ ] Creada al menos 1 plantilla O
- [ ] Recopilado feedback de 1-2 usuarios

**¡Cualquier progreso es buen progreso!** 🎉

---

## 📖 Siguientes Pasos

Revisar tareas completadas y elegir el trabajo de mañana de `TASKS.md`

---

*Última actualización: 26 de Febrero de 2026*
