# Requerimientos de Negocio - Backoffice de Trámites

**Autores:** Noe Nieto, Jose Ramon Bogarin, Carlos Ahizotl
**Estatus:** Aprobado
**Fecha de actualización:** 4 Mayo 2026

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

#### RF-04.1: Catálogo de Tipos de Trámite
**Prioridad:** Alta
**Descripción:** Mantener catálogo maestro de tipos de trámites disponibles.

**Campos:**
- Código único
- Nombre del trámite
- Descripción detallada
- Área/Departamento responsable
- Tiempo estimado de respuesta (en días)
- URL de información adicional
- Estado activo/inactivo

**Funcionalidad:**
- Consulta de tipos de trámites disponibles
- Referencia en trámites
- Solo lectura desde el backoffice
- Modificado por sistemas externos o procedimientos administrativos

#### RF-04.2: Catálogo de Estatus
**Prioridad:** Alta
**Descripción:** Definir los estados posibles de un trámite.

**Campos:**
- Código numérico (con prefijo 1xx, 2xx, 3xx)
- Nombre del estatus
- Responsable del estado
- Descripción del significado del estado
- Categoría (100s, 200s, 300s)

**Funcionalidad:**
- Referencia en todos los trámites
- Usado en validación de transiciones de workflow
- Solo lectura desde el backoffice
- Modificado por sistemas externos

#### RF-04.3: Catálogo de Peritos Autorizados
**Prioridad:** Alta
**Descripción:** Mantener registro de peritos autorizados por el gobierno.

**Campos:**
- Nombre completo (paterno, materno, nombre)
- Domicilio
- Colonia
- Teléfono y celular
- Correo electrónico
- Fecha de registro
- Fecha de revalidación
- RFC
- Número de cédula profesional
- Especialidad técnica
- Estado activo/inactivo

**Funcionalidad:**
- Búsqueda por nombre, RFC, cédula
- Consulta de peritos disponibles
- Solo lectura desde el backoffice
- Alerta de vencimiento de revalidación (opcional)

#### RF-04.4: Catálogo de Usuarios del Sistema
**Prioridad:** Baja
**Descripción:** Registro de usuarios del sistema interno (distintos de gestión de autenticación).

**Nota:** Este catálogo existe para compatibilidad con sistema legacy, pero NO se usa para autenticación. La autenticación se maneja a través de Django auth (session-based).

**Campos:**
- Nombre completo
- Usuario (username)
- Contraseña (encriptada) - gestionada por Django
- Fecha de alta
- Fecha de baja
- Estatus activo/inactivo
- Nivel de acceso
- Correo electrónico

**Funcionalidad:**
- Consulta de usuarios disponibles para referencia
- Solo lectura desde el backoffice
- Autenticación manejada por Django auth (no por este catálogo)

#### RF-04.5: Catálogos Complementarios
**Prioridad:** Baja
**Descripción:** Catálogos adicionales para clasificación y organización de trámites.

**Catálogos incluidos:**
- `cat_actividad`: Actividades realizadas durante trámite
- `cat_categoria`: Categorías de trámites
- `cat_inciso`: Incisos presupuestarios (si aplica)
- `cat_requisito`: Requisitos por tipo de trámite

**Funcionalidad:**
- Consulta de catálogos complementarios
- Referencia en relaciones many-to-many
- Solo lectura desde el backoffice
- Modificados por sistemas externos

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

**Objetivos de Performance basados en estándares de la industria:**

| Operación | Objetivo | Referencia Técnica | Justificación |
|-----------|----------|-------------------|---------------|
| **Carga inicial de página** | < 2.5s | Google Core Web Vitals - LCP | Largest Contentful Paint (LCP) debe ser < 2.5s para buena experiencia de usuario |
| **Interacciones (clics, botones, formularios)** | < 200ms | Google Core Web Vitals - INP | Interaction to Next Paint (INP) < 200ms para respuestas fluidas |
| **Consultar trámite individual** | < 1-2s | Nielsen Norman (1s rule) | 1 segundo mantiene el flujo de pensamiento del usuario sin interrupción |
| **Listar trámites (página)** | < 2-3s | Core Web Vitals LCP | Lista con datos paginados, ajustado a estándares de carga web |
| **Cambiar estatus de trámite** | < 500ms | Nielsen Norman (0.1s ideal) | Respuesta inmediata para acciones de escritura, feedback visual rápido |
| **Descargar documento PDF** | < 3-5s | UX heuristics (3s tolerable) | Depende de tamaño de archivo y red del usuario, feedback de progreso |
| **Búsqueda/filtros** | < 1-2s | UX best practices | Búsqueda con feedback visual, indicadores de carga |

