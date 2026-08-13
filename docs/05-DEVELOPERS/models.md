# Referencia de Modelos Django

> **Módulo:** `tramites.models`
> **Última actualización:** Mayo 2026

______________________________________________________________________

## Advertencia: Migraciones deshabilitadas

Todos los modelos usan `managed = False`. Django **no genera ni ejecuta migraciones** — los modelos son **mapeos de solo lectura** a tablas y vistas existentes en PostgreSQL. El router (`core/db_router.py`) bloquea `allow_migrate` para todos los modelos registrados con `allow_migrations=False`.

> **Nunca** ejecutes `makemigrations` o `migrate` para las tablas de este proyecto. El esquema lo administra directamente el DBA.

______________________________________________________________________

## Separación de esquemas

El proyecto usa dos conexiones PostgreSQL definidas en `settings.DATABASES`:

| Conexión (`db_alias`) | Esquema PostgreSQL | Nivel de acceso | Propietario |
|-----------------------|--------------------|-----------------|-------------|
| `backend` | `backoffice` | `READ_ONLY` (catálogos), `APPEND_ONLY` (actividades) | Backoffice Django |
| `default` | `backoffice` | `READ_ONLY` (vista `v_tramites_unificado`) | Backoffice Django |

> **Nota:** Originalmente existía una conexión al esquema `public` (legado Java), pero actualmente **todos los modelos se rutean a `backend` o `default`**. Los catálogos (`cat_*`) son propiedad de la app legada Java y NO se modifican desde Django; el manager `ReadOnlyManager` lo impide a nivel ORM.

El enrutamiento se controla con el decorador `@register_model(db_alias, access_pattern, allow_migrations)` de `core/model_config.py`, registrado en `core/db_router.ModelBasedRouter`.

______________________________________________________________________

## Managers y patrones de acceso

Antes de documentar cada modelo, es clave entender los managers personalizados que imponen el nivel de acceso:

| Manager | Clase base | Permite | Bloquea | Uso |
|---------|-----------|---------|---------|-----|
| `ReadOnlyManager` | `ReadOnlyQuerySet` | `all()`, `filter()`, `get()` | `create()`, `update()`, `delete()`, `bulk_create()` | Catálogos, relaciones |
| `CachedReadOnlyManager` | `ReadOnlyQuerySet` + caché | Lectura + `all_cached()`, `get_cached()`, `all_cached_as_dict()` | Todas las escrituras | `Requisito` (28 filas, consultas frecuentes) |
| `CreateOnlyManager` | `CreateOnlyQuerySet` | `create()`, `bulk_create()` | `update()`, `delete()`, `save()` en instancias existentes | `Actividades` (audit log) |
| `TramiteQuerySet` | `models.QuerySet` | Todo (lectura) + atajos `en_proceso()`, `finalizados()`, `asignados_a()`, `sin_asignar()` | N/A (modelo sobre vista) | `Tramite` |

Todos los managers exponen métodos de caché (`all_cached()`, `get_cached()`) con invalidación manual vía `invalidate_cache()`.

______________________________________________________________________

## Resumen de modelos

| Tabla/Vista SQL | Modelo Django | `db_table` | `db_alias` | Acceso | Manager |
|----------------|--------------|------------|------------|--------|---------|
| `cat_tramite` | `TramiteCatalogo` | `cat_tramite` | `backend` | `READ_ONLY` | `ReadOnlyManager` |
| `cat_estatus` | `TramiteEstatus` | `cat_estatus` | `backend` | `READ_ONLY` | `ReadOnlyManager` |
| `cat_perito` | `Perito` | `cat_perito` | `backend` | `READ_ONLY` | `ReadOnlyManager` |
| `cat_actividad` | `Actividad` | `cat_actividad` | `backend` | `READ_ONLY` | `ReadOnlyManager` |
| `cat_categoria` | `Categoria` | `cat_categoria` | `backend` | `READ_ONLY` | `ReadOnlyManager` |
| `cat_requisito` | `Requisito` | `cat_requisito` | `backend` | `READ_ONLY` | `CachedReadOnlyManager` |
| `cat_tipo` | `Tipo` | `cat_tipo` | `backend` | `READ_ONLY` | `ReadOnlyManager` |
| `actividades` | `Actividades` | `actividades` | `backend` | `APPEND_ONLY` | `CreateOnlyManager` |
| `rel_tmt_categoria` | `TramiteCatalogoCategoria` | `rel_tmt_categoria` | `backend` | `READ_ONLY` | `ReadOnlyManager` |
| `rel_tmt_cate_req` | `TramiteCatalogoRequisito` | `rel_tmt_cate_req` | `backend` | `READ_ONLY` | `ReadOnlyManager` |
| `rel_tmt_tipo_req` | `TramiteCatalogoTipoRequisito` | `rel_tmt_tipo_req` | `backend` | `READ_ONLY` | `ReadOnlyManager` |
| `rel_tmt_actividad` | `TramiteCatalogoActividad` | `rel_tmt_actividad` | `backend` | `READ_ONLY` | `ReadOnlyManager` |
| `v_tramites_unificado` | `Tramite` | `v_tramites_unificado` | `default` | `READ_ONLY` | `TramiteQuerySet` |

______________________________________________________________________

## Catálogos (`tramites/models/catalogos.py`)

Tablas de referencia con prefijo `cat_`. Propiedad de la app legada Java. Solo lectura desde Django.

### TramiteCatalogo

Tipos de trámites disponibles en el sistema.

| Campo | Tipo | BD (`db_column`) | Notas |
|-------|------|-------------------|-------|
| `id` | `AutoField` (PK) | `id` | |
| `nombre` | `CharField(255)` | `nombre` | |
| `descripcion` | `CharField(600, null)` | `descripcion` | |
| `area` | `CharField(80, null)` | `area` | |
| `respuesta_dias` | `DecimalField(5,2, null)` | `respuesta_dias` | |
| `pago_inicial` | `BooleanField(null)` | `pago_inicial` | |
| `url` | `CharField(512, null)` | `url` | |
| `activo` | `BooleanField(null)` | `activo` | |

### TramiteEstatus

Estatus de trámites con prefijo numérico por familia.

| Campo | Tipo | BD (`db_column`) | Notas |
|-------|------|-------------------|-------|
| `id` | `AutoField` (PK) | `id` | Ver `IntegerChoices` abajo |
| `estatus` | `CharField(30)` | `estatus` | |
| `responsable` | `CharField(64, null)` | `responsable` | |
| `descripcion` | `CharField(255, null)` | `descripcion` | |

**Familias de estatus** (`IntegerChoices`):

| Prefijo | Familia | Valores |
|---------|---------|---------|
| `1xx` | **Inicio** | `101` BORRADOR, `102` PENDIENTE_PAGO, `103` PAGO_EXPIRADO |
| `2xx` | **Proceso** | `201` PRESENTADO, `202` EN_REVISION, `203` REQUERIMIENTO, `204` SUBSANADO, `205` EN_DILIGENCIA |
| `3xx` | **Finalizado** | `301` POR_RECOGER, `302` RECHAZADO, `303` FINALIZADO, `304` CANCELADO |

**Métodos de clase:**

- `es_activo(estatus)` → `True` si estatus está en proceso (201–205)
- `finalizados()` → tupla de IDs de estatus terminales (301–304, 103)
- `get_en_revision()` → devuelve la instancia con `id=202` desde caché

### Perito

Peritos autorizados para trámites.

| Campo | Tipo | BD (`db_column`) | Notas |
|-------|------|-------------------|-------|
| `id` | `AutoField` (PK) | `id` | |
| `paterno` | `CharField(30, null)` | `paterno` | |
| `materno` | `CharField(30, null)` | `materno` | |
| `nombre` | `CharField(90, null)` | `nombre` | |
| `domicilio` | `CharField(250, null)` | `domicilio` | |
| `colonia` | `CharField(120, null)` | `colonia` | |
| `telefono` | `CharField(16, null)` | `telefono` | |
| `celular` | `CharField(16, null)` | `celular` | |
| `correo` | `CharField(255, null)` | `correo` | |
| `revalidacion` | `DateField(null)` | `revalidacion` | |
| `fecha_registro` | `DateField(null)` | `fecha_registro` | |
| `rfc` | `CharField(17, null)` | `rfc` | |
| `estatus` | `BooleanField` | `estatus` | |
| `cedula` | `CharField(19, null)` | `cedula` | |

**Propiedad:** `nombre_completo` → concatenación `"{paterno} {materno} {nombre}"`.

### Actividad (catálogo)

Actividades posibles durante un trámite.

| Campo | Tipo | BD (`db_column`) | Notas |
|-------|------|-------------------|-------|
| `id` | `AutoField` (PK) | `id` | |
| `actividad` | `CharField(250)` | `actividad` | |

### Categoria

Categorías de trámites.

| Campo | Tipo | BD (`db_column`) | Notas |
|-------|------|-------------------|-------|
| `id` | `AutoField` (PK) | `id` | |
| `categoria` | `CharField(120, null)` | `categoria` | |

### Requisito

Requisitos para trámites. Usa `CachedReadOnlyManager` (caché de 1 hora).

| Campo | Tipo | BD (`db_column`) | Notas |
|-------|------|-------------------|-------|
| `id` | `AutoField` (PK) | `id` | |
| `requisito` | `CharField(480)` | `requisito` | |

### Tipo

Tipos de trámite (para costos).

| Campo | Tipo | BD (`db_column`) | Notas |
|-------|------|-------------------|-------|
| `id` | `AutoField` (PK) | `id` | |
| `tipo` | `CharField(120)` | `tipo` | |

______________________________________________________________________

## Modelo transaccional (`tramites/models/actividades.py`)

### Actividades

Registro de cada acción realizada sobre un trámite. **Solo inserción** (`APPEND_ONLY`).

| Campo | Tipo | BD (`db_column`) | Notas |
|-------|------|-------------------|-------|
| `id` | `AutoField` (PK) | `id` | |
| `tramite` | `FK → Tramite` | `id_tramite` | `CASCADE` |
| `estatus` | `FK → TramiteEstatus` | `id_cat_estatus` | `RESTRICT` |
| `backoffice_user_id` | `IntegerField(null)` | `backoffice_user_id` | Sin FK al auth user |
| `observacion` | `CharField(255, null)` | `observacion` | |
| `timestamp` | `DateTimeField` | `timestamp` | `db_default=Now()`, PostgreSQL asigna `CURRENT_TIMESTAMP` |

**DTOs auxiliares** (no son modelos Django, son `@dataclass`):

| Clase | Uso |
|-------|-----|
| `RequisitoFile` | Archivo PDF de requisito con metadata SFTP + nombre del catálogo |
| `ActividadFile` | Archivo PDF de actividad con metadata del registro |
| `TimelineEntry` | Entrada del timeline: actividad + archivos adjuntos + usuario |

______________________________________________________________________

## Relaciones / Tablas pivote (`tramites/models/relaciones.py`)

Tablas many-to-many entre `TramiteCatalogo` y catálogos. Todas son **solo lectura**.

### TramiteCatalogoCategoria

`TramiteCatalogo ↔ Categoria`

| Campo | Tipo | BD (`db_column`) |
|-------|------|-------------------|
| `id` | `AutoField` (PK) | `id` |
| `tramite_catalogo` | `FK → TramiteCatalogo` | `id_cat_tramite` |
| `categoria` | `FK → Categoria` | `id_cat_categoria` |

### TramiteCatalogoRequisito

`TramiteCatalogo ↔ Requisito ↔ Categoria` (opcional)

| Campo | Tipo | BD (`db_column`) |
|-------|------|-------------------|
| `id` | `AutoField` (PK) | `id` |
| `tramite_catalogo` | `FK → TramiteCatalogo` | `id_cat_tramite` |
| `requisito` | `FK → Requisito` | `id_cat_requisito` |
| `categoria` | `FK → Categoria` (null) | `id_cat_categoria` |

### TramiteCatalogoTipoRequisito

`Tipo ↔ TramiteCatalogo ↔ Requisito`

| Campo | Tipo | BD (`db_column`) |
|-------|------|-------------------|
| `id` | `AutoField` (PK) | `id` |
| `tipo` | `FK → Tipo` | `id_cat_tipo` |
| `tramite_catalogo` | `FK → TramiteCatalogo` | `id_cat_tramite` |
| `requisito` | `FK → Requisito` | `id_cat_requisito` |

### TramiteCatalogoActividad

`TramiteCatalogo ↔ Actividad`

| Campo | Tipo | BD (`db_column`) |
|-------|------|-------------------|
| `id` | `AutoField` (PK) | `id` |
| `tramite_catalogo` | `FK → TramiteCatalogo` | `id_cat_tramite` |
| `actividad` | `FK → Actividad` | `id_cat_actividad` |

> Todas las FK en relaciones usan `on_delete=DO_NOTHING` ya que Django no gestiona el ciclo de vida de estos datos.

______________________________________________________________________

## Tramite — Modelo principal (`tramites/models/tramite.py`)

### Tramite

Mapea a la **vista** `v_tramites_unificado` en el esquema `backoffice`. Esta vista unifica trámites con sus actividades, usuarios asignados y categorías.

No es una tabla — es una vista PostgreSQL de solo lectura. Las escrituras se realizan indirectamente vía el modelo `Actividades` (insertar filas que la vista luego refleja).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `IntegerField` (PK) | ID del trámite |
| `folio` | `CharField(50)` | Folio (ej. `DAU-260420-AAAE-B`) |
| `tramite_id` | `IntegerField` | ID del tipo de trámite (catálogo) |
| `tramite_nombre` | `CharField(255)` | Nombre del tipo de trámite |
| `tramite_categoria_id` | `IntegerField(null)` | ID de categoría |
| `tramite_categoria_nombre` | `CharField(255, null)` | Nombre de categoría |
| `tramite_tipo_cobro_id` | `IntegerField(null)` | ID del tipo de cobro |
| `tramite_tipo_cobro_nombre` | `CharField(100, null)` | Nombre del tipo de cobro |
| `clave_catastral` | `CharField(100, null)` | Clave catastral del inmueble |
| `es_propietario` | `BooleanField` | Si el solicitante es propietario |
| `importe_total` | `DecimalField(12,2, null)` | Importe total |
| `urgente` | `BooleanField` | Si el trámite es urgente |
| `solicitante_nombre` | `CharField(200, null)` | Nombre del solicitante |
| `solicitante_telefono` | `CharField(20, null)` | Teléfono |
| `solicitante_correo` | `CharField(100, null)` | Correo electrónico |
| `solicitante_comentario` | `TextField(null)` | Comentario del solicitante |
| `perito_id` | `IntegerField(null)` | ID del perito asignado |
| `perito_nombre` | `CharField(200, null)` | Nombre del perito |
| `ultima_actividad_estatus_id` | `IntegerField(null)` | ID del estatus de la última actividad |
| `ultima_actividad_estatus` | `CharField(100, null)` | Nombre del estatus actual |
| `ultima_actividad_responsable` | `CharField(100, null)` | Responsable de la última actividad |
| `ultima_actividad_descripcion` | `TextField(null)` | Descripción de la última actividad |
| `ultima_actividad_observacion` | `TextField(null)` | Observación de la última actividad |
| `asignado_user_id` | `IntegerField(null)` | ID del analista asignado |
| `asignado_username` | `CharField(150, null)` | Username del analista |
| `asignado_nombre` | `CharField(150, null)` | Nombre completo del analista |
| `asignado_group_id` | `IntegerField(null)` | ID del grupo/rol del analista |
| `asignado_rol` | `CharField(150, null)` | Nombre del rol |
| `creado` | `DateTimeField` | Fecha de creación |
| `actualizado` | `DateTimeField(null)` | Fecha de última actualización |

**Ordenamiento por defecto:** `-creado`, `urgente`

### TramiteQuerySet — Atajos de consulta

| Método | Filtro | Uso |
|--------|--------|-----|
| `en_proceso()` | `ultima_actividad_estatus_id >= 201` y `< 301` | Trámites activos en revisión |
| `finalizados()` | `ultima_actividad_estatus_id >= 301` | Trámites terminados |
| `asignados_a(user_id)` | `asignado_user_id = user_id` | Trámites de un analista |
| `sin_asignar()` | `asignado_user_id IS NULL` | Trámites en el pool |

### Acciones de workflow (métodos de instancia)

Todas las acciones de workflow delegan a `registrar_actividad()` que inserta un registro en `Actividades`.

