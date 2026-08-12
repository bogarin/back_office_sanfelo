# Referencia: Comandos

> **Comandos de desarrollo y administración del proyecto**
> Última actualización: 23 de abril de 2026

______________________________________________________________________

## Resumen

Todos los comandos de desarrollo se ejecutan con `just` (task runner). Los comandos de Django se ejecutan con `uv run manage.py`.

______________________________________________________________________

## Comandos Justfile

### Setup y Desarrollo

| Comando | Descripción |
|---------|-------------|
| `just setup` | Instalar dependencias y configurar hooks (`uv sync` + pre-commit) |
| `just run` | Servidor de desarrollo (`runserver` en puerto 8000) |

### Base de Datos

| Comando | Descripción |
|---------|-------------|
| `just migrate` | Aplicar migraciones pendientes |
| `just setup_roles` | Crear grupos RBAC (Administrador, Coordinador, Analista) |

### Calidad de Código

| Comando | Descripción |
|---------|-------------|
| `just pre-commit` | Ejecutar todos los hooks de pre-commit |
| `just lint *ARGS` | Linting con ruff (solo lectura) |
| `just format *ARGS` | Corregir problemas de linting automáticamente y formatear código |
| `just typecheck *ARGS` | Type checking con pyright |
| `just djlint *ARGS` | Formatear templates de Django |
| `just lint && just typecheck` | Ejecutar lint + typecheck |
| `just audit-tests` | Auditoría AST de suite de tests |

### Testing

| Comando | Descripción |
|---------|-------------|
| `just test` | Ejecutar todos los tests |
| `just test <args>` | Ejecutar tests pasando args a pytest |

### Docker

| Comando | Descripción |
|---------|-------------|
| `just container-build` | Construir imagen Docker/Podman |
| `just container-push` | Push imagen Docker a staging |
| `just container-run` | Ejecutar contenedor localmente |
| `just deploy` | Desplegar (build + push) |
| `just check-nginx` | Verificar configuración de nginx |

______________________________________________________________________

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
1. Bloquea intentos de crear migraciones para apps del schema `public` (gestionado externamente)

```bash
# Correcto: crear migración para app del schema backoffice
uv run manage.py makemigrations core

# Bloqueado: las apps de negocio NO usan Django migrations
uv run manage.py makemigrations tramites  # → Error
```

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## Ver también

- [Variables de Entorno](environment-vars.md)
- [Referencia RBAC](rbac.md)
- [Referencia SFTP](sftp.md)
- [Tutorial: Setup de desarrollo](./local-dev-setup.md)
- [ADR-008: Schema Separation](../02-DECISIONES/008-postgresql-schema-separation.md)