**Referencias Técnicas:**

1. **Google Core Web Vitals (Estándar Web Internacional)**
   - **LCP (Largest Contentful Paint)**: < 2.5s para una buena experiencia de carga
     - Referencia: https://web.dev/articles/vitals
     - Métrica principal de performance web usada por Google para SEO
   - **INP (Interaction to Next Paint)**: < 200ms para interacciones fluidas
     - Referencia: https://developers.google.com/search/blog/2023/05/introducing-inp
     - Reemplazó a FID en marzo 2024 como métrica de respuesta
     - Mide la latencia de interacciones del usuario

2. **Nielsen Norman Group (Estándar de UX)**
   - **0.1 segundo (100ms)**: Respuesta instantánea - usuario siente que controla directamente el sistema
   - **1.0 segundo**: Flujo de pensamiento continuo - usuario no pierde el hilo mental
   - **10 segundos**: Límite de atención del usuario - después de esto, la paciencia disminuye drásticamente
     - Referencia: https://www.nngroup.com/articles/response-times-3-important-limits/
     - Límites establecidos por investigación de UX desde 1993, válidos en 2025

3. **ISO 25010:2011 (Estándar de Calidad de Software)**
   - **Time Behaviour**: Característica de calidad que mide tiempos de respuesta y throughput
   - Define métricas de performance para sistemas en operación
     - Referencia: https://iso25000.com/index.php/en/iso-25000-standards/iso-25010
     - Estándar internacional para calidad de producto de software

4. **Sello de Excelencia en Gobierno Digital (México)**
   - **Criterio 3.4**: Disminuir el tiempo de entrega por canal con la utilización del canal digital
   - Aunque no especifica cifras numéricas, establece la necesidad de mejorar tiempos de respuesta
     - Referencia: https://www.gob.mx/sellodeexcelencia/articulos/criterios-de-seleccion-183170
     - Estándar mexicano para certificación de trámites digitales

5. **ORFIS (Oficina para la Reforma Institucional y la Innovación Social - México)**
   - **Estándar 3**: Desempeño y Adaptabilidad - Velocidad de carga
   - Reconoce la velocidad de carga como estándar actual para sitios web de gobierno
     - Referencia: Estándares y tendencias para sitios web de gobierno (2016)
     - https://www.orfis.gob.mx/BibliotecaVirtual/archivos/02122016103210.pdf

**NOTA IMPORTANTE:**

Los tiempos de respuesta mostrados son **objetivos iniciales basados en estándares de la industria** (Core Web Vitals, Nielsen Norman, ISO 25010, Sello de Excelencia en Gobierno Digital México).

Estos valores serán **ajustados y refinados** después de:

1. **Implementación de pruebas de carga** (Locust, k6, JMeter)
   - Simular usuarios concurrentes reales
   - Medir performance bajo diferentes escenarios de carga
   - Identificar cuellos de botella en backend y frontend

2. **Medición de baseline en ambiente de staging**
   - Establecer baseline de performance antes de producción
   - Medir tiempos de respuesta reales de endpoints Django
   - Optimizar consultas SQL, índices, y caché

3. **Análisis de métricas reales en producción**
   - Implementar APM (Application Performance Monitoring)
   - Medir LCP, INP, CLS con Google PageSpeed Insights
   - Monitorizar tiempos de respuesta de usuarios reales

4. **Optimización iterativa basada en datos**
   - Implementar caché de catálogos (LocMemCache, Redis si es necesario)
   - Optimizar consultas SQL con select_related, prefetch_related
   - Implementar paginación eficiente en listados grandes

**Estos objetivos NO son compromisos contractuales sin pruebas de rendimiento validadas.**

**Plan de Validación de Performance:**

| Fase | Actividad | Herramienta | Métrica |
|------|-----------|-------------|---------|
| **Desarrollo** | Tests de unidad de rendimiento | Django Debug Toolbar | Tiempo de query SQL |
| **Staging** | Pruebas de carga baselines | Locust | Usuarios concurrentes, tiempos de respuesta |
| **Producción** | Monitorización APM | New Relic / Datadog / Sentry | LCP, INP, CLS, tiempos de endpoint |
| **Mantenimiento** | Auditoría de performance mensual | Google PageSpeed Insights | Puntuación Web Vitals |

