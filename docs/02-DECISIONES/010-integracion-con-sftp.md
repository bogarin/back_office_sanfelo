# Integración con Servidor SFTP para Descarga de Requisitos

## Contexto y Planteamiento del Problema

Los ciudadanos que inician un trámite en San Felipe deben subir documentos PDF como evidencia de los requisitos solicitados. Estos archivos se almacenan en un servidor SFTP externo al backoffice. Los analistas del área de ventanillas necesitan revisar estos documentos para validar que el ciudadano haya cumplido con los requisitos, solicitar correcciones, o darle curso al trámite.

El problema es que el backoffice no tiene acceso directo al sistema de archivos del servidor SFTP. Se requiere una integración que permita a los usuarios autenticados del admin (analistas, coordinadores, administradores) descargar los archivos PDF subidos por los ciudadanos sin exponer el servidor SFTP directamente a internet.

La integración debe cumplir con los requisitos de un sistema gubernamental: auditoría de descargas, autorización a nivel de objeto, defensa en profundidad contra inyección de rutas, y caché local para optimizar el rendimiento en archivos de 10-50 MB.

## Opciones Consideradas

* **Opción 1**: Servicio Django con classmethods y caché local — Acceso via Nginx X-Accel-Redirect
* **Opción 2**: Proxy SFTP vía nginx sin validación en aplicación
* **Opción 3**: Descarga directa por URL firmada con expiry (AWS S3 presigned URL style)

## Resultado de la Decisión

Opción elegida: **"Servicio Django con classmethods y caché local"**, porque es la única opción que permite validación de autorización a nivel de objeto antes de servir el archivo, mantiene auditoría completa de descargas, y permite defensa en profundidad con validación de caracteres prohibidos y regex en Python antes de cualquier interacción con el servidor SFTP.

---

## Decisiones de Arquitectura

### Caché Local

| Parámetro | Valor | Notas |
|-----------|-------|-------|
| `SFTP_CACHE_DIR` | `.sftp_cache` (dev) o `/app/.sftp_cache` (prod) | Directorio configurado via variable de entorno |
| `SFTP_CACHE_TTL` | 3600 segundos (1 hora) | Tiempo de vida antes de eviction |
| `SFTP_CACHE_MAX_SIZE_MB` | 500 MB | Límite máximo del directorio de caché |
| `MAX_DOWNLOAD_FILE_SIZE_BYTES` | 52428800 bytes (50 MB) | Validación de tamaño antes de descarga completa |

**Estrategia de eviction**: El comando de administración `clearsftpcache` implementa tres políticas:
1. Evict de archivos con antigüedad mayor a TTL
2. Evict LRU cuando se excede el tamaño máximo
3. Limpieza de archivos huérfanos con extensión `.downloading` mayores a 2x TTL

**Diseño del directorio de caché**: Estructura `{caché_dir}/{folio}/{filename}` para evitar colisiones entre trámites. La verificación de cache-hit usa `O_NOFOLLOW` para prevenir ataques de symlink malicious. El renombrado atómico de archivo temporal a final se realiza con `os.rename()`, el cual es atómico en Linux cuando origen y destino están en el mismo filesystem.

### Gestión de Conexiones

**Estrategia**: Conexión por solicitud (connection-per-request). Cada método público crea una instancia del servicio, ejecuta la operación, y cierra la conexión en el bloque `finally`. No se utiliza pooling de conexiones.

**Razón del rechazo de pooling**: La complejidad adicional de gestión de estado (reconexión automática, heartbeat), el riesgo de conexiones zombis en entornos WSGI con reload, y el hecho de que paramiko no provee pooling nativo. El overhead del handshake SSH es marginal comparado con la latencia de red para transferir archivos de 10-50 MB.

**Autenticación soportada** (en orden de prioridad):
1. SSH private key (RSA, Ed25519, ECDSA) con passphrase opcional
2. Password authentication

**Políticas de host key** (graduadas según entorno):
- `RejectPolicy`: Producción con variable `SFTP_HOST_KEY` configurada
- `WarningPolicy`: Desarrollo sin host key (loguea warning)
- Error: Producción sin host key (configuración inválida)

### API Pública (classmethods)

Los siguientes cuatro métodos constituyen la interfaz pública del servicio:

| Método | Propósito |
|--------|----------|
| `serve_requisito_pdf(tramite, filename)` | Pipeline completo: validación → cache → download → response |
| `fetch_requisito_files(folio)` | Listado de PDFs disponibles para un folio desde el directorio SFTP |
| `download_to_path(folio, filename, local_path)` | Descarga a ruta arbitraria (para CLI y management commands) |
| `ping()` | Test de conectividad con el servidor SFTP |

No se requiere instanciación explícita. Todos los métodos son `@classmethod` y crean la instancia internamente.

### Response Builder

| Entorno | Mecanismo de respuesta |
|---------|---------------------|
| `DEBUG=True` (desarrollo) | `FileResponse` directa desde el sistema de archivos local |
| `DEBUG=False` (producción) | `X-Accel-Redirect` con header `X-Accel-Redirect: /sftp-cache/{folio}/{filename}` |

En producción se añaden headers de seguridad: `X-Content-Type-Options: nosniff` y `X-Frame-Options: DENY`.

### Variables de Configuración

