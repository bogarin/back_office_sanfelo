# ¿Qué es el Backoffice de Trámites?

## Resumen

El **Backoffice de Trámites** es un microservicio de gestión de expedientes diseñado para las dependencias del gobierno de San Felipe. Este sistema permite gestionar el ciclo de vida completo de los trámites, desde su creación hasta su cierre, con auditoría completa de todas las operaciones.

---

## Para quién es

Este sistema está diseñado para múltiples roles de usuarios, cada uno con necesidades específicas:

### 👷 Operadores
Gestionan trámites diarios, registran nuevos expedientes, actualizan estados, adjuntan documentos y realizan búsquedas. Son los usuarios principales del sistema.

### 👔 Administradores
Configuran y administran el sistema. Gestionan usuarios y grupos, configuran catálogos (tipos de trámites, estatus, requisitos), definen costos por trámite y agregan peritos especializados.

### 💻 Desarrolladores
Desarrollan, mantienen y contribuyen al código del sistema. Necesitan entender la arquitectura, la API, las decisiones de diseño y el proceso de contribución.

### 🔧 Sysadmins
Despliegan, configuran y mantienen el sistema en producción. Necesitan saber sobre Docker, bases de datos, monitoreo, backups y troubleshooting.

### 🤖 Agentes de IA
Procesan información para tareas automatizadas. Necesitan contexto estructurado del proyecto, especificaciones técnicas parsables, patrones de código y restricciones arquitectónicas.

---

## Qué hace

El Backoffice de Trámites proporciona las siguientes capacidades principales:

### 📝 Gestión Completa de Trámites
- Creación de nuevos trámites con numeración automática (formato: TRAM-AAAA-XXXXX)
- Seguimiento del ciclo de vida completo
- Historial de todos los cambios (auditoría completa)
- Asignación de trámites a usuarios específicos
- Gestión de prioridades de trámites

### 🗃️ Catálogos Configurables
El sistema incluye catálogos flexibles que se pueden adaptar según las necesidades del negocio:
- **Tipos de Trámite**: Categorías de trámites con tiempos estimados
- **Estatus**: Estados por los que puede pasar un trámite
- **Requisitos**: Documentación necesaria según tipo de trámite
- **Peritos**: Profesionales especializados que participan en trámites
- **Relaciones**: Mapeos many-to-many entre catálogos

### 💰 Sistema de Costos
- Cálculo automático de costos por trámite
- Uso de UMA (Unidad de Medida Actualizada) para cálculos
- Configuración flexible de costos según tipo de trámite
- Actualización de valores cuando cambia la UMA oficial

### 📊 Auditoría Completa (Bitácora)
- Registro de todos los cambios en trámites
- Información del usuario que realizó el cambio
- Tipo de acción realizada
- Campos modificados con valores anteriores y nuevos
- Consultas de historial completo

### 🔐 Sistema de Permisos y Roles
- Dos niveles principales de acceso: **Admin** y **Operador**
- Los administradores pueden configurar el sistema completo
- Los operadores solo pueden gestionar trámites asignados a ellos
- Permisos granulares según grupo de usuario

### 🔄 Arquitectura de Microservicio con API REST
- API REST completa para todas las operaciones
- Autenticación integrada
- Soporte para integraciones externas
- Endpoints bien documentados

---

## Arquitectura Técnica

### Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|----------|
| **Lenguaje** | Python | 3.14 | Lenguaje de desarrollo |
| **Framework** | Django | 6.0.2 | Framework web principal |
| **Gestor de Paquetes** | uv | latest | Gestión de dependencias |
| **Base de Datos (Auth)** | SQLite | - | Datos de Django (users, auth, sessions) |
| **Base de Datos (Negocio)** | PostgreSQL | - | Datos de negocio (tramites, catalogos, costos, bitácora) |
| **Caché** | Redis | - | Caché para mejorar rendimiento |
| **Interface** | Django Admin | - | Interface de administración |
| **WSGI Server** | Gunicorn | - | Servidor de aplicaciones para producción |
| **Contenedor** | Docker | - | Empaquetado y despliegue |