**Referencias de Gobierno Digital - México y Baja California:**

**México - Estándares Nacionales:**
1. **Sello de Excelencia en Gobierno Digital**
   - Criterio de impacto: "Disminuir el tiempo de entrega por canal con la utilización del canal de atención en línea"
   - Criterios de eficiencia: Interoperabilidad, fuentes de confianza, integración de canales
   - Criterios de satisfacción: Encuestas de satisfacción ciudadana, participación digital
   - Referencia: https://www.gob.mx/sellodeexcelencia/articulos/criterios-de-seleccion-183170
   - Certificación de trámites digitales de alta calidad

2. **ORFIS - Oficina para la Reforma Institucional y la Innovación Social**
   - Estándar 3: Desempeño y Adaptabilidad - Velocidad de carga como estándar actual
   - Estándar 1: Experiencia de Usuario (UX) - Información útil, utilizable, atractiva, encontrable
   - Estándar 2: Indexabilidad y Búsquedas Internas - Buscador con funciones avanzadas
   - Referencia: Estándares y tendencias para sitios web de gobierno (2016)
   - https://www.orfis.gob.mx/BibliotecaVirtual/archivos/02122016103210.pdf

3. **Lineamientos de Digitalización de Trámites y Servicios**
   - Lineamientos relativos a la digitalización estandarizada con apego a la Estrategia Digital
   - Indicador: Tecnologías de la Información
   - Referencia: https://www.gob.mx/buengobierno/documentos/lineamientos-de-la-digitalizacion-de-tramites-y-servicios
   - Guía para estandarización de trámites digitales en el gobierno federal

4. **Guía para la estandarización y certificación de los trámites digitales**
   - Acuerdo por el que se emite la Guía para la estandarización y certificación de los trámites digitales con el Sello de Excelencia en Gobierno Digital
   - Referencia: https://dof.gob.mx/nota_detalle_popup.php?codigo=5446678
   - Marco normativo para trámites digitales de alta calidad

**Baja California - Recursos Estatales:**
1. **Agencia Digital del Estado de Baja California (ADBC)**
   - RETYS: Registro Estatal de Trámites y Servicios - plataforma centralizada oficial
   - Modelo Único de Atención Ciudadana para trámites gubernamentales
   - Referencia: https://www.adbc.gob.mx/Herramienta/15 (RETYS)
   - Referencia: https://www.ventanillabc.bajacalifornia.gob.mx/muac/assets/doc/Lineamientos.pdf (Lineamientos)
   - Implementación local de Estrategia Digital Nacional

2. **Coordinación de Gobierno Digital - Baja California**
   - Revisión Técnica de las TICS - Cámara Digital, Normas y Estándares, Software y Manuales
   - Referencia: https://www.bajacalifornia.gob.mx/adbc/dictaminacion/
   - Lineamientos técnicos para implementación de gobierno digital en el estado

**Notas Importantes:**
- Aunque los estándares nacionales de gobierno digital en México enfatizan la mejora de tiempos de respuesta (Sello de Excelencia: "disminuir tiempo de entrega"), **no existen cifras numéricas específicas** documentadas públicamente
- Por lo tanto, este documento usa **estándares internacionales de la industria** (Core Web Vitals, Nielsen Norman, ISO 25010) complementados con principios de gobierno digital mexicano
- Estos objetivos de performance se consideran **alineados con las prioridades de gobierno digital mexicano** de mejora continua y satisfacción ciudadana
- Los valores se ajustarán según resultados de pruebas de carga y métricas reales de producción

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
| **P2 - Alto** | RF-03 (Documentos SFTP), RF-04.1 (Tipos de trámite), RF-04.2 (Estatus), RF-04.3 (Peritos), RNF-01 (Tiempos de respuesta) |
| **P3 - Medio** | RF-04.4 (Usuarios sistema), RF-04.5 (Catálogos complementarios), RF-06 (Búsquedas), RF-07 (Estadísticas), RNF-03 (Usabilidad) |
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
- [ADR Repository](../02-DECISIONES/) - Decisiones de arquitectura
