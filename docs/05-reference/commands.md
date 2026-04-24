# Referencia: Comandos

> **Comandos de desarrollo y administración del proyecto**
> Última actualización: 23 de abril de 2026

---

## Resumen

Todos los comandos de desarrollo se ejecutan con `just` (task runner). Los comandos de Django se ejecutan con `uv run manage.py`.

---

## Comandos Justfile

### Setup y Desarrollo

| Comando | Descripción |
|---------|-------------|
| `just install` | Instalar dependencias (`uv sync`) |
| `just run` | Servidor de desarrollo (`runserver` en puerto 8000) |
| `just shell` | Django shell interactivo |

### Base de Datos

| Comando | Descripción |
|---------|-------------|
| `just migrate` | Aplicar migraciones pendientes |
| `just migrate-status` | Ver estado de migraciones |
| `just makemigrations APP` | Crear migración para una app (solo schema backoffice) |
| `just validate-schema` | Validar sync entre modelos Django y PostgreSQL |

### Usuarios y Roles

| Comando | Descripción |
|---------|-------------|
| `just createsuperuser` | Crear usuario administrador |
| `just setup_roles` | Crear grupos RBAC (Administrador, Coordinador, Analista) |

### Calidad de Código

| Comando | Descripción |
|---------|-------------|
| `just lint` | Linting con ruff |
| `just lint-fix` | Corregir problemas de linting automáticamente |
| `just format` | Formatear código con ruff |
| `just typecheck` | Type checking con pyright |
| `just check` | Ejecutar lint + typecheck |

### Testing

| Comando | Descripción |
|---------|-------------|
| `just test` | Ejecutar todos los tests |
| `just test APP` | Ejecutar tests pasando args a pytest |
| `just test-app APP` | Tests de una app específica |
| `just test-cov` | Tests con cobertura HTML + terminal |
| `just test-fast` | Tests saltando los marcados como `slow` |
| `just test-create-db` | Tests recreando la base de datos |

### Docker

| Comando | Descripción |
|---------|-------------|
| `just container-build` | Construir imagen Docker/Podman |
| `just check-system` | Verificar estado del sistema Django |

---

## Comandos Django (Management Commands)

### Comandos nativos útiles

```bash
# Verificar configuración
uv run manage.py check

# Ver todas las configuraciones
uv run manage.py diffsettings

# Ver migraciones aplicadas
uv run manage.py showmigrations

# Archivos estáticos
uv run manage.py collectstatic --no-input

# Cambiar contraseña de usuario
uv run manage.py changepassword USERNAME
```

### Comandos personalizados

#### `setup_roles`

Crea los 3 grupos RBAC y asigna permisos.

```bash
uv run manage.py setup_roles
```

Ver: [Referencia RBAC](rbac.md)

#### `validate_schema`

Verifica que los modelos Django estén sincronizados con las tablas PostgreSQL en el schema `public`.

```bash
uv run manage.py validate_schema
```

> **Nota:** Solo valida el schema `public` (datos de negocio). El schema `backoffice` usa Django migrations.

#### `sftp`

Gestión de archivos en servidor SFTP remoto.

```bash
# Verificar conectividad
uv run manage.py sftp ping

# Listar archivos de un trámite
uv run manage.py sftp list FOLIO-123456

# Descargar archivo específico
uv run manage.py sftp download FOLIO-123456 --output /tmp/

# Limpiar cache local de PDFs
uv run manage.py sftp cleanup_cache
```

Ver: [Referencia SFTP](sftp.md)

#### `simular_pago`

Simula un pago para crear trámites de prueba con estatus "Presentado" (201).

```bash
uv run manage.py simular_pago
```

Útil para desarrollo local con datos de prueba.

#### `makemigrations` (custom guard)

El comando nativo `makemigrations` está sobrecargado con un guard que:

1. Solo permite crear migraciones para apps del schema `backoffice` (`core`, `auth`, etc.)
2. Bloquea intentos de crear migraciones para apps del schema `public` (gestionado externamente)

```bash
# Correcto: crear migración para app del schema backoffice
uv run manage.py makemigrations core

# Bloqueado: las apps de negocio NO usan Django migrations
uv run manage.py makemigrations tramites  # → Error
```

---

## Docker Compose

```bash
# Iniciar todos los servicios (PostgreSQL + app)
docker compose up -d

# Ver logs
docker compose logs -f

# Reiniciar aplicación
docker compose restart backoffice

# Ejecutar comando dentro del contenedor
docker compose exec backoffice python manage.py setup_roles

# Detener todo
docker compose down
```

---

## Notas importantes

### Migraciones

- **Schema `backoffice`:** Se gestiona con Django migrations (`just migrate`)
- **Schema `public`:** Se gestiona externamente — **NO usar Django migrations**. Usar fixtures (`loaddata`) o SQL directo

### Base de datos

El proyecto usa un solo PostgreSQL con routing automático por schema:

- Modelos `@register_model(access=FULL_ACCESS)` → schema `backoffice` (Django managea)
- Modelos `@register_model(access=READ_ONLY)` → schema `public` (externo)
- Modelos `@register_model(access=APPEND_ONLY)` → schema `public` (solo INSERT)

No hay flag `--database` — el router determina automáticamente la conexión.

---

## Ver también

- [Variables de Entorno](environment-vars.md)
- [Referencia RBAC](rbac.md)
- [Referencia SFTP](sftp.md)
- [Tutorial: Setup de desarrollo](../02-tutorials/developers/local-dev-setup.md)
- [ADR-008: Schema Separation](../06-decisions/008-postgresql-schema-separation.md)
