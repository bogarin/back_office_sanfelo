# Despliegue en Producción - Guía para Sysadmins

> **Guía para sysadmins**
> Tiempo estimado: 2 horas
> Última actualización: 26 de Febrero de 2026

---

## Resumen

Esta guía te mostrará cómo desplegar el Backoffice de Trámites en el entorno de producción (intranet del Gobierno de San Felipe). Al final, tendrás el sistema corriendo con Docker y Gunicorn, configurado para alta disponibilidad y seguridad.

## Lo que aprenderás

- Configurar variables de entorno para producción
- Configurar Docker Compose para producción
- Iniciar los servicios (backoffice, PostgreSQL, Redis)
- Verificar que todos los servicios estén corriendo correctamente
- Configurar logs y monitoreo
- Realizar backup y restore de la base de datos

## Requisitos previos

- Docker y Docker Compose instalados
- Docker Hub access (para pull de imágenes)
- PostgreSQL y Redis disponibles
- Usuario con permisos para Docker en el servidor de producción
- Conexión a la intranet del Gobierno de San Felipe
- Conocimiento básico de contenedores Docker

---

## Paso 1: Preparar Variables de Entorno

### 1.1 Obtener el Archivo de Ejemplo

```bash
# Copiar el archivo de ejemplo
cp .env.example .env
```

### 1.2 Editar el Archivo .env

Edita el archivo `.env` con los valores reales de producción:

```bash
# Usar tu editor favorito (nano, vim, VS Code, etc.)
nano .env
```

### 1.3 Variables de Entorno Obligatorias

Las siguientes variables DEBEN estar configuradas:

```env
# Core
DJANGO_SECRET_KEY=<your-secret-key-here>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=backoffice.intranet.gob.sanfelipe

# Database
BACKEND_DB_URL=postgresql://backoffice:secure_password@postgres:5432/backoffice_tramites

# Redis
REDIS_URL=redis://:6379:0

# Email
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_EMAIL_HOST=smtp.gob.sanfelipe
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_USE_TLS=True
DJANGO_EMAIL_HOST_USER=noreply@sanfelipe.gob.mx
DJANGO_EMAIL_HOST_PASSWORD=<your-smtp-password>

# Logging
DJANGO_LOG_LEVEL=INFO
```

> **IMPORTANTE**:
> - `DJANGO_SECRET_KEY`: Debe ser una clave secreta fuerte. Genera una única vez y guárdala en lugar seguro.
> - `BACKEND_DB_URL`: Cambia `secure_password` por la contraseña real de PostgreSQL.
> - `DJANGO_ALLOWED_HOSTS`: Lista de hosts permitidos separados por comas.
> - NO NUNCA uses el `.env.example` directamente en producción.

### 1.4 Generar Clave Secreta Segura

```bash
# Generar una clave secreta usando Python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# O usar OpenSSL
openssl rand -base64 48
```

Copia la clave generada al campo `DJANGO_SECRET_KEY` en tu archivo `.env`.

---

## Paso 2: Configurar Docker Compose

El proyecto incluye un archivo `docker-compose.yml` que define todos los servicios necesarios.

### 2.1 Revisar el Archivo docker-compose.yml

```bash
# Revisar la configuración
cat docker-compose.yml
```

Verás una configuración similar a esta:

```yaml
version: '3.8'

services:
  backoffice:
    build: .
    ports:
      - "${HTTP_PORT:-8090}:8090"
    environment:
      - BACKEND_DB_URL
      - REDIS_URL
      - DJANGO_SECRET_KEY
      - DJANGO_DEBUG
      - DJANGO_ALLOWED_HOSTS
      - DJANGO_LOG_LEVEL
    volumes:
      - ./logs:/app/logs
      - ./media:/app/media
      - ./static:/app/static
    depends_on:
      - postgres
      - redis
    restart: always

  postgres:
    image: postgres:15-alpine
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    environment:
      - POSTGRES_DB: backoffice_tramites
      - POSTGRES_USER: backoffice
      - POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    restart: always

volumes:
  postgres_data:
  redis_data:
```

### 2.2 Entender la Configuración

**Servicio backoffice**:
- Port: 8090 (configurable con `HTTP_PORT`)
- Environment: Usa variables del archivo `.env`
- Volumes: Logs, media, static para persistencia
- Depends_on: PostgreSQL y Redis (inicia antes de estos)

