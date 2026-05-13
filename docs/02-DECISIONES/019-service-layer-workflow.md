# 019: Service Layer para Workflow de Trámites

**Date:** 10 de mayo de 2026
**Status:** Accepted
**Resolves:** [AUDIT-002 H-002-001](../03-AUDITORIAS/002-limpieza-de-codigo.md) (God Model), [AUDIT-002 H-002-002](../03-AUDITORIAS/002-limpieza-de-codigo.md) (Sin service layer), [AUDIT-002 §7](../03-AUDITORIAS/002-limpieza-de-codigo.md) (ADR pendiente: state machine)
**Supersedes (partially):** [ADR-014](014-custom-user-workflow-permissions.md) (sección Workflow — se mantiene el dict `TRANSITIONS` pero la lógica se extrae del modelo)
**Related:** [ADR-018](018-backoffice-multi-departamento.md) (multi-departamento), [PLAN.md](../../PLAN.md) (fase de implementación)

## Contexto y Planteamiento del Problema

El modelo `Tramite` (`tramites/models/tramite.py`) tiene 484 líneas y 18 métodos. Contiene la orquestación completa del workflow de trámites: 5 acciones de workflow (`asignar`, `requerir_documentos`, `en_diligencia`, `cerrar`, `registrar_actividad`), 3 guards internos (`_validate_transition`, `_assert_activo`, `_assert_asignado_a`), 5 métodos de permisos (`can_view`, `can_download`, `can_assign`, `can_release`, `can_execute_action`), y 1 método de UI (`available_actions`). No existe `services.py` en todo el proyecto.

AUDIT-002 clasificó esto como **H-002-001 (Crítico)**: "God Model — lógica de negocio atrapada en ORM" y **H-002-002 (Crítico)**: "Sin capa de servicios". La sección 7 del mismo audit recomienda: "Evaluar adopción de librería de state machine (e.g., `django-fsm`) para el workflow de trámites."

Con la adición de soporte multi-departamento (ADR-018), la complejidad aumenta: se agrega `DISABLED_TRANSITIONS` (per-department filtering), helper functions, y actualizaciones a `available_actions`. Agregar esta complejidad al God Model empeora el problema.

### Restricciones arquitectónicas

1. **`Tramite` es read-only.** Mapea a la vista `v_tramites_unificado` (`managed=False`). Jamás se llama `tramite.save()`.
2. **Los cambios de estado ocurren vía `Actividades.objects.create()`.** Cada acción inserta un registro en la tabla append-only `actividades`.
3. **`TRANSITIONS` dict funciona.** ADR-014 evaluó alternativas (django-fsm, tabla en BD) y eligió el dict. No se necesita cambiar la estructura de datos.
4. **`django-lifecycle` no aplica.** Intercepta `save()`/`delete()` — incompatible con un modelo que nunca se guarda.
5. **Los métodos `can_*` son del dominio del modelo.** Responden "puede este usuario realizar esta acción sobre este trámite?" — son consultas, no mutaciones.

## Opciones Consideradas

* **A) Service layer** — Extraer workflow a `tramites/services.py` con clase `TramiteWorkflowService`
* **B) django-fsm u otra librería FSM** — Decoradores `@transition` en métodos del modelo
* **C) Mantener status quo** — Agregar DISABLED_TRANSITIONS directamente al God Model
* **D) Multi-modelos especializados por departamento** — Abstract `TramiteBase` + concrete `TramiteDAU`/`TramiteSEC`/`TramiteTES` con modelo swappable vía `ACTIVE_TRAMITE_MODEL`

### Evaluación de Opción D: Multi-modelos especializados

**Descripción:** Crear una jerarquía de modelos con `TramiteBase` (abstract, 20 campos compartidos) y modelos concretos por departamento: `TramiteDAU` (+6 campos DAU-specific), `TramiteSEC` (sin campos extra), `TramiteTES` (sin campos extra inicialmente). Selección del modelo activo vía `ACTIVE_TRAMITE_MODEL = env('ACTIVE_TRAMITE_MODEL', default='tramites.TramiteDAU')` (patrón similar a `AUTH_USER_MODEL`). Proxy models generados dinámicamente con `type()`.

**Rechazada por las siguientes razones:**

