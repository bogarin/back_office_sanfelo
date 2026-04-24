# Requerimientos de Alto Nivel
## Backoffice de Trámites - Gobierno de San Felipe

**Versión**: 1.0
**Fecha**: 25 de Febrero de 2026
**Estado**: Finalizado
**Cliente**: Gobierno de San Felipe

---

## 📋 TABLA DE CONTENIDOS

1. [Introducción](#1-introducción)
2. [Actores del Sistema](#2-actores-del-sistema)
3. [Requerimientos Funcionales](#3-requerimientos-funcionales)
4. [Requerimientos No Funcionales](#4-requerimientos-no-funcionales)
5. [Requerimientos de Integración](#5-requerimientos-de-integración)
6. [Requerimientos de Seguridad](#6-requerimientos-de-seguridad)
7. [Requerimientos de Arquitectura](#7-requerimientos-de-arquitectura)
8. [Requerimientos de Datos](#8-requerimientos-de-datos)
9. [Requerimientos de Auditoría](#9-requerimientos-de-auditoría)
10. [Restricciones y Limitaciones](#10-restricciones-y-limitaciones)
11. [Criterios de Aceptación](#11-criterios-de-aceptación)

---

## 1. INTRODUCCIÓN

### 1.1 Propósito del Documento

Este documento establece los requerimientos de alto nivel para el **Backoffice de Trámites**, un microservicio destinado a la gestión de procedimientos administrativos (trámites) del Gobierno de San Felipe.

### 1.2 Descripción del Sistema

El sistema es una aplicación web que permite gestionar trámites gubernamentales, incluyendo:
- Gestión completa de trámites (CRUD)
- Catálogos de tipos de trámites, estatus, peritos, requisitos
- Sistema de costos con cálculo dinámico basado en UMA
- Auditoría completa de todas las operaciones
- Integración con sistema de autenticación centralizado (Keycloak)
- Despliegue en intranet del gobierno

### 1.3 Alcance

**Incluye:**
- Gestión de trámites y sus estados
- Catálogos maestros del sistema
- Sistema de pagos y costos
- Bitácora de auditoría
- Integración con Keycloak
- API REST para consumo por frontend

**No incluye:**
- Gestión de usuarios (delegada a Keycloak)
- Interfaz de usuario frontend (el backend es API-only)
- Generación de documentos físicos
- Notificaciones por correo electrónico
- Sistema de mensajería interna

### 1.4 Referencias

- Normativas del Gobierno de San Felipe
- Ley de Transparencia y Acceso a la Información Pública
- Manual de Procedimientos Administrativos

---

## 2. ACTORES DEL SISTEMA

| Actor | Descripción | Rol Principal |
|--------|--------------|----------------|
| **Administrador** | Usuario con permisos completos del sistema | Gestión total de trámites, catálogos, costos |
| **Operador** | Funcionario encargado de procesar trámites | Gestión de trámites asignados |
| **Visualizador** | Usuario con permisos solo de lectura | Consulta de trámites y reportes |
| **Ciudadano** | Solicitante de trámites (exclusivo en frontend) | Inicia trámites y sigue su estado |
| **Perito** | Experto técnico que valida trámites | Asignación y revisión de trámites |
| **Sistema Keycloak** | Servicio externo de autenticación | Gestión de usuarios, roles y permisos |
| **Sistema Kong** | API Gateway para seguridad | Validación de tokens JWT, rate limiting |

---

## 3. REQUERIMIENTOS FUNCIONALES

### 3.1 Módulo de Trámites

#### RF-001: Gestión de Trámites
**Prioridad**: Alta
**Descripción**: El sistema debe permitir la gestión completa del ciclo de vida de un trámite.

**Requerimientos:**
- RF-001.1: Crear nuevos trámites con información del solicitante
- RF-001.2: Consultar trámites por folio, ID o filtros múltiples
- RF-001.3: Actualizar información de trámites existentes
- RF-001.4: Eliminar trámites (solo administradores)
- RF-001.5: Cambiar el estatus del trámite en cualquier momento

**Campos obligatorios:**
- Nombre del solicitante
- Tipo de trámite
- Estatus (por defecto: Borrador/Pendiente)
- Prioridad (por defecto: Urgente)

**Campos opcionales:**
- Clave catastral
- Teléfono de contacto
- Correo electrónico
- Observaciones

---

#### RF-002: Generación Automática de Folio
**Prioridad**: Alta
**Descripción**: Cada trámite debe tener un folio único generado automáticamente.

**Especificaciones:**
- Formato: `TRAM-YYYY-XXXXX` donde:
  - `YYYY`: Año actual
  - `XXXXX`: Número consecutivo de 5 dígitos
- Generado por trigger de base de datos al insertar
- Único e inmutable
- Reinicio anual del contador

**Ejemplo**: `TRAM-2026-00001`, `TRAM-2026-00002`

---

#### RF-003: Estados del Trámite
**Prioridad**: Alta
**Descripción**: Los trámites deben pasar por una secuencia de estados definida.

**Estados con prefijos:**

| Prefijo | Rango | Descripción |
|---------|--------|-------------|
| **1xx** | 100-199 | Inicio del proceso |
| **2xx** | 200-299 | En proceso |
| **3xx** | 300-399 | Finalizado |

**Estados específicos:**
- `101` - Borrador/Pendiente pago
- `102` - Pagado
- `201` - Presentado
- `202` - En revisión
- `203` - En validación
- `301` - Completado
- `302` - Rechazado
- `303` - Cancelado

---

#### RF-004: Prioridades y Urgencia
**Prioridad**: Media
**Descripción**: Los trámites pueden marcarse como urgentes para priorizar su atención.

**Tipos de prioridad:**
- `Urgente` (por defecto)
- `Alta`
- `Media`
- `Baja`

**Funcionalidad:**
- Filtrar trámites por prioridad
- Ordenar listados por urgencia
- Indicador visual en la interfaz de tramites urgentes

---

#### RF-005: Asignación de Peritos
**Prioridad**: Media
**Descripción**: Los trámites pueden ser asignados a peritos autorizados para su revisión.

**Requerimientos:**
- Asignar un perito a un trámite (opcional)
- Un perito puede tener múltiples trámites asignados
- Un trámite solo puede tener un perito asignado
- Historial de asignaciones

---

### 3.2 Módulo de Catálogos

#### RF-006: Catálogo de Tipos de Trámite
**Prioridad**: Alta
**Descripción**: Mantener catálogo maestro de tipos de trámites disponibles.

**Campos:**
- Código único
- Nombre del trámite
- Descripción detallada
- Área/Departamento responsable
- Tiempo estimado de respuesta (en días)
- URL de información adicional
- Estado activo/inactivo

**Funcionalidad:**
- CRU D completo
- Solo administradores pueden modificar
- Referencia por otras entidades (tramites, costos, requisitos)

---

#### RF-007: Catálogo de Estatus
**Prioridad**: Alta
**Descripción**: Definir los estados posibles de un trámite.

**Campos:**
- Código numérico (con prefijo 1xx, 2xx, 3xx)
- Nombre del estatus
- Responsable del estado
- Descripción del significado del estado

**Funcionalidad:**
- Solo administradores pueden modificar
- Usado en todos los trámites
- Estructura jerárquica por prefijo

---

#### RF-008: Catálogo de Peritos
**Prioridad**: Media
**Descripción**: Mantener registro de peritos autorizados por el gobierno.

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
- Estatus activo/inactivo

**Funcionalidad:**
- Búsqueda por nombre, RFC, cédula
- Asignación a trámites
- Alerta de vencimiento de revalidación

---

#### RF-009: Catálogo de Usuarios del Sistema
**Prioridad**: Baja
**Descripción**: Registro de usuarios del sistema interno (distintos de Keycloak).

**Nota**: Este catálogo existe para compatibilidad con sistema legado, pero NO se usa para autenticación.

**Campos:**
- Nombre completo
- Usuario (username)
- Contraseña (encriptada)
- Fecha de alta
- Fecha de baja
- Estatus activo/inactivo
- Nivel de acceso
- Correo electrónico

---

#### RF-010: Catálogos Complementarios
**Prioridad**: Baja
**Descripción**: Catálogos adicionales para clasificación y costos.

**Catálogos incluidos:**
- `cat_actividad`: Actividades realizadas durante trámite
- `cat_categoria`: Categorías de trámites
- `cat_inciso`: Incisos presupuestarios
- `cat_requisito`: Requisitos por tipo de trámite
- `cat_tipo`: Tipos para cálculo de costos

**Funcionalidad:**
- CRUD básico
- Referencia en relaciones many-to-many
- Solo administradores pueden modificar

---

### 3.3 Módulo de Relaciones

#### RF-011: Relaciones Many-to-Many
**Prioridad**: Alta
**Descripción**: Establecer relaciones entre trámites, requisitos, categorías, incisos y actividades.

**Relaciones:**

1. **Trámite ↔ Requisito ↔ Categoría** (`rel_tmt_cate_req`)
   - Un trámite puede tener múltiples requisitos
   - Un requisito puede aplicar a múltiples categorías

2. **Trámite ↔ Categoría** (`rel_tmt_categoria`)
   - Un trámite pertenece a una o más categorías

3. **Trámite ↔ Inciso** (`rel_tmt_inciso`)
   - Un trámite puede impactar múltiples incisos presupuestarios

4. **Tipo ↔ Trámite ↔ Requisito** (`rel_tmt_tipo_req`)
   - Relación ternaria para costos por tipo

5. **Trámite ↔ Actividad** (`rel_tmt_actividad`)
   - Un trámite tiene actividades predefinidas

**Funcionalidad:**
- Gestión de relaciones en catálogo de tipos de trámite
- Consulta de relaciones al visualizar trámite
- Flexibilidad en asignación de requisitos

---

### 3.4 Módulo de Actividades

#### RF-012: Registro de Actividades
**Prioridad**: Alta
**Descripción**: Seguimiento paso a paso de las actividades realizadas en un trámite.

**Campos:**
- Trámite asociado
- Tipo de actividad (del catálogo)
- Estatus del trámite al momento de la actividad
- Fecha de inicio y fin
- Usuario que realizó la actividad
- Número de secuencia (orden cronológico)
- Observaciones

**Funcionalidad:**
- Agregar actividades automáticamente al cambiar estatus
- Historial cronológico completo
- Consulta de timeline de trámite
- Reportes de tiempo de atención

---

### 3.5 Módulo de Costos

#### RF-013: Cálculo Dinámico de Costos
**Prioridad**: Alta
**Descripción**: Calcular el costo de un trámite basado en UMA y reglas configurables.

**Conceptos:**
- **UMA (Unidad de Medida y Actualización)**: Valor actualizado periódicamente
- **Fórmulas**: Expresiones matemáticas para cálculo
- **Rangos**: Costos variables según valor del trámite
- **UMAs**: Cantidad de UMAs a cobrar
- **Contribuciones**: Cruz Roja, Bomberos (porcentajes)

**Campos del costo:**
- Trámite asociado
- Año de vigencia
- Fórmula de cálculo (opcional)
- Cantidad de UMAs
- Rango inicial y final (para costos variables)
- Inciso presupuestario
- Aportaciones especiales (Cruz Roja, Bomberos)
- Indicador de fomento (aplica descuentos)
- Estado activo/inactivo
- Usuario que actualizó
- Fecha de actualización

**Funcionalidad:**
- Definir reglas de costo por tipo de trámite
- Consultar costo actual de un trámite
- Histórico de costos por año
- Actualización de UMA via procedimiento almacenado

---

#### RF-014: Gestión de Pagos
**Prioridad**: Alta
**Descripción**: Registrar los pagos realizados por los trámites.

**Requerimientos:**
- Marcar trámite como pagado/no pagado
- Registrar detalles del pago (cobros)
- Múltiples pagos por trámite
- Concepto del pago
- Importe total
- Inciso presupuestario afectado

**Campos del cobro:**
- Concepto de pago
- Importe
- Inciso (opcional)
- Trámite asociado

**Funcionalidad:**
- Agregar pagos a trámite
- Consultar historial de pagos
- Cálculo de importes pendientes
- Reportes de recaudación

---

#### RF-015: Actualización de UMA
**Prioridad**: Alta
**Descripción**: Mantener actualizado el valor de la UMA del sistema.

**Funcionalidad:**
- Almacenar valor actual de UMA en tabla `uma`
- Actualizar valor via procedimiento almacenado `sp_actualizar_uma()`
- Registro único con ID=1
- Cálculos de costos usan el valor de UMA

---

### 3.6 Módulo de Auditoría

#### RF-016: Bitácora de Auditoría
**Prioridad**: Crítica
**Descripción**: Registrar todas las operaciones realizadas en el sistema.

**Operaciones auditadas:**
- Creación de trámite (INSERT)
- Modificación de trámite (UPDATE)
- Eliminación de trámite (DELETE)
- Cambios en catálogos
- Cambios de estatus
- Asignaciones
- Pagos

**Campos de bitácora:**
- Usuario del sistema que realizó la acción
- Tipo de movimiento (INSERT, UPDATE, DELETE)
- Usuario de PC (IP o máquina)
- Fecha y hora de la acción
- Máquina donde se realizó
- Valor anterior (para UPDATE)
- Valor nuevo (para INSERT/UPDATE)
- Observaciones de la acción

**Funcionalidad:**
- Registro automático en cada operación CRUD
- Consulta de historial por trámite
- Consulta de historial por usuario
- Reportes de auditoría
- Exportación de bitácora

---

#### RF-017: Trazabilidad Completa
**Prioridad**: Alta
**Descripción**: Garantizar que cada cambio en el sistema sea rastreable.

**Requerimientos:**
- Timestamp en cada registro (creado, modificado)
- Usuario responsable de cada cambio
- Valor antes y después (para actualizaciones)
- No se pueden eliminar registros de bitácora

---

### 3.7 Módulo de Autenticación y Autorización

#### RF-018: Autenticación con Keycloak
**Prioridad**: Crítica
**Descripción**: El sistema debe usar Keycloak como único proveedor de identidad.

**Flujo de autenticación:**
1. Usuario ingresa credenciales en frontend
2. Frontend autentica con Keycloak (OIDC)
3. Keycloak emite token JWT
4. Frontend envía token a Kong API Gateway
5. Kong valida token y lo reenvía al backend
6. Backend extra información del usuario del token
7. Backend procesa solicitud

**Información de usuario disponible:**
- `user_id`: ID único de Keycloak (sub claim)
- `username`: Nombre de usuario
- `email`: Correo electrónico
- `roles`: Lista de roles asignados

---

#### RF-019: Roles de Usuario
**Prioridad**: Alta
**Descripción**: Sistema de control de acceso basado en roles (RBAC).

**Roles definidos:**

| Rol | Permisos |
|------|-----------|
| **admin** | CRUD completo de trámites, catálogos, costos, bitácora |
| **operator** | CRUD de trámites, consulta de catálogos, consulta de costos |
| **viewer** | Solo lectura de trámites, catálogos, costos, bitácora |

**Reglas:**
- Los roles se asignan en Keycloak
- Un usuario puede tener múltiples roles
- Verificación de roles en cada endpoint

---

#### RF-020: No Gestión Local de Usuarios
**Prioridad**: Alta
**Descripción**: El sistema NO debe gestionar usuarios ni contraseñas localmente.

**Requerimientos:**
- No hay tabla local de usuarios de autenticación
- Toda gestión de usuarios se realiza en Keycloak
- Almacenamiento de `user_id` de Keycloak en trámites (denormalizado)
- Almacenamiento de `username` de Keycloak en trámites (denormalizado)

---

---

## 4. REQUERIMIENTOS NO FUNCIONALES

### 4.1 Performance

#### RNF-001: Tiempos de Respuesta
**Prioridad**: Alta

| Operación | Tiempo máximo aceptable |
|-----------|------------------------|
| Consulta de trámite por folio | < 200 ms |
| Listado de trámites (100 registros) | < 500 ms |
| Creación de trámite | < 1 s |
| Actualización de trámite | < 500 ms |
| Consulta de catálogos | < 100 ms |

**Condiciones:**
- Medido en red de intranet (1 Gbps)
- Base de datos con < 1 millón de registros
- Sin concurrencia alta

---

#### RNF-002: Carga Concurrente
**Prioridad**: Media

**Capacidades:**
- Mínimo: 10 usuarios simultáneos
- Recomendado: 50 usuarios simultáneos
- Máximo: 100 usuarios simultáneos

**Requerimientos:**
- Sin degradación de performance bajo carga moderada
- Mecanismos de rate limiting (Kong)
- Balanceo de carga en múltiples instancias (escalabilidad)

---

#### RNF-003: Escalabilidad Horizontal
**Prioridad**: Alta

**Requerimientos:**
- Capacidad de desplegar múltiples instancias del backend
- Balanceo de carga automático (Kong)
- Almacenamiento de sesión en Redis (no local)
- Base de datos centralizada (PostgreSQL)

**Estrategia:**
```
Frontend → Kong → [Backend-1, Backend-2, Backend-N] → PostgreSQL
                          ↓
                        Redis (sessions/cache)
```

---

### 4.2 Disponibilidad

#### RNF-004: Uptime del Sistema
**Prioridad**: Alta

**Objetivos:**
- Horario laboral (8:00 - 16:00): 99.9% (15 min/mes de inactividad)
- Fuera de horario laboral: 95% aceptable
- Tiempo medio de recuperación (MTTR): < 15 minutos

**Estrategias:**
- Despliegue en infraestructura redundante
- Backup automatizado de base de datos
- Sistema de alertas
- Procedimientos de contingencia

---

#### RNF-005: Mantenimiento Programado
**Prioridad**: Media

**Requerimientos:**
- Ventanas de mantenimiento programado anunciarlas con 48 horas
- Mantenimientos fuera de horario pico (fines de semana)
- Duración máxima de ventana: 4 horas
- Sistema debe mostrar mensaje de mantenimiento

---

### 4.3 Usabilidad

#### RNF-006: Interfaz API Consistente
**Prioridad**: Alta

**Requerimientos:**
- Diseño RESTful consistente
- Códigos HTTP estándar (200, 201, 400, 404, 500)
- Documentación de API (OpenAPI/Swagger)
- Mensajes de error claros y descriptivos
- Formatos de respuesta estandarizados

---

#### RNF-007: Filtrado y Búsqueda
**Prioridad**: Alta

**Funcionalidades:**
- Filtrado por múltiples campos simultáneos
- Búsqueda full-texto en campos relevantes
- Ordenamiento por cualquier campo
- Paginación en todas las listas
- Tamaño de página configurable

---

### 4.4 Mantenibilidad

#### RNF-008: Gestión de Esquema Externo
**Prioridad**: Crítica

**Requerimientos:**
- El esquema de base de datos es controlado externamente
- NO se usan migraciones automáticas
- Los modelos del ORM deben mapear exactamente al esquema SQL
- Validación de sincronización modelo ↔ esquema
- Procedimiento para actualizaciones de esquema

---

#### RNF-009: Separación de Preocupaciones
**Prioridad**: Alta

**Arquitectura:**
- **API Layer**: Endpoints HTTP, validación de entradas
- **Business Logic Layer**: Reglas de negocio, cálculos
- **Data Access Layer**: ORM, consultas a base de datos
- **Audit Layer**: Registro de cambios

---

#### RNF-010: Logs y Monitoreo
**Prioridad**: Alta

**Requerimientos:**
- Logging estructurado (JSON)
- Niveles de log: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Logs por módulo y funcionalidad
- Rotación automática de logs (10 MB, 10 archivos)
- Métricas básicas (requests, errores, tiempos)
- Health check endpoint

---

### 4.5 Compatibilidad

#### RNF-011: Navegadores Soportados
**Prioridad**: Media

**Navegadores:**
- Chrome (última versión)
- Firefox (última versión)
- Edge (última versión)
- Safari (última versión)

**Nota**: Esto aplica al frontend. El backend es API-only.

---

#### RNF-012: Protocolos y Formatos
**Prioridad**: Alta

**Soportado:**
- Protocolo: HTTP/1.1, HTTP/2
- Formato de datos: JSON (application/json)
- Autenticación: JWT (Bearer token)
- Documentación: OpenAPI 3.0

---

### 4.6 Seguridad

#### RNF-013: Cumplimiento de Normativas
**Prioridad**: Crítica

**Normativas:**
- Ley Federal de Protección de Datos Personales (México)
- Ley de Transparencia y Acceso a la Información Pública
- Normas de ciberseguridad del Gobierno de San Felipe

---

#### RNF-014: Gestión de Vulnerabilidades
**Prioridad**: Alta

**Requerimientos:**
- Dependencias actualizadas regularmente
- Escaneo de vulnerabilidades en CI/CD
- Parches de seguridad en < 72 horas
- Auditorías de seguridad periódicas

---

---

## 5. REQUERIMIENTOS DE INTEGRACIÓN

### 5.1 Keycloak

#### RI-001: Autenticación OIDC
**Prioridad**: Crítica

**Requerimientos:**
- Uso del protocolo OpenID Connect (OIDC)
- Endpoints de Keycloak:
  - `/auth/realms/{realm}/.well-known/openid-configuration`
  - `/auth/realms/{realm}/protocol/openid-connect/token`
- Validación de tokens JWT
- Extracción de claims: `sub`, `preferred_username`, `email`, `realm_access.roles`

**Configuración:**
```
KEYCLOAK_SERVER_URL: https://keycloak.sanfelipe.gob.ar/auth
KEYCLOAK_REALM: sanfelipe
KEYCLOAK_CLIENT_ID: tramites-backend
KEYCLOAK_CLIENT_SECRET: <secret>
KEYCLOAK_ALGORITHM: RS256
```

---

### 5.2 Kong API Gateway

#### RI-002: Validación de Tokens
**Prioridad**: Crítica

**Funcionalidad:**
- Kong valida tokens JWT antes de llegar al backend
- Plugin `jwt` de Kong configurado con:
  - URL de JWK de Keycloak
  - Algoritmo RS256
  - Claims a verificar: `exp`
- Token reenviado al backend en header `Authorization: Bearer <token>`

---

#### RI-003: Rate Limiting
**Prioridad**: Alta

**Requerimientos:**
- Limitar requests por minuto
- Configuración:
  - Usuarios normales: 60 requests/minuto
  - Administradores: 300 requests/minuto
- Response `429 Too Many Requests` al exceder límite

---

#### RI-004: CORS
**Prioridad**: Media

**Configuración:**
- Orígenes permitidos: URLs de frontend en intranet
- Métodos permitidos: GET, POST, PUT, DELETE, OPTIONS
- Headers permitidos: Authorization, Content-Type
- Credenciales: Permitido

---

### 5.3 PostgreSQL

#### RI-005: Conexión a Base de Datos
**Prioridad**: Crítica

**Requerimientos:**
- Motor: PostgreSQL 15+
- Pool de conexiones: 10-20 conexiones
- Pre-ping: Verificar conexiones antes de usar
- Timeout: 30 segundos
- Reintento automático en fallos

**Cadena de conexión:**
```
postgresql+asyncpg://user:pass@host:5432/sanfelipe_tramites
```

---

#### RI-006: Esquema Externo
**Prioridad**: Crítica

**Requerimientos:**
- El esquema es gestionado por terceros
- Aplicación NO crea/modifica tablas
- Actualizaciones de esquema:
  1. Proveedor entrega scripts SQL
  2. Scripts aplicados manualmente a PostgreSQL
  3. Modelos ORM actualizados para coincidir
  4. Validación de sincronización

---

### 5.4 Redis

#### RI-007: Sesiones y Cache
**Prioridad**: Alta

**Usos:**
- Almacenamiento de sesiones (si aplica)
- Cache de catálogos (frecuentemente consultados)
- Rate limiting (complementario a Kong)
- Locking distribuido

**Configuración:**
```
REDIS_URL: redis://localhost:6379/1
TTL default: 3600 segundos (1 hora)
```

---

---

## 6. REQUERIMIENTOS DE SEGURIDAD

### 6.1 Autenticación

#### RS-001: Autenticación Obligatoria
**Prioridad**: Crítica

**Requerimientos:**
- TODOS los endpoints (excepto `/health`) requieren autenticación
- Token JWT válido obligatorio en header `Authorization`
- Excepciones: Solo endpoints de health check y documentación

---

#### RS-002: Validación de Tokens
**Prioridad**: Crítica

**Requerimientos:**
- Verificar firma RSA del token
- Verificar expiración (`exp` claim)
- Verificar emisor (`iss` claim)
- Rechazar tokens inválidos con HTTP 401

---

#### RS-003: Revocación de Tokens
**Prioridad**: Media

**Requerimientos:**
- Implementar lista negra de tokens en Redis
- Al cerrar sesión, agregar token a lista negra
- TTL de tokens en lista negra = tiempo restante de expiración
- Verificar token no esté en lista negra antes de procesar

---

### 6.2 Autorización

#### RS-004: Control de Acceso Basado en Roles (RBAC)
**Prioridad**: Crítica

**Matriz de permisos por rol:**

| Funcionalidad | admin | operator | viewer |
|--------------|--------|-----------|---------|
| Crear trámites | ✅ | ✅ | ❌ |
| Modificar trámites | ✅ | ✅ | ❌ |
| Eliminar trámites | ✅ | ❌ | ❌ |
| Consultar trámites | ✅ | ✅ | ✅ |
| Crear catálogos | ✅ | ❌ | ❌ |
| Modificar catálogos | ✅ | ❌ | ❌ |
| Modificar costos | ✅ | ❌ | ❌ |
| Consultar bitácora | ✅ | ✅ | ✅ |
| Consultar reportes | ✅ | ✅ | ✅ |

---

#### RS-005: Principio de Menor Privilegio
**Prioridad**: Alta

**Requerimientos:**
- Usuarios deben tener solo permisos necesarios
- Roles deben ser granulares (no excesivos)
- Auditoría de cambios de permisos (en Keycloak)

---

### 6.3 Protección de Datos

#### RS-006: Datos Sensibles
**Prioridad**: Alta

**Datos protegidos:**
- Datos personales de ciudadanos (RFC, domicilio)
- Datos de contacto (teléfono, correo)
- Historial completo de trámites

**Medidas:**
- Encriptación en tránsito (HTTPS en producción)
- No exponer datos en logs
- No exponer datos sensibles en respuestas de error
- Anonimización en reportes públicos

---

#### RS-007: Integridad de Datos
**Prioridad**: Crítica

**Requerimientos:**
- Validación de todos los inputs de usuario
- Uso de transacciones en operaciones multi-paso
- Verificación de referencias antes de insertar/actualizar
- Constraints en base de datos (PK, FK, NOT NULL, UNIQUE)

---

### 6.4 Auditoría de Seguridad

#### RS-008: Logging de Eventos de Seguridad
**Prioridad**: Crítica

**Eventos a registrar:**
- Intentos fallidos de autenticación
- Intentos de acceso no autorizado (403)
- Intentos de inyección SQL u otros ataques
- Cambios de roles/permisos
- Acceso a datos sensibles

---

#### RS-009: Bitácora Inmutable
**Prioridad**: Alta

**Requerimientos:**
- Registros de bitácora NO pueden ser modificados
- Registros de bitácora NO pueden ser eliminados
- Solo se pueden insertar nuevos registros
- Respaldos regulares de bitácora

---

### 6.5 Protección contra Ataques

#### RS-010: SQL Injection
**Prioridad**: Crítica

**Medidas:**
- Uso obligatorio de ORM con parámetros (SQLAlchemy)
- Prohibido SQL dinámico con concatenación de strings
- Validación de todos los inputs numéricos

---

#### RS-011: XSS (Cross-Site Scripting)
**Prioridad**: Alta

**Medidas:**
- Escapar todos los datos provenientes de usuario
- Content-Type correcto en respuestas (application/json)
- Headers de seguridad: `X-Content-Type-Options: nosniff`

---

#### RS-012: CSRF (Cross-Site Request Forgery)
**Prioridad**: Media

**Medidas:**
- El sistema usa JWT (Bearer token), que mitiga CSRF
- SameSite cookies si se usan sesiones
- Verificación de Origin/Referer headers

---

#### RS-013: Rate Limiting
**Prioridad**: Alta

**Medidas:**
- Kong implementa rate limiting
- Por IP: 60 requests/minuto
- Por usuario: 60 requests/minuto
- Bloqueo temporal tras exceder límite

---

### 6.6 Conformidad

#### RS-014: Ley Federal de Protección de Datos Personales
**Prioridad**: Crítica

**Requerimientos:**
- Consentimiento explícito para recolección de datos
- Acceso limitado a datos personales (solo roles autorizados)
- Derechos ARCO: Acceso, Rectificación, Cancelación, Oposición
- Retención mínima de datos (solo lo necesario)
- Procedimientos de respuesta a solicitudes de ciudadanos

---

#### RS-015: Transparencia y Acceso a la Información
**Prioridad**: Alta

**Requerimientos:**
- Bitácora pública de actividades gubernamentales (anonimizada)
- API para consulta de estatus de trámites por ciudadanos
- Publicación de estadísticas de trámites
- Cumplimiento de plazos de respuesta

---

---

## 7. REQUERIMIENTOS DE ARQUITECTURA

### 7.1 Arquitectura General

#### RA-001: Microservicio Autónomo
**Prioridad**: Alta

**Características:**
- Aplicación stateless (no sesiones locales)
- API RESTful como única interfaz
- Desacoplado de frontend (puede ser cualquier SPA)
- Escalabilidad horizontal fácil

---

#### RA-002: Capas de Arquitectura
**Prioridad**: Alta

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)          │
│  - Endpoints HTTP                    │
│  - Validación (Pydantic)            │
│  - Documentation (OpenAPI)            │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│    Business Logic Layer (Services)      │
│  - Reglas de negocio                 │
│  - Cálculos de costos               │
│  - Orquestación de operaciones       │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│     Data Access Layer (SQLAlchemy)      │
│  - Modelos ORM                      │
│  - Consultas SQL                    │
│  - Transacciones                    │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│       Database Layer (PostgreSQL)       │
│  - Tablas de esquema externo        │
│  - Índices optimizados              │
│  - Stored procedures                 │
└─────────────────────────────────────────┘
```

---

### 7.2 Tecnologías

#### RA-003: Stack Tecnológico
**Prioridad**: Crítica

| Componente | Tecnología | Versión | Justificación |
|-------------|-------------|-----------|----------------|
| Backend | FastAPI | Latest | Async, rápido, type hints |
| ORM | SQLAlchemy | Latest | Soporte async, maduro |
| Auth | Keycloak OIDC | Latest | Estándar del gobierno |
| Database | PostgreSQL | 15+ | Robusto, soporta esquema externo |
| Cache | Redis | Latest | Sesiones, rate limiting |
| Gateway | Kong | Latest | JWT validation, rate limiting |
| Package Manager | uv | Latest | Rápido, moderno |
| Python | 3.14+ | Latest | Últimas features |
| Validation | Pydantic | v2 | Type safety, performance |
| CRUD | fastcrud | Latest | Simplifica operaciones |
| Testing | pytest + httpx | Latest | Async testing |

---

#### RA-004: NO Migraciones de ORM
**Prioridad**: Crítica

**Requerimientos:**
- NO usar Alembic para gestionar esquema
- El esquema es controlado externamente
- Los modelos ORM son MAPEOS, no definiciones
- Validación de sincronización modelo ↔ esquema SQL

**Razón:**
- El esquema de base de datos es propiedad de terceros
- Cambios en esquema vienen en scripts SQL externos
- La aplicación debe adaptarse al esquema, no lo define

---

### 7.3 Despliegue

#### RA-005: Despliegue en Docker
**Prioridad**: Alta

**Requerimientos:**
- Imagen Docker optimizada (multi-stage)
- Docker Compose para orquestación
- Variables de entorno configurables
- Health checks
- Logs en stdout/stderr

**Servicios en Docker Compose:**
```
┌─────────────────────────────────────┐
│         Docker Compose             │
├─────────────────────────────────────┤
│ - tramites-backend (FastAPI)      │
│ - postgres (PostgreSQL 15+)        │
│ - redis (Redis)                   │
│ - keycloak (Keycloak) [opcional]  │
│ - kong (Kong) [opcional]          │
└─────────────────────────────────────┘
```

---

#### RA-006: Configuración por Entorno
**Prioridad**: Alta

**Entornos:**
- `development`: Desarrollo local
- `staging`: Pre-producción
- `production`: Producción (intranet)
- `test`: Testing automatizado

**Archivos de configuración:**
- `.env`: Variables de entorno (no versionado)
- `.env.example`: Plantilla (versionado)
- `.env.production`: Ejemplo producción (versionado)

**Variables críticas:**
- `BACKEND_DB_URL`
- `KEYCLOAK_SERVER_URL`
- `KEYCLOAK_REALM`
- `KEYCLOAK_CLIENT_ID`
- `KEYCLOAK_CLIENT_SECRET`
- `REDIS_URL`
- `ENVIRONMENT`

---

### 7.4 Comunicación

#### RA-007: API RESTful
**Prioridad**: Alta

**Principios REST:**
- Recursos identificados por URIs
- Métodos HTTP semánticos (GET, POST, PUT, DELETE)
- Códigos de estado HTTP apropiados
- Sin estado (stateless)
- HATEOAS opcional (enlaces entre recursos)

**Ejemplo de URIs:**
```
GET    /api/v1/tramites/           # Listar trámites
GET    /api/v1/tramites/{id}       # Obtener trámite
POST   /api/v1/tramites/           # Crear trámite
PUT    /api/v1/tramites/{id}       # Actualizar trámite
DELETE /api/v1/tramites/{id}       # Eliminar trámite
GET    /api/v1/catalogos/tipos/     # Listar tipos
```

---

#### RA-008: Documentación de API
**Prioridad**: Alta

**Requerimientos:**
- Documentación automática vía FastAPI (OpenAPI/Swagger)
- Disponible en `/docs` (Swagger UI)
- Disponible en `/redoc` (ReDoc)
- Descripciones detalladas de cada endpoint
- Ejemplos de requests y responses
- Modelos Pydantic documentados
- Versión de API en URI (`/api/v1/`)

---

---

## 8. REQUERIMIENTOS DE DATOS

### 8.1 Estructura de Datos

#### RD-001: Tablas del Sistema
**Prioridad**: Crítica

**Total de tablas**: 20+

**Categorías:**

1. **Catálogos (cat_*)**: 9 tablas
   - cat_tramite
   - cat_estatus
   - cat_usuario
   - cat_perito
   - cat_actividad
   - cat_categoria
   - cat_inciso
   - cat_requisito
   - cat_tipo

2. **Relaciones (rel_*)**: 5 tablas
   - rel_tmt_cate_req
   - rel_tmt_categoria
   - rel_tmt_inciso
   - rel_tmt_tipo_req
   - rel_tmt_actividad

3. **Entidades Principales**: 3 tablas
   - tramite
   - actividades
   - cobro

4. **Auditoría y Configuración**: 3 tablas
   - bitacora
   - costo
   - uma

---

#### RD-002: Denormalización Intencional
**Prioridad**: Alta

**Campos denormalizados:**
- `tramite.id_cat_tramite` (Integer, no FK)
- `tramite.id_cat_estatus` (Integer, no FK)
- `tramite.id_cat_perito` (Integer, no FK)
- `tramite.nom_sol` (nombre del solicitante)
- `actividades.id_cat_usuario` (Integer, no FK)

**Razón:**
- Mejor performance (evita JOINs)
- Evita FKs entre microservicios
- Datos de catálogos cambiados lentamente
- Espacio de disco no es problema

---

### 8.2 Integridad de Datos

#### RD-003: Claves Primarias
**Prioridad**: Crítica

**Requerimientos:**
- Cada tabla tiene PK con `id` (AutoField)
- PKs son únicas y no nulas
- Uso de secuencia auto-incremental

---

#### RD-004: Claves Únicas
**Prioridad**: Alta

**Campos con UNIQUE:**
- `tramite.folio`: No puede haber dos trámites con mismo folio

---

#### RD-005: Valores No Nulos
**Prioridad**: Alta

**Campos NOT NULL obligatorios (ejemplos):**
- `tramite.id_cat_tramite`: Todo trámite debe tener tipo
- `tramite.nom_sol`: Todo trámite debe tener solicitante
- `cat_tramite.nombre`: Todo tipo de trámite debe tener nombre

---

### 8.3 Índices

#### RD-006: Índices Optimizados
**Prioridad**: Alta

**Índices en tabla `tramite`:**
```sql
CREATE INDEX idx_tramite_folio ON tramite(folio);
CREATE INDEX idx_tramite_estatus_creado ON tramite(id_cat_estatus, creado DESC);
CREATE INDEX idx_tramite_estatus_no_pagado ON tramite(pagado, creado DESC);
CREATE INDEX idx_tramite_urgente ON tramite(id, creado DESC)
  WHERE urgente = TRUE;
CREATE INDEX idx_tramite_urgente_no_pagado ON tramite(id, creado DESC)
  WHERE urgente = TRUE AND pagado = FALSE;
CREATE INDEX idx_tramite_prioridad ON tramite(urgente DESC, id_cat_estatus, creado DESC)
  WHERE pagado = FALSE;
```

**Otros índices:**
- `cat_tramite.nombre`
- `cat_estatus.estatus`
- `cat_perito.paterno`, `cat_perito.materno`, `cat_perito.nombre`

---

### 8.4 Timestamps

#### RD-007: Campos de Auditoría Temporal
**Prioridad**: Crítica

**Campos en `tramite`:**
- `creado`: DateTime, auto_now_add (insert)
- `modificado`: DateTime, auto_now (update)

**Campos en `bitacora`:**
- `fecha`: Date (fecha de la acción)

**Requerimientos:**
- Sistema UTC o con zona horaria configurada
- Formato ISO 8601 en APIs
- Inmutabilidad de `creado`
- Actualización automática de `modificado`

---

### 8.5 Datos de Catálogos

#### RD-008: Datos Iniciales (Seed Data)
**Prioridad**: Alta

**Requerimientos:**
- Scripts SQL con datos iniciales en `sql/data/`
- Incluye:
  - Tipos de trámite básicos
  - Estandares de estatus (1xx, 2xx, 3xx)
  - Peritos de ejemplo
  - Categorías principales
  - Requisitos comunes

---

#### RD-009: Valor Inicial de UMA
**Prioridad**: Alta

**Requerimientos:**
- Tabla `uma` tiene registro con `id = 1`
- Valor de UMA actualizado según decreto oficial
- Procedimiento almacenado `sp_actualizar_uma(valor)` para actualizar

---

---

## 9. REQUERIMIENTOS DE AUDITORÍA

### 9.1 Registro de Auditoría

#### RAUD-001: Auditoría Automática
**Prioridad**: Crítica

**Requerimientos:**
- Cada operación CRUD debe crear registro en `bitacora`
- No se puede desactivar la auditoría
- No se puede modificar registros de bitácora
- No se puede eliminar registros de bitácora

**Operaciones auditadas:**
| Operación | Tipo de movimiento | Detalles |
|-----------|-------------------|-----------|
| Crear trámite | INSERT | Todos los campos del nuevo trámite |
| Modificar trámite | UPDATE | Campos modificados, valor anterior y nuevo |
| Eliminar trámite | DELETE | Trámite eliminado, campos antes de eliminación |
| Cambiar estatus | UPDATE | Estatus anterior y nuevo |
| Asignar perito | UPDATE | Perito asignado |
- Modificar catálogos | INSERT/UPDATE/DELETE | Catálogo modificado, detalles del cambio |
- Registrar pago | INSERT | Datos del pago, trámite afectado |

---

#### RAUD-002: Datos de Auditoría
**Prioridad**: Crítica

**Campos obligatorios en bitácora:**
- `usuario_sis`: Usuario de Keycloak que realizó acción
- `tipo_mov`: Tipo de operación (INSERT, UPDATE, DELETE)
- `usuario_pc`: IP o máquina donde se realizó
- `fecha`: Fecha de la acción
- `val_anterior`: Valor antes del cambio (solo UPDATE)
- `val_nuevo`: Valor después del cambio (INSERT/UPDATE)
- `observaciones`: Contexto adicional

---

#### RAUD-003: Consulta de Auditoría
**Prioridad**: Alta

**Funcionalidades:**
- Consultar historial de un trámite específico
- Consultar historial por usuario
- Consultar por rango de fechas
- Consultar por tipo de movimiento
- Exportar bitácora a CSV/Excel
- Paginación de resultados (bitácora puede ser muy grande)

---

### 9.2 Reportes de Auditoría

#### RAUD-004: Reportes de Actividad
**Prioridad**: Media

**Reportes disponibles:**
- Trámites creados por usuario
- Trámites modificados por usuario
- Cambios de estatus por día
- Tiempos de respuesta por tipo de trámite
- Peritos más activos

**Formatos:**
- JSON (API)
- CSV (exportación)
- PDF (reportes oficiales)

---

---

## 10. RESTRICCIONES Y LIMITACIONES

### 10.1 Restricciones Técnicas

#### RTL-001: Sin Migraciones Automáticas
**Prioridad**: Crítica

**Restricción:**
- NO se puede usar Alembic para crear/modificar tablas
- El esquema es propiedad de terceros
- Solo se pueden MAPEAR tablas existentes al ORM

---

#### RTL-002: Sin Gestión Local de Usuarios
**Prioridad**: Crítica

**Restricción:**
- NO se puede crear/eliminar usuarios en el backend
- Toda gestión de usuarios en Keycloak
- Solo se almacenan `user_id` y `username` de Keycloak

---

#### RTL-003: Relaciones No Declarativas
**Prioridad**: Alta

**Restricción:**
- NO se pueden declarar FKs en modelos SQLAlchemy
- Relaciones se manejan con campos Integer
- JOINs se hacen manualmente cuando necesario

**Razón:**
- El esquema externo no tiene FKs declaradas
- Evita conflictos entre ORM y esquema

---

### 10.2 Limitaciones de Rendimiento

#### RTL-004: Base de Datos Centralizada
**Prioridad**: Media

**Limitación:**
- Una sola base de datos PostgreSQL
- Sin sharding o particionamiento
- Toda aplicación usa la misma BD

**Impacto:**
- Escalabilidad vertical (más recursos en servidor de BD)
- Posible cuello de botella en alta carga

---

#### RTL-005: Sin Caché Distribuido Avanzado
**Prioridad**: Baja

**Limitación:**
- Redis básico (no Redis Cluster)
- Sin caché de segundo nivel
- Cache invalidation manual

---

### 10.3 Limitaciones Funcionales

#### RTL-006: Sin Notificaciones
**Prioridad**: Media

**Limitación:**
- NO envía correos electrónicos
- NO envía SMS
- NO push notifications
- Los usuarios deben consultar estatus manualmente

---

#### RTL-007: Sin Generación de Documentos
**Prioridad**: Media

**Limitación:**
- NO genera PDF de constancias
- NO imprime documentos
- NO firma digitalmente
- Los documentos se generan en frontend o sistema externo

---

#### RTL-008: Sin Workflow Avanzado
**Prioridad**: Baja

**Limitación:**
- NO tiene motor de workflow (BPMN)
- Cambios de estatus son manuales
- NO tiene reglas de transición de estados
- NO tiene notificaciones de asignación

---

### 10.4 Restricciones de Seguridad

#### RTL-009: Autenticación Obligatoria
**Prioridad**: Crítica

**Restricción:**
- NO hay endpoints públicos (excepto health)
- TODOS requieren token JWT válido
- NO hay acceso anónimo

---

#### RTL-010: Acceso Solo en Intranet
**Prioridad**: Alta

**Restricción:**
- Sistema diseñado para intranet
- NO expuesto a internet pública
- Kong maneja firewall/red

---

---

## 11. CRITERIOS DE ACEPTACIÓN

### 11.1 Criterios Generales

#### CA-001: Funcionalidad Completa
**Prioridad**: Crítica

**Criterio:**
- TODOS los requerimientos funcionales RF-001 a RF-020 implementados
- TODOS los requerimientos de integración RI-001 a RI-007 funcionales
- Sistema puede gestionar ciclo completo de trámites

**Evidencia:**
- Listado de RF implementados con pruebas
- Documentación de API completa
- Demo funcional

---

#### CA-002: Performance Aceptable
**Prioridad**: Crítica

**Criterio:**
- Todos los tiempos de respuesta de RNF-001 cumplidos
- Sistema soporta 50 usuarios concurrentes (RNF-002)
- Sin degradación bajo carga moderada

**Evidencia:**
- Benchmark de tiempos de respuesta
- Pruebas de carga con JMeter/k6
- Reporte de performance

---

#### CA-003: Seguridad Validada
**Prioridad**: Crítica

**Criterio:**
- TODOS los requerimientos de seguridad RS-001 a RS-015 implementados
- Auditoría de seguridad RS-008 activa
- Penetration test sin vulnerabilidades críticas

**Evidencia:**
- Reporte de pentest
- Checklist de seguridad completado
- Logs de seguridad revisados

---

### 11.2 Criterios por Módulo

#### CA-004: Módulo de Trámites
**Prioridad**: Alta

**Criterios:**
- ✅ Crear trámite con folio único auto-generado
- ✅ Consultar trámite por folio (< 200ms)
- ✅ Listar trámites con filtros (estatus, pagado, urgente)
- ✅ Actualizar trámite (bitácora registrada)
- ✅ Eliminar trámite (solo admin, bitácora registrada)
- ✅ Cambiar estatus (bitácora registrada)

**Pruebas:**
- Test de creación con folio único
- Test de búsqueda por folio
- Test de listado con filtros
- Test de actualización con auditoría

---

#### CA-005: Módulo de Costos
**Prioridad**: Alta

**Criterios:**
- ✅ Cálculo de costo usando UMA actual
- ✅ Registro de pagos
- ✅ Actualización de valor de UMA
- ✅ Consulta de costos por tipo de trámite

**Pruebas:**
- Test de cálculo de costo
- Test de registro de pago
- Test de actualización de UMA

---

#### CA-006: Módulo de Auditoría
**Prioridad**: Crítica

**Criterios:**
- ✅ Cada operación CRUD crea registro en bitácora
- ✅ Registros de bitácora son inmutables
- ✅ Consulta de historial por trámite
- ✅ Consulta de historial por usuario
- ✅ Exportación de bitácora

**Pruebas:**
- Test de auditoría automática
- Test de inmutabilidad
- Test de consultas de historial

---

#### CA-007: Autenticación y Autorización
**Prioridad**: Crítica

**Criterios:**
- ✅ TODOS los endpoints requieren token JWT
- ✅ Validación de firma y expiración de token
- ✅ Control de acceso basado en roles (RBAC)
- ✅ Keycloak como única fuente de usuarios
- ✅ Integro con Kong API Gateway

**Pruebas:**
- Test de autenticación exitosa
- Test de rechazo sin token (401)
- Test de rechazo con token inválido (401)
- Test de rechazo sin rol (403)

---

### 11.3 Criterios de Calidad

#### CA-008: Código y Arquitectura
**Prioridad**: Alta

**Criterios:**
- ✅ Código sigue PEP 8 y mejores prácticas
- ✅ Type hints en TODAS las funciones públicas
- ✅ Documentación (docstrings) en TODOS los módulos
- ✅ Cobertura de tests > 80%
- ✅ Sin code smells detectados por linters
- ✅ Arquitectura en capas bien separadas

**Evidencia:**
- Reporte de cobertura (pytest-cov)
- Reporte de linters (ruff, mypy)
- Revisión de código peer-reviewed

---

#### CA-009: Documentación
**Prioridad**: Alta

**Criterios:**
- ✅ README con instrucciones de instalación y uso
- ✅ Documentación de API (Swagger/ReDoc)
- ✅ Documentación de despliegue (Docker)
- ✅ Documentación de configuración (.env.example)
- ✅ Este documento de requerimientos actualizado

**Evidencia:**
- Documentos publicados en repositorio
- Links accesibles desde README

---

#### CA-010: Tests
**Prioridad**: Alta

**Criterios:**
- ✅ Unit tests para modelos y CRUD
- ✅ Integration tests para endpoints
- ✅ Tests de autenticación y autorización
- ✅ Tests de auditoría
- ✅ Tests de error handling
- ✅ Todos los tests pasan en CI/CD

**Evidencia:**
- Reporte de pytest
- Pipeline de CI/CD funcionando

---

### 11.4 Criterios de Despliegue

#### CA-011: Entornos de Despliegue
**Prioridad**: Media

**Criterios:**
- ✅ Dockerfile optimizado y documentado
- ✅ docker-compose.yml con todos los servicios
- ✅ Variables de entorno configurables
- ✅ Health check endpoint funcional
- ✅ Logs estructurados en stdout

**Evidencia:**
- `docker build` exitoso
- `docker-compose up -d` exitoso
- Health check responde `/health`

---

#### CA-012: Integración con Infraestructura
**Prioridad**: Alta

**Criterios:**
- ✅ Conexión a PostgreSQL exitosa
- ✅ Conexión a Redis exitosa
- ✅ Validación de tokens JWT por Kong exitosa
- ✅ Comunicación con Keycloak (OIDC) funcional

**Evidencia:**
- Logs de conexión exitosos
- Tokens aceptados por Kong
- Autenticación en Keycloak funcionando

---

## 📚 GLOSARIO

| Término | Definición |
|----------|-------------|
| **Trámite** | Procedimiento administrativo o solicitud que realiza un ciudadano |
| **Folio** | Identificador único alfanumérico de un trámite |
| **UMA** | Unidad de Medida y Actualización - valor monetario de referencia |
| **Perito** | Experto técnico autorizado para validar trámites |
| **Keycloak** | Sistema de gestión de identidad y acceso (IAM) del gobierno |
| **Kong** | API Gateway para gestión de tráfico, seguridad y rate limiting |
| **OIDC** | OpenID Connect - Protocolo de autenticación estándar |
| **JWT** | JSON Web Token - Formato de token estándar |
| **RBAC** | Role-Based Access Control - Control de acceso basado en roles |
| **Bitácora** | Registro de auditoría de todas las operaciones |
| **CRUD** | Create, Read, Update, Delete - Operaciones básicas |
| **RESTful** | Estilo arquitectónico de APIs basado en REST |
| **ORM** | Object-Relational Mapping - Capa de abstracción de base de datos |
| **SPA** | Single Page Application - Aplicación web de una sola página |
| **Intranet** | Red privada interna de la organización |
| **Denormalización** | Almacenar datos relacionados directamente (evita JOINs) |

---

## 📊 RESUMEN DE REQUERIMIENTOS

| Categoría | Cantidad | Prioridad Alta+ | Prioridad Crítica |
|------------|-------------|------------------|-------------------|
| **Funcionales (RF)** | 20 | 15 | 5 |
| **No Funcionales (RNF)** | 13 | 8 | 4 |
| **Integración (RI)** | 7 | 5 | 2 |
| **Seguridad (RS)** | 15 | 7 | 5 |
| **Arquitectura (RA)** | 8 | 5 | 2 |
| **Datos (RD)** | 9 | 7 | 3 |
| **Auditoría (RAUD)** | 4 | 2 | 1 |
| **TOTAL** | **76** | **49** | **22** |

**Prioridades:**
- 🔴 Crítica: 22 requerimientos
- 🟠 Alta: 49 requerimientos
- 🟡 Media: 5 requerimientos

---

## 📝 HISTORIAL DE CAMBIOS

| Versión | Fecha | Autor | Cambio |
|---------|--------|---------|---------|
| 1.0 | 2026-02-25 | Documento inicial - Requerimientos completos |

---

## 📞 CONTACTO

**Cliente:** Gobierno de San Felipe
**Proyecto:** Backoffice de Trámites
**Versión:** 1.0.0

---

**Fin del Documento**