### Decisión de Arquitectura Clave: Base de Datos Dual

El sistema utiliza **dos bases de datos separadas** por diseño:

1. **SQLite**: Almacena datos internos de Django
   - Usuarios del sistema
   - Sesiones
   - Permisos de Django Admin
   - Metadatos de migraciones

2. **PostgreSQL**: Almacena datos de negocio
   - Trámites
   - Catálogos
   - Costos
   - Bitácora/auditoría

**¿Por qué esta separación?**
- Los datos de negocio son gestionados por un equipo externo
- Permite independencia de los sistemas
- Facilita migraciones y actualizaciones
- Mejora el mantenimiento y la seguridad

Para más información: Ver [Concepto: Dual Database](../04-concepts/dual-database.md)

---

## Características Principales

- ✅ **Arquitectura de Microservicio** - API REST autónoma
- ✅ **Gestión de Trámites** - CRUD completo con historial
- ✅ **Auditoría Completa** - Historial de todos los cambios (bitácora)
- ✅ **Sistema de Costos** - Cálculo de costos por trámite con UMA
- ✅ **Catálogos Completos** - Tipos, estatus, requisitos, categorías, peritos
- ✅ **Relaciones Many-to-Many** - Tablas de relación entre catálogos
- ✅ **Base de Datos Dual** - SQLite (Django) + PostgreSQL (legacy business data)
- ✅ **Sin Migraciones de Django** - Esquema gestionado en repositorio separado

---

## Comenzar

Elige tu rol para comenzar:

### 👷 ¿Eres Operador?
Empezar a usar el sistema: **[Tutorial: Crear tu primer trámite](../02-tutorials/operators/create-tramite.md)**

### 👔 ¿Eres Administrador?
Configurar el sistema: **[Tutorial: Configurar usuarios](../02-tutorials/admins/setup-users.md)**

### 💻 ¿Eres Desarrollador?
Setup de desarrollo local: **[Tutorial: Setup de desarrollo](../02-tutorials/developers/local-dev-setup.md)**

### 🔧 ¿Eres Sysadmin?
Desplegar en producción: **[Guía: Despliegue en producción](../03-guides/sysadmins/deploy-production.md)**

### 🤖 ¿Eres Agente de IA?
Ver documentación optimizada: **[Contexto para LLMs](../08-ai-optimized/context.md)**

---

## Leer más

### Arquitectura Detallada
Para entender la arquitectura completa del sistema, incluyendo diagramas y flujo de datos:
**→ [Arquitectura Detallada](./architecture-overview.md)**

### Glosario de Términos
Para entender términos clave del negocio como "tramite", "perito", "UMA":
**→ [Glosario](./glossary.md)**

### Documentación Completa
Para ver toda la documentación disponible organizada:
**→ [Mapa de Documentación](../README.md)**

---

## Contexto del Proyecto

### Gobierno de San Felipe
El sistema es parte de la infraestructura de la **Gobierno de San Felipe** y opera dentro de la intranet gubernamental. Los trámites gestionados por este sistema son parte de los servicios ciudadanos proporcionados por las distintas dependencias gubernamentales.

### Enfoque en Calidad
El proyecto se enfoca en:
- **Auditoría completa**: Toda acción es registrada
- **Sistema de costos transparente**: UMA como estándar de medición
- **Flexibilidad de configuración**: Catálogos adaptables
- **Documentación exhaustiva**: Soporte completo para usuarios

---

## Tecnologías Específicas

### Python 3.14
La versión más reciente de Python con mejoras de rendimiento, typing mejorado y nuevas características del lenguaje.

### Django 6.0.2
Framework web maduro con:
- ORM robusto
- Admin interface integrada
- Sistema de autenticación incorporado
- API REST framework (DRF)

