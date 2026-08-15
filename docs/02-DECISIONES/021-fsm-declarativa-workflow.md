# 021: FSM Declarativa para el Workflow de Trámites

**Date:** 14 de agosto de 2026
**Status:** Accepted
**Resolves (partially):** [AUDIT-002 H-002-001](../03-AUDITORIAS/002-limpieza-de-codigo.md) (God Model — la lógica de workflow sale del ORM)
**Supersedes:** [ADR-019](019-service-layer-workflow.md) (Service Layer para Workflow — aceptado en mayo 2026, nunca implementado)
**Related:** [ADR-014](014-custom-user-workflow-permissions.md) (dict `TRANSITIONS` original), [ADR-018](018-backoffice-multi-departamento.md) (`BACKOFFICE_DISABLED_TRANSITIONS`), [workflow.md](../05-DEVELOPERS/workflow.md) (especificación del flujo)

## Contexto y Planteamiento del Problema

Tras la revisión con el cliente (agosto 2026) se detectaron inconsistencias en el flujo de trabajo del Analista. La especificación corregida (`docs/05-DEVELOPERS/workflow.md`, 14-ago-2026) introduce requisitos que la estructura vigente no puede expresar:

1. **Roles por transición.** El flujo nuevo es rol-dependiente ("205→301 exclusivo de coordinador", "el coordinador hereda las acciones de revisión sin estar asignado"). Un dict `dict[(from,to), bool]` no tiene dónde declarar roles, guardas ni labels; esas reglas vivían dispersas como condicionales en `cancelar()`, `available_actions()` y `can_execute_action()`.
1. **Self-loop 203→203** (reiterar requerimiento): registra actividad sin cambiar de estatus. El diseño actual asume que cada acción cambia el estatus.
1. **Destinos de cierre dependientes del origen.** Desde 202/203/204 solo se cierra a 302/304; 301 es alcanzable únicamente desde 205. El formulario de cancelación ofrecía siempre 301/302/304.
1. **Doble fuente de verdad.** `available_actions()` re-implementaba con `if/elif` lo que `TRANSITIONS` ya declaraba, sin consultarlo — divergencia latente y bug del helper `any()` de cierres.

Además, **ADR-019 (service layer, Accepted, 10-may-2026) nunca se implementó** (no existe `tramites/services.py`), y su diseño conservaba el dict `TRANSITIONS` tal cual, por lo que tampoco resolvía los requisitos nuevos.

Restricciones que se mantienen: `Tramite` mapea a la vista read-only `v_tramites_unificado` (jamás se llama `save()`); el estado se persiste insertando filas en `Actividades` (append-only); `BACKOFFICE_DISABLED_TRANSITIONS` se lee de settings en runtime.

## Opciones Consideradas

- **A) Cambio mínimo (fat model):** editar `TRANSITIONS` + extender el `if/elif` de `available_actions()` + más condicionales de rol en `cancelar()`.
- **B) FSM declarativa en módulo dedicado `tramites/workflow.py`:** tabla de `Transition` (dataclass con acción, origen, destino, roles, guardas) + funciones puras; el modelo delega pero conserva su API pública.
- **C) Intermedio:** dataclass por transición dentro de `tramites/models/tramite.py`.
- **D) Biblioteca externa** (django-fsm-2, viewflow).
- **E) Implementar ADR-019 ahora** (service layer `TramiteWorkflowService`) junto con el cambio de flujo.

### Evaluación

| | A (mínimo) | **B (workflow.py)** | C (in-model) | D (librería) | E (service layer) |
|---|---|---|---|---|---|
| Esfuerzo | S-M | **M** | S-M | L | M-L |
| Riesgo de regresión | Medio | **Medio-bajo** (2 fases) | Medio | Alto | Medio-alto |
| Expresa roles por transición | ✗ (condicionales) | **✓ declarativo** | ✓ | Forzado | ✗ |
| Elimina doble fuente de verdad | ✗ | **✓** | ✓ | Parcial | ✗ |
| Cambia la API de admin/views/templates | No | **No** | No | Sí | Sí |
| Compatible con vista + Actividades | ✓ | **✓** | ✓ | ✗ | ✓ |

**D es inviable:** django-fsm-2/viewflow giran en torno a un campo de estado persistente actualizado en `save()` — incompatible con un modelo unmanaged sobre una vista donde el estado vive en `Actividades`. ADR-014 y ADR-019 ya lo habían descartado.

## Resultado de la Decisión

Opción elegida: **"B — FSM declarativa en `tramites/workflow.py`"**, porque una sola tabla declarativa resuelve roles-por-transición, self-loops y destinos de cierre por origen sin cambiar la API pública del modelo (admin, views, templates y sus tests no cambian de forma de invocación), y respeta la arquitectura read-only/append-only ya establecida.

### Arquitectura

