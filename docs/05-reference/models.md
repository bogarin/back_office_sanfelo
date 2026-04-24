# Mapeo de Modelos Django a Esquema SQL

Este documento describe cómo los modelos Django se mapean a las tablas SQL existentes del sistema DAU.

## Principio Fundamental

**Los modelos Django son SOLAMENTE mapeos de lectura/escritura a las tablas SQL.**
- NO modificar el esquema SQL desde Django
- NO usar migraciones Django (están desactivadas)
- Los campos deben coincidir EXACTAMENTE con las columnas SQL

---

## Tablas SQL y Modelos Django

### tramites/models.py

| Tabla SQL | Modelo Django | Descripción |
|-----------|----------------|-------------|
| `v_tramites_unificado` | `Tramite` | Vista unificada con todos los datos de trámites (READ-ONLY) |
| `tramite` | `TramiteLegacy` | Tabla original de trámites (DEPRECATED, READ-ONLY) |

**Detalles del modelo `Tramite` (vista unificada):**
Este modelo mapea a la vista SQL `v_tramites_unificado` que contiene todos los datos denormalizados para consultas eficientes.

 Campos principales:
- `id`: AutoField (PK)
- `folio`: CharField(50) - ÚNICO
- `cat_tramite_nombre`: CharField(100) - Nombre del tipo de trámite (denormalizado)
- `cat_estatus_nombre`: CharField(50) - Nombre del estatus (denormalizado)
- `cat_estatus_estatus`: CharField(10) - Código del estatus (denormalizado)
- `usuario_asignado_nombre`: CharField(100) - Nombre del analista asignado (nullable)
- `ultima_actividad_fecha`: DateTimeField - Fecha de la última actividad (nullable)
- `ultima_actividad_tipo`: CharField(50) - Tipo de última actividad (nullable)
- `cantidad_actividades`: IntegerField - Total de actividades realizadas
- `cantidad_documentos`: IntegerField - Total de documentos
- `clave_catastral`: CharField(16)
- `es_propietario`: BooleanField
- `nom_sol`: CharField(200)
- `tel_sol`: CharField(16)
- `correo_sol`: CharField(255)
- `importe_total`: DecimalField(12,2)
- `pagado`: BooleanField
- `tipo`: CharField(120)
- `observacion`: TextField
- `urgente`: BooleanField
- `creado`: DateTimeField
- `modificado`: DateTimeField

**Detalles del modelo `TramiteLegacy` (DEPRECATED):**
Este modelo mapea a la tabla SQL original `tramite` y está configurado como READ-ONLY.

 Campos principales:
- `id`: AutoField (PK)
- `folio`: CharField(50) - ÚNICO, auto-generado por trigger SQL
- `id_cat_tramite`: IntegerField → FK a cat_tramite
- `id_cat_estatus`: IntegerField → FK a cat_estatus (default: 101)
- `id_cat_perito`: IntegerField → FK a cat_perito (nullable)
- `clave_catastral`: CharField(16)
- `es_propietario`: BooleanField
- `nom_sol`: CharField(200)
- `tel_sol`: CharField(16)
- `correo_sol`: CharField(255)
- `importe_total`: DecimalField(12,2)
- `pagado`: BooleanField
- `tipo`: CharField(120)
- `observacion`: TextField
- `urgente`: BooleanField
- `creado`: DateTimeField (auto_now_add)
- `modificado`: DateTimeField (auto_now)

**Modelos Proxy:**
- `Abiertos` - Filtra trámites abiertos (estatus código 'iniciado')
- `Asignados` - Filtra trámites asignados a un analista
- `Finalizados` - Filtra trámites finalizados (estatus código 'finalizado')

---

### catalogos/models.py

| Tabla SQL | Modelo Django | Descripción |
|-----------|----------------|-------------|
| `cat_tramite` | `CatTramite` | Tipos de trámites disponibles |
| `cat_estatus` | `CatEstatus` | Estados por los que pasa un trámite (1xx=Inicio, 2xx=Proceso, 3xx=Finalizado) |
| `cat_usuario` | `CatUsuario` | Usuarios del sistema |
| `cat_perito` | `CatPerito` | Peritos autorizados |
| `cat_actividad` | `CatActividad` | Actividades realizadas durante el trámite |
| `cat_categoria` | `CatCategoria` | Categorías de trámites |
| `cat_inciso` | `CatInciso` | Incisos presupuestarios |
| `cat_requisito` | `CatRequisito` | Requisitos para trámites |
| `cat_tipo` | `CatTipo` | Tipos para costos |
| `actividades` | `Actividades` | Registro de actividades realizadas durante el trámite |
| `cobro` | `Cobro` | Registro de cobros por trámite |

---

### bitacora/models.py

