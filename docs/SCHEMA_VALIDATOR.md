# Validador de Esquema (Schema Validator)

## Visión General

El `schema_validator.py` es una herramienta esencial que valida que los modelos Django estén sincronizados con el esquema externo de PostgreSQL.

## Por Qué Es Necesario

En nuestro proyecto de base de datos dual:

| Base de Datos | Uso | Migraciones Django |
|--------------|------|-------------------|
| **SQLite** (default) | Django auth, admin, sessions | ✅ Activas |
| **PostgreSQL** (business) | tramites, catalogos, costos, bitacora | ❌ Desactivadas (`managed=False`) |

**Problema:** Cuando el esquema PostgreSQL cambia (gestionado externamente), los modelos Django pueden quedar desincronizados, causando:
- ❌ Errores en producción
- ❌ Campos perdidos o incorrectos
- ❌ Incompatibilidades de tipos de datos

**Solución:** El `schema_validator.py` detecta estas discrepancias antes de que causen problemas en producción.

## Cómo Funciona

### 1. Comparación de Modelos ↔ Esquema SQL

El validador compara:

**Django Models →**  
```python
class Tramite(models.Model):
    folio = models.CharField(max_length=50, unique=True)
    estado = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
```

**↑ Compara con ↑**

**PostgreSQL Schema →**  
```sql
CREATE TABLE tramite (
    folio VARCHAR(50) UNIQUE,
    estado VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Detección de Diferencias

El validador reporta:

| Tipo | Descripción | Ejemplo |
|------|-------------|----------|
| ❌ **Error** | Campo en Django no en SQL (o viceversa) | `Field 'new_field' exists in Tramite but not in table 'tramite'` |
| ⚠️ **Warning** | Tipo de dato incompatible | `Type mismatch for Tramite.estado: Django=CharField, SQL=INTEGER` |
| ⚠️ **Warning** | `max_length` diferente | `Max length mismatch for Tramite.folio: Django=50, SQL=100` |
| ⚠️ **Warning** | `nullable` diferente | `Nullable mismatch for Tramite.descripcion: Django=NOT NULL, SQL=nullable` |

### 3. Validación Solo de BD de Negocio

El validador **no** verifica SQLite (usa migraciones Django normales).

Solo valida la base de datos `business` (PostgreSQL):

```python
# En schema_validator.py
def main():
    # Check if business database is PostgreSQL
    if not settings.DATABASES.get('business', {}).get('ENGINE', '').startswith('postgresql'):
        print('❌ Schema validation only works with PostgreSQL business database')
        sys.exit(1)
```

## Uso

### Ejecutar el Validador

```bash
# Desde la raíz del proyecto
uv run python -m core.schema_validator

# O usando just
just validate-schema  # Si agregas este comando al justfile
```

### Salida de Ejemplo

```
============================================================
SCHEMA VALIDATION REPORT
============================================================

Validating: CatTramite → cat_tramite
Validating: Tramite → tramite
Validating: Bitacora → bitacora

============================================================
SUMMARY
============================================================

⚠️  Warnings (2):
  - Nullable mismatch for Tramite.descripcion: Django=NOT NULL, SQL=nullable
  - Max length mismatch for CatTramite.nombre: Django=255, SQL=100

❌ Errors (1):
  - Field 'new_column' exists in Tramite but not in table 'tramite'

✅ All models are synchronized with database schema!
```

### Códigos de Salida

- **Exit 0**: Validación exitosa (sin errores)
- **Exit 1**: Errores encontrados o configuración inválida

## Mapeo de Tipos

El validador conoce estos mapeos Django ↔ PostgreSQL:

| Django Field Type | PostgreSQL Type |
|------------------|-----------------|
| AutoField | integer |
| BigIntegerField | bigint |
| CharField | character varying |
| BooleanField | boolean |
| DateField | date |
| DateTimeField | timestamp without time zone |
| DecimalField | numeric |
| FloatField | double precision |
| IntegerField | integer |
| TextField | text |
| UUIDField | uuid |
| ForeignKey | integer |
| OneToOneField | integer |
| ManyToManyField | integer (junction table) |

## Integración con CI/CD

### Pipeline de GitLab

```yaml
# .gitlab-ci.yml
stages:
  - test