**Servicio postgres**:
- Image: PostgreSQL 15 Alpine
- Port: 5432 (configurable con `POSTGRES_PORT`)
- Database: `backoffice_tramites`
- User: `backoffice`
- Password: `secure_password` (cámbiar en producción)
- Volume: `postgres_data` para persistencia

**Servicio redis**:
- Image: Redis 7 Alpine
- Port: 6379 (configurable con `HTTP_PORT`)
- Volume: `redis_data` para persistencia

---

## Paso 3: Iniciar los Servicios

### 3.1 Verificar que no haya Servicios Corriendo

```bash
# Verificar contenedores existentes
docker-compose ps
```

Si ves contenedores del proyecto corriendo, detén primero:
```bash
docker-compose down
```

### 3.2 Crear y Levantar Volúmenes

```bash
# Crear volúmenes (si no existen)
docker volume create postgres_data
docker volume create redis_data
```

### 3.3 Iniciar Todos los Servicios

```bash
# Iniciar todos los servicios
docker-compose up -d
```

**Resultado esperado**: Verás salida como esta:
```
Creating network "backoffice_default"
Creating volume "backoffice_postgres_data"
Creating volume "backoffice_redis_data"
Creating volume "backoffice_static"
Creating volume "backoffice_media"
Creating volume "backoffice_logs"
Creating backoffice_postgres_1 ...
Creating backoffice_backoffice_1 ...
Creating backoffice_redis_1 ...
Creating backoffice_backoffice_1 ... done
```

**Tiempo estimado**: 30-60 segundos (dependiendo de la velocidad de descarga de imágenes).

---

## Paso 4: Verificar que los Servicios Estén Funcionando

### 4.1 Verificar el Estado de los Servicios

```bash
# Ver estado de los servicios
docker-compose ps
```

Deberías ver algo como:

```
NAME                    STATUS         PORTS
backoffice_backoffice_1   Up              0.0.0.0:8090->8090/tcp
backoffice_postgres_1      Up              0.0.0.0:5432->5432/tcp
backoffice_redis_1         Up              0.0.0.0:6379->6379/tcp
```

**Verifica que todos los servicios estén en estado "Up"**.

### 4.2 Verificar los Logs del Backoffice

```bash
# Ver logs del backoffice
docker-compose logs backoffice -f

# Ver últimos 20 líneas
docker-compose logs backoffice --tail 20
```

Deberías ver mensajes de inicio del servidor Django, como:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (1 silenced).
...

Starting development server at http://0.0.0.0:8090/...
Quit the server with CONTROL-C.
```

### 4.3 Verificar la Conexión a PostgreSQL

```bash
# Ver logs de postgres
docker-compose logs postgres -f

# Ver que la base de datos se inició correctamente
```

Busca mensajes como:
```
database system is ready to accept connections
```

### 4.4 Verificar la Conexión a Redis

```bash
# Ver logs de redis
docker-compose logs redis -f
```

Busca mensajes como:
```
Ready to accept connections
```

### 4.5 Verificar el Health Check

```bash
# Verificar health check
curl http://localhost:8090/health/
```

**Resultado esperado**: Deberías ver `"OK"`.

---

## Paso 5: Aplicar Migraciones de Django (SQLite)

```bash
# Ejecutar comando desde el contenedor
docker-compose exec backoffice python manage.py migrate
```

**Resultado esperado**:
```
Operations to perform:
  Apply all migrations: tramites, catalogos, bitacora, costos, core, contenttypes, auth, s...
Running migrations:
  No migrations to apply.
```

### 5.1 Crear Superusuario en Producción

```bash
# Crear superusuario en el contenedor
docker-compose exec backoffice python manage.py createsuperuser

# O usar --noinput para no interactivo
docker-compose exec -T backoffice python manage.py createsuperuser \
  --username admin \
  --email admin@sanfelipe.gob.mx \
  --noinput \
  --password <secure-password>
```

**Resultado esperado**: `Superuser created successfully.`

> **IMPORTANTE**: Reemplaza `<secure-password>` por una contraseña segura real para producción.

---

## Paso 6: Verificar el Despliegue

### 6.1 Acceder desde el Navegador

1. Abre tu navegador web
2. Navega a la URL de producción: `http://<server-ip>:8090/`
3. Deberías ver la página de inicio o redirección

### 6.2 Acceder al Django Admin