| Tabla SQL | Modelo Django | Descripción |
|-----------|----------------|-------------|
| `bitacora` | `Bitacora` | Registro de movimientos del sistema (auditoría) |

**Detalles del modelo `Bitacora`:**
- `id`: AutoField (PK)
- `usuario_sis`: CharField(20)
- `tipo_mov`: CharField(20)
- `usuario_pc`: CharField(20)
- `fecha`: DateField
- `maquina`: CharField(20)
- `val_anterior`: CharField(120)
- `val_nuevo`: CharField(120)
- `observaciones`: CharField(220)

---

### costos/models.py

| Tabla SQL | Modelo Django | Descripción |
|-----------|----------------|-------------|
| `costo` | `Costo` | Costos asociados a trámites |
| `uma` | `Uma` | Valor de la UMA (único registro) |

---

### Tablas de Relaciones (catalogos/models.py)

Las siguientes tablas SQL implementan relaciones Many-to-Many entre catálogos:

| Tabla SQL | Modelo Django | Relación | Descripción |
|-----------|----------------|-----------|-------------|
| `rel_tmt_cate_req` | `RelTmtCateReq` | Trámite ↔ Requisito ↔ Categoría | Relación ternaria entre trámites, requisitos y categorías |
| `rel_tmt_categoria` | `RelTmtCategoria` | Trámite ↔ Categoría | Relación directa entre trámites y categorías |
| `rel_tmt_inciso` | `RelTmtInciso` | Trámite ↔ Inciso | Relación entre trámites e incisos presupuestarios |
| `rel_tmt_tipo_req` | `RelTmtTipoReq` | Tipo ↔ Trámite ↔ Requisito | Relación ternaria con tipo, trámite y requisito |
| `rel_tmt_actividad` | `RelTmtActividad` | Trámite ↔ Actividad | Relación entre trámites y actividades disponibles |

**Detalles del modelo `Costo`:**
- `id`: AutoField (PK)
- `id_tramite`: IntegerField → FK a cat_tramite
- `axo`: IntegerField (default: 2020)
- `descripcion`: CharField(255)
- `formula`: CharField(255)
- `cant_umas`: DecimalField(10,4)
- `rango_ini`: DecimalField(10,4)
- `rango_fin`: DecimalField(10,4)
- `inciso`: IntegerField
- `fomento`: BooleanField
- `cruz_roja`: DecimalField(10,4)
- `bomberos`: DecimalField(10,4)
- `activo`: BooleanField
- `id_usuario`: IntegerField
- `fecha_actualiza`: DateField
- `observacion`: CharField(600)
- `id_tipo`: IntegerField

**Detalles del modelo `Uma`:**
- `id`: AutoField (PK)
- `valor`: DecimalField(10,4)

---

### Tablas de Actividad y Cobros (catalogos/models.py)

**Detalles del modelo `Actividades`:**
- `id`: AutoField (PK)
- `id_tramite`: IntegerField → FK a tramite
- `id_cat_actividad`: IntegerField → FK a cat_actividad
- `id_cat_estatus`: IntegerField → FK a cat_estatus
- `fecha_inicio`: DateField
- `fecha_fin`: DateField
- `id_cat_usuario`: IntegerField → FK a cat_usuario
- `secuencia`: IntegerField
- `observacion`: CharField(255)

**Detalles del modelo `Cobro`:**
- `id`: AutoField (PK)
- `concepto`: CharField(250)
- `importe`: DecimalField(10,2)
- `inciso`: IntegerField
- `id_tramite`: IntegerField → FK a tramite

**Nota importante**: La tabla `uma` mantiene un SOLO registro. Usa el procedimiento almacenado `sp_actualizar_uma()` para actualizar.

---

## Relaciones y Foreign Keys

### Foreign Keys Directas en Tramites

Todas las FKs están implementadas como IntegerField que referencia IDs de las tablas de catálogo:

```
tramite
  ├─ id_cat_tramite → cat_tramite.id
  ├─ id_cat_estatus → cat_estatus.id
  └─ id_cat_perito → cat_perito.id

costo
  ├─ id_tramite → cat_tramite.id
  ├─ inciso → cat_inciso.id
  └─ id_tipo → cat_tipo.id
```

### Relaciones Many-to-Many (Tablas rel_*)

Las relaciones entre catálogos se implementan en tablas separadas:

```
RelTmtCateReq (rel_tmt_cate_req)
  ├─ id_cat_tramite → cat_tramite.id
  ├─ id_cat_requisito → cat_requisito.id
  └─ id_cat_categoria → cat_categoria.id

RelTmtCategoria (rel_tmt_categoria)
  ├─ id_cat_tramite → cat_tramite.id
  └─ id_cat_categoria → cat_categoria.id

RelTmtInciso (rel_tmt_inciso)
  ├─ id_cat_inciso → cat_inciso.id
  └─ id_cat_tramite → cat_tramite.id

RelTmtTipoReq (rel_tmt_tipo_req)
  ├─ id_cat_tipo → cat_tipo.id
  ├─ id_cat_tramite → cat_tramite.id
  └─ id_cat_requisito → cat_requisito.id

RelTmtActividad (rel_tmt_actividad)
  ├─ id_cat_tramite → cat_tramite.id
  └─ id_cat_actividad → cat_actividad.id
```

**IMPORTANTE**: NO usamos `models.ManyToManyField` en Django porque las tablas de relación están definidas en SQL.

**IMPORTANTE**: NO usamos `models.ForeignKey` en Django porque las FKs están definidas en SQL.

---

## Funciones y Triggers SQL

El esquema SQL incluye varias funciones y triggers que se ejecutan automáticamente:

### Auto-generación de Folio
- **Función**: `generar_folio_letras(depto_nombre)`
- **Trigger**: `trigger_generar_folio_tramite`
- **Descripción**: Genera un folio único con formato `DEPTO-YYMMDD-XXXX-D` donde D es dígito de validación Luhn

### Actualización de Timestamp
- **Función**: `actualizar_tramite_timestamp()`
- **Trigger**: `tramite_actualizado`
- **Descripción**: Actualiza `modificado` cuando se actualiza un registro

### Validación de Folio
- **Función**: `validar_folio_luhn(folio_completo)`
- **Descripción**: Valida el dígito de verificación del folio

### Gestión de UMA
- **Procedimiento**: `sp_actualizar_uma(p_valor)`
- **Trigger**: `trg_uma_single_row` (mantiene solo 1 registro)
- **Descripción**: Actualiza el valor de la UMA

---

## Índices SQL

El esquema incluye múltiples índices optimizados:

### Índices en `tramite`
- `idx_tramite_folio` (UNIQUE) en `folio`
- `idx_tramite_creado` en `creado DESC`
- `idx_tramite_estatus_creado` en `(id_cat_estatus, creado DESC)`
- `idx_tramite_estatus_no_pagado` en `(id_cat_estatus, creado DESC) WHERE pagado=false`
- `idx_tramite_prioridad` en `(urgente DESC, id_cat_estatus, creado DESC) WHERE pagado=false`
- `idx_tramite_urgente` en `(id, creado DESC) WHERE urgente=true`
- `idx_tramite_urgente_no_pagado` en `(id, creado DESC) WHERE (urgente=true AND pagado=false)`

---

## Reglas de Mapeo

### Mapeo de Tipos SQL a Django

| SQL Type | Django Field |
|-----------|---------------|
| `integer` | `IntegerField` |
| `bigint` | `BigIntegerField` |
| `serial` | `AutoField` (PK) |
| `character varying(n)` | `CharField(max_length=n)` |
| `character(n)` | `CharField(max_length=n)` |
| `text` | `TextField` |
| `boolean` | `BooleanField` |
| `date` | `DateField` |
| `timestamp without time zone` | `DateTimeField` |
| `numeric(m,n)` | `DecimalField(max_digits=m, decimal_places=n)` |
| `money` | `DecimalField` (PostgreSQL money está deprecado, usar numeric) |

### Campos NOT NULL

En SQL, `NOT NULL` se mapea a `blank=False` o sin especificar:

```python
# SQL: descripcion character varying(255) NOT NULL
# Django:
descripcion = models.CharField(max_length=255, verbose_name="Descripción")
```

### Campos con DEFAULT

Los defaults de SQL NO se especifican en Django (se manejan en la base de datos):

```python
# SQL: id_cat_estatus integer DEFAULT 101 NOT NULL
# Django (sin default - SQL lo maneja):
id_cat_estatus = models.IntegerField(verbose_name="ID Catálogo Estatus")
```

**EXCEPCIÓN**: Para valores simples, se pueden especificar defaults en Django si se necesita para validación.

---

## Ejemplos de Uso

### Crear un trámite

**Nota:** Para crear trámites, usa el modelo `TramiteLegacy` (tabla `tramite` en DB backend). El modelo `Tramite` es una vista READ-ONLY.

```python
from tramites.models import TramiteLegacy
from catalogos.models import CatTramite, CatEstatus

tramite = TramiteLegacy.objects.create(
    folio="",  # Dejar vacío, el trigger SQL lo generará
    id_cat_tramite=1,  # CERTIFICADO DE LIBERTAD DE GRAVAMEN
    id_cat_estatus=101,  # BORRADOR
    nom_sol="Juan Pérez",
    tel_sol="6861234567",
    correo_sol="juan@example.com",
    es_propietario=True,
    urgente=True,
)
# El trigger SQL generará automáticamente: folio = "DAU-2502XX-AAAA-B"
```