1. **Vulnerabilidades de seguridad inherentes (2 CRITICAL, 1 HIGH):** `apps.get_model()` desde una variable de entorno sin validación de tipo permite resolver el modelo `Tramite` a cualquier modelo registrado (e.g., `core.User` con `FULL_ACCESS`). Los proxy models generados con `type()` bypassan el registry de `@register_model` (usa identity-based lookup), causando que el DB router caiga a defaults inseguros. No existe validación de que el modelo activo corresponda a la base de datos conectada.

2. **Cero beneficio de seguridad vs. views PostgreSQL:** El aislamiento de datos por departamento ya se logra a nivel de base de datos (instancias separadas con DBs separadas) + views PostgreSQL que retornan `NULL`/`FALSE` para campos no aplicables. Modelos Django separados no agregan ninguna capa adicional de protección.

3. **Incompatibilidad con el metaclass de Django:** `type()` no invoca `ModelBase.__new__()` — los proxies no se registran en `ContentType`, app registry, ni admin. `apps.get_model()` a nivel de módulo causa `AppRegistryNotReady`.

4. **Violación de Open/Closed Principle:** Agregar un departamento requiere crear un nuevo modelo concreto + actualizar imports + actualizar `__init__.py` vs. copiar `.env` + crear DB + deploy Docker container (cero cambios de código con la arquitectura actual).

5. **TramiteSEC y TramiteTES no tienen diferenciación:** Ambas tendrían cero campos extra, métodos `can_*` idénticos (role-based, no department-based), y `TRANSITIONS` dict idéntico. Clases sin diferenciación de comportamiento o estructura son configuración, no clases.

6. **Los 6 campos DAU-specific ya existen con `null=True`:** `tramite_categoria_id`, `tramite_categoria_nombre`, `clave_catastral`, `es_propietario`, `perito_id`, `perito_nombre` ya están en el modelo único. La view SEC retorna `NULL`/`FALSE` para estos campos. No hay cambio necesario.

**Revisión de seguridad (l337-lady):** 11 hallazgos en primera ronda. 4 son inherentes al enfoque multi-modelo (CRITICAL-001: resolución arbitraria, CRITICAL-002: proxies bypass router, HIGH-002: sin validación model↔DB, MEDIUM-001: isinstance() se rompe). Todos se evitan con modelo único.

**Revisión de arquitectura (python-architect):** "Clases que solo difieren en `db_table` son configuración, no clases. El umbral para justificar modelos separados es ~35 campos totales o tipos en conflicto para la misma columna. Actualmente hay 26 campos y ningún conflicto de tipos."

## Resultado de la Decisión

Opción elegida: **"A — Service layer"**, porque resuelve los hallazgos críticos de auditoría (H-002-001, H-002-002), es compatible con la arquitectura read-only, y no agrega dependencias externas.

### Arquitectura

```
tramites/services.py          ← NUEVO
┌─────────────────────────────────────────────────┐
│  Funciones de módulo (puras):                    │
│    _get_disabled_transitions() -> set[int]       │
│    _is_transition_allowed(from, to) -> bool      │
│                                                   │
│  TramiteWorkflowService:                          │
│    __init__(tramite: Tramite, user: User)         │
│    asignar(analista, observacion)                 │
│    requerir_documentos(observacion)               │
│    en_diligencia(observacion)                     │
│    cerrar(estatus_cierre, observacion)            │
│    liberar(observacion)                           │
│    available_actions() -> list[str]               │
│    _validate_transition(to_status)                │
│    _assert_activo()                               │
│    _assert_asignado_a()                           │
│    _registrar_actividad(...)                      │
│    _asignar_analista(analista, ...)               │
└─────────────────────────────────────────────────┘

tramites/models/tramite.py   ← ADELGAZADO
┌─────────────────────────────────────────────────┐
│  TRANSITIONS dict (compartido)                    │
│  class Tramite(models.Model):                     │
│    - campos, Meta, __str__                        │
│    - historial_actividades (property)             │
│    - can_view(), can_download()                   │
│    - can_assign(), can_release()                  │
│    - can_execute_action()                         │
│  class Buzon(Tramite): proxy                      │
│  class Disponible(Tramite): proxy                 │
│  class Cerrado(Tramite): proxy                    │
└─────────────────────────────────────────────────┘
```

### Qué se mueve y qué se queda