```
tramites/workflow.py            ← ÚNICA FUENTE DE VERDAD
┌────────────────────────────────────────────────────────────┐
│  Transition (frozen dataclass):                             │
│    action, source, target, label, roles,                    │
│    requires_assignment, requires_note,                      │
│    changes_status, offers_action                            │
│                                                             │
│  WORKFLOW: tabla declarativa de transiciones                │
│  TRANSITIONS: dict derivado (compat: tests/_validate)       │
│                                                             │
│  Funciones puras (testeables sin BD):                       │
│    get_disabled_transitions()                               │
│    transitions_from(source)                                 │
│    user_may(user, transition, assigned)                     │
│    offered_actions(user, source, assigned, disabled)        │
│    closure_destinations() / closure_targets(source, dis.)   │
└────────────────────────────────────────────────────────────┘

tramites/models/tramite.py      ← DELEGA, API PÚBLICA INTACTA
┌────────────────────────────────────────────────────────────┐
│  TRANSITIONS = workflow.TRANSITIONS (alias de compat.)      │
│  available_actions() → workflow.offered_actions()           │
│  _validate_transition() usa el dict derivado                │
│  cancelar() valida destinos con workflow.closure_*()        │
│  _assert_revisor_autorizado() implementa la herencia de     │
│    revisión del coordinador (sin requerir asignación)       │
└────────────────────────────────────────────────────────────┘
```

### Ejecución en dos fases

1. **PR 1 — refactor sin cambio de comportamiento:** `workflow.py` reproducía el flujo viejo exacto; el modelo pasa a derivar de la tabla. Verificado con la suite completa en verde **sin modificar un solo test** (512 passed).
1. **PR 2 — flip de datos al flujo refinado:** solo cambian filas de `WORKFLOW` + consumidores derivados (choices de cancelación, queryset de `Disponible`) + tests.

### Decisiones de negocio registradas (fuente: workflow.md 14-ago-2026)

| Cambio | Detalle |
|---|---|
| Self-loop 203→203 | Reiterar requerimiento: registra actividad sin cambio de estatus (`changes_status=False`) |
| 204 (SUBSANADO) es estado de trabajo | Requerir (204→203), enviar a firma (204→205), cerrar (204→302/304) |
| 301 (POR_RECOGER) solo desde 205 | Única ruta: cierre desde diligencia por coordinador/administrador |
| Cierre de revisión acotado | 202/203/204 cierran únicamente a 302/304 |
| Coordinador hereda revisión sin asignación | Nuevo `_assert_revisor_autorizado()`; antes veía los botones pero recibía `PermissionDenied` |
| `Disponible` filtra por 201 | `presentados()`; cierra gap doc↔código (trámites residuales 203/204 sin asignar ya no aparecen como autoasignables) |
| Casos de uso NO habilitados | 203→202 y 203→205 quedan expresamente fuera ("no especificado en requerimientos"); habilitarlos requiere ADR |

## Consecuencias

- **Bueno, porque** hay una sola fuente de verdad: `available_actions()`, validación de transiciones, destinos del dropdown de cancelación y (parcialmente) la documentación derivan de la misma tabla.
- **Bueno, porque** los roles por transición son datos declarativos que integran `BackOfficeRole` de `core/rbac`, reemplazando condicionales dispersos.
- **Bueno, porque** resuelve parcialmente H-002-001 (God Model): la lógica de workflow sale del ORM hacia un módulo puro, testeable sin BD ni modelos.
- **Bueno, porque** la API pública del modelo no cambia — admin, views, templates y la mayoría de tests siguen invocando igual.
- **Bueno, porque** no agrega dependencias externas.
- **Bueno, porque** `BACKOFFICE_DISABLED_TRANSITIONS` ahora filtra destinos realmente alcanzables desde el estado actual (elimina el bug del helper `any()`).
- **Malo, porque** agrega una indirección: el modelo delega en `workflow.py` y mantiene aliases de compatibilidad (`TRANSITIONS`, `_get_disabled_transitions`) que deberán retirarse cuando los imports migren.
- **Malo, porque** el dict derivado `TRANSITIONS` no distingue roles ni acciones: dos filas con el mismo `(source, target)` y distinto permiso colapsarían — si eso ocurre, la validación debe pasar a consultas por acción (`transitions_from` + `user_may`).
- **Malo, porque** la herencia de revisión del coordinador es un cambio de comportamiento (antes `_assert_asignado_a` le bloqueaba la ejecución aunque `available_actions` le mostrara los botones); documentado aquí y en `workflow.md`.

### Estado de ADR-019

ADR-019 queda **superseded**: su objetivo (extraer la lógica del God Model) se alcanza con la alternativa más ligera de este ADR — módulo de funciones puras en lugar de clase `TramiteWorkflowService`, conservando la API del modelo. La intención de "service layer" puede retomarse en el futuro si aparece lógica de orquestación que no quepa en `workflow.py`.

______________________________________________________________________

## Ver también

- [ADR-014: Custom User, Workflow, Permissions](014-custom-user-workflow-permissions.md) — dict `TRANSITIONS` original
- [ADR-018: Backoffice Multi-Departamento](018-backoffice-multi-departamento.md) — `BACKOFFICE_DISABLED_TRANSITIONS`
- [ADR-019: Service Layer para Workflow](019-service-layer-workflow.md) — superseded por este ADR
- [Workflow de Trámites — Guía para Desarrolladores](../05-DEVELOPERS/workflow.md) — especificación del flujo
- [Código fuente](../../tramites/workflow.py) — tabla `WORKFLOW`
