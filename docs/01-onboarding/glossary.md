# Glosario de Términos del Backoffice de Trámites

> **Términos clave del dominio que necesitas conocer**
> Última actualización: 26 de Febrero de 2026

---

## 📋 Índice Rápido

| Término | Tipo | Descripción Rápida |
|----------|------|-------------------|
| **Trámite** | Dominio | Expediente o solicitud gestionada en el sistema |
| **UMA** | Negocio | Unidad de Medida Actualizada (estándar monetario) |
| **Perito** | Dominio | Profesional especializado que participa en trámites |
| **Tipo de Trámite** | Sistema | Categoría que define el tipo de expediente |
| **Estatus** | Sistema | Estado por el que puede pasar un trámite |
| **Bitácora** | Sistema | Registro histórico de todos los cambios (auditoría) |
| **Catálogo** | Sistema | Tabla maestra de valores configurables |
| **Requisito** | Dominio | Documentación necesaria según tipo de trámite |
| **Admin** | Rol | Usuario con permisos de configuración completa |
| **Operador** | Rol | Usuario que gestiona trámites diariamente |

---

## 🗂️ Términos de Negocio

### Trámite

**Definición**: ExpEDIANTE o solicitud formal gestionada en el sistema, que sigue un ciclo de vida desde su creación hasta su cierre.

**Características**:
- Tiene un número único: formato `TRAM-AAAA-XXXXX`
- Pertenece a un **Tipo de Trámite** específico
- Tiene un **Estatus** actual
- Puede ser **asignado** a un usuario específico
- Tiene **costos** calculados según su tipo
- Tiene un **historial completo** de cambios

**Ejemplo**: TRAM-2026-00045 - Trámite de Licencia de Construcción

**Ver también**: [Modelo de Trámite](../05-reference/models/data-models.md)

---

### UMA (Unidad de Medida Actualizada)

**Definición**: Estándar oficial del gobierno mexicano para medir el valor monetario. La UMA se actualiza periódicamente por el gobierno.

**Propósito en el sistema**:
- Utilizada como base para calcular **costos de trámites**
- Permite actualizaciones automáticas cuando cambia la UMA oficial
- Estandariza la cuantificación de servicios y derechos

**Calculo**:
```
Costo del Trámite = (Valor en UMAs) × (Valor actual de UMA en MXN)
```

**Por qué usar UMA**:
- Permite ajustes automáticos por inflación
- Es un estándar legal transparente
- Facilita comparaciones entre diferentes servicios

**Referencia**: [Sistema de Costos](../05-reference/components/costos.md)

---

### Perito

**Definición**: Profesional especializado que participa en el proceso de un trámite, proporcionando opiniones técnicas, evaluaciones o validaciones.

**Tipos comunes**:
- Perito arquitectónico
- Perito topógrafo
- Perito ingeniero civil
- Perito valuador
- Otros especialistas según el tipo de trámite

**En el sistema**:
- Los peritos se gestionan en un **catálogo**
- Se pueden asignar a diferentes tipos de trámites
- Su información se usa para calcular costos adicionales
- Se registra su participación en la bitácora

**Ejemplo**: Para un trámite de construcción, se asigna un perito arquitectónico para evaluar el proyecto.

**Ver también**: [Guía: Agregar Peritos](../03-guides/admins/add-peritos.md)

---

### Tipo de Trámite

**Definición**: Categoría que define el tipo de expediente o solicitud, con sus características específicas.

**Atributos**:
- **Código**: Identificador único (ej: "LIC-CONST")
- **Nombre**: Descripción del tipo (ej: "Licencia de Construcción")
- **Departamento**: Dependencia responsable del trámite
- **Tiempo Estimado**: Días estimados para completar el trámite
- **Costo en UMAs**: Valor base en UMAs
- **Activo**: Indica si el tipo está actualmente disponible

**Ejemplos**:
- L-CONST: Licencia de Construcción
- L-USE-OCC: Licencia de Uso de Suelo
- DIV-LIN: División de Línecero
- REG-PROP: Registro de Propiedad