**Se mueve a `TramiteWorkflowService`:**

| Método | Líneas actuales | Razón |
|---|---|---|
| `asignar()` | 316-338 | Mutación de estado |
| `_asignar_analista()` | 422-454 | Mutación de estado |
| `_liberar()` | 404-420 | Mutación de estado |
| `requerir_documentos()` | 340-349 | Mutación de estado |
| `en_diligencia()` | 351-360 | Mutación de estado |
| `cerrar()` | 362-398 | Mutación de estado |
| `registrar_actividad()` | 282-310 | Persistencia de estado |
| `_validate_transition()` | 264-280 | Guard de transición |
| `_assert_activo()` | 244-247 | Guard de transición |
| `_assert_asignado_a()` | 249-262 | Guard de transición |
| `available_actions()` | 214-238 | Derivado de transiciones + permisos |

**Se queda en `Tramite`:**

| Elemento | Razón |
|---|---|
| Campos, `Meta`, `__str__` | Definición ORM |
| `historial_actividades` | Property de solo lectura |
| `can_view()`, `can_download()`, `can_assign()`, `can_release()`, `can_execute_action()` | Permission checks — responden "puede este usuario?" |
| `TRANSITIONS` dict | Constante compartida entre modelo y service |
| Proxy models (`Buzon`, `Disponible`, `Cerrado`) | Solo definen Meta alternativas |

### Integración con DISABLED_TRANSITIONS

Las funciones `_get_disabled_transitions()` y `_is_transition_allowed()` viven en `services.py`. El service las usa internamente para:
- `_validate_transition()` — rechazar transiciones deshabilitadas
- `available_actions()` — ocultar botones de acciones deshabilitadas
- Logging de auditoría al instanciar el service

El modelo `Tramite` no conoce `DISABLED_TRANSITIONS` — la configuración per-departamento permanece encapsulada en el service.

### API de consumo

Los consumidores (admin, views) cambian de:

```python
tramite.requerir_documentos(analista, observacion)
actions = tramite.available_actions(user)
```

A:

```python
svc = TramiteWorkflowService(tramite, request.user)
svc.requerir_documentos(observacion)
actions = svc.available_actions()
```

### Tests

| Archivo | Contenido |
|---|---|
| `tests/tramites/test_models.py` | Permisos `can_*`, campos, proxy models |
| `tests/tramites/test_services.py` | **NUEVO** — workflow methods, guards, DISABLED_TRANSITIONS, `available_actions` |

Los tests existentes de workflow (37 en `test_models.py`) se migran a `test_services.py` adaptando el patrón de fixture: en vez de `tramite.requerir_documentos(...)`, usan `svc.requerir_documentos(...)`.

## Consecuencias

* **Bueno, porque** resuelve H-002-001 (God Model) — el modelo baja de ~484 a ~200 líneas
* **Bueno, porque** resuelve H-002-002 (service layer) — la lógica de negocio ya no está atrapada en el ORM
* **Bueno, porque** el workflow es testeable sin instanciar el modelo — solo se necesita un mock del tramite
* **Bueno, porque** `DISABLED_TRANSITIONS` se encapsula en el service — el modelo no conoce departamentos
* **Bueno, porque** no agrega dependencias externas
* **Bueno, porque** los consumidores existentes solo cambian la forma de invocación, no la lógica
* **Malo, porque** agrega una capa de indirección — `TramiteWorkflowService(tramite, user)` en vez de `tramite.metodo(user)`
* **Malo, porque** requiere migrar 37+ tests de workflow de `test_models.py` a `test_services.py`
* **Malo, porque** las transiciones de liberación (`_liberar`) siguen siendo una excepción que no está en `TRANSITIONS`

---

## Ver también

* [ADR-014: Custom User, Workflow, Permissions](014-custom-user-workflow-permissions.md) — Decisión original del dict TRANSITIONS (parcialmente superseded en implementación, no en diseño)
* [ADR-018: Backoffice Multi-Departamento](018-backoffice-multi-departamento.md) — DISABLED_TRANSITIONS
* [AUDIT-002: Limpieza de Código](../03-AUDITORIAS/002-limpieza-de-codigo.md) — H-002-001, H-002-002
* [PLAN.md](../../PLAN.md) — Fase de implementación
