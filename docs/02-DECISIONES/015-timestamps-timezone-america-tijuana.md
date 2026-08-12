# 015: Estrategia Unificada de Timestamps y Zona Horaria (America/Tijuana)

**Date:** 2026-04-30
**Status:** Accepted
**Related:** 008-postgresql-schema-separation.md

## Contexto y Planteamiento del Problema

El sistema Backoffice Trámites es un microservicio Django que comparte la base de datos PostgreSQL (schema `public`) con aplicaciones Java legacy. Las tablas del backend (`actividades`, `tramite`, etc.) usan columnas `timestamp` **sin timezone** (`timestamp` en PostgreSQL, no `timestamptz`).

Se detectó que Django insertaba timestamps en UTC (ej: `07:47`) mientras que las aplicaciones Java insertaban en hora local de Tijuana (ej: `00:47`). Esto causaba:

- **Datos inconsistentes**: la misma columna contenía timestamps con 7 horas de diferencia según el origen
- **Ordenamiento roto**: `ORDER BY timestamp` mezclaba horas UTC y locales
- **Display incorrecto**: el admin mostraba UTC crudo; los templates convertían incorrectamente

## Opciones Consideradas

- **Opción A**: Dejar que PostgreSQL maneje los timestamps vía `DEFAULT CURRENT_TIMESTAMP`, configurando la sesión con `timezone=America/Tijuana`. Django no enviaría el campo timestamp en el INSERT.
- **Opción B**: Usar `default=timezone.localtime` en Django para enviar hora local explícitamente en cada INSERT.
- **Opción C**: Migrar las columnas PostgreSQL a `timestamptz` (con timezone).
- **Opción D**: Usar `db_default=Now()` (Django 5.1+) para que el ORM omita el campo del INSERT y PostgreSQL use su `DEFAULT CURRENT_TIMESTAMP`.

## Resultado de la Decisión

Opción elegida: **"D — `db_default=Now()` con sesión PostgreSQL en America/Tijuana"**.

### Por qué se descartaron las otras opciones

- **Opción A** (sin default, sin auto_now_add): Django ORM envía `NULL` explícitamente → error `violates not-null constraint`.
- **Opción B** (`default=timezone.localtime`): Con `USE_TZ=True`, Django convierte datetimes aware a UTC antes del INSERT. Se intentó strippear tzinfo (`_local_now()` naive), pero es un workaround feo.
- **Opción C** (migrar a `timestamptz`): Requiere migraciones SQL en tablas compartidas con Java, riesgo alto.

### Por qué `db_default` es la solución elegante

`db_default` (disponible desde Django 5.1, proyecto usa 6.0.4) es un parámetro de campo que delega el valor default a la **base de datos**. El ORM de Django:

1. Detecta que el campo tiene `db_default`
1. Marca el valor como `DatabaseDefault` (sentinel)
1. **Omite el campo del INSERT** (ver `SQLInsertCompiler`, líneas 137-149)
1. PostgreSQL ejecuta `DEFAULT CURRENT_TIMESTAMP` → hora local America/Tijuana

Resultado: mismo comportamiento que Java, sin workarounds, sin funciones auxiliares.

### Causa raíz: psycopg2 vs psycopg3

El proyecto originalmente usaba **psycopg2** como driver de PostgreSQL. En psycopg2, Django configuraba el timezone de la sesión mediante las OPTIONS de conexión (`-c timezone=`). Sin embargo, este mecanismo es inconsistente y la sesión podía quedar en UTC a pesar de la configuración.

Se migró a **psycopg3** (`psycopg[binary]>=3.3.3` en `pyproject.toml`), donde Django maneja el timezone de forma diferente y más robusta:

1. **psycopg2**: El timezone se configuraba via `-c timezone=America/Tijuana` en las OPTIONS, pero Django sobrescribía el valor después de conectar, resultando en UTC.
1. **psycopg3**: Django usa la clave `TIME_ZONE` directamente en la configuración de cada base de datos, ejecutando `SET timezone` como una consulta SQL separada al abrir la conexión. Esto **sí** se respeta correctamente.