**Relación con Trámite**:
Cada trámite pertenece exactamente a **un tipo de trámite**. El tipo de trámite define:
- El flujo de trabajo
- Los requisitos necesarios
- Los costos base
- Los estatus posibles

**Ver también**: [Gestión de Catálogos](../02-tutorials/admins/manage-catalogs.md)

---

### Estatus (Estado del Trámite)

**Definición**: Estado por el que puede pasar un trámite durante su ciclo de vida.

**Estatuses Comunes**:
- **Registrado**: Trámite creado inicialmente
- **En Revisión**: Trámite siendo revisado por operador
- **En Proceso**: Trámite en proceso de atención
- **Esperando Documentos**: Requiere documentación adicional del solicitante
- **En Espera de Perito**: Asignado a perito para evaluación
- **Pendiente de Pago**: Awaiting payment
- **Completo**: Trámite finalizado exitosamente
- **Rechazado**: Trámite no aprobado
- **Cancelado**: Trámite cancelado por el solicitante

**Transiciones**:
Los trámites pueden cambiar de estatus siguiendo las reglas de negocio:
- No se pueden saltar estatus
- Algunas transiciones requieren autorización
- Todas las transiciones son registradas en la bitácora

**Ver también**: [Guía: Cambiar Estado](../03-guides/operators/change-status.md)

---

### Requisito

**Definición**: Documentación o condición necesaria para un tipo específico de trámite.

**Tipos**:
- **Documentos**: Identificación, comprobantes, planos, etc.
- **Formularios**: Formularios específicos firmados
- **Pagos**: Comprobantes de pago
- **Otros**: Cualquier otro requisito específico

**En el sistema**:
- Los requisitos se configuran por **tipo de trámite**
- Se marcan como obligatorios u opcionales
- Se pueden asignar múltiples requisitos a un tipo
- El sistema valida que los requisitos estén cumplidos

**Ejemplo**: Para "Licencia de Construcción":
- Requerido: Identificación oficial
- Requerido: Comprobante de domicilio
- Requerido: Planos arquitectónicos
- Opcional: Constancia de no adeudo de impuestos

---

## 🖥️ Términos de Sistema

### Bitácora (Historial de Auditoría)

**Definición**: Registro histórico completo de todos los cambios realizados en los trámites del sistema.

**Propósito**:
- Auditoría completa de todas las acciones
- Trazabilidad de quién hizo qué y cuándo
- Capacidad de reversión de cambios si es necesario
- Cumplimiento legal y normativo

**Información Registrada**:
- **Usuario**: Quién realizó el cambio (ID y username)
- **Acción**: Tipo de acción realizada (crear, actualizar, eliminar, cambiar estatus, etc.)
- **Campo**: Campo modificado (ej: "estatus", "asignado_a")
- **Valor Anterior**: Valor antes del cambio
- **Valor Nuevo**: Valor después del cambio
- **Timestamp**: Cuándo se realizó el cambio

**Ejemplo de Registro**:
```
Trámite: TRAM-2026-00045
Usuario: María González (ID: 123)
Acción: Cambiar estatus
Campo: status
Valor Anterior: En Revisión
Valor Nuevo: En Proceso
Timestamp: 2026-02-26 15:30:00
```

**Importancia**:
- Permite reconstructir la historia completa de cualquier trámite
- Facilita auditorías y revisiones
- Proporciona evidencia en caso de disputas
- Cumple requisitos de transparencia y trazabilidad

**Ver también**: [Concepto: Sistema de Auditoría](../04-concepts/audit-system.md)

---

### Catálogo

**Definición**: Tabla maestra o tabla de referencia que contiene valores configurables del sistema.

**Catálogos en el Sistema**:
- **Catálogo de Tipos de Trámite**: Define las categorías de trámites
- **Catálogo de Estatus**: Define los estados posibles
- **Catálogo de Requisitos**: Define documentos necesarios
- **Catálogo de Peritos**: Peritos especializados disponibles
- **Catálogo de Costos**: Valores base en UMAs por tipo
- **Catálogos de Relación**: Mapeos many-to-many entre catálogos

