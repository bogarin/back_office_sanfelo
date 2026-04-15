# Instalación y Setup de Desarrollo Local

> **Tutorial para desarrolladores**
> Tiempo estimado: 35 minutos
> Última actualización: 15 de Abril de 2026

---

## Resumen

Esta guía te mostrará cómo configurar un entorno de desarrollo local para el Backoffice de Trámites. Al final, tendrás el proyecto ejecutándose en tu máquina con todas las dependencias instaladas.

## Lo que aprenderás

- Clonar el repositorio del proyecto
- Instalar dependencias con uv
- Configurar PostgreSQL con separación de esquemas
- Crear el superusuario de Django
- Iniciar el servidor de desarrollo
- Verificar que todo funciona correctamente

## Requisitos previos

- Python 3.14
- uv (package manager moderno)
- PostgreSQL
- Redis
- git (opcional, para clonar el repositorio)
- Conexión a la intranet del Gobierno de San Felipe (para clonar repositorio)

---

## Paso 1: Clonar el Repositorio

```bash
# Clonar el repositorio
git clone <repo-url>
cd backoffice_tramites
```

> **Nota**: Reemplaza `<repo-url>` con la URL real del repositorio Git.

**Resultado esperado**: Tienes el código fuente del proyecto en tu máquina local.

---

## Paso 2: Instalar Dependencias

```bash
# Instalar todas las dependencias
uv sync
```

**Qué hace `uv sync`**:
- Crea el entorno virtual automáticamente
- Instala todas las dependencias listadas en `pyproject.toml`
- Utiliza el cache de uv para instalaciones más rápidas

**Resultado esperado**: Verás una lista de paquetes instalados. Si hay errores, corrige según las instrucciones.

**Tiempo estimado**: 1-3 minutos (depende de tu conexión a internet).

---

## Paso 3: Configurar PostgreSQL con Separación de Esquemas

El sistema usa una arquitectura de **separación de esquemas en PostgreSQL**:
- **Esquema `backoffice`**: Datos internos de Django (auth, admin, sessions) y tablas de asignación (AsignacionTramite)
- **Esquema `public`**: Tablas de negocio legacy (tramites, catalogos, relaciones, actividades)

Esta separación permite que Django administre sus tablas en el esquema `backoffice`, mientras que el esquema `public` contiene las tablas de negocio legacy gestionadas externamente.

### 3.1 Crear la Base de Datos y Esquemas

El archivo `.env.example` muestra la configuración correcta. Copia `.env.example` a `.env` y personaliza los valores:

```bash
# .env file
POSTGRESQL_DB_URL=postgres://postgres:YOUR_PASSWORD@localhost:5432/YOUR_DATABASE
BACKOFFICE_DB_SCHEMA=backoffice
BACKEND_DB_SCHEMA=public
```

> **Nota**: Reemplaza `YOUR_PASSWORD` y `YOUR_DATABASE` con tus credenciales reales de PostgreSQL.

**Tiempo estimado**: 1 minuto.

---

## Paso 4: Aplicar Migraciones de Django

Django gestiona sus tablas en el esquema `backoffice` usando el ModelBasedRouter. Las tablas de negocio en el esquema `public` son legacy y se gestionan externamente (managed=False).

### 4.1 Ejecutar Migraciones

```bash
# Aplicar migraciones de Django al esquema backoffice
uv run python manage.py migrate --database=default
```

**Resultado esperado**: Verás:
```
Operations to perform:
  Apply all migrations: tramites, catalogos, bitacora, costos, core, contenttypes, auth, sessions, admin
Running migrations:
  No migrations to apply.
Your models in app(s):
  * contenttypes
  * auth
  * sessions
  * admin
Running migrations:
  No migrations to apply.
```

> **Nota**: Estas migraciones solo se aplican al esquema `backoffice` (vía la configuración de Django y ModelBasedRouter). No se ejecutan migraciones para la base de datos `backend` ya que las tablas de negocio legacy se gestionan externamente (managed=False) y están bloqueadas con custom managers (ReadOnlyManager, CreateOnlyManager).

