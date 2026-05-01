# Historias de Usuario

**Autores:** Noe Nieto, Jose Ramon Bogarin, Carlos Ahizotl
**Estatus:** Aprobado
**Fecha de actualización:** 28 Abril 2026

## 1. Introducción

Este documento contiene las historias de usuario agrupadas por rol, que cubren las funcionalidades principales del sistema de gestión de trámites municipales.

**Roles del sistema:**
1. Programador (Desarrollo)
2. Sysadmin/DBA (Infraestructura)
3. Administrador (Negocio - gestión del sistema)
4. Coordinador (Negocio - supervisión)
5. Analista (Negocio - operación)

---

## 2. Rol: Programador

### HU-01: Configurar Entorno de Desarrollo

**Como** programador,
**quiero** configurar el entorno de desarrollo rápidamente,
**para** empezar a desarrollar nuevas funcionalidades.

**Criterios de aceptación:**
- ✅ Comando único para instalar dependencias (`uv sync`)
- ✅ Scripts automatizados para migraciones de base de datos
- ✅ Servidor de desarrollo con hot-reload (`just dev`)
- ✅ Configuración local sin dependencias externas (SFTP mock)

**Prioridad:** Alta
**Epic:** Onboarding de desarrollo
**Referencias:**
- [docs/01-onboarding/](../01-onboarding/) - Guía completa de onboarding

---

### HU-02: Agregar Nuevo Modelo al Sistema

**Como** programador,
**quiero** agregar un nuevo modelo al sistema siguiendo las convenciones existentes,
**para** mantener consistencia y evitar errores.

**Criterios de aceptación:**
- ✅ Definir access pattern (FULL_ACCESS, READ_ONLY, APPEND_ONLY)
- ✅ Aplicar decorador `@register_model()` con schema correcto
- ✅ Asignar manager apropiado (DefaultManager, ReadOnlyManager, CreateOnlyManager)
- ✅ Crear tests unitarios para el modelo

**Ejemplo:**

```python
@register_model('backend', AccessPattern.READ_ONLY, False)
class NuevoModelo(models.Model):
    campos = ...
    objects = ReadOnlyManager()
```

**Prioridad:** Media
**Epic:** Desarrollo de nuevas funcionalidades
**Referencias:**
- [01-ARQUITECTURA.md](01-ARQUITECTURA.md) - Access patterns y managers
- [03-MODELO-DE-DATOS.md](03-MODELO-DE-DATOS.md) - Convenciones de modelos

---

### HU-03: Desplegar en Staging

**Como** programador,
**quiero** desplegar cambios a ambiente de staging,
**para** probar nuevas funcionalidades antes de producción.

**Criterios de aceptación:**
- ✅ Pipeline automatizado de CI/CD
- ✅ Despliegue en contenedor Docker
- ✅ Migraciones de base de datos automáticas
- ✅ Tests automatizados antes del despliegue
- ✅ Rollback simple en caso de error

**Prioridad:** Alta
**Epic:** Despliegue continuo
**Referencias:**
- [README.md](../README.md) - Comandos de despliegue

---

### HU-04: Ejecutar Tests Automatizados

**Como** programador,
**quiero** ejecutar tests automatizados para validar cambios,
**para** asegurar que no rompo funcionalidades existentes.

**Criterios de aceptación:**
- ✅ Comando simple para ejecutar todos los tests (`pytest`)
- ✅ Comando para ejecutar tests específicos de un módulo
- ✅ Cobertura de código visible en reportes
- ✅ Tests rápidos (< 5 segundos para suite completa)

**Prioridad:** Alta
**Epic:** Calidad de código
**Referencias:**
- [README.md](../README.md) - Comandos de testing

---

## 3. Rol: Sysadmin/DBA

### HU-05: Monitorear Base de Datos PostgreSQL

**Como** sysadmin/DBA,
**quiero** monitorear el rendimiento de PostgreSQL,
**para** identificar cuellos de botella y optimizar queries.

**Criterios de aceptación:**
- ✅ Dashboard con métricas en tiempo real (conexiones, locks, slow queries)
- ✅ Alertas para queries lentos (> 2 segundos)
- ✅ Monitoreo de espacio en disco por esquema
- ✅ Logs de consultas disponibles para análisis