**Características**:
- Administrables: Se pueden agregar, modificar y eliminar entries
- Configurables: Se adaptan según las necesidades del negocio
- Jerárquicos: Algunos catálogos tienen estructura jerárquica
- Relacionables: Los catálogos pueden relacionarse entre sí

**Por qué usar catálogos**:
- Flexibilidad: No require cambios de código para nuevas categorías
- Mantenibilidad: Los administradores pueden gestionar sin desarrolladores
- Escalabilidad: Fácil de extender con nuevos tipos, estatus, etc.

**Ver también**: [Tutorial: Gestión de Catálogos](../02-tutorials/admins/manage-catalogs.md)

---

### Base de Datos Dual

**Definición**: Arquitectura que utiliza dos bases de datos separadas para diferentes propósitos.

**Bases de Datos en el Sistema**:

#### 1. SQLite (Base de Datos de Django)
**Propósito**: Almacena datos internos del framework Django
**Contenido**:
- `auth_user`: Usuarios del sistema
- `auth_group`: Grupos de usuarios
- `django_admin_log`: Logs de admin
- `django_session`: Sesiones de usuario
- Metadatos de migraciones

**Características**:
- Liviana, sin configuración externa
- Gestionada por Django (usa migraciones normales)
- Solo para datos internos del framework

#### 2. PostgreSQL (Base de Datos de Negocio)
**Propósito**: Almacena todos los datos de negocio del sistema
**Contenido**:
- `tramite_tramite`: Trámites
- `tramite_tipo_tramite`: Tipos de trámite
- `catalogos_*`: Todos los catálogos
- `costos_*`: Sistema de costos
- `bitacora_bitacora`: Registro de auditoría

**Características**:
- Gestionada externamente (equipo de base de datos)
- **No usa migraciones de Django** - esquema SQL directo
- Datos legacy y de negocio actuales

**¿Por qué esta separación?**
- Los datos de negocio son responsabilidad de un equipo externo
- Permite independencia y especialización
- Facilita migraciones de esquema sin afectar Django
- Mejora mantenimiento y seguridad

**Ver también**: [Concepto: Dual Database](../04-concepts/dual-database.md)

---

## 👥 Términos de Roles

### Admin (Administrador)

**Definición**: Usuario con permisos completos de configuración y administración del sistema.

**Permisos**:
- ✅ Gestionar usuarios y grupos
- ✅ Configurar catálogos (tipos, estatus, requisitos)
- ✅ Definir costos por tipo de trámite
- ✅ Gestionar peritos especializados
- ✅ Ver todo el historial y auditoría
- ✅ Configurar parámetros del sistema
- ✅ Acceder a Django Admin con todos los permisos

**Responsabilidades**:
- Configurar el sistema para los operadores
- Mantener los catálogos actualizados
- Gestionar el personal del sistema
- Revisar y aprobar configuraciones

**Ver también**: [Tutorial: Configurar Usuarios](../02-tutorials/admins/setup-users.md)

---

### Operador

**Definición**: Usuario que gestiona trámites diariamente, interactuando con el sistema para registrar y actualizar expedientes.

**Permisos**:
- ✅ Crear nuevos trámites
- ✅ Ver trámites asignados a ellos
- ✅ Actualizar estatus de trámites
- ✅ Adjuntar documentos a trámites
- ✅ Ver el historial de sus trámites
- ✅ Buscar y filtrar trámites
- ❌ No pueden ver trámites de otros operadores
- ❌ No pueden configurar catálogos
- ❌ No pueden gestionar usuarios

**Responsabilidades**:
- Registrar nuevos trámites cuando llegan solicitudes
- Actualizar estatus según avanza el proceso
- Adjuntar documentos requeridos
- Notificar a usuarios cuando hay cambios importantes
- Resolver dudas de ciudadanos sobre sus trámites