1. Navega a: `http://<server-ip>:8090/admin/`
2. Ingresa las credenciales de superusuario
3. Verás el panel de administración

### 6.3 Verificar una Operación CRUD

1. Desde el panel de admin, navega a "Trámites"
2. Intenta crear un trámite de prueba
3. Verifica que se guardó correctamente en la base de datos

**Resultado esperado**: El trámite debería aparecer en la lista de trámites y la información persistir en PostgreSQL.

---

## Paso 7: Configurar Logs y Monitoreo

### 7.1 Ubicación de Logs

Los logs se guardan en:
- **Servidor**: `./logs/` (volumen Docker montado)
- **Contenedor**: `/app/logs` (dentro del contenedor backoffice)
- **Rotación automática**: Máximo 10 MB por archivo, hasta 10 archivos históricos

### 7.2 Tipos de Logs

- **django.log**: Logs generales de la aplicación Django
- **gunicorn-access.log**: Logs de acceso HTTP
- **gunicorn-error.log**: Logs de errores de Gunicorn

### 7.3 Ver Logs en Tiempo Real

```bash
# Ver logs en tiempo real
docker-compose logs -f backoffice

# Ver logs específicos de un servicio
docker-compose logs -f postgres
```

### 7.4 Niveles de Logging

Los niveles de logging configurados:
- **DEBUG**: Información detallada para desarrollo
- **INFO**: Información normal de operación
- **WARNING**: Algo inesperado pero no crítico
- **ERROR**: Error que requiere atención
- **CRITICAL**: Error crítico que requiere acción inmediata

Configuración en `.env`:
```env
DJANGO_LOG_LEVEL=INFO  # Cambia a DEBUG para desarrollo
```

---

## Paso 8: Backup y Restore

### 8.1 Backup de la Base de Datos PostgreSQL

```bash
# Backup de la base de datos
docker exec postgres pg_dump -U backoffice backoffice_tramites > backup_$(date +%Y%m%d_%H%M%S).sql

# Guardar en el host
docker cp <container-id>:/backup_YYYYMMDD_HHMMSS.sql ./backups/
```

**Resultado esperado**: Tienes un archivo `.sql` con el respaldo completo de la base de datos.

### 8.2 Restore de la Base de Datos

```bash
# Restaurar la base de datos
docker exec -i postgres psql -U backoffice backoffice_tramites < backup_YYYYMMDD_HHMMSS.sql
```

### 8.3 Automatización de Backups

**Crontab para backups diarios**:

```bash
# Editar crontab
crontab -e

# Agregar línea para backup diario a las 3 AM
0 3 * * * /usr/bin/docker exec postgres pg_dump -U backoffice backoffice_tramites > /backups/daily_backups.sql
```

---

## Paso 9: Actualizar la Aplicación

### 9.1 Desplegar Nueva Versión

```bash
# Actualizar código (git pull)
git pull origin main

# Detener servicios temporalmente
docker-compose down

# Reconstruir la imagen
docker-compose build

# Iniciar servicios nuevamente
docker-compose up -d
```

### 9.2 Rollback si hay Problemas

Si el nuevo despliegue tiene problemas:

```bash
# Volver a versión anterior
git revert

# Rebuild de imagen anterior
docker-compose build

# Iniciar servicios
docker-compose up -d
```

---

## Paso 10: Troubleshooting Común

### 10.1 El Contenedor No Inicia

**Posibles causas**:
- Puerto ya en uso
- Error en variables de entorno
- Error en configuración de Docker

**Soluciones**:

```bash
# Ver puertos en uso
netstat -tulpn

# Ver logs detallados
docker-compose logs backoffice

# Ver configuración de variables
docker-compose config
```

### 10.2 Conexión a Base de Datos Falla

**Verificar**:
```bash
# Verificar que postgres está corriendo
docker-compose ps

# Ver logs de postgres
docker-compose logs postgres -f

# Verificar conectividad
docker-compose exec backoffice python manage.py dbshell -c "SELECT 1;"
```

**Si falla, revisa**:
- `BACKEND_DB_URL` en `.env`
- Credenciales correctas en Docker Compose
- Firewall o reglas de seguridad

### 10.3 La Aplicación No Responde