**Prioridad:** Media
**Epic:** Monitoreo y observabilidad
**Referencias:**
- [01-ARQUITECTURA.md](01-ARQUITECTURA.md) - Arquitectura de base de datos

---

### HU-06: Realizar Backups Automáticos

**Como** DBA,
**quiero** realizar backups automáticos diarios de PostgreSQL,
**para** proteger los datos del sistema ante fallos.

**Criterios de aceptación:**
- ✅ Backup completo diario a las 2 AM
- ✅ Backup incremental cada 6 horas
- ✅ Retención de 7 días de backups
- ✅ Restauración probada mensualmente
- ✅ Backups almacenados en ubicación segura (off-site)

**Prioridad:** Alta
**Epic:** Recuperación de desastres
**Referencias:**
- [ADR-008: PostgreSQL Schema Separation](../06-decisions/008-postgresql-schema-separation.md)

---

### HU-07: Monitorear Servidor SFTP

**Como** sysadmin,
**quiero** monitorear el servidor SFTP de documentos,
**para** asegurar disponibilidad y detectar anomalías.

**Criterios de aceptación:**
- ✅ Monitoreo de espacio en disco (`/data/tramites/`)
- ✅ Alertas cuando espacio > 80%
- ✅ Logs de accesos y descargas disponibles
- ✅ Verificación de integridad de archivos almacenados

**Prioridad:** Media
**Epic:** Monitoreo de servicios externos
**Referencias:**
- [ADR-010: Integración con SFTP](../06-decisions/010-integracion-con-sftp.md)

---

### HU-08: Escalar Contenedor Docker

**Como** sysadmin,
**quiero** escalar el contenedor Docker cuando aumenta la carga,
**para** mantener performance del sistema.

**Criterios de aceptación:**
- ✅ Métricas de CPU y memoria del contenedor disponibles
- ✅ Escalado manual vía comandos simples
- ✅ Escalado automático basado en thresholds configurables
- ✅ Zero-downtime durante escalado

**Prioridad:** Media
**Epic:** Escalabilidad y performance
**Referencias:**
- [README.md](../README.md) - Despliegue y contenedores

---

## 4. Rol: Administrador

### HU-09: Crear Usuario Nuevo

**Como** administrador,
**quiero** crear un nuevo usuario en el sistema,
**para** permitir que un nuevo funcionario acceda al backoffice.

**Criterios de aceptación:**
- ✅ Formulario con campos: username, correo, nombre completo
- ✅ Asignación de rol (Administrador, Coordinador, Analista)
- ✅ Generación automática de contraseña temporal
- ✅ Envío de correo con credenciales de acceso
- ✅ Opción para forzar cambio de contraseña en primer login

**Prioridad:** Alta
**Epic:** Gestión de usuarios
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-05 (Auditoría)

---

### HU-10: Editar Usuario Existente

**Como** administrador,
**quiero** editar datos de un usuario existente,
**para** mantener la información actualizada.

**Criterios de aceptación:**
- ✅ Permitir cambiar: correo, nombre completo, rol
- ✅ Restringir cambio de username (inmutable por seguridad)
- ✅ Bloquear usuario (is_active = False) si es necesario
- ✅ Desbloquear usuario y restablecer contraseña

**Prioridad:** Media
**Epic:** Gestión de usuarios
**Referencias:**
- [01-ARQUITECTURA.md](01-ARQUITECTURA.md) - Custom User Model

---

### HU-11: Eliminar Usuario

**Como** administrador,
**quiero** eliminar un usuario que ya no trabaja en el municipio,
**para** mantener el sistema limpio.

**Criterios de aceptación:**
- ✅ Confirmación con advertencia de riesgos
- ✅ Verificación de que el usuario no tiene trámites asignados activos
- ✅ Opción de reasignar trámites a otro usuario antes de eliminar
- ✅ Auditoría de la acción en log de actividades

**Prioridad:** Baja
**Epic:** Gestión de usuarios
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-05 (Auditoría)

---

### HU-12: Asignar Rol a Usuario

**Como** administrador,
**quiero** asignar o cambiar el rol de un usuario,
**para** controlar qué funcionalidades puede acceder.

**Criterios de aceptación:**
- ✅ Selector de rol: Administrador, Coordinador, Analista
- ✅ Descripción clara de permisos de cada rol
- ✅ Confirmación antes de cambiar rol
- ✅ Auditoría del cambio en log de actividades

