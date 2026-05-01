# Requerimientos de Negocio - Backoffice de Trámites

**Autores:** Noe Nieto, Jose Ramon Bogarin, Carlos Ahizotl
**Estatus:** Aprobado
**Fecha de actualización:** 28 Abril 2026

## 1. Resumen Ejecutivo

El sistema debe permitir a los analistas administrar el ciclo de vida completo de los trámites municipales con trazabilidad completa y control de acceso basado en tres roles principales: Administrador, Coordinador y Analista.

## 2. Dominio del Problema

### 2.1 Contexto

El Gobierno de San Felipe gestiona cientos de trámites municipales diariamente. Anteriormente, los analistas trabajaban con sistemas dispersos, archivos en papel y procesos manuales que dificultaban el seguimiento y la toma de decisiones.

### 2.2 Objetivo del Sistema

Centralizar la gestión de trámites en una aplicación web que permita:
- Asignación transparente de trámites a analistas
- Seguimiento del estado de cada trámite en tiempo real
- Auditoría completa de todas las acciones
- Acceso controlado según tres roles definidos

## 3. Usuarios del Sistema

| Rol | Descripción | Responsabilidades Principales |
|-----|-------------|------------------------------|
| **Analista** | Funcionario que procesa trámites | Ver sus trámites + disponibles, tomar trámites, cambiar estatus |
| **Coordinador** | Supervisor de área | Asignar/reasignar trámites, monitorear carga de trabajo |
| **Administrador** | Gestor del sistema | Configuración, usuarios, catálogos, reportes |

## 4. Requerimientos Funcionales de Negocio

### RF-01: Ciclo de Vida de Trámites

El sistema debe soportar el flujo completo de trámites con 11 estados organizados en tres categorías principales:

#### Estados de Inicio (1xx)
- **101 - BORRADOR**: El ciudadano está capturando información del trámite
- **102 - PENDIENTE_PAGO**: El trámite está bloqueado esperando confirmación de pago
- **103 - PAGO_EXPIRADO**: La línea de captura venció sin confirmación de pago

#### Estados de Proceso (2xx)
- **201 - PRESENTADO**: Pago confirmado, trámite entra a bandeja para asignación
- **202 - EN_REVISION**: Analista está revisando documentos y validando requisitos
- **203 - REQUERIMIENTO**: Falta información, ciudadano debe corregir o completar
- **205 - EN_DILIGENCIA**: Fase de campo: mediciones, inspecciones, visitas a terreno

#### Estados Finalizados (3xx)
- **301 - POR_RECOGER**: Documento disponible para descarga por el ciudadano
- **302 - RECHAZADO**: Resolución negativa del trámite
- **303 - FINALIZADO**: Ciudadano recibió el documento, ciclo completo
- **304 - CANCELADO**: Trámite interrumpido por alguna razón

**Transiciones clave de negocio:**
- Ciudadano paga → Presentado (201)
- Coordinador asigna → En Revisión (202)
- Analista requiere documentos → Requerimiento (203)
- Analista solicita fase de campo → En Diligencia (205)
- Analista finaliza → Finalizado (303) o Rechazado (302)

### RF-02: Asignación de Trámites

#### RF-02.1: Coordinadores
Los coordinadores deben poder:
- Asignar trámites específicos a analistas de su equipo
- Reasignar trámites entre analistas cuando sea necesario
- Liberar trámites de analistas y devolverlos al pool
- Ver la carga de trabajo actual de cada analista

#### RF-02.2: Analistas
Los analistas deben poder:
- Autoasignarse trámites disponibles del pool
- Ver solo sus trámites asignados (Buzón)
- Ver trámites disponibles para autoasignación
- Ver trámites finalizados (solo coordinadores)

### RF-03: Gestión de Documentos (SFTP)

Los PDFs de trámites se almacenan en un servidor SFTP externo. El sistema debe permitir:
- Listar documentos disponibles por trámite
- Permitir descarga de documentos con caché temporal
- Auditoría de todas las descargas realizadas
- Acceso controlado según rol del usuario

### RF-04: Catálogos de Referencia (Read-Only)

El sistema consulta catálogos maestros que son administrados externamente:
- Tipos de trámites disponibles
- Estados posibles del workflow
- Peritos autorizados
- Categorías de trámites
- Requisitos por tipo de trámite

**Restricción importante:** Estos catálogos son SOLO LECTURA. No se pueden modificar ni administrar a través del sistema backoffice.

### RF-05: Auditoría Completa

Cada acción realizada en el sistema debe registrarse en tabla de auditoría:
- Qué usuario realizó la acción
- Qué trámite fue afectado
- Qué estado cambió (antes → después)
- Cuándo ocurrió la acción (timestamp)
- Observaciones opcionales sobre la acción

**Restricción importante:** El historial de actividades es inmodificable (no se pueden editar ni borrar registros).

### RF-06: Búsquedas y Filtros