**ATENCIÓN:** `TramiteLegacy` está configurado como READ-ONLY en producción. Para crear trámites, usa los servicios apropiados o el procedimiento almacenado en la base de datos backend.

### Obtener requisitos y categorías de un trámite

```python
from catalogos.models import RelTmtCateReq, CatRequisito, CatCategoria

# Obtener relaciones para un trámite
relaciones = RelTmtCateReq.objects.filter(id_cat_tramite=1)

for rel in relaciones:
    req = CatRequisito.objects.get(id=rel.id_cat_requisito)
    cat = CatCategoria.objects.filter(id=rel.id_cat_categoria).first()
    print(f"Requisito: {req.requisito}")
    if cat:
        print(f"  Categoría: {cat.categoria}")
```

### Obtener incisos de un trámite

```python
from catalogos.models import RelTmtInciso, CatInciso

# Obtener incisos para un trámite
incisos_rel = RelTmtInciso.objects.filter(id_cat_tramite=3)

for rel in incisos_rel:
    inciso = CatInciso.objects.get(id=rel.id_cat_inciso)
    print(f"Inciso: {inciso.inciso} - {inciso.descripcion}")
```

### Obtener categorías de un trámite

```python
from catalogos.models import RelTmtCategoria, CatCategoria

# Obtener categorías directas para un trámite
cats_rel = RelTmtCategoria.objects.filter(id_cat_tramite=2)

for rel in cats_rel:
    cat = CatCategoria.objects.get(id=rel.id_cat_categoria)
    print(f"Categoría: {cat.categoria}")
```

### Obtener requisitos con tipos específicos

```python
from catalogos.models import RelTmtTipoReq, CatRequisito, CatTipo

# Obtener requisitos de un trámite con su tipo
relaciones = RelTmtTipoReq.objects.filter(id_cat_tramite=4)

for rel in relaciones:
    tipo = CatTipo.objects.get(id=rel.id_cat_tipo)
    req = CatRequisito.objects.get(id=rel.id_cat_requisito)
    print(f"Tipo: {tipo.tipo} - Requisito: {req.requisito}")
```

### Consultar trámites con catálogos

```python
from tramites.models import Tramite

# Usar el modelo Tramite (vista unificada) que ya tiene campos denormalizados
# No necesitas select_related para catálogos - los datos ya están denormalizados
tramites = Tramite.objects.all().order_by('-creado')

for t in tramites:
    print(f"{t.folio} - {t.cat_estatus_nombre}")
    print(f"  Tipo: {t.cat_tramite_nombre}")
    print(f"  Asignado a: {t.usuario_asignado_nombre or 'Sin asignar'}")
    print(f"  Actividades: {t.cantidad_actividades}")
    print(f"  Documentos: {t.cantidad_documentos}")
```

**Ventajas de usar `Tramite` (vista unificada):**
- Los campos de catálogos ya están denormalizados (sin N+1 queries)
- Contiene información agregada (cantidad de actividades, documentos)
- Eficiente para listados y dashboards del admin

**Usar `TramiteLegacy` cuando:**
- Necesitas acceder a los IDs de catálogos (id_cat_tramite, id_cat_estatus, etc.)
- Necesitas relacionar con otras tablas usando FKs
- Necesitas acceso a campos que no están en la vista unificada

### Actualizar el valor de UMA

```python
from costos.models import Uma
import decimal

# Usar el procedimiento almacenado
Uma.update_uma(decimal.Decimal("117.31"))
```

### Obtener el valor actual de UMA

```python
from costos.models import Uma

uma_valor = Uma.get_current_uma()
print(f"UMA actual: ${uma_valor}")
```

---

## Archivos SQL de Referencia

Los esquemas SQL se encuentran en:
- `~/Code/SF/esquemas_de_dau/dau_schema.sql` - Estructura de tablas
- `~/Code/SF/esquemas_de_dau/dau_data.sql` - Datos iniciales

**NO COPIAR estos archivos al proyecto**. Son archivos de referencia externos que se actualizan por terceros.

---

---

## Notas Importantes

1. **NO usar `makemigrations` o `migrate`**: Los cambios al esquema vienen de terceros
2. **NO crear nuevas tablas desde Django**: Solo mapear tablas existentes
3. **NO usar `models.ForeignKey`**: Usar `IntegerField` que referencie IDs
4. **NO modificar triggers SQL desde Django**: Los triggers se gestionan externamente
5. **Los campos `creado` y `modificado`** se actualizan automáticamente por triggers SQL
6. **El `folio` se genera automáticamente** por trigger SQL - no especificarlo en `create()`