validate-schema:
  stage: test
  script:
    - uv sync
    - uv run python -m core.schema_validator
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### Pipeline de GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  validate-schema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - name: Install dependencies
        run: pip install uv && uv sync
      - name: Validate schema
        run: uv run python -m core.schema_validator
```

## Flujo de Trabajo Recomendado

### Cuando el Esquema SQL Cambia

1. **Equipo externo entrega nuevo script SQL**
   ```bash
   # Ejemplo: sql/migrations/002_add_new_field.sql
   ALTER TABLE tramite ADD COLUMN new_field VARCHAR(100);
   ```

2. **Aplicar script a base de datos**
   ```bash
   psql -h postgres-host -U postgres -d business_db -f sql/migrations/002_add_new_field.sql
   ```

3. **Actualizar modelo Django correspondiente**
   ```python
   class Tramite(models.Model):
       # ... campos existentes
       new_field = models.CharField(max_length=100)  # Agregar campo
   ```

4. **Ejecutar validador de esquema**
   ```bash
   uv run python -m core.schema_validator
   ```

5. **Si pasa → Commit**
   - Si muestra `✅ All models are synchronized`, hacer commit

6. **Si falla → Corregir**
   - Revisar tipos, longitudes, nombres de campos
   - Corregir modelo Django
   - Volver a paso 4

## Troubleshooting

### Error: "Table 'xxx' not found in database"

**Causa:** La tabla no existe en PostgreSQL o nombre está mal.

**Solución:**
```bash
# Verificar tabla existe
psql -h postgres-host -U postgres -d business_db -c "\dt"

# Verificar nombre exacto
psql -h postgres-host -U postgres -d business_db -c "\d nombre_tabla"

# Si no existe, aplicar scripts SQL
psql -h postgres-host -U postgres -d business_db -f sql/migrations/001_init_schema.sql
```

### Error: "Schema validation only works with PostgreSQL"

**Causa:** Configuración de BD incorrecta en `settings.py`.

**Solución:**
```python
# Verificar DATABASES en settings.py
DATABASES = {
    "default": {  # SQLite - ignorado por validador
        "ENGINE": "django.db.backends.sqlite3",
        # ...
    },
    "business": {  # PostgreSQL - DEBE existir
        "ENGINE": "django.db.backends.postgresql",
        # ...
    }
}
```

### Warning: "Nullable mismatch: Django=NOT NULL, SQL=nullable"

**Causa:** El modelo Django requiere campo obligatorio, pero SQL permite nulos.

**Solución:**
```python
# Opción 1: Hacer campo opcional en Django
campo = models.CharField(max_length=100, blank=True, null=True)

# Opción 2: Agregar NOT NULL en SQL
ALTER TABLE nombre_tabla ALTER COLUMN campo SET NOT NULL;
```

### Warning: "Max length mismatch"

**Causa:** `max_length` diferente entre Django y SQL.

**Solución:**
```python
# Ajustar max_length en Django para coincidir con SQL
campo = models.CharField(max_length=100)  # Cambiar a valor correcto
```

## Mejoras Futuras Posibles

- [ ] Soporte para detectar índices faltantes/excedentes
- [ ] Validación de constraints (UNIQUE, CHECK, FOREIGN KEY)
- [ ] Soporte para múltiples esquemas PostgreSQL
- [ ] Exportar reporte en formato JSON para integración CI/CD
- [ ] Sugerir SQL para corregir discrepancias encontradas

## Relación con ADRs

Este validador está directamente relacionado con:

- **[ADR-002](decisiones/002-configuracion-multiples-bases-de-datos.md)**: Configuración de múltiples bases de datos - Documenta la arquitectura de doble BD que hace necesario este validador
- **[ADR-003](decisiones/003-estrategia-caching-rendimiento.md)**: Estrategia de caching y rendimiento

## Referencias

- [Django Models](https://docs.djangoproject.com/en/stable/topics/db/models/)
- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