| Variable | Propósito |
|----------|-----------|
| `SFTP_HOST` | Hostname del servidor SFTP |
| `SFTP_PORT` | Puerto (default 22) |
| `SFTP_USERNAME` | Usuario para autenticación |
| `SFTP_PRIVATE_KEY_PATH` | Ruta a la clave privada SSH |
| `SFTP_PASSWORD` | Contraseña (si se usa autenticación por password) |
| `SFTP_BASE_DIR` | Directorio base en el servidor SFTP donde se almacenan los archivos |
| `SFTP_CACHE_DIR` | Directorio local de caché |
| `SFTP_CACHE_TTL` | Tiempo de vida del caché en segundos |
| `SFTP_CACHE_MAX_SIZE_MB` | Tamaño máximo del directorio de caché en MB |
| `SFTP_HOST_KEY` | Clave host del servidor SFTP (SHA256) para verificación en producción |
| `SFTP_TIMEOUT` | Timeout para operaciones SFTP (opcional) |

---

## Características de Seguridad Implementadas

### Modelo de Autorización

Se implementó autorización a nivel de objeto mediante la función `_check_download_permission()`. Esta función replica exactamente las reglas del admin queryset de Django:

| Grupo | Acceso |
|------|-------|
| **Superusuario** | Completo a cualquier trámite |
| **Administrador** | Completo a cualquier trámite |
| **Coordinador** | Completo a cualquier trámite |
| **Analista** | Trámites asignados al analista (cualquier estatus) + trámites no asignados con estatus en rango 200-299 |

**Divergencia documentada respecto al admin**: El admin filtra estatus 200-299 para analistas en el queryset. Sin embargo, la descarga permite acceso a trámites asignados independientemente del estatus. Esto es intencional: los analistas necesitan revisar los documentos antes de marcar el trámite como recibido, lo cual cambia el estatus.

### Defensa en Profundidad (Defense-in-Depth)

La validación de entradas sigue tres capas:

1. **Rechazo de caracteres prohibidos**: Los caracteres `/`, `\`, `NUL` (byte 0), y para folio también `.` son rechazados primero. Esto neutraliza ataques de path traversal en la capa más baja.

2. **Validación por regex anclado**: Se aplica regex con anclaje `^` y `$` para`folio` (`^[A-Z]+-\d{6}-[A-Z]{4}-[A-Z]$`) y para `filename` (`^[A-Z]+-\d{6}-[A-Z]{4}-[A-Z]-(?P<nombre>[A-Z]+)\.pdf$`). El anclaje garantiza que no haya secuencias de escape como `../../../etc/passwd.pdf`.

3. **Aserción en el boundary con nginx**: Se añade una aserción defensiva que verifica que la ruta construida para X-Accel-Redirect no contiene `..`, proporcionando una última capa de defensa antes de handed-off a nginx.

### Registro de Auditoría

Cada descarga registra: ID del usuario, PK del trámite, folio, nombre del archivo, y dirección IP del cliente. El registro se realiza en el log de auditoría del sistema.

### Decorator de Autenticación

La vista de descarga utiliza el decorator `@staff_member_required` de Django admin como requisito mínimo de autenticación.

### Verificación de Integridad de Caché

Al verificar un archivo en caché, se valida que:
- El archivo no sea un symlink (`O_NOFOLLOW` en `os.open`)
- El tamaño sea mayor a cero (`st_size > 0`)
- El archivo sea regular (`S_ISREG`)

Esto previene ataques de symlink maliciosos donde un atacante crea un symlink en el directorio de caché pointing a `/etc/passwd` o archivos sensibles.

---

## Decisiones Descartadas

### Streaming con X-Accel en Desarrollo

**Alternativa**: Usar X-Accel también en modo desarrollo.

**Razón del rechazo**: Requiere ejecutar nginx como proceso separado en desarrollo, lo cual complica el workflow local. El trade-off entre simplicidad y consistencia entre entornos no justifica el overhead.

### Connection Pooling

**Alternativa**: Pool de conexiones persistentes compartido entre requests.

**Razón del rechazo**: Complejidad adicional de gestión de estado, riesgo de conexiones zombis, y paramiko no provee pooling nativo. El overhead de handshake SSH es marginal vs. latencia de red para transferir archivos de 10-50 MB.

### Thumbnails para Preview

**Alternativa**: Generar thumbnails de páginas de los PDFs para previsualización rápida.

**Razón del rechazo**: Scope fuera de requisitos actuales (solo descarga), complejidad adicional de rendering, y almacenamiento extra.

### Cache Invalidation por Push

**Alternativa**: Notificación desde SFTP cuando cambia un archivo.

**Razón del rechazo**: Acoplamiento con sistema de archivos externo, complejidad de event handling, y TTL de 1 hora es suficiente para el volumen esperado.

---

## Siguientes Pasos (Deuda Técnica)

### Configuración nginx

Documentar la configuración nginx recomendada para producción, incluyendo el location `/sftp-cache/` con `internal;`, apuntando al directorio de caché, y headers de cache apropiados.

### Docker Volume para Caché

Implementar mount explícito del directorio de caché como volume nomeado o bind mount en `docker-compose.production.yml` para persistencia entre recreados del contenedor.

### Healthcheck Mejorado

Actualizar el healthcheck para incluir no solo listing del directorio base sino también verificación de latencia de conexión, escritura al directorio temporal, y permisos de lectura.

### Métricas de Cache Hit/Miss

Instrumentar el servicio con métricas (Prometheus o datadog) para registrar hit/miss del caché y optimizar los valores de TTL y tamaño máximo.

---

## Información Adicional

Este ADR complementa las decisiones documentadas en:
- ADR 007: Implementación RBAC Django 3. Decisión de roles de backoffice (analista, coordinador, administrador)
- ADR 005: Despliegue Docker + Gunicorn. Configuración de contenedor

---

Formato basado en [MADR](https://adr.github.io/madr/)