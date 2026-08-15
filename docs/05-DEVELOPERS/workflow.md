# Workflow de Trámites — Guía para Desarrolladores

> **Fuente de verdad:** `tramites/workflow.py` (tabla declarativa `WORKFLOW`; `TRANSITIONS` en el modelo es una vista derivada)
> Última actualización: 14 de agosto de 2026

## Resumen

El workflow de trámites es una máquina de estados finitos implementada como tabla declarativa `WORKFLOW` en `tramites/workflow.py` (dataclass `Transition`: acción, origen, destino, roles autorizados, guardas). Cada transición queda definida explícitamente como `(from_status, to_status)`, y los métodos de acción (`asignar`, `requerir_documentos`, `enviar_a_firma`, `cancelar`) del modelo `Tramite` validan contra el dict derivado `TRANSITIONS` antes de ejecutarse. `available_actions()` y los destinos del dropdown de cancelación derivan de la misma tabla.

Este documento describe los estados, transiciones, acciones, permisos y el flujo típico de un trámite desde su creación hasta su cancelación.

## 1. Estados del Workflow

Los estados están definidos en `TramiteEstatus.Estatus` (`tramites/models/catalogos.py`) como `IntegerChoices`. Se agrupan en tres rangos por prefijo:

| Código | Constante | Responsable | Descripción |
|--------|-----------|-------------|-------------|
| **Inicio (1XX)** | | | |
| 101 | `BORRADOR` | Ciudadano | El ciudadano captura información y sube requisitos. Sin validez oficial. DEPRECADO. |
| 102 | `PENDIENTE_PAGO` | Ciudadano | El trámite está bloqueado esperando confirmación de pago. |
| 103 | `PAGO_EXPIRADO` | Sistema | La línea de captura venció y el trámite se detuvo por falta de pago. |
| **Proceso (2XX)** | | | |
| 201 | `PRESENTADO` | Sistema | El pago se confirmó y el trámite entró oficialmente a la bandeja de la dependencia. Sin asignar. |
| 202 | `EN_REVISION` | Funcionario | Un analista ha tomado el expediente para validar documentos y datos. |
| 203 | `REQUERIMIENTO` | Ciudadano | Se detectó error o falta de información. El ciudadano debe corregir. |
| 204 | `SUBSANADO` | Funcionario | El ciudadano respondió al requerimiento. El trámite vuelve a la fila de revisión. |
| 205 | `EN_DILIGENCIA` | Perito | Fase de campo: mediciones, inspecciones, deslindes, etc. Ahora se llama "Mandar a firma" |
| **Finalizado (3XX)** | | | |
| 301 | `POR_RECOGER` | Ciudadano | El documento final está disponible para descarga o recolección. |
| 302 | `RECHAZADO` | Funcionario | Resolución negativa: no procedió legal o técnicamente. |
| 303 | `FINALIZADO` | Sistema | El ciudadano recibió su documento y el expediente se cierra. |
| 304 | `CANCELADO` | Sistema | Trámite interrumpido por el ciudadano o impedimento administrativo. |

> **Nota:** Los estados 1XX (inicio) son gestionados por el sistema externo de portal ciudadano. El backoffice solo gestiona los estados 2XX y las transiciones hacia 3XX. El estado 303 (`FINALIZADO`) se alcanza desde `POR_RECOGER` vía el sistema externo, no desde el backoffice.

### Helper: `es_activo()`

El class method `TramiteEstatus.Estatus.es_activo(estatus)` retorna `True` para los estados de proceso activo:

```python
@classmethod
def es_activo(cls, estatus: int) -> bool:
    return estatus in (
        cls.PRESENTADO,      # 201
        cls.EN_REVISION,     # 202
        cls.REQUERIMIENTO,   # 203
        cls.SUBSANADO,       # 204
        cls.EN_DILIGENCIA,   # 205
    )
```

## 2. Transiciones Válidas

### Transiciones válidas para Inicio (1XX)

Por el momento este proyecto no está orientado a administrar trámites con estatus en el grupo de Inicio (1XX).

### Transiciones para Analista

El funcionario (analista) solo tiene permiso de hacer estos movimientos:

| Actual | Siguiente | Válido | Razón |
| ------ | --------- | ------ | ----- |
| 1XX | XXX | NO | `Analista` no debe ver ni operar sobre tickets que estan en estos estados. |
| 2XX | 1XX | NO | `Analista` no puede mandar ningun tramite 2XX a Borrador, pendiente de pago o pago expirado. No le corresponde. |
| 3XX | XXX | NO | `Analista` no puede cambiar el estado de un tramite que ya ha sido cerrado/terminado/cancelado. |
| ------ | --------- | ------ | ----- |
| 201 | 201 | NO | Sin significado semantico. |
| 201 | 202 | SI | `Analista` se autoasigna un tramite. |
| 201 | 203 | NO | Debe asignarse el tramite primero. |
| 201 | 204 | NO | Debe asignarse el tramite primero. |
| 201 | 205 | NO | Debe asignarse el tramite primero. |
| 201 | 3XX | NO | Salto invalido. Debe asignarse el tramite primero. |
| ------ | --------- | ------ | ----- |
| 202 | 201 | NO | Restringido al coordinador. |
| 202 | 202 | NO | Restringido al coordinador. |
| 202 | 203 | SI | `Analista` determina que el trámite procede, pero requiere más información del Ciudadano. |
| 202 | 204 | NO | Sin significado semantico. |
| 202 | 205 | SI | `Analista` determina que el trámite es procedente y manda el trámite a firmar. |
| 202 | 301 | NO | Ruta inválida: 301 solo se alcanza desde 205 (firma). Enviar a firma primero. |
| 202 | 302 | SI | `Analista` determina que el trámite es improcedente y cierra el trámite. |
| 202 | 303 | NO | Sin significado semántico. 303 solo se alcanza desde 301 vía el sistema externo. |
| 202 | 304 | SI | `Analista` cancela el trámite (p. ej. solicitud expresa del ciudadano). |
| ------ | --------- | ------ | ----- |
| 203 | 201 | NO | Sin significado semantico o incoherente. |
| 203 | 202 | NO | Potencialmente valido, pero el caso de uso no ha sido especificado en requerimientos. |
| 203 | 203 | SI | `Analista` ya pidió más información al ciudadano, pero no la ha recibido o requiere alguna otra información. |
| 203 | 204 | NO | Esto solo le corresponde al ciudadano y se hace mediante otro sistema. |
| 203 | 205 | NO | Potencialmente valido, pero el caso de uso no ha sido especificado en requerimientos. Delegado a Coordinador. |
| 203 | 301 | NO | Ruta inválida: 301 solo se alcanza desde 205 (firma). El trámite debe subsanarse (→204) y firmarse (→205) primero. |
| 203 | 302 | SI | `Analista` requirió más información pero el ciudadano no la proporcionó en tiempo y forma. Se cierra el trámite. |
| 203 | 303 | NO | Sin significado semántico. 303 solo se alcanza desde 301 vía el sistema externo. |
| 203 | 304 | SI | `Analista` cancela el trámite (p. ej. solicitud expresa del ciudadano). |
| ------ | --------- | ------ | ----- |
| 204 | 201 | NO | Sin significado semantico. |
| 204 | 202 | NO | Sin significado semántico. |
| 204 | 203 | SI | `Analista` rechaza uno o varios de los requisitos subsanados por el ciudadano. |
| 204 | 204 | NO | Sin significado semantico. |
| 204 | 205 | SI | `Analista` determina que el trámite es procedente y manda el trámite a firmar. |
| 204 | 301 | NO | Ruta inválida: 301 solo se alcanza desde 205 (firma). Enviar a firma primero. |
| 204 | 302 | SI | `Analista` determina que el trámite es improcedente y cierra el trámite. |
| 204 | 303 | NO | Sin significado semántico. 303 solo se alcanza desde 301 vía el sistema externo. |
| 204 | 304 | SI | `Analista` cancela el trámite (p. ej. solicitud expresa del ciudadano). |
| ------ | --------- | ------ | ----- |
| 205 | XXX | NO | Restringido al coordinador: el cierre desde diligencia (205 → 301/302/304) es exclusivo de coordinador/administrador. |

### Transiciones para Coordinador

El usuario con rol de `Coordinador` hereda todas las acciones de revisión del `Analista` (sin requerir estar asignado al trámite) y además tiene permisos exclusivos sobre la gestión de asignaciones y el cierre desde diligencia:

- 201 → 202 (Asignación de trámite a `Analista`)
- 202 → 202 (Reasignación de trámite a otro `Analista`)
- 202 → 201 (Eliminar `Analista` asignado sin asignar a otro. El trámite sigue disponible)
- 205 → 301/302/304 (Cierre del trámite desde diligencia; reservado a coordinador/administrador. Es la única ruta hacia 301)

| Actual | Siguiente | Válido | Razón |
| ------ | --------- | ------ | ----- |
| 1XX | XXX | NO | Estados de inicio gestionados por el sistema externo (portal ciudadano). El backoffice no opera sobre 1XX. |
| 2XX | 1XX | NO | El backoffice no puede regresar ningún trámite 2XX a Borrador, pendiente de pago o pago expirado. |
| 3XX | XXX | NO | Los estados 3XX son terminales: no admiten transiciones. |
| ------ | --------- | ------ | ----- |
| 201 | 201 | NO | Sin significado semántico. |
| 201 | 202 | SI | Asignación de trámite a un `Analista` (el propio analista también puede autoasignarse; ver tabla de Analista). |
| 201 | 203 | NO | Debe asignarse a un analista primero: las acciones de revisión operan sobre trámites asignados. |
| 201 | 204 | NO | Sin significado semántico. 204 solo se alcanza desde 203, por el ciudadano (sistema externo). |
| 201 | 205 | NO | Ruta inválida: 205 se alcanza desde 202/204 mediante envío a firma. |
| 201 | 3XX | NO | Salto inválido. Debe asignarse y revisarse primero. |
| ------ | --------- | ------ | ----- |
| 202 | 201 | SI | Liberar: elimina el `Analista` asignado y el trámite vuelve al pool (exclusivo). |
| 202 | 202 | SI | Reasignación de trámite a otro `Analista` (exclusivo). |
| 202 | 203 | SI | Acción de revisión; normalmente delegada en el analista asignado. |
| 202 | 204 | NO | Sin significado semántico. 204 lo genera el ciudadano (sistema externo). |
| 202 | 205 | SI | Envía el trámite a firma; normalmente delegado en el analista asignado. |
| 202 | 301 | NO | Ruta inválida: 301 solo se alcanza desde 205 (firma). |
| 202 | 302 | SI | Cierra el trámite por improcedencia. |
| 202 | 303 | NO | Sin significado semántico. 303 solo se alcanza desde 301 vía el sistema externo. |
| 202 | 304 | SI | Cancela el trámite. |
| ------ | --------- | ------ | ----- |
| 203 | 201 | SI | Liberar (excepción `_liberar()`): reset permitido desde cualquier estado activo; el requerimiento queda en el historial de `Actividades`. |
| 203 | 202 | NO | Potencialmente válido, pero el caso de uso no ha sido especificado en requerimientos. |
| 203 | 203 | SI | Reitera el requerimiento al ciudadano (self-loop: registra actividad sin cambiar de estatus). |
| 203 | 204 | NO | Solo el ciudadano puede subsanar (sistema externo). |
| 203 | 205 | NO | Caso de uso no especificado en requerimientos. Si se habilita, correspondería al coordinador (requiere ADR). |
| 203 | 301 | NO | Ruta inválida: 301 solo se alcanza desde 205 (firma). |
| 203 | 302 | SI | Cierra el trámite: el ciudadano no proporcionó la información requerida en tiempo y forma. |
| 203 | 303 | NO | Sin significado semántico. 303 solo se alcanza desde 301 vía el sistema externo. |
| 203 | 304 | SI | Cancela el trámite. |
| ------ | --------- | ------ | ----- |
| 204 | 201 | SI | Liberar (excepción `_liberar()`): reset permitido desde cualquier estado activo. |
| 204 | 202 | NO | Sin significado semántico. |
| 204 | 203 | SI | Rechaza la subsanación: uno o varios requisitos siguen incumplidos. |
| 204 | 204 | NO | Sin significado semántico. |
| 204 | 205 | SI | Manda el trámite a firma. |
| 204 | 301 | NO | Ruta inválida: 301 solo se alcanza desde 205 (firma). |
| 204 | 302 | SI | Cierra el trámite por improcedencia. |
| 204 | 303 | NO | Sin significado semántico. 303 solo se alcanza desde 301 vía el sistema externo. |
| 204 | 304 | SI | Cancela el trámite. |
| ------ | --------- | ------ | ----- |
| 205 | 2XX | NO | Sin significado semántico: el envío a firma no se deshace; liberar y reasignar están bloqueados en 205. |
| 205 | 301 | SI | Cierre positivo desde diligencia (exclusivo). Única ruta hacia 301. |
| 205 | 302 | SI | Cierre negativo desde diligencia (exclusivo). |
| 205 | 303 | NO | Sin significado semántico. 303 solo se alcanza desde 301 vía el sistema externo. |
| 205 | 304 | SI | Cancelación desde diligencia (exclusivo). |

### Transiciones para Administrador

El usuario con rol de `Administrador` puede ejecutar **toda transición válida del sistema**: su matriz de transiciones es idéntica a la de `Coordinador` y no tiene transiciones exclusivas. Las diferencias son transversales, no de workflow:

- No requiere estar asignado al trámite para ejecutar acciones de revisión.
- `can_view()`, `can_download()`, `can_assign()`, `can_release()` y `can_execute_action()` retornan siempre `True` (ver sección 4).
- Acceso completo al admin de Django (usuarios, grupos, catálogos), fuera del alcance del workflow.

> Nota: el `superuser` de Django se comporta igual que el `Administrador` para todos los efectos del workflow.

### Implementación

La tabla `WORKFLOW` en `tramites/workflow.py` define todas las transiciones permitidas (con acción, roles y guardas). El dict `TRANSITIONS` se deriva de ella y es lo que consume `_validate_transition()`. Equivale a:

```python
TRANSITIONS: dict[tuple[int, int], bool] = {
    # Asignar: presentado → en revisión
    (201, 202): True,
    # Reasignar: en revisión → en revisión (cambio de analista)
    (202, 202): True,
    # Liberar: en revisión → presentado (volver al pool)
    (202, 201): True,
    # Requerir documentos: en revisión → requerimiento
    (202, 203): True,
    # Reiterar requerimiento (self-loop, sin cambio de estatus): requerimiento → requerimiento
    (203, 203): True,
    # Enviar a firma: en revisión → en diligencia
    (202, 205): True,
    # Rechazar subsanación: subsanado → requerimiento
    (204, 203): True,
    # Enviar a firma desde subsanado: subsanado → en diligencia
    (204, 205): True,
    # Cierre directo por analista (rechazo o cancelación, sin pasar por firma)
    (202, 302): True,  # rechazado
    (202, 304): True,  # cancelado
    (203, 302): True,  # rechazado
    (203, 304): True,  # cancelado
    (204, 302): True,  # rechazado
    (204, 304): True,  # cancelado
    # Cierre desde diligencia (solo coordinador/administrador)
    (205, 301): True,  # por recoger
    (205, 302): True,  # rechazado
    (205, 304): True,  # cancelado
}
```

### Diagrama de estados

```mermaid
stateDiagram-v2
    title Workflow de Trámites — Transiciones por rol

    state "Proceso (2XX)" as proceso {
        [*] --> PRESENTADO : Pago confirmado (sistema externo)
        PRESENTADO : 201 — Sin asignar
        EN_REVISION : 202 — Asignado a analista
        REQUERIMIENTO : 203 — Esperando correcciones del ciudadano
        SUBSANADO : 204 — Ciudadano respondió al requerimiento
        EN_DILIGENCIA : 205 — Trabajo de campo / firma

        PRESENTADO --> EN_REVISION : asignar / autoasignar (201→202)
        EN_REVISION --> EN_REVISION : reasignar (202→202)
        EN_REVISION --> PRESENTADO : liberar (202→201)
        EN_REVISION --> REQUERIMIENTO : requerir documentos (202→203)
        REQUERIMIENTO --> SUBSANADO : ciudadano corrige (sistema externo)
        SUBSANADO --> REQUERIMIENTO : rechazar requerimientos (204→203)
        SUBSANADO --> EN_DILIGENCIA : mandar a firma (204→205)
    }

    state "Finalizado (3XX)" as finalizado {
        POR_RECOGER : 301
        RECHAZADO : 302
        FINALIZADO : 303
        CANCELADO : 304

        POR_RECOGER --> FINALIZADO : ciudadano recoge (sistema externo)
    }

    EN_REVISION --> RECHAZADO : improcedente (202→302)
    REQUERIMIENTO --> RECHAZADO : cerrar sin respuesta (203→302)
    SUBSANADO --> RECHAZADO : improcedente (204→302)
    EN_REVISION --> CANCELADO : cancelación (202→304)
    REQUERIMIENTO --> CANCELADO : cancelación (203→304)
    SUBSANADO --> CANCELADO : cancelación (204→304)
    EN_DILIGENCIA --> POR_RECOGER : cierre positivo (205→301, coordinador)
    EN_DILIGENCIA --> RECHAZADO : cierre negativo (205→302, coordinador)
    EN_DILIGENCIA --> CANCELADO : cancelación (205→304, coordinador)

    FINALIZADO --> [*]
    RECHAZADO --> [*]
    CANCELADO --> [*]
```

### Validación de transiciones

El método `_validate_transition(to_status)` valida que la transición exista en el dict:

```python
def _validate_transition(self, to_status: int) -> None:
    from_status = self.ultima_actividad_estatus_id
    if (from_status, to_status) not in TRANSITIONS:
        raise EstadoNoPermitidoError(
            f'No es posible realizar esta acción en el estatus actual '
            f'del trámite {self.folio} (estatus actual: {from_status}).'
        )
```

**Agregar una transición nueva = agregar una línea al dict.** No se necesita modificar lógica en los métodos de acción.

## 3. Acciones del Workflow

Los métodos de acción viven en el modelo `Tramite` y son la API pública para cambiar el estado de un trámite. Cada acción valida la transición, verifica la asignación y registra una actividad.

### Resumen de acciones

| Método | Transición | Permisos requeridos | Descripción |
|--------|------------|---------------------|-------------|
| `asignar()` | 201→202, 202→202, →201 | `can_assign()` o `can_execute_action()` | Asignar, reasignar o liberar un trámite |
| `requerir_documentos()` | 202→203, 203→203, 204→203 | `can_execute_action()` | Requiere documentos adicionales al ciudadano (desde 203: reitera el requerimiento; desde 204: rechaza la subsanación) |
| `enviar_a_firma()` | 202→205, 204→205 | `can_execute_action()` | Envía el trámite a firma; al pasar a 205 sale del buzón del analista |
| `cancelar()` | 202/203/204→302/304; 205→301/302/304 | Desde 202/203/204: `can_execute_action()`; desde 205: solo coordinador/administrador | Cierra el trámite con un estatus terminal |

### `asignar(analista, asignado_por, observacion='')`

Método polimórfico que maneja tres casos según el valor de `analista`:

| `analista` | Comportamiento | Transición |
|------------|----------------|------------|
| `User` (nuevo analista, != actual) | Reasignar | 202→202 o 201→202 |
| `User` (mismo analista actual) | Ignorar (silencioso) | — |
| `None` | Liberar al pool | Cualquier activo → 201 |

**Validaciones:**

1. `_assert_activo()` — el trámite debe estar en estado activo
1. `_validate_transition(EN_REVISION)` — la transición debe existir en `TRANSITIONS` (solo para asignar/reasignar, no para liberar)
1. Si ya está asignado al mismo analista, sale silenciosamente sin crear actividad

**Ejemplo de uso:**

```python
# Asignar trámite a un analista
tramite.asignar(analista=ana, asignado_por=coordinador)

# Autoasignar (analista toma el trámite del pool)
tramite.asignar(analista=ana, asignado_por=ana)

# Liberar trámite (volver al pool)
tramite.asignar(analista=None, asignado_por=coordinador)
```

### `requerir_documentos(analista, observacion)`

Requiere documentos adicionales al ciudadano. Aplica desde revisión (202), para reiterar un requerimiento (203→203) y para rechazar una subsanación (204→203).

**Validaciones:**

1. `_assert_activo()` — estado activo
1. `_validate_transition(REQUERIMIENTO)` — transición (202→203, 203→203 o 204→203) válida
1. `_assert_asignado_a(analista)` — el trámite debe estar asignado al usuario que ejecuta

**Ejemplo:**

```python
tramite.requerir_documentos(
    analista=request.user,
    observacion='Falta comprobante de domicilio actualizado',
)
```

### `enviar_a_firma(analista, observacion)`

Pone el trámite en fase de campo (inspecciones, mediciones, etc.).

**Validaciones:** mismas que `requerir_documentos`, pero validando transición (202→205).

**Ejemplo:**

```python
tramite.enviar_a_firma(
    analista=request.user,
    observacion='Se requiere inspección ocular del inmueble',
)
```

### `cancelar(analista, estatus_cierre, observacion)`

Cancela el trámite con un estatus terminal. Es la acción más estricta: requiere observación obligatoria.

**Validaciones:**

1. `observacion` debe ser texto no vacío (si no, `ValueError`)
1. `estatus_cierre` debe ser `POR_RECOGER` (301), `RECHAZADO` (302) o `CANCELADO` (304)
1. `_assert_activo()` — estado activo
1. `_validate_transition(estatus_cierre)` — transición válida
1. Desde 202/203/204: `_assert_asignado_a(analista)` — asignado al usuario que ejecuta
1. Desde 205 (`EN_DILIGENCIA`): solo el coordinador/administrador/superuser puede cancelar; un analista recibe `PermissionDenied` aunque esté asignado

**Ejemplo:**

```python
# Cierre positivo (301): solo desde EN_DILIGENCIA (205) y solo coordinador/administrador
tramite.cancelar(
    analista=request.user,  # coordinador
    estatus_cierre=TramiteEstatus.Estatus.POR_RECOGER,
    observacion='Firma completada. Listo para entrega.',
)
```

> **Regla del coordinador (estatus 205):** `cancelar()` es la única acción disponible desde `EN_DILIGENCIA` (205), y solo puede ejecutarla el coordinador, administrador o superuser — un analista (incluso si es el asignado) recibe `PermissionDenied`. Además, la liberación está bloqueada en 205: `_liberar()` lanza `EstadoNoPermitidoError` y `can_release()` retorna `False` para todo rol mientras el trámite esté en diligencia.

### Métodos internos

| Método | Descripción |
|--------|-------------|
| `_assert_activo()` | Lanza `TramiteNoAsignableError` si el estatus no es activo (no está en 201–205) |
| `_assert_asignado_a(usuario)` | Lanza `PermissionDenied` si `asignado_user_id != usuario.id` |
| `_validate_transition(to_status)` | Lanza `EstadoNoPermitidoError` si `(from, to)` no está en `TRANSITIONS` |
| `_liberar(liberado_por, observacion)` | Caso interno de `asignar(None, ...)` — solo valida `_assert_activo()` |
| `_asignar_analista(analista, asignado_por, observacion)` | Caso interno de `asignar(user, ...)` — valida transición |
| `registrar_actividad(estatus_id, analista_id, observacion)` | Crea un registro en la tabla `Actividades` (APPEND_ONLY) |

**Excepción notada:** `_liberar()` usa `_assert_activo()` pero **no** `_validate_transition()`. La liberación es un "reset" que puede aplicarse desde cualquier estado activo, y la transición `(activo, 201)` no siempre está en `TRANSITIONS`. El sistema confía en que `_assert_activo()` es suficiente.

## 4. Permisos por Estado

Los permisos se controlan mediante métodos en el modelo `Tramite` (patrón Fat Models). Cada método evalúa el rol del usuario y el estado actual.

### Métodos de permisos

| Método | Retorna | Descripción |
|--------|---------|-------------|
| `can_view(user)` | `bool` | ¿Puede ver el detalle del trámite? |
| `can_download(user)` | `bool` | ¿Puede descargar documentos? |
| `can_assign(user)` | `bool` | ¿Puede asignar/reasignar? |
| `can_release(user)` | `bool` | ¿Puede liberar al pool? |
| `can_execute_action(user)` | `bool` | ¿Puede ejecutar acciones de workflow? |
| `available_actions(user)` | `list[str]` | Lista de acciones disponibles según rol + estatus |

### Matriz de permisos por rol

#### Ver y descargar

| Rol | `can_view()` | `can_download()` |
|-----|-------------|-----------------|
| Superuser / Administrador | Siempre | Siempre |
| Coordinador | Siempre | Siempre |
| Analista | Solo si está asignado al trámite | Si asignado, o si trámite disponible y activo |

#### Gestionar asignaciones

| Rol | `can_assign()` | `can_release()` |
|-----|---------------|----------------|
| Superuser / Administrador | ✅ | ✅ |
| Coordinador | ✅ | ✅ |
| Analista | ❌ | ❌ |

#### Ejecutar acciones de workflow

| Rol | `can_execute_action()` |
|-----|----------------------|
| Superuser / Administrador | Siempre |
| Coordinador | Siempre |
| Analista | Solo si está asignado al trámite |

### Acciones disponibles por estatus

El método `available_actions(user)` combina `can_execute_action()` con el estatus actual:

| Estatus actual | Acciones disponibles |
|----------------|---------------------|
| `EN_REVISION` (202) | `['requerir_documentos', 'enviar_a_firma', 'cancelar']` |
| `REQUERIMIENTO` (203) | `['requerir_documentos' (reiterar), 'cancelar']` |
| `SUBSANADO` (204) | `['requerir_documentos', 'enviar_a_firma', 'cancelar']` |
| `EN_DILIGENCIA` (205) | `['cancelar']` — solo coordinador/administrador; analista: `[]` |
| Otro estatus | `[]` (sin acciones) |

Si `can_execute_action(user)` retorna `False`, `available_actions` retorna `[]` independientemente del estatus. En `EN_DILIGENCIA` (205) la acción `cancelar` solo se ofrece a coordinadores/administradores/superusers; para un analista retorna `[]` incluso si está asignado.

### Consumidores de permisos

| Consumidor | Métodos usados |
|------------|---------------|
| `tramites/admin.py` (change_view) | `can_view()` para protección IDOR; `available_actions()` para POST y template |
| `tramites/admin.py` (liberar_rapido) | `can_release()` |
| `tramites/admin.py` (acciones_disponibles) | `can_release()` para mostrar botón de liberar |
| `tramites/views.py` (download_requisito_pdf) | `can_download()` |
| `templates/admin/tramite_detail.html` | `{% if 'accion' in available_actions %}` para botones condicionales |

## 5. Flujo Típico

Este es el recorrido completo de un trámite desde que llega al backoffice hasta su cancelación:

### Paso 1: Llegada al backoffice (estado 201 — PRESENTADO)

El ciudadano completa su trámite en el portal externo y confirma el pago. El sistema externo cambia el estatus a `PRESENTADO` (201). El trámite aparece en el listado de **Trámites Disponibles** (`Disponible`) sin analista asignado.

```
asignado_user_id = NULL
estatus = 201 (PRESENTADO)
```

### Paso 2: Asignación (201 → 202)

Un **Coordinador** asigna el trámite a un analista, o un **Analista** lo autoasigna desde el listado de disponibles.

```python
# Coordinador asigna
tramite.asignar(analista=analista_lopez, asignado_por=coordinador_garcia)

# Analista autoasigna
tramite.asignar(analista=analista_lopez, asignado_por=analista_lopez)
```

El trámite pasa a `EN_REVISION` (202) y se asigna `asignado_user_id = analista.id`.

### Paso 3: Revisión — tomar acción

El analista revisa la documentación y puede ejecutar una de tres acciones:

#### Opción A: Requerir documentos (202 → 203)

El expediente tiene información incompleta o errores:

```python
tramite.requerir_documentos(
    analista=analista_lopez,
    observacion='Falta acta de nacimiento actualizada',
)
```

El estatus cambia a `REQUERIMIENTO` (203). Desde este estado, la única acción disponible es `cancelar`.

#### Opción B: Enviar a firma (202 → 205)

Se requiere trabajo de campo (inspección, medición):

```python
tramite.enviar_a_firma(
    analista=analista_lopez,
    observacion='Inspección ocular requerida para deslinde',
)
```

El estatus cambia a `EN_DILIGENCIA` (205). El trámite sale del buzón del analista y ya no aparece como disponible; desde este estado, la única acción disponible es `cancelar`, y solo puede ejecutarla el coordinador o administrador.

#### Opción C: Cerrar directamente (202 → 302/304)

La resolución es negativa, o el ciudadano solicita la cancelación:

```python
# Rechazo
tramite.cancelar(
    analista=analista_lopez,
    estatus_cierre=TramiteEstatus.Estatus.RECHAZADO,
    observacion='No cumple con los requisitos del artículo 14.',
)

# Cancelación
tramite.cancelar(
    analista=analista_lopez,
    estatus_cierre=TramiteEstatus.Estatus.CANCELADO,
    observacion='Solicitud de cancelación por el ciudadano.',
)
```

> **Nota:** `POR_RECOGER` (301) no es alcanzable desde 202. Un dictamen positivo se tramita con `enviar_a_firma()` (202→205) y el cierre a 301 lo ejecuta el coordinador desde diligencia.

### Paso 4: Cierre desde estados intermedios (203/204 → 302/304; 205 → 301/302/304)

Si el trámite está en `REQUERIMIENTO` (203) o `SUBSANADO` (204), el analista asignado puede cerrarlo con `RECHAZADO` (302) o `CANCELADO` (304). Desde `EN_DILIGENCIA` (205), solo el coordinador o administrador puede cerrar — y es la única ruta hacia `POR_RECOGER` (301):

```python
# Cerrar desde requerimiento (analista asignado)
tramite.cancelar(analista=analista, estatus_cierre=302, observacion='...')

# Cerrar desde diligencia (solo coordinador/administrador)
tramite.cancelar(analista=coordinador, estatus_cierre=301, observacion='...')
```

### Paso 5: Finalización completa (301 → 303)

El estado `POR_RECOGER` (301) indica que el documento está listo. Cuando el ciudadano lo recoge (física o digitalmente), el sistema externo cambia el estatus a `FINALIZADO` (303). **El backoffice no gestiona esta transición.**

### Acciones transversales: Reasignar y Liberar

Un **Coordinador** o **Administrador** puede reasignar desde revisión (202) y liberar desde cualquier estado activo (bloqueado en 205):

```python
# Reasignar a otro analista (202 → 202)
tramite.asignar(analista=analista_martinez, asignado_por=coordinador_garcia)

# Liberar al pool (activo → 201; bloqueado en 205)
tramite.asignar(analista=None, asignado_por=coordinador_garcia)
```

## 6. Proxy Models en el Workflow

Los proxy models (`Buzon`, `Disponible`, `Tramite`, `EnDiligencia`, `Cerrado`) son vistas filtradas del mismo modelo base, diseñadas para controlar qué trámites ve cada rol en el admin de Django.

| Proxy Model | Filtros | Roles | Sección en sidebar |
|-------------|---------|-------|--------------------|
| `Tramite` | Estatus activos (201–205) | Administrador, Coordinador | "Trámites en curso" |
| `Buzon` | `asignado_user_id == request.user.id` + activos (excluye 205) | Analista | "Mis trámites" |
| `Disponible` | `asignado_user_id IS NULL` + estatus 201 (excluye 205) | Todos los roles | "Disponibles" |
| `EnDiligencia` | Estatus `EN_DILIGENCIA` (205) | Coordinador, Administrador | "En diligencia" |
| `Cerrado` | Estatus finalizados (301–304) | Coordinador | "Finalizados" |

### Cómo se relacionan con el workflow

```mermaid
graph LR
    subgraph "Estados del Trámite"
        P201["PRESENTADO<br/>(201)"]
        P202["EN REVISIÓN<br/>(202)"]
        P203["REQUERIMIENTO<br/>(203)"]
        P205["EN DILIGENCIA<br/>(205)"]
        F301["POR RECOGER<br/>(301)"]
        F302["RECHAZADO<br/>(302)"]
        F303["FINALIZADO<br/>(303)"]
        F304["CANCELADO<br/>(304)"]
    end

    subgraph "Proxy Models"
        D["Disponible"]
        B["Buzon"]
        T["Tramite"]
        E["EnDiligencia"]
        C["Cerrado"]
    end

    P201 --> D
    P202 --> B
    P202 --> T
    P203 --> T
    P205 --> T
    P205 --> E
    F301 --> C
    F302 --> C
    F303 --> C
    F304 --> C
```

### Definiciones

#### `Disponible` — Trámites sin asignar

Solo muestra trámites en estatus `PRESENTADO` (201) sin analista asignado. El analista puede autoasignarse ("Tomar"), y el coordinador puede asignar a un analista específico.

```python
class Disponible(Tramite):
    class Meta:
        proxy = True
        verbose_name = 'Trámite disponible para autoasignación'
        verbose_name_plural = 'Trámites disponibles'
```

#### `Buzon` — Mis trámites

Solo muestra trámites asignados al usuario actual (`asignado_user_id == request.user.id`) en estados activos, **excluyendo** los que están en `EN_DILIGENCIA` (205). Es la vista principal del analista.

```python
class Buzon(Tramite):
    class Meta:
        proxy = True
        verbose_name = 'Mis trámites'
        verbose_name_plural = 'Buzón de trámites'
```

#### `EnDiligencia` — Trámites en diligencia

Muestra solo trámites en estatus `EN_DILIGENCIA` (205). Visible únicamente para coordinadores y administradores, que desde ahí pueden ejecutar `cancelar()`.

```python
class EnDiligencia(Tramite):
    class Meta:
        proxy = True
        verbose_name = 'Trámite en diligencia'
        verbose_name_plural = 'Trámites en diligencia'
```

#### `Tramite` — Todos los trámites activos

Muestra todos los trámites en estados activos (201–205) sin filtro de asignación. Vista para administradores y coordinadores.

#### `Cerrado` — Trámites finalizados

Muestra trámites en estados terminales (301–304). Solo visible para coordinadores y administradores.

```python
class Cerrado(Tramite):
    class Meta:
        proxy = True
        verbose_name = 'Trámites finalizados'
        verbose_name_plural = 'Trámites finalizados'
```

## 7. Personalización

### Agregar una nueva transición

Para habilitar una transición entre dos estados existentes:

1. **Agregar una fila** a la tabla `WORKFLOW` en `tramites/workflow.py`:

```python
Transition(
    'reanudar_revision',                              # nombre público de la acción
    TramiteEstatus.Estatus.REQUERIMIENTO,             # origen
    TramiteEstatus.Estatus.EN_REVISION,               # destino
    'Reanudar revisión',                              # label para UI/docs
    _ROLES_REVISION,                                  # roles autorizados
),
```

El dict `TRANSITIONS` (derivado) y `available_actions()` se actualizan solos.

2. **Si la acción es nueva** (no reutiliza `requerir_documentos`/`enviar_a_firma`/`cancelar`), agregar el método correspondiente en `Tramite` que valide con `_validate_transition()` y registre la actividad.

1. **Crear un ADR** en `docs/02-DECISIONES/` documentando la razón de la nueva transición.

1. **Agregar tests** en `tests/tramites/`:

```python
def test_requerimiento_to_en_revision():
    """La transición REQUERIMIENTO → EN_REVISION es válida."""
    assert (203, 202) in TRANSITIONS
```

### Agregar un nuevo estado

Los estados viven en la tabla legacy `cat_estatus` y en `TramiteEstatus.Estatus`. Para agregar uno nuevo:

1. **Insertar en la base de datos** (`cat_estatus`) — vía migración SQL o DBA

1. **Agregar la constante** en `TramiteEstatus.Estatus` (`tramites/models/catalogos.py`):

```python
class Estatus(models.IntegerChoices):
    # ... existentes ...
    NUEVO_ESTADO = 206, 'NUEVO ESTADO'
```

3. **Actualizar `es_activo()`** si el nuevo estado es un estado activo:

```python
@classmethod
def es_activo(cls, estatus: int) -> bool:
    return estatus in (
        cls.PRESENTADO,
        cls.EN_REVISION,
        cls.REQUERIMIENTO,
        cls.SUBSANADO,
        cls.EN_DILIGENCIA,
        cls.NUEVO_ESTADO,  # nuevo
    )
```

4. **Agregar transiciones** al dict `TRANSITIONS` según corresponda

1. **Crear un ADR** documentando la decisión (siguiendo el formato MADR en `docs/02-DECISIONES/`)

1. **Actualizar tests y documentación**

### Proceso ADR

Toda modificación al workflow (nueva transición, nuevo estado, cambio de permisos) debe documentarse como un ADR (Architecture Decision Record) en `docs/02-DECISIONES/`. Seguir el formato MADR:

- **Contexto**: qué problema se está resolviendo
- **Opciones consideradas**: alternativas evaluadas
- **Decisión**: qué se eligió y por qué
- **Consecuencias**: impacto esperado (positivo y negativo)

> **Referencia:** [ADR-014: Custom User Model, Workflow Refactoring, Permission Methods](../02-DECISIONES/014-custom-user-workflow-permissions.md)

## Ver también

- [Referencia RBAC](rbac.md) — Roles, permisos y proxy models
- [Modelo de Datos](../01-ARQUITECTURA/03-MODELO-DE-DATOS.md) — Diagrama ERD y acceso a datos
- [Estados de Trámites](./workflow.md) — Descripción detallada de cada estado
- [ADR-014: Workflow Permissions](../02-DECISIONES/014-custom-user-workflow-permissions.md) — Decisión de arquitectura
- [Código fuente](../../tramites/models/tramite.py) — `TRANSITIONS` dict + métodos de acción
- [Catálogo de estatus](../../tramites/models/catalogos.py) — `TramiteEstatus.Estatus`