**Pasos**:
1. Verificar que backoffice está "Up" en `docker-compose ps`
2. Verificar logs del backoffice: `docker-compose logs backoffice -f`
3. Verificar que el puerto 8090 esté accesible
4. Usar `curl` para health check: `curl http://localhost:8090/health/`
5. Verificar logs de Gunicorn en `logs/gunicorn-error.log`

### 10.4 Problemas de Rendimiento

**Pasos para diagnosticar**:
1. Usar `docker stats` para verificar uso de recursos
2. Verificar logs de Gunicorn para errores
3. Revisar logs de Django para consultas lentas
4. Verificar que Redis está siendo usado correctamente

---

## Resumen

En esta guía has aprendido:

✅ Configurar variables de entorno para producción
✅ Configurar Docker Compose para producción
✅ Iniciar todos los servicios (backoffice, PostgreSQL, Redis)
✅ Verificar que los servicios están funcionando correctamente
✅ Configurar logs y monitoreo
✅ Realizar backup de la base de datos
✅ Desplegar nuevas versiones del sistema
✅ Solucionar problemas comunes de despliegue

---

## ¿Qué sigue?

### Para mantenimiento operativo continuo:
- 📋 [Guía: Backup y Restore](./backup-restore.md) - Guía detallada de backups
- 🔧 [Guía: Monitoring](./monitoring.md) - Configuración de monitoreo
- 🔧 [Guía: Troubleshooting avanzado](./troubleshoot.md) - Solución de problemas complejos

### Para desarrolladores:
- 💻 [Tutorial: Setup de Desarrollo Local](../../02-tutorials/developers/local-dev-setup.md) - Para desarrollo local
- 🧠 [Concepto: Arquitectura Dual](../../04-concepts/dual-database.md) - Para entender la arquitectura

### Para todos los roles:
- 🔍 [Referencia: Variables de Entorno](../../05-reference/configuration/environment-vars.md) - Documentación completa de variables
- 📋 [Guía: Troubleshooting](../../03-guides/sysadmins/troubleshoot.md) - Solución de problemas comunes

---

## Problemas Comunes

| Problema | Posible Causa | Solución |
|----------|---------------------------|
| `Error: port 8090 already in use` | Puerto ocupado por otro servicio | Cambia `HTTP_PORT` en `.env` o verifica qué servicio usa el puerto |
| `Error: Connection refused` | PostgreSQL no accesible | Verifica firewall y configuración de red |
| `Error: Host not found` | `DJANGO_ALLOWED_HOSTS` mal configurado | Verifica que el host esté incluido en la lista |
| `docker-compose up: Build failed` | Error en código o dependencias | Ver logs para identificar el error |
| `Container restarting repeatedly` | Error en configuración | Ver logs para identificar la causa |
| `Health check returns error` | Aplicación no está sana | Verifica logs y usa curl con -v para más detalles |

---

## Consejos y Mejores Prácticas

1. **Usa secrets management**: No almacenes contraseñas en texto plano. Usa `docker secrets` o variables de entorno del sistema.

2. **Configura TLS/SSL**: En producción, usa HTTPS. Configura NGINX o proxy para terminación TLS.

3. **Limita recursos**: Configura límites en Docker Compose para que los contenedores no usen todos los recursos del servidor.

4. **Usa tags de Docker**: Usa tags para versionar tus despliegues: `docker tag backoffice:latest`, `docker tag backoffice:v1.0.0`.

5. **Documenta cambios**: Mantén un registro de cambios para saber qué se desplegó y cuándo.

6. **Monitorea logs regularmente**: Revisa los logs al menos una vez al día para detectar problemas temprano.

7. **Ten plan de rollback**: Siempre mantén la versión anterior funcionando por si la nueva versión tiene problemas.

---

## Referencias Adicionales

- [Documentación de Gunicorn](https://docs.gunicorn.org/) - Configuración completa
- [Documentación de Docker](https://docs.docker.com/) - Guía de referencia
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/) - Configuración y administración
- [Documentación de Redis](https://redis.io/documentation) - Configuración y administración
- [Docker Compose](https://docs.docker.com/compose/) - Orquestación de múltiples contenedores

---

**¿Necesitas ayuda?**
- Consulta las [Guías Sysadmin](../../03-guides/sysadmins/)
- Contacta a tu equipo de DevOps
- Revisa el [Glosario de Términos](../01-onboarding/glossary.md) para entender términos técnicos

---

*Última actualización: 26 de Febrero de 2026*