**Prioridad:** Alta
**Epic:** Gestión de usuarios y RBAC
**Referencias:**
- [01-ARQUITECTURA.md](01-ARQUITECTURA.md) - Matriz de permisos por rol

---

### HU-13: Ver Estadísticas Generales del Sistema

**Como** administrador,
**quiero** ver estadísticas generales del sistema,
**para** monitorear la salud del backoffice.

**Criterios de aceptación:**
- ✅ Dashboard con métricas: total de trámites, trámites por estado, trámites por analista
- ✅ Gráficos de tendencia mensual de trámites
- ✅ Tiempos promedio de proceso por tipo de trámite
- ✅ Usuarios activos en el último mes

**Prioridad:** Media
**Epic:** Reporting y analítica
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-07 (Estadísticas)

---

## 5. Rol: Coordinador

### HU-14: Ver Todos los Trámites Activos

**Como** coordinador,
**quiero** ver todos los trámites activos del sistema,
**para** tener visibilidad completa del flujo de trabajo.

**Criterios de aceptación:**
- ✅ Listado de trámites con filtros: estado, tipo, analista, fecha, urgente
- ✅ Paginación de 50 trámites por página
- ✅ Ordenamiento por defecto: creado DESC, urgente DESC
- ✅ Resaltado visual de trámites urgentes

**Prioridad:** Alta
**Epic:** Monitoreo de trámites
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-08 (Vistas por rol)

---

### HU-15: Asignar Trámite a Analista Específico

**Como** coordinador,
**quiero** asignar un trámite del pool a un analista específico,
**para** distribuir la carga de trabajo equitativamente.