Los usuarios deben poder buscar y filtrar trámites por:
- Folio único
- Tipo de trámite
- Estado actual
- Analista asignado
- Rango de fechas (creado, modificado)
- Palabras clave en observaciones

### RF-07: Estadísticas Básicas

Coordinadores y administradores deben poder consultar:
- Número de trámites por estado
- Trámites por analista
- Tiempos promedio de proceso
- Trámites con estado de urgencia

### RF-08: Vistas por Rol

El sistema debe presentar diferentes vistas según el rol:
- **Todos**: Administradores y Coordinadores ven todos los trámites activos
- **Buzón (Mis Trámites)**: Analistas ven solo sus trámites asignados
- **Disponibles**: Todos ven los trámites sin asignar en pool
- **Cerrados**: Coordinadores ven trámenes finalizados (estados 3xx)

## 5. Requerimientos No Funcionales

### RNF-01: Tiempos de Respuesta

- **Consultar trámite individual**: < 2 segundos
- **Listar trámites (página)**: < 3 segundos
- **Cambiar estatus de trámite**: < 1 segundo
- **Descargar documento PDF**: < 5 segundos (según tamaño)

### RNF-02: Disponibilidad

- **Horario laboral (8am-4pm)**: 99% uptime obligatorio
- **Fuera de horario laboral**: 95% aceptable

### RNF-03: Usabilidad

- Interfaz intuitiva basada en Django Admin con tema Jazzmin
- Búsqueda y filtros rápidos y accesibles
- Acciones comunes (asignar, liberar, cambiar estatus) en menos de 3 clicks
- Visualización clara del estado de cada trámite con colores indicativos

### RNF-04: Seguridad

- Autenticación robusta de usuarios
- Control de acceso basado en roles (RBAC)
- Auditoría completa de todas las acciones
- Cifrado de comunicaciones (HTTPS)

### RNF-05: Escalabilidad

- Sistema debe soportar crecimiento esperado de usuarios y trámites
- Cache de catálogos para reducir carga de base de datos
- Consultas optimizadas para grandes volúmenes de datos

## 6. Requerimientos de Datos

### RD-01: Unidad de Trámite

Cada trámite debe contener como mínimo:
- Folio único e inmutable
- Tipo de trámite (referencia a catálogo)
- Datos del solicitante (nombre, teléfono, correo electrónico)
- Estado actual (1xx, 2xx, o 3xx)
- Analista asignado (si aplica)
- Historial completo de actividades
- Observaciones opcionales

### RD-02: Integridad de Datos

- No se puede eliminar trámites activos (solo cambiar estado a CANCELADO)
- No se puede modificar historial de actividades
- Folios son únicos e inmutables una vez creados
- Estados deben seguir transiciones válidas predefinidas

### RD-03: Auditoría

Cada acción debe留下 registro imborrable:
- Usuario que realizó la acción
- Fecha y hora exacta
- Tipo de acción realizada
- Contexto del trámite afectado

### RD-04: Catálogos

Los catálogos de referencia son inmutables desde el backoffice:
- Solo lectura desde la aplicación
- Modificados por sistemas externos o procedimientos administrativos
- Mapeados a modelos Django con patrón READ_ONLY

## 7. Priorización de Requerimientos

| Prioridad | Requerimientos |
|-----------|----------------|
| **P1 - Crítico** | RF-01 (Ciclo de vida), RF-02 (Asignación), RF-05 (Auditoría) |
| **P2 - Alto** | RF-03 (Documentos SFTP), RF-04 (Catálogos), RNF-01 (Tiempos de respuesta) |
| **P3 - Medio** | RF-06 (Búsquedas), RF-07 (Estadísticas), RNF-03 (Usabilidad) |
| **P4 - Bajo** | RF-08 (Vistas por rol), RNF-02 (Disponibilidad), RNF-05 (Escalabilidad) |

## 8. Notas Importantes

### 8.1 Terminología

**Convención de acentos (aplicado en todo el sistema):**
- Campo `observacion` (sin acento)
- Estado `en_diligencia` (sin acento)
- Campo `es_activo` (sin acento)

### 8.2 Restricciones de Negocio

- Solo coordinadores y administradores pueden asignar trámites
- Analistas solo pueden cambiar estatus de trámites asignados
- El historial de actividades es inmodificable (append-only)
- Catálogos son solo lectura desde el backoffice

### 8.3 Referencias Externas

Para especificaciones técnicas, ver:
- [01-ARQUITECTURA.md](01-ARQUITECTURA.md) - Arquitectura técnica
- [02-HISTORIAS-USUARIO.md](02-HISTORIAS-USUARIO.md) - Historias de usuario por rol
- [03-MODELO-DE-DATOS.md](03-MODELO-DE-DATOS.md) - Modelo de datos completo
- [ADR Repository](../06-decisions/) - Decisiones de arquitectura