**Lección aprendida**: Con psycopg3, usar siempre `'TIME_ZONE': tz` en la configuración de DATABASES. No confiar en las OPTIONS para configurar el timezone.

### Configuración del timezone de la sesión PostgreSQL

Para que `CURRENT_TIMESTAMP` devuelva hora local, la sesión PostgreSQL debe tener el timezone configurado. La forma correcta es usar la clave `TIME_ZONE` en la configuración de cada base de datos:

```python
DATABASES = {
    'default': {
        **db,
        'TIME_ZONE': tz,  # Django ejecuta SET timezone='America/Tijuana'
    },
    'backend': {
        **db,
        'TIME_ZONE': tz,
    },
}
```

**Nota importante**: No usar `-c timezone=` en las OPTIONS. Django sobrescribe el timezone después de conectar. La clave `TIME_ZONE` es el mecanismo oficial de Django para configurar el timezone de la conexión PostgreSQL.

### Configuración implementada

| Componente | Configuración | Propósito |
|---|---|---|
| Dockerfile (`TZ`) | `America/Tijuana` | Zona horaria del contenedor (logs, procesos SO) |
| Django (`TIME_ZONE` global) | `env('DJANGO_TIME_ZONE', default='America/Tijuana')` | Zona horaria para Django templates/forms |
| Django (`USE_TZ`) | `True` | Django maneja datetimes con timezone awareness |
| PostgreSQL sesión (`default` DB) | `TIME_ZONE: tz` en DATABASES | Consistencia en queries directos |
| PostgreSQL sesión (`backend` DB) | `TIME_ZONE: tz` en DATABASES | CURRENT_TIMESTAMP devuelve hora local (consistente con Java) |
| `.env.example` | `DJANGO_TIME_ZONE=America/Tijuana` | Variable de entorno documentada |

### Flujo de timestamps

```
INSERT con db_default=Now()
    → Django ORM detecta db_default en el campo
    → Omite "timestamp" del INSERT SQL
    → PostgreSQL ejecuta DEFAULT CURRENT_TIMESTAMP
    → CURRENT_TIMESTAMP = hora local America/Tijuana (por TIME_ZONE en DATABASES)
    → Resultado: 00:47 (igual que Java)
```

### Lectura de timestamps (display)

Los timestamps almacenados son naive (sin timezone info) porque la columna PostgreSQL es `timestamp` (sin tz). Esto requiere manejo especial:

- **Admin (`_display_timestamp`)**: Usa `make_aware()` para naive datetimes, luego `localtime()` + `strftime()`
- **Templates (`|date`)**: `|date` formatea naive datetimes directamente (ya están en hora local, no necesitan conversión). **No usar `|localtime`** — lanza error con naive datetimes.

### Cambios en código

1. **`sanfelipe/settings/__init__.py`**:

   - Variable `tz` leída de `DJANGO_TIME_ZONE` antes de DATABASES
   - Ambas conexiones usan `'TIME_ZONE': tz` en la configuración de la DB
   - `TIME_ZONE = tz` (reutiliza la misma variable)

1. **`tramites/models/actividades.py`**:

   - Campo `timestamp` con `db_default=Now()` (ORM omite campo del INSERT)
   - `editable=False` — no se muestra en forms
   - `auto_now_add=True` eliminado (enviaba UTC)

1. **`tramites/admin.py`**:

   - `_display_timestamp()` usa `make_aware()` + `localtime()` para manejar naive datetimes

1. **`templates/admin/tramite_detail.html`**:

   - Timestamps usan `|date:"Y-m-d H:i:s"` (sin `|localtime`, que falla con naive datetimes)

### Consecuencias

- Bueno, porque los timestamps de Django y Java son consistentes en la misma tabla
- Bueno, porque usa `db_default` — feature nativa de Django 5.1+, sin workarounds
- Bueno, porque respeta el diseño original de las tablas sin requerir migraciones SQL
- Bueno, porque la zona horaria es configurable via variable de entorno
- Malo, porque la lectura de timestamps requiere `make_aware()` explícito en el admin para naive datetimes
- Malo, porque el campo no puede usar `auto_now_add` (Django enviaría UTC)

______________________________________________________________________

Formato basado en [MADR](https://adr.github.io/madr/)