**Ver también**: [Tutorial: Flujo de Trabajo Diario](../02-tutorials/operators/manage-workflow.md)

---

## 🔧 Términos Técnicos

### API (Application Programming Interface)

**Definición**: Conjunto de endpoints que permiten la comunicación programática con el sistema Backoffice de Trámites.

**Características**:
- RESTful API
- Autenticación requerida para todos los endpoints
- Respuestas en formato JSON
- Códigos de estado HTTP estándar
- Documentación completa de endpoints

**Uso**:
- Integraciones con otros sistemas
- Aplicaciones móviles o web frontend
- Automatización de procesos
- Scripts de administración

**Ver también**: [Referencia: API Endpoints](../05-reference/api/endpoints.md)

---

### Django Admin

**Definición**: Interface de administración integrada del framework Django, utilizada como interface principal del sistema.

**Características**:
- Generación automática de forms basados en modelos
- Buscador y filtrado integrado
- Autenticación y permisos integrados
- Acciones en lote (bulk actions)
- Navegación jerárquica

**En este proyecto**:
- Es la **única interface** para operadores y administradores
- Todos los CRUD se realizan a través de Django Admin
- Personalizada con CSS y JavaScript según necesidades
- Organizada por apps (tramites, catalogos, costos, bitácora)

**Ventajas**:
- Desarrollo rápido (no requiere crear interfaces personalizadas)
- Seguridad integrada
- Mantenimiento sencillo
- Consistencia en toda la aplicación

**Ver también**: [Referencia: Django Admin](../05-reference/components/admin-interface.md)

---

### Gunicorn (Green Unicorn)

**Definición**: Servidor WSGI (Web Server Gateway Interface) para aplicaciones Python, utilizado para desplegar Django en producción.

**Propósito**:
- Servir la aplicación Django en producción
- Manejar múltiples solicitudes concurrentes
- Proveer balanceo de carga y procesos workers

**Configuración típica**:
```bash
gunicorn sanfelipe.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --access-logfile logs/gunicorn-access.log \
    --error-logfile logs/gunicorn-error.log \
    --log-level info
```

**Ver también**: [Guía: Despliegue en Producción](../03-guides/sysadmins/deploy-production.md)

---

### Redis

**Definición**: Sistema de almacenamiento en memoria usado como caché, message broker y store de sesiones.

**Usos en este proyecto**:
- **Caché**: Almacenar resultados de consultas frecuentes
- **Sessions**: Gestión distribuida de sesiones de usuario
- **Locking**: Prevención de condiciones de carrera

**Ventajas**:
- Mejora el rendimiento de la aplicación
- Reduce la carga en base de datos
- Permite escalabilidad horizontal

**Ver también**: [Referencia: Caché Redis](../05-reference/components/cache-redis.md)

---

## 📊 Categorías de Términos

| Categoría | Términos |
|-----------|-----------|
| **Negocio** | Trámite, UMA, Perito, Tipo de Trámite, Estatus, Requisito |
| **Sistema** | Bitácora, Catálogo, API, Django Admin |
| **Roles** | Admin, Operador, Desarrollador, Sysadmin |
| **Técnico** | Gunicorn, Redis, PostgreSQL, SQLite, Docker, uv |

---

## 🤝 ¿No encuentras un término?

Si encuentras un término en la documentación que no está definido en este glosario:

1. Busca en el [Índice del glosario](#-índice-rápido)
2. Revisa la [Documentación de Referencia](../05-reference/)
3. Consulta el [Mapa de Documentación](../README.md) para ubicaciones
4. Si aún no lo encuentras, reporta para que lo agreguemos

---

## 📚 Referencias Adicionales

- [Documentación de Django](https://docs.djangoproject.com/)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)
- [Documentación de Redis](https://redis.io/documentation)
- [Concepto: Dual Database](../04-concepts/dual-database.md)
- [Gestión de Catálogos](../02-tutorials/admins/manage-catalogs.md)

---

*Última actualización: 26 de Febrero de 2026*