### 4.2 Validar el Esquema

Verifica que los modelos Django están correctamente sincronizados con el esquema PostgreSQL:

```bash
# Ejecutar el validador de esquema
uv run python -m core.schema_validator
```

**Resultado esperado**: Verás un reporte indicando que los modelos están sincronizados. Si hay discrepancias, el validador te mostrará qué modelos necesitan ajuste.

> **IMPORTANTE**: El esquema `public` se actualiza por el equipo de base de datos. Cuando hay cambios en el esquema:
1. Obtén la actualización del esquema del repositorio externo
2. Aplica los cambios manualmente al esquema `public`
3. Verifica la sincronización con el validador de esquema

**Tiempo estimado**: 1-2 minutos.

---

## Paso 5: Crear Superusuario

```bash
# Crear superusuario de Django
uv run python manage.py createsuperuser
```

El sistema te pedirá la siguiente información:

1. **Nombre de usuario** (Username)
   - Ingresa tu nombre de usuario
   - Ejemplo: `admin`

2. **Correo electrónico** (Email)
   - Ingresa tu email
   - Ejemplo: `admin@sanfelipe.gob.mx`

3. **Contraseña** (Password)
   - Ingresa una contraseña segura
   - Mínimo 8 caracteres
   - Recomendación: Mezcla de mayúsculas, minúsculas, números y símbolos

4. **Confirmar contraseña**
   - Vuelve a ingresar la contraseña

**Resultado esperado**: Verás `Superuser created successfully.`

> **Nota**: Este usuario tendrá todos los permisos del sistema Django Admin, incluyendo acceso completo a todos los datos.

**Tiempo estimado**: 1 minuto.

---

## Paso 6: Iniciar el Servidor de Desarrollo

```bash
# Iniciar servidor de desarrollo de Django
uv run python manage.py runserver
```

**Resultado esperado**:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

El servidor estará corriendo en `http://127.0.0.1:8000/` (localhost).

**Tiempo estimado**: El servidor continuará corriendo hasta que lo detengas.

---

## Paso 7: Verificar el Funcionamiento

### 7.1 Acceder a Django Admin

1. Abre tu navegador web
2. Navega a: `http://127.0.0.1:8000/admin/`
3. Ingresa el usuario y contraseña creados en el Paso 5
4. Verás el panel de administración de Django

**Resultado esperado**: Verás el panel de Django Admin con todas las aplicaciones disponibles:
- Usuarios y grupos
- Asignación de trámites
- Sitio

### 7.2 Verificar el Health Check

1. Abre otra pestaña o usa curl:
```bash
curl http://127.0.0.1:8000/health/
```

**Resultado esperado**: Deberías ver `"OK"`.

---

## Resumen

En este tutorial has aprendido:

✅ Clonar el repositorio del proyecto
✅ Instalar todas las dependencias con uv
✅ Configurar PostgreSQL con separación de esquemas (backoffice y public)
✅ Crear y configurar los esquemas de PostgreSQL
✅ Aplicar las migraciones de Django al esquema backoffice
✅ Validar la sincronización del esquema
✅ Crear el superusuario de Django
✅ Iniciar el servidor de desarrollo
✅ Acceder al Django Admin
✅ Verificar el health check

---

## ¿Qué sigue?

Ahora que tu entorno de desarrollo está configurado, puedes:

### Para desarrolladores:
- 📖 [Tutorial: Primera llamada a la API](../02-tutorials/developers/first-api-call.md) - Aprender a usar la API REST
- 🧠 [Concepto: Schema Separation](../../04-concepts/schema-separation.md) - Entender la arquitectura de separación de esquemas
- 🧠 [ADR-008: PostgreSQL Schema Separation](../../06-adr/008-postgresql-schema-separation.md) - Decisiones arquitectónicas sobre separación de esquemas
- 🧠 [Concepto: No Migrations](../../04-concepts/no-migrations.md) - Entender por qué no usamos migraciones Django para tablas legacy