| Método | Transición | Descripción |
|--------|-----------|-------------|
| `asignar(analista, asignado_por, obs)` | `→ 202` | Asigna a analista. `analista=None` libera. |
| `requerir_documentos(analista, obs)` | `202 → 203` | Solicita documentos adicionales |
| `enviar_a_firma(analista, obs)` | `202 → 205` | Envía a firma |
| `cancelar(analista, estatus_cierre, obs)` | `202/203/205 → 301/302/304` | Cancela con estatus terminal |
| `_liberar(liberado_por, obs)` | `→ 201` | Vuelve al pool (interno) |

**Validaciones:** `_assert_activo()`, `_assert_asignado_a()`, `_validate_transition()`.

**Matriz de transiciones válidas** (definida en `TRANSITIONS`):

```
PRESENTADO (201) ──→ EN_REVISION (202)
EN_REVISION (202) ──→ EN_REVISION (202)     [reasignar]
EN_REVISION (202) ──→ PRESENTADO (201)      [liberar]
EN_REVISION (202) ──→ REQUERIMIENTO (203)
EN_REVISION (202) ──→ EN_DILIGENCIA (205)
EN_REVISION (202) ──→ POR_RECOGER (301)
EN_REVISION (202) ──→ RECHAZADO (302)
EN_REVISION (202) ──→ CANCELADO (304)
REQUERIMIENTO (203) ──→ POR_RECOGER (301)
REQUERIMIENTO (203) ──→ RECHAZADO (302)
REQUERIMIENTO (203) ──→ CANCELADO (304)
EN_DILIGENCIA (205) ──→ POR_RECOGER (301)
EN_DILIGENCIA (205) ──→ RECHAZADO (302)
EN_DILIGENCIA (205) ──→ CANCELADO (304)
```

### Métodos de permisos

| Método | Regla |
|--------|-------|
| `can_view(user)` | Superuser/Admin/Coordinador → siempre; Analista → solo si asignado |
| `can_download(user)` | Superuser/Admin/Coordinador → siempre; Analista → asignados o activos sin asignar |
| `can_assign(user)` | Solo Coordinador/Admin/Superuser |
| `can_release(user)` | Solo Coordinador/Admin/Superuser |
| `can_execute_action(user)` | Superuser/Admin/Coordinador → siempre; Analista → solo si asignado |
| `available_actions(user)` | Lista de acciones según rol + estatus actual |

______________________________________________________________________

## Modelos proxy (`tramites/models/tramite.py`)

Los tres proxy models comparten la misma tabla (`v_tramites_unificado`) pero filtrados por rol. No agregan campos — solo personalizan el queryset y la presentación en Django Admin.

| Modelo proxy | Admin para | Filtro implícito | `verbose_name` |
|-------------|-----------|-------------------|----------------|
| `Buzon` | Analistas | Trámites asignados al usuario actual | "Buzón de trámites" |
| `Disponible` | Analistas | Trámites en proceso y sin asignar | "Trámites disponibles" |
| `Cerrado` | Coordinadores | Trámites finalizados | "Trámites finalizados" |

El filtrado real se implementa en las clases `ModelAdmin` correspondientes (no en el modelo), usando `TramiteQuerySet.en_proceso()`, `.asignados_a()`, `.sin_asignar()` y `.finalizados()`.

______________________________________________________________________

## Notas de relaciones entre entidades

```
TramiteCatalogo ──┬── TramiteCatalogoCategoria ──── Categoria
                  ├── TramiteCatalogoRequisito ──── Requisito (+ Categoria opcional)
                  ├── TramiteCatalogoTipoRequisito ─ Tipo + Requisito
                  └── TramiteCatalogoActividad ───── Actividad

Tramite (vista) ──── Actividades ──── TramiteEstatus
                        └── backoffice_user_id (sin FK, referencia por ID)
```

- `Tramite` **no tiene ForeignKeys** — todos los campos son planos (IntegerField, CharField). Los datos relacionales los resuelve la vista `v_tramites_unificado` en PostgreSQL.
- `Actividades` sí usa FK reales: `tramite → Tramite` (`CASCADE`) y `estatus → TramiteEstatus` (`RESTRICT`).
- `Actividades.backoffice_user_id` es un `IntegerField` sin FK, para evitar dependencias cruzadas con `auth.User` que vive en otra base de datos.
