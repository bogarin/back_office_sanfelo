# Instalación y Setup de Desarrollo Local

> **Tutorial para desarrolladores**
> Tiempo estimado: 30 minutos
> Última actualización: 26 de Febrero de 2026

---

## Resumen

Esta guía te mostrará cómo configurar un entorno de desarrollo local para el Backoffice de Trámites. Al final, tendrás el proyecto ejecutándose en tu máquina con todas las dependencias instaladas.

## Lo que aprenderás

- Clonar el repositorio del proyecto
- Instalar dependencias con uv
- Configurar las bases de datos (SQLite y PostgreSQL)
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

## Paso 3: Configurar Base de Datos SQLite (Django)

El sistema usa **SQLite** para los datos internos de Django:
- Usuarios del sistema
- Sesiones
- Permisos de Django Admin
- Metadatos de migraciones

Esta base de datos se configura automáticamente al crear el proyecto.

```bash
# Aplicar migraciones de Django a SQLite
uv run python manage.py migrate
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
  * tramites
  * catalogos
  * bitacora
  * costos
  * core
Running migrations:
  No migrations to apply.
```

> **Nota**: Estas migraciones son para la base de datos **SQLite solamente**. La base de datos de negocio (PostgreSQL) tiene su propio esquema gestionado externamente.

**Tiempo estimado**: 30 segundos.

---

## Paso 4: Configurar Base de Datos PostgreSQL (Negocio)

### 4.1 Crear la Base de Datos

```bash
# Crear la base de datos en PostgreSQL
createdb -h localhost -U postgres -d backoffice_tramites
```

**Resultado esperado**: Verás un mensaje `CREATE DATABASE` si se crea exitosamente.

### 4.2 Aplicar el Esquema Inicial

El esquema de PostgreSQL se gestiona externamente. Los scripts SQL están en `sql/migrations/`.

```bash
# Aplicar el esquema inicial
psql -U postgres -d backoffice_tramites -f sql/migrations/001_init_schema.sql
```

**Resultado esperado**: Verás la salida del script SQL con todos los mensajes de creación de tablas.

### 4.3 Cargar Datos Iniciales

```bash
# Cargar datos iniciales (tipos de trámites)
psql -U postgres -d backoffice_tramites -f sql/data/001_tipos_tramites.sql
```

**Resultado esperado**: Verás los registros insertados en la base de datos.

> **IMPORTANTE**: El esquema de PostgreSQL se actualiza por el equipo de base de datos. Cuando hay cambios en el esquema:
1. Obtén los nuevos scripts SQL del repositorio externo
2. Aplicalos manualmente: `psql -U postgres -d backoffice_tramites -f sql/migrations/xxx.sql`
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
- Trámites
- Catálogos
- Costos
- Bitácora
- Usuarios y grupos
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
✅ Configurar la base de datos SQLite (migraciones Django)
✅ Crear la base de datos PostgreSQL (esquema externo)
✅ Aplicar el esquema SQL inicial
✅ Cargar datos iniciales
✅ Crear el superusuario de Django
✅ Iniciar el servidor de desarrollo
✅ Acceder al Django Admin
✅ Verificar el health check

---

## ¿Qué sigue?

Ahora que tu entorno de desarrollo está configurado, puedes:

### Para desarrolladores:
- 📖 [Tutorial: Primera llamada a la API](../02-tutorials/developers/first-api-call.md) - Aprender a usar la API REST
- 🧠 [Concepto: Dual Database](../../04-concepts/dual-database.md) - Entender la arquitectura de dos bases de datos
- 🧠 [Concepto: No Migrations](../../04-concepts/no-migrations.md) - Entender por qué no usamos migraciones Django

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
| `Error: Table 'tramites' does not exist` | Esquema SQL no aplicado | Ejecuta los scripts SQL en `sql/migrations/` |
| `No migrations to apply` | Ya están aplicadas | Es normal, no requiere acción |
| `Permission denied` | Usuario sin permisos | Verifica con tu administrador |

---

## Consejos y Mejores Prácticas

1. **Usa entornos virtuales**: uv maneja esto automáticamente, pero puedes usar venv o pyvenv si prefieres.

2. **Mantén PostgreSQL corriendo**: Durante el desarrollo, es útil tener el servidor de PostgreSQL disponible para las consultas de base de datos.

3. **Usa el validador de esquema**: Después de cualquier cambio en modelos Django o scripts SQL, ejecuta:
   ```bash
   uv run python -m core.schema_validator
   ```
   Esto asegura que tus modelos están sincronizados con el esquema PostgreSQL.

4. **Mantén el código actualizado**: Haz `git pull` regularmente para mantener tu código sincronizado.

5. **Desactiva el modo DEBUG en producción**: El modo DEBUG no debe usarse en producción por razones de seguridad y rendimiento.

---

## Referencias

- [Documentación de Comandos Django](../../05-reference/commands/index.md) - Guía completa de comandos de gestión de Django
- [Variables de Entorno](../../05-reference/configuration/environment-vars.md) - Referencia completa de configuración
- [Documentación de Schema Validator](../../05-reference/components/schema-validator.md) - Guía del validador de esquema
- [Guía: Despliegue en Producción](../../03-guides/sysadmins/deploy-production.md) - Guía completa de despliegue

---

**¿Necesitas ayuda?**
- Consulta las [Guías de Desarrolladores](../../03-guides/developers/)
- Revisa el [Glosario de Términos](../01-onboarding/glossary.md) para entender términos
- Contacta a tu equipo de desarrollo

---

*Última actualización: 26 de Febrero de 2026*