### Para todos los roles:
- 🔍 [Búsqueda avanzada de trámites](../../03-guides/operators/search-tramites.md) - Encontrar trámites específicos
- 📋 [Guía: Ejecutar Tests](../../03-guides/developers/run-tests.md) - Cómo probar tu código
- 🔧 [Guía: Troubleshooting](../../03-guides/sysadmins/troubleshoot.md) - Solución de problemas comunes

---

## Problemas Comunes

| Problema | Posible Causa | Solución |
|----------|-----------------|----------|
| `uv: command not found` | uv no está instalado | Instala uv: https://docs.astral.sh/uv/ |
| `git clone: repository not found` | URL del repo incorrecta | Verifica la URL con tu administrador |
| `psql: error: connection refused` | PostgreSQL no está corriendo | Inicia PostgreSQL antes de continuar |
| `psql: error: database "backoffice_tramites" does not exist` | Base de datos no creada | Ejecuta el comando `createdb` antes |
| `Error: schema "backoffice" does not exist` | Esquema no creado | Ejecuta el script de creación de esquemas en el Paso 3 |
| `relation does not exist` | Tabla en esquema incorrecto | Verifica que `BACKEND_DB_URL` usa `currentSchema=public` y `BACKOFFICE_DB_URL` usa `currentSchema=backoffice` |
| `No migrations to apply` | Ya están aplicadas | Es normal, no requiere acción |
| `Permission denied` | Usuario sin permisos en esquema | Ejecuta `GRANT ALL PRIVILEGES` en el Paso 3 |
| `Schema validation failed` | Modelos desincronizados con esquema | Revisa el reporte del validador y ajusta los modelos |

---

## Consejos y Mejores Prácticas

1. **Usa entornos virtuales**: uv maneja esto automáticamente, pero puedes usar venv o pyvenv si prefieres.

2. **Mantén PostgreSQL corriendo**: Durante el desarrollo, es útil tener el servidor de PostgreSQL disponible para las consultas de base de datos.

3. **Usa el validador de esquema regularmente**: Después de cualquier cambio en modelos Django o en el esquema PostgreSQL, ejecuta:
   ```bash
   uv run python -m core.schema_validator
   ```
   Esto asegura que tus modelos están sincronizados con ambos esquemas PostgreSQL.

4. **Asegúrate de usar el decorador @register_model**: Para que el ModelBasedRouter funcione correctamente, todos los modelos que deben ir al esquema `public` deben estar decorados con `@register_model`:
   ```python
   from core.models import register_model

   @register_model
   class Tramite(models.Model):
       # ...
   ```

5. **Verifica las variables de entorno**: Asegúrate de que `BACKEND_DB_URL` y `BACKOFFICE_DB_URL` están correctamente configuradas con el parámetro `currentSchema`.

6. **Mantén el código actualizado**: Haz `git pull` regularmente para mantener tu código sincronizado.

7. **Desactiva el modo DEBUG en producción**: El modo DEBUG no debe usarse en producción por razones de seguridad y rendimiento.

---

## Referencias

- [Documentación de Comandos Django](../../05-reference/commands/index.md) - Guía completa de comandos de gestión de Django
- [Variables de Entorno](../../05-reference/configuration/environment-vars.md) - Referencia completa de configuración
- [Documentación de Schema Validator](../../05-reference/components/schema-validator.md) - Guía del validador de esquema
- [ADR-008: PostgreSQL Schema Separation](../../06-adr/008-postgresql-schema-separation.md) - Decisiones arquitectónicas sobre separación de esquemas
- [ModelBasedRouter](../../05-reference/components/model-based-router.md) - Documentación del enrutador de modelos
- [Guía: Despliegue en Producción](../../03-guides/sysadmins/deploy-production.md) - Guía completa de despliegue

---

**¿Necesitas ayuda?**
- Consulta las [Guías de Desarrolladores](../../03-guides/developers/)
- Revisa el [Glosario de Términos](../01-onboarding/glossary.md) para entender términos
- Contacta a tu equipo de desarrollo

---

*Última actualización: 15 de Abril de 2026*