**Criterios de aceptación:**
- ✅ Acción "Asignar" disponible en trámites sin asignar
- ✅ Selector de analistas (solo usuarios con rol Analista activos)
- ✅ Mostrar carga actual de trabajo de cada analista (# trámites asignados)
- ✅ Confirmación antes de asignar
- ✅ Auditoría de la asignación en log de actividades

**Prioridad:** Alta
**Epic:** Gestión de asignaciones
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-02 (Asignación)

---

### HU-16: Reasignar Trámite Entre Analistas

**Como** coordinador,
**quiero** reasignar un trámite de un analista a otro,
**para** ajustar la carga de trabajo o por cambio de asignación.

**Criterios de aceptación:**
- ✅ Acción "Reasignar" disponible en trámites asignados
- ✅ Mostrar analista actual y permitir seleccionar nuevo analista
- ✅ Campo de observación obligatorio para justificar reasignación
- ✅ Auditoría de la reasignación en log de actividades

**Prioridad:** Alta
**Epic:** Gestión de asignaciones
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-02 (Asignación)

---

### HU-17: Liberar Trámite al Pool

**Como** coordinador,
**quiero** liberar un trámite asignado y devolverlo al pool,
**para** que esté disponible para otros analistas.

**Criterios de aceptación:**
- ✅ Acción "Liberar" disponible en trámites asignados
- ✅ Confirmación con advertencia de que perderá asignación
- ✅ Campo de observación opcional para justificar liberación
- ✅ Auditoría de la liberación en log de actividades

**Prioridad:** Alta
**Epic:** Gestión de asignaciones
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-02 (Asignación)

---

### HU-18: Ver Carga de Trabajo por Analista

**Como** coordinador,
**quiero** ver la carga de trabajo de cada analista,
**para** distribuir trámites equitativamente.

**Criterios de aceptación:**
- ✅ Tabla con: analista, # trámites asignados, # urgentes, tiempo promedio en estatus
- ✅ Ordenamiento por # de trámites asignados
- ✅ Filtros por fecha y tipo de trámite
- ✅ Actualización en tiempo real (cache de 5 minutos)

**Prioridad:** Media
**Epic:** Monitoreo de carga de trabajo
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-07 (Estadísticas)

---

### HU-19: Ver Trámites Cerrados

**Como** coordinador,
**quiero** ver trámenes finalizados (estados 3xx),
**para** analizar tendencias y métricas de cierre.

**Criterios de aceptación:**
- ✅ Vista "Cerrados" filtrada por estados 3xx
- ✅ Filtros: rango de fechas, tipo de trámite, analista
- ✅ Paginación de 50 trámites por página
- ✅ Exportación a CSV/Excel para análisis externo

**Prioridad:** Media
**Epic:** Análisis de trámites cerrados
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-08 (Vistas por rol)
- [03-MODELO-DE-DATOS.md](03-MODELO-DE-DATOS.md) - Modelo proxy Cerrado

---

### HU-20: Cambiar Estatus de Cualquier Trámite

**Como** coordinador,
**quiero** cambiar el estatus de cualquier trámite,
**para** corregir errores o ajustar el flujo de trabajo.

**Criterios de aceptación:**
- ✅ Selector de estatus filtrado por transiciones válidas (diccionario TRANSITIONS)
- ✅ Campo de observación obligatorio para justificar cambio
- ✅ Confirmación antes de cambiar estatus
- ✅ Auditoría del cambio en log de actividades

**Prioridad:** Alta
**Epic:** Gestión de workflow
**Referencias:**
- [01-ARQUITECTURA.md](01-ARQUITECTURA.md) - Workflow engine (TRANSITIONS)

---

## 6. Rol: Analista

### HU-21: Ver Mis Trámites Asignados

**Como** analista,
**quiero** ver solo mis trámites asignados (buzón),
**para** enfocarme en mi carga de trabajo personal.

**Criterios de aceptación:**
- ✅ Vista "Buzón" filtrada por `asignado_user_id == user.id`
- ✅ Solo trámites en estados activos (2xx)
- ✅ Filtros: estado, tipo de trámite, fecha, urgente
- ✅ Paginación de 50 trámites por página
- ✅ Ordenamiento por defecto: creado DESC, urgente DESC

**Prioridad:** Alta
**Epic:** Gestión personal de trámites
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-02 (Asignación)
- [03-MODELO-DE-DATOS.md](03-MODELO-DE-DATOS.md) - Modelo proxy Buzon

---

### HU-22: Ver Trámites Disponibles

**Como** analista,
**quiero** ver trámites disponibles en el pool,
**para** autoasignarme trámites cuando tenga capacidad.

**Criterios de aceptación:**
- ✅ Vista "Disponibles" filtrada por `asignado_user_id IS NULL`
- ✅ Solo trámites en estado PRESENTADO (201)
- ✅ Filtros: tipo de trámite, fecha, urgente
- ✅ Paginación de 50 trámites por página
- ✅ Acción "Tomar" disponible para autoasignación

**Prioridad:** Alta
**Epic:** Autoasignación de trámites
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-02 (Asignación)
- [03-MODELO-DE-DATOS.md](03-MODELO-DE-DATOS.md) - Modelo proxy Disponible

---

### HU-23: Autoasignar Trámite

**Como** analista,
**quiero** autoasignarme un trámite disponible,
**para** comenzar a trabajar en él inmediatamente.

**Criterios de aceptación:**
- ✅ Acción "Tomar" disponible en trámites de la vista "Disponibles"
- ✅ Confirmación simple para confirmar autoasignación
- ✅ Auditoría de la autoasignación en log de actividades
- ✅ Trámite desaparece de "Disponibles" y aparece en "Buzón"

**Prioridad:** Alta
**Epic:** Autoasignación de trámites
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-02 (Asignación)

---

### HU-24: Cambiar Estatus de Mis Trámites

**Como** analista,
**quiero** cambiar el estatus de mis trámites asignados,
**para** avanzar el workflow del trámite.

**Criterios de aceptación:**
- ✅ Selector de estatus filtrado por transiciones válidas (diccionario TRANSITIONS)
- ✅ Solo puedo cambiar estatus de trámites asignados a mí
- ✅ Campo de observación obligatorio para justificar cambio
- ✅ Confirmación antes de cambiar estatus
- ✅ Auditoría del cambio en log de actividades

**Prioridad:** Alta
**Epic:** Gestión de workflow personal
**Referencias:**
- [01-ARQUITECTURA.md](01-ARQUITECTURA.md) - Permission methods

---

### HU-25: Descargar Documentos de Mis Trámites

**Como** analista,
**quiero** descargar los documentos PDF de mis trámites asignados,
**para** revisar los requisitos presentados por el ciudadano.

**Criterios de aceptación:**
- ✅ Lista de documentos disponibles por trámite
- ✅ Acción "Descargar" con X-Accel-Redirect para performance
- ✅ Auditoría de cada descarga en log de actividades
- ✅ Cache de archivos descargados en servidor

**Prioridad:** Alta
**Epic:** Gestión de documentos
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-03 (Gestión de documentos SFTP)
- [ADR-010: Integración con SFTP](../06-decisions/010-integracion-con-sftp.md)

---

### HU-26: Agregar Observaciones a Trámite

**Como** analista,
**quiero** agregar observaciones a un trámite,
**para** documentar notas importantes o decisiones.

**Criterios de aceptación:**
- ✅ Campo de texto libre para observaciones
- ✅ Validación de longitud mínima (10 caracteres)
- ✅ Observaciones almacenadas en campo `observacion` (**SIN acento**)
- ✅ Auditoría de la adición en log de actividades

**Prioridad:** Media
**Epic:** Gestión de trámites
**Referencias:**
- [03-MODELO-DE-DATOS.md](03-MODELO-DE-DATOS.md) - Convenciones de acentos

---

### HU-27: Buscar Trámite por Folio

**Como** analista,
**quiero** buscar un trámite específico por su folio,
**para** ubicarlo rápidamente.

**Criterios de aceptación:**
- ✅ Campo de búsqueda de texto libre en vista de trámites
- ✅ Búsqueda por folio exacto o parcial
- ✅ Resultados destacados visualmente
- ✅ Autocomplete de folios frecuentes

**Prioridad:** Media
**Epic:** Búsqueda y filtrado
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-06 (Búsquedas y filtros)

---

### HU-28: Ver Historial de Actividades de Trámite

**Como** analista,
**quiero** ver el historial completo de actividades de un trámite,
**para** entender su evolución y acciones previas.

**Criterios de aceptación:**
- ✅ Timeline de actividades con: fecha, usuario, estatus_anterior → estatus_nuevo, observacion
- ✅ Orden cronológico (más reciente arriba)
- ✅ Filtros por rango de fechas y usuario
- ✅ Exportación a PDF para compartir

**Prioridad:** Media
**Epic:** Trazabilidad de trámites
**Referencias:**
- [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md) - RF-05 (Auditoría completa)
- [03-MODELO-DE-DATOS.md](03-MODELO-DE-DATOS.md) - Modelo Actividades (APPEND_ONLY)

---

## 7. Matriz de Prioridades por Rol

| Rol | HUs Alta Prioridad | HUs Media Prioridad | HUs Baja Prioridad |
|-----|-------------------|---------------------|-------------------|
| **Programador** | HU-01, HU-02, HU-04 | HU-03 | - |
| **Sysadmin/DBA** | HU-06 | HU-05, HU-07, HU-08 | - |
| **Administrador** | HU-09, HU-12 | HU-10, HU-13 | HU-11 |
| **Coordinador** | HU-14, HU-15, HU-16, HU-17, HU-20 | HU-18, HU-19 | - |
| **Analista** | HU-21, HU-22, HU-23, HU-24, HU-25 | HU-26, HU-27, HU-28 | - |

---

## 8. Notas Importantes

### 8.1 Convención de Acentos

Todas las observaciones y textos usan **SIN acentos**:
- Campo `observacion` (no `observación`)
- Estado `en_diligencia` (no `en_diligència`)
- Campo `es_activo` (no `es_actívo`)

### 8.2 Auditoría

Todas las acciones de negocio (crear, editar, eliminar) generan un registro en la tabla `actividades` para trazabilidad completa.

### 8.3 Permisos

Analistas SOLO pueden:
- Ver y cambiar estatus de sus trámites asignados
- Descargar documentos de trámites asignados o disponibles activos

Coordinadores y Administradores pueden:
- Ver y cambiar estatus de CUALQUIER trámite
- Descargar documentos de CUALQUIER trámite
- Asignar/reasignar/liberar trámites

---

## 9. Referencias Externas

Para detalles completos sobre:

- **Requerimientos de negocio:** [00-REQUERIMIENTOS.md](00-REQUERIMIENTOS.md)
- **Arquitectura técnica:** [01-ARQUITECTURA.md](01-ARQUITECTURA.md)
- **Modelo de datos:** [03-MODELO-DE-DATOS.md](03-MODELO-DE-DATOS.md)
- **Decisiones de arquitectura:** [ADR Repository](../06-decisions/)
