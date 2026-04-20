# Comandos de Gestión de Django (Django Management Commands)

> "Estos son los comandos integrados de Django para gestionar la aplicación. No necesitas scripts personalizados - Django ya lo incluye todo."

## Índice

1. [Operaciones de Base de Datos](#operaciones-de-base-de-datos)
2. [Servidor de Desarrollo](#servidor-de-desarrollo)
3. [Archivos Estáticos](#archivos-estáticos)
4. [Pruebas](#pruebas)
5. [Shell Interactivo](#shell-interactivo)
6. [Caché](#caché)
7. [Comandos Personalizados](#comandos-personalizados)
8. [Usuarios y Permisos](#usuarios-y-permisos)
9. [Comandos de Utilidad](#comandos-de-utilidad)

---

## Operaciones de Base de Datos

### makemigrations
Crea nuevos archivos de migración basados en cambios en los modelos.

**Uso:**
```bash
# Crear migraciones para todas las apps
uv run python manage.py makemigrations

# Crear migraciones para una app específica
uv run python manage.py makemigrations tramites

# Crear migraciones con nombre personalizado
uv run python manage.py makemigrations --name cambiar_nombre_campo
```

**Nota:** Solo usa esto para la base de datos **SQLite** (Django auth, admin, sessions). La base de datos **PostgreSQL** (business data) NO usa migraciones.

### migrate
Aplica las migraciones pendientes a la base de datos.

**Uso:**
```bash
# Aplicar todas las migraciones
uv run python manage.py migrate

# Aplicar migraciones de una app específica
uv run python manage.py migrate tramites

# Falso primer (ver SQL, no ejecutar)
uv run python manage.py migrate --plan

# Ver estado de migraciones
uv run python manage.py showmigrations
```

**Nota:** Solo usa esto para la base de datos **SQLite**. Para PostgreSQL (business DB), aplica scripts SQL manualmente.

### createsuperuser
Crea un superusuario para acceder al admin de Django.

**Uso:**
```bash
# Interactivo (te pedirá username/email/password)
uv run python manage.py createsuperuser

# No interactivo (pasa datos como argumentos)
uv run python manage.py createsuperuser \
  --username admin \
  --email admin@sanfelipe.gob.ar \
  --noinput
```

### dbshell
Abre una shell de base de datos interactiva.

**Uso:**
```bash
# SQLite (default DB)
uv run python manage.py dbshell

# PostgreSQL (business DB)
uv run python manage.py dbshell --database=business
```

**Nota:** En PostgreSQL, esto abre `psql` conectado a la base de datos de negocio.

---

## Servidor de Desarrollo

### runserver
Inicia el servidor de desarrollo Django.

**Uso:**
```bash
# Puerto por defecto (8000)
uv run python manage.py runserver

# Puerto personalizado
uv run python manage.py runserver 8090

# IP específica
uv run python manage.py runserver 0.0.0.0:8090

# Recargar automáticamente en cambios de archivos Python
uv run python manage.py runserver --reload

# Verbose para debugging
uv run python manage.py runserver --verbosity 3
```

**Justfile:**
```makefile
run:
    uv run python manage.py runserver
```

---

## Archivos Estáticos

### collectstatic
Recolecta todos los archivos estáticos en `STATIC_ROOT`.

**Uso:**
```bash
# Recolección estándar
uv run python manage.py collectstatic

# Recolección sin confirmación interactiva
uv run python manage.py collectstatic --noinput

# Recolección limpiando archivos anteriores
uv run python manage.py collectstatic --clear --noinput

# Recolección con verbosity
uv run python manage.py collectstatic --verbosity 2
```

**En Docker:** Esto se ejecuta automáticamente en el Dockerfile (línea 53).

### findstatic
Encuentra archivos estáticos sin referencias (archivos huérfanos).

**Uso:**
```bash
# Buscar archivos no referenciados
uv run python manage.py findstatic

# Buscar con verbosidad
uv run python manage.py findstatic --verbosity 2
```

---

## Pruebas

### test
Ejecuta las pruebas de la aplicación.

**Uso:**
```bash
# Ejecutar todas las pruebas
uv run python manage.py test

# Ejecutar pruebas de una app específica
uv run python manage.py test tramites

# Ejecutar una prueba específica
uv run python manage.py test tramites.tests.TestTramiteModel

# Con verbose output
uv run python manage.py test --verbosity 2

# Paralelizar pruebas
uv run python manage.py test --parallel
```

**Requerimiento previo:**
```bash
# Instalar pytest si no está instalado
uv pip install pytest pytest-django
```

### test --settings
Ejecuta pruebas con configuración de settings diferente.

**Uso:**
```bash
# Usar settings de prueba
uv run python manage.py test --settings=sanfelipe.settings.test

# Deshabilitar migraciones en pruebas
TESTING=True uv run python manage.py test
```

---

## Shell Interactivo

### shell
Abre una shell de Python interactiva con el entorno Django configurado.

**Uso:**
```bash
# Shell estándar
uv run python manage.py shell

# Shell con IPython (si está instalado)
uv run python manage.py shell --interface ipython

# Shell con bpython (si está instalado)
uv run python manage.py shell --interface bpython
```

**Ejemplo de uso:**
```python
# Dentro de la shell Django
>>> from tramites.models import Tramite, TramiteLegacy
>>> Tramite.objects.count()
42

>>> TramiteLegacy.objects.count()
42

>>> from catalogos.models import CatTramite
>>> for cat in CatTramite.objects.all():
...     print(cat.nombre)
```

### shell_plus
Shell mejorada con django-extensions (si está instalado).

**Instalación:**
```bash
uv pip install django-extensions
```

**Características adicionales:**
- Autocompletado mejorado
- Comandos SQL directos `sql models` para ejecutar queries
- Comando `show_urls` para ver URLs registradas
- Comando `show_template_context` para ver contexto de templates

---

## Caché

### createcachetable
Crea las tablas de caché en la base de datos.

**Uso:**
```bash
# Crear tablas de caché
uv run python manage.py createcachetable
```

### clearcache
Limpia todo el caché.

**Uso:**
```bash
# Limpiar caché completo
uv run python manage.py clearcache

# Limpiar caché específico
uv run python manage.py clearcache default

# Limpiar múltiples cachés
uv run python manage.py clearcache default sessions
```

---

## Usuarios y Permisos

### changepassword
Cambia la contraseña de un usuario.

**Uso:**
```bash
# Interactivo (pedirá nueva contraseña)
uv run python manage.py changepassword

# No interactivo
uv run python manage.py changepassword --noinput username admin
```

---

## Comandos Personalizados

### Crear Comandos de Gestión Personalizados

Django permite crear comandos de gestión personalizados. Se almacenan en `management/commands/` de cada app.

**Estructura:**
```
tramites/
├── management/
│   └── commands/
│       ├── __init__.py
│       ├── cleanup_old_tramites.py
│       └── export_tramites_csv.py
catalogos/
├── management/
│   └── commands/
│       ├── __init__.py
│       └── import_data.py
```

**Ejemplo: Comando para limpiar trámites antiguos**

```python
# tramites/management/commands/cleanup_old_tramites.py

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from tramites.models import TramiteLegacy


class Command(BaseCommand):
    """Limpia trámites antiguos (más de 1 año)."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se eliminaría sin ejecutar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=365)

        queryset = TramiteLegacy.objects.filter(creado__lt=cutoff_date)
        count = queryset.count()

        self.stdout.write(f"Trámites a eliminar: {count}")

        if not dry_run:
            deleted_count, _ = queryset.delete()
            self.stdout.write(f"Eliminados: {deleted_count}")
```

**Uso:**
```bash
# Ver qué se eliminaría
uv run python manage.py cleanup_old_tramites --dry-run

# Ejutar limpieza
uv run python manage.py cleanup_old_tramites
```

**Ejemplo: Comando para exportar a CSV**

```python
# tramites/management/commands/export_tramites_csv.py

from django.core.management.base import BaseCommand
from tramites.models import Tramite
import csv


class Command(BaseCommand):
    """Exporta trámites a archivo CSV usando la vista unificada."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='tramites_export.csv',
            help='Archivo de salida',
        )

    def handle(self, *args, **options):
        output_file = options['output']

        # Usar Tramite (vista unificada) para export con campos denormalizados
        queryset = Tramite.objects.all()

        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Escribir cabeceras
            writer.writerow(['folio', 'estado', 'creado', 'modificado'])
            
            # Escribir datos
            for tramite in queryset:
                writer.writerow([
                    tramite.folio,
                    tramite.get_estado_display(),
                    tramite.creado,
                    tramite.modificado,
                ])
        
        self.stdout.write(f"Exportados {queryset.count()} trámites a {output_file}")
```

**Uso:**
```bash
# Exportar a archivo CSV
uv run python manage.py export_tramites_csv

# Exportar a archivo personalizado
uv run python manage.py export_tramites_csv --output=mi_exporte.csv
```

---

## Comandos de Utilidad

### check
Verifica el proyecto por problemas comunes.

**Uso:**
```bash
# Verificar configuración
uv run python manage.py check

# Desplegar proyecto sin migraciones
uv run python manage.py check --deploy

# Verificar tags de plantilla
uv run python manage.py check --tag settings
```

### diffsettings
Muestra diferencias entre los settings actuales y los defaults de Django.

**Uso:**
```bash
# Mostrar diferencias
uv run python manage.py diffsettings
```

### inspectdb
Inspecciona la base de datos y muestra su estructura.

**Uso:**
```bash
# Inspeccionar base de datos default (SQLite)
uv run python manage.py inspectdb

# Inspeccionar base de datos de negocio (PostgreSQL)
uv run python manage.py inspectdb --database=business
```

### showmigrations
Muestra todas las migraciones y su estado.

**Uso:**
```bash
# Mostrar todas las migraciones
uv run python manage.py showmigrations

# Mostrar con formato de tabla
uv run python manage.py showmigrations --plan

# Mostrar migraciones de una app
uv run python manage.py showmigrations tramites
```

### sqlmigrate
Muestra las sentencias SQL que se ejecutarían con una migración (sin ejecutarla).

**Uso:**
```bash
# Ver SQL de migración pendiente
uv run python manage.py sqlmigrate tramites 0002

# Ver SQL hacia adelante (rollback)
uv run python manage.py sqlmigrate tramites 0002 --backwards
```

### sqlflush
Muestra las sentencias SQL para limpiar la base de datos.

**Uso:**
```bash
# Ver SQL para vaciar tablas
uv run python manage.py sqlflush

# Confirmar acción
uv run python manage.py flush
```

---

## Validador de Esquema

### Ejecutar Validador de Esquema

El proyecto incluye un validador personalizado para verificar que los modelos Django estén sincronizados con el esquema PostgreSQL externo.

**Uso:**
```bash
# Ejecutar validador
uv run python -m core.schema_validator

# O usando just (si agregas al justfile)
just validate-schema
```

**Salida esperada:**
```
============================================================
SCHEMA VALIDATION REPORT
============================================================

Validating: Tramite → v_tramites_unificado
Validating: TramiteLegacy → tramite
Validating: CatTramite → cat_tramite
Validating: Bitacora → bitacora

============================================================
SUMMARY
============================================================

⚠️  Warnings (2):
  - Nullable mismatch for Tramite.descripcion: Django=NOT NULL, SQL=nullable
  - Max length mismatch for CatTramite.nombre: Django=255, SQL=100

❌ Errors (0):
✅ All models are synchronized with database schema!
```

**Documentación completa:** Ver [docs/SCHEMA_VALIDATOR.md](SCHEMA_VALIDATOR.md) para guía detallada.

---

## Comandos con `just`

Si tienes un `justfile`, puedes usar comandos más cortos:

```makefile
# Justfile
default:
    @just --list

# Base de datos
migrate:
    uv run python manage.py migrate

makemigrations APP:
    uv run python manage.py makemigrations {{ APP }}

dbshell:
    uv run python manage.py dbshell

# Desarrollo
run:
    uv run python manage.py runserver

shell:
    uv run python manage.py shell

# Pruebas
test:
    uv run python manage.py test

# Estáticos
collectstatic:
    uv run python manage.py collectstatic --noinput --clear

# Caché
clearcache:
    uv run python manage.py clearcache

# Validación de esquema
validate-schema:
    uv run python -m core.schema_validator

# Validación de configuración
check:
    uv run python manage.py check
```

---

## Troubleshooting

### Error: "You have unapplied migrations"

**Causa:** Hay migraciones creadas pero no aplicadas.

**Solución:**
```bash
# Ver estado de migraciones
uv run python manage.py showmigrations

# Aplicar migraciones
uv run python manage.py migrate
```

### Error: "No module named 'psycopg2'"

**Causa:** No está instalado el driver de PostgreSQL.

**Solución:**
```bash
# Instalar psycopg2
uv pip install psycopg2-binary

# O agregar a pyproject.toml
# [project]
# dependencies = [
#     "psycopg2-binary>=2.9.11",
# ]
```

### Error: "django.db.sqlite3" doesn't exist

**Causa:** Base de datos SQLite no creada.

**Solución:**
```bash
# Crear base de datos y aplicar migraciones
uv run python manage.py migrate

# O solo crear tablas de migraciones (sin datos)
uv run python manage.py migrate --run-syncdb
```

### Error: "relation 'xxx' does not exist" (PostgreSQL)

**Causa:** Tabla no existe en la base de datos PostgreSQL.

**Solución:**
```bash
# Aplicar scripts SQL del esquema inicial
psql -h postgres-host -U postgres -d business_db -f sql/migrations/001_init_schema.sql

# Verificar que tabla existe
psql -h postgres-host -U postgres -d business_db -c "\d nombre_tabla"
```

---

## Referencias

- [Django Management Commands](https://docs.djangoproject.com/en/stable/ref/cli/)
- [Django Admin Commands](https://docs.djangoproject.com/en/stable/ref/django-admin/)
- [Custom Management Commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)
- [Schema Validator Guide](SCHEMA_VALIDATOR.md)
- [Environment Variables Reference](ENVIRONMENT_VARIABLES.md)
- [ADR-002: Dual Database Setup](decisiones/002-configuracion-multiples-bases-de-datos.md)

---

## Best Practices

1. **Siempre usa `uv run`** para ejecutar comandos de gestión
2. **Especifica la app** cuando ejecutes `makemigrations` o `migrate` para evitar confusiones
3. **Usa `--dry-run`** para comandos destructivos antes de ejecutarlos realmente
4. **Valida cambios** ejecutando `check` después de modificar settings o models
5. **Usa schema validator** después de cambios en el esquema SQL externo
6. **En Docker**, los comandos de gestión se ejecutan dentro del contenedor
7. **Para comandos complejos**, crea comandos personalizados de gestión en lugar de scripts bash
