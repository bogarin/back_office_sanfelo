# Glosario de Términos del Backoffice de Trámites

> **Términos clave del dominio que necesitas conocer**
> Última actualización: 23 de abril de 2026

---

## Términos de Negocio

### Trámite

Un procedimiento administrativo que un ciudadano inicia ante el gobierno municipal. Ejemplos: licencia de construcción, permiso de uso de suelo, constancia de residencia.

En el sistema, un trámite se representa como un registro en la vista `v_tramites_unificado` con datos del solicitante, tipo de trámite, estatus actual y asignación.

### Folio

Número identificador único de un trámite. Formato: `XXXXXX-XXXXXX-XXXX-A-N` (ejemplo: `SF2026-000001-0001-A-1`). Se usa para buscar y referenciar trámites.

### Estatus

Estado actual del trámite en su ciclo de vida. Códigos numéricos agrupados:

- **1xx (Inicio):** Borrador, Pendiente de pago, Pago expirado
- **2xx (Proceso):** Presentado, En revisión, Requerimiento, Subsanado, En diligencia
- **3xx (Final):** Por recoger, Rechazado, Finalizado, Cancelado

Ver: [Referencia de estados](../05-reference/estados-tramites.md)

### Actividad

Registro de un evento ocurrido en un trámite. Cada cambio de estatus, asignación u observación genera una nueva actividad. Las actividades son **APPEND_ONLY**: se crean pero nunca se modifican ni eliminan. Son la fuente de verdad y auditoría del sistema.

### Asignación

Vinculación de un trámite con un analista específico. Un trámite puede estar:

- **Sin asignar:** Disponible para que cualquier analista lo tome
- **Asignado:** Vinculado a un analista específico

La asignación se registra en la tabla `asignacion_tramite` (schema backoffice).

### Requisito

Documento PDF que el solicitante debe presentar como parte de su trámite. Los archivos se almacenan en un servidor SFTP externo y se accede a ellos desde el sistema.

### Perito

Profesional registrado que interviene en ciertos tipos de trámites (ej: avalúos, peritajes). Los peritos se registran en el catálogo `cat_perito` y se asocian a trámites específicos.

### Catálogo

Tabla de referencia con datos maestros del sistema. Los catálogos son gestionados externamente (no por este sistema):

- `cat_tramite` — Tipos de trámites disponibles
- `cat_estatus` — Estados posibles de un trámite
- `cat_perito` — Peritos registrados
- `cat_actividad` — Tipos de actividades
- `cat_categoria` — Categorías de trámites
- `cat_requisito` — Requisitos para trámites
- `cat_tipo` — Tipos de requisito

---

## Términos Técnicos

### Django Admin

Interfaz de administración web que Django proporciona automáticamente. Es la **única interfaz** de este sistema. Se accede en `/admin/`.

### jazzmin

Paquete de terceros que aplica un tema Bootstrap moderno al Django Admin. Mejora la apariencia y usabilidad del panel.

### Schema (Esquema PostgreSQL)

Espacio de nombres dentro de una base de datos PostgreSQL. Este proyecto usa dos:

- **`backoffice`:** Datos propios de Django (usuarios, sesiones, asignaciones)
- **`public`:** Datos de negocio (trámites, catálogos, actividades)

Ver: [ADR-008: Schema Separation](../06-decisions/008-postgresql-schema-separation.md)

### Vista PostgreSQL (`v_tramites_unificado`)

Vista SQL que consolida datos de múltiples tablas en una sola estructura optimizada para lectura. El modelo `Tramite` de Django mapea a esta vista.

Ver: [ADR-009: Vista Unificada](../06-decisions/009-vista-postgresql-para-tramites.md)

### Proxy Model

Modelo Django que hereda de otro modelo sin crear una nueva tabla. En este sistema:

- `Tramite` — Modelo base (todos los trámites activos)
- `Buzon` — Proxy de Tramite (trámites asignados al usuario)
- `Disponible` — Proxy de Tramite (trámites sin asignar)

### RBAC (Role-Based Access Control)

Sistema de control de acceso basado en roles. Define qué puede ver y hacer cada tipo de usuario. Tres roles: Administrador, Coordinador, Analista.

Ver: [Referencia RBAC](../05-reference/rbac.md)

### Access Pattern (Patrón de Acceso)

Clasificación de cómo un modelo interactúa con la base de datos:

- **FULL_ACCESS:** CRUD completo (AsignacionTramite, auth)
- **READ_ONLY:** Solo lectura (Tramite, catálogos)
- **APPEND_ONLY:** Solo creación + lectura (Actividades)

### SFTP (SSH File Transfer Protocol)

Protocolo para transferir archivos de forma segura. En este sistema, los PDFs de requisitos se almacenan en un servidor SFTP externo y se sirven a través de Nginx X-Accel-Redirect.

### Nginx

Servidor web que actúa como proxy reverso dentro del contenedor Docker:

- Puerto 8080 (externo): Recibe peticiones HTTP
- Puerto 8081 (interno): Redirige a Gunicorn
- Sirve archivos estáticos directamente
- Gestiona descargas de PDFs via X-Accel-Redirect
- Rate limiting en `/admin/tramites/`

### Gunicorn

Servidor WSGI que ejecuta la aplicación Django. Se configura con múltiples workers para manejar peticiones concurrentes.

### LocMemCache

Backend de cache que Django proporciona por defecto. Almacena datos en memoria RAM por proceso. Cada worker de Gunicorn tiene su propia cache.

---

## Abreviaturas

| Abreviatura | Significado |
|-------------|-------------|
| RBAC | Role-Based Access Control (Control de Acceso Basado en Roles) |
| ORM | Object-Relational Mapping (Mapeo Objeto-Relacional) |
| FK | Foreign Key (Llave Foránea) |
| CSP | Content Security Policy (Política de Seguridad de Contenido) |
| CSRF | Cross-Site Request Forgery (Falsificación de Petición) |
| TTL | Time To Live (Tiempo de vida del cache) |
| WSGI | Web Server Gateway Interface |
| CRUD | Create, Read, Update, Delete |
| ADR | Architecture Decision Record (Registro de Decisión de Arquitectura) |

---

## Ver también

- [Overview del sistema](overview.md)
- [Arquitectura detallada](architecture-overview.md)
- [Referencia de estados de trámites](../05-reference/estados-tramites.md)
- [Glosario de comandos Django](../05-reference/commands.md)