### uv
Gestor de paquetes moderno y rápido, reemplazo de pip y venv.

### Redis
Sistema de caché en memoria para:
- Sesiones distribuidas
- Caché de consultas
- Almacenamiento temporal

---

## Consideraciones de Diseño

### Estrategia Sin Migraciones
Este proyecto **NO usa migraciones de Django** para la base de datos de negocio (PostgreSQL). El esquema es gestionado externamente por el equipo de base de datos.

**¿Por qué?**
- El esquema es responsabilidad de un equipo externo
- Facilita la coordinación con sistemas legacy
- Evita conflictos de esquema

Para más información: Ver [ADR-002: Configuración de Múltiples Bases de Datos](../06-decisions/002-configuracion-multiples-bases-de-datos.md)

### Denormalización de Datos
Algunos datos están denormalizados intencionalmente:
- `tipo_nombre` en lugar de joins a tabla de tipos
- `usuario_username` en lugar de joins a tabla de usuarios

**¿Por qué?**
- Mejor performance de consultas
- Evita FKs complejas entre microservicios
- Simplicidad en la capa de datos

**Trade-off**: Redundancia de datos a cambio de performance

Para más información: Ver [ADR-003: Estrategia de Caching y Rendimiento](../06-decisions/003-estrategia-caching-rendimiento.md)

---

## Seguridad y Cumplimiento

### Seguridad
- ✅ Autenticación Django integrada
- ✅ HTTPS en producción (intranet)
- ✅ CORS configurado para integraciones
- ✅ Validación de permisos
- ✅ Logs completos de auditoría

### Cumplimiento
- ✅ Auditoría de todos los cambios
- ✅ Trazabilidad completa de acciones
- ✅ Sistema de permisos granular

---

## Preguntas Frecuentes

### ¿Puedo acceder al sistema desde fuera?
No, el sistema opera en la intranet del Gobierno de San Felipe. No es accesible públicamente.

### ¿Cómo se calculan los costos?
Los costos se calculan usando **UMA (Unidad de Medida Actualizada)**, que es un estándar oficial del gobierno mexicano para el valor monetario. Los valores se actualizan cuando cambia la UMA oficial.

### ¿Qué sucede si cometo un error?
Todos los errores son registrados en la bitácora (auditoría). Puedes ver el historial de cambios para cualquier trámite. Si necesitas deshacer un cambio, consulta con un administrador.

### ¿El sistema guarda automáticamente?
Sí, el sistema guarda automáticamente cada acción que realizas. No necesitas guardar manualmente.

---

## Soporte y Ayuda

### ¿Necesitas ayuda técnica?
- Consulta las [Guías de Troubleshooting](../03-guides/sysadmins/troubleshoot.md)
- Revisa el [Glosario](./glossary.md) para términos
- Contacta al equipo de soporte

### ¿Tienes sugerencias?
El proyecto mejora continuamente. Si tienes sugerencias para mejorar el sistema:
1. Contacta a tu administrador del sistema
2. Reporta el issue a través del canal oficial

---

## Próximos Pasos

Dependiendo de tu rol, continúa con:

### Operadores
1. Tutorial: Crear tu primer trámite
2. Tutorial: Flujo de trabajo diario
3. Guías: Cambiar estado, subir documentos, buscar trámites

### Administradores
1. Tutorial: Configurar usuarios
2. Tutorial: Gestionar catálogos
3. Guías: Agregar peritos, configurar costos, gestionar grupos

### Desarrolladores
1. Tutorial: Setup de desarrollo local
2. Tutorial: Primera llamada a la API
3. Conceptos: Dual database, no migraciones
4. Guías: Crear endpoint, ejecutar tests

### Sysadmins
1. Guía: Despliegue en producción
2. Guía: Setup de Docker
3. Guía: Backup y restore
4. Guía: Monitoring

---

*Última actualización: 26 de Febrero de 2026*
