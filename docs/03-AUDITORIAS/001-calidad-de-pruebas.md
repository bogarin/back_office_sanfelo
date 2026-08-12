# AUDIT-001: calidad-de-pruebas-unitarias-integracion

> **Fecha:** 2026-05-02 – 2026-05-04
> **Tipo:** Calidad
> **Estado:** Completada

______________________________________________________________________

## 1. Objetivo

Evaluar la calidad y efectividad de todas las pruebas unitarias y de integración del proyecto Backoffice Trámites para verificar que el suite de tests sea confiable, sin duplicados, sin pruebas placeholder, y con cobertura de los módulos críticos del sistema (workflow de trámites, RBAC, middleware, señales).

## 2. Alcance

**Incluye:**

- Todos los archivos bajo `tests/` (13 archivos, 307 tests)
- Modelos de trámite: workflow, transiciones de estado, permisos
- Core: RBAC, middleware, señales, protección de superusuario
- Infraestructura: DB router, CSP, admin registration
- Fixtures compartidos en `tests/conftest.py`

**Excluye:**

- Tests E2E (no existen aún)
- Cobertura de código por rutas (no se evaluó con `--cov`)
- Performance benchmarks

## 3. Metodología y Criterios de Evaluación

Análisis manual de cada archivo de test contra criterios de calidad: duplicación, efectividad, consistencia de estilo (pytest vs TestCase), y cobertura de lógica de negocio.

| Criterio | Umbral aceptable | Referencia |
|----------|-----------------|------------|
| Pass rate | 100% | Cero tests rotos en CI |
| Sin duplicados | 0 tests duplicados | DRY |
| Sin placeholders | 0 tests `assertTrue(True)` | Valor mínimo |
| Estilo consistente | 100% pytest (sin TestCase) | Convención del proyecto |
| Sin guards silenciosos | 0 `if hasattr` que pasan sin verificar | Tests deben fallar, no pasar |

## 4. Hallazgos

### Críticos

> Los que bloqueaban CI o comprometían la integridad del suite.

- **H-001-001:** 33 tests fallaban por `django-debug-toolbar` en settings de test
  - **Severidad:** Crítico
  - **Evidencia:** `NoReverseMatch: 'djdt' is not a registered namespace` en `test_user_lifecycle.py`, `test_integration.py`, `test_sidebar_permissions.py`, `test_sftp.py`

### Altos

> Los que degradaban significativamente la calidad o mantenibilidad.

- **H-001-002:** 3 archivos de test completamente duplicados (`test_management.py`, `test_integration.py`, `test_views.py`) — ~45 tests redundantes

  - **Severidad:** Alto
  - **Evidencia:** Tests idénticos entre archivos: `test_setup_roles_creates_acceso_perms`, `test_user_with_role_can_access_admin[3]`, `assertTrue(True)`

- **H-001-003:** Bug en `_liberar(asignado_por=None)` — `AttributeError` silencioso en producción

  - **Severidad:** Alto
  - **Evidencia:** `tramites/models/tramite.py` línea 401: `liberado_por.get_full_name()` cuando `liberado_por` es `None`

- **H-001-004:** Test CSP con assertion incorrecta — validaba `CSP.NONCE` en vez de `CSP.SELF`

  - **Severidad:** Alto
  - **Evidencia:** `tests/sanfelipe/test_csp.py` línea 42-51

### Medios

> Los que deberían corregirse en el corto plazo.

- **H-001-005:** `test_error_handling.py` usaba `try/except Exception` sin verificar condición real

  - **Severidad:** Medio
  - **Evidencia:** Líneas 19-25, pasaba sin importar el resultado

- **H-001-006:** Fixtures duplicados en `test_models.py`: `analista` definido 5x, `coordinador` 2x, `tramite_en_revision` 4x

  - **Severidad:** Medio
  - **Evidencia:** Múltiples `@pytest.fixture` con mismo nombre en distintas clases

- **H-001-007:** 3 archivos usaban `TestCase` en vez de pytest (`test_csp.py`, `test_db_router.py`, `test_error_handling.py`)

  - **Severidad:** Medio
  - **Evidencia:** `from django.test import TestCase` + `class TestX(TestCase)`

- **H-001-008:** `test_admin_generic.py` solo verificaba 2 de 5 modelos registrados en admin

  - **Severidad:** Medio
  - **Evidencia:** Solo `Tramite` y `User`, faltaban `Buzon`, `Disponible`, `Cerrado`

### Bajos

> Mejoras deseables pero no urgentes.

- **H-001-009:** 4 de 5 tests CSP tenían `if hasattr` guards que pasaban silenciosamente

  - **Severidad:** Bajo
  - **Evidencia:** `test_csp_blocks_plugins`, `test_csp_blocks_frames`

- **H-001-010:** Sin tests de middleware (`CacheUserRolesMiddleware`)

  - **Severidad:** Bajo
  - **Evidencia:** No existe archivo `test_signals_middleware.py` ni equivalente

- **H-001-011:** Sin tests de señales (`post_migrate` → `setup_roles`)

  - **Severidad:** Bajo
  - **Evidencia:** No hay tests que verifiquen el handler de señal directamente

- **H-001-012:** Sin tests de validaciones del modelo Trámite (state machine, TRANSITIONS, permisos can\_\*)

  - **Severidad:** Bajo
  - **Evidencia:** No existía `test_validations.py`

## 5. Acciones Correctivas

| Hallazgo | Acción | Responsable | Estado | Fecha límite |
|----------|--------|-------------|--------|--------------|
| H-001-001 | Eliminar `debug_toolbar` de `settings_test.py` INSTALLED_APPS y MIDDLEWARE | nnieto | Resuelto | 2026-05-02 |
| H-001-002 | Eliminar 3 archivos duplicados, migrar 4 tests únicos | nnieto | Resuelto | 2026-05-02 |
| H-001-003 | Agregar validación `liberado_por is None → ValueError` en `_liberar` | nnieto | Resuelto | 2026-05-02 |
| H-001-004 | Reescribir test CSP para validar `CSP.SELF` en vez de `CSP.NONCE` | nnieto | Resuelto | 2026-05-02 |
| H-001-005 | Reescribir con 3 tests pytest con asserts reales | nnieto | Resuelto | 2026-05-03 |
| H-001-006 | Consolidar fixtures a nivel módulo (analista 5→1, coordinador 2→1) | nnieto | Resuelto | 2026-05-03 |
| H-001-007 | Migrar `test_csp.py`, `test_db_router.py`, `test_error_handling.py` a pytest | nnieto | Resuelto | 2026-05-04 |
| H-001-008 | Parametrizar 5 modelos registrados en admin | nnieto | Resuelto | 2026-05-04 |
| H-001-009 | Eliminar `if` guards, fallar si CSP no configurado | nnieto | Resuelto | 2026-05-04 |
| H-001-010 | Crear `test_signals_middleware.py` con 8 tests | nnieto | Resuelto | 2026-05-04 |
| H-001-011 | Incluir `post_migrate` signal test en `test_signals_middleware.py` | nnieto | Resuelto | 2026-05-04 |
| H-001-012 | Crear `test_validations.py` con 27 tests | nnieto | Resuelto | 2026-05-04 |

## 6. Métricas

| Métrica | Baseline | Post-corrección | Delta |
|---------|----------|----------------|-------|
| Total tests | 307 | 344 | +37 |
| Pass rate | 89% (273/307) | 100% (344/344) | +11 pp |
| Tests fallando | 34 (11%) | 0 (0%) | -34 |
| Archivos de test | 13 | 12 | -3 eliminados, +2 nuevos |
| Tests duplicados | ~45 | 0 | -45 |
| TestCase legacy | 3 archivos | 0 | -3 |
| Archivos placeholder | 1 (`test_views.py`) | 0 | -1 |
| Cobertura middleware/señales | 0 tests | 8 tests | +8 |
| Cobertura validaciones Trámite | 0 tests | 27 tests | +27 |

## 7. Decisiones Derivadas

Ninguna. La auditoría no generó cambios de arquitectura ni ADRs. Las correcciones fueron a nivel de calidad de pruebas sin impacto en diseño.

## 8. Trabajo Futuro

Áreas identificadas durante la auditoría que quedan fuera del alcance actual pero deberían abordarse en iteraciones futuras:

| Prioridad | Área | Detalle | Criterio de éxito |
|-----------|------|---------|-------------------|
| Media | **Cobertura por rutas (`--cov`)** | Esta auditoría evaluó calidad cualitativa (duplicados, estilo, efectividad). No se midió % de líneas/ramas cubiertas. | ≥ 80% line coverage, ≥ 70% branch coverage |
| Media | **Tests E2E** | No existen tests end-to-end. El flujo completo (login → crear trámite → asignar → cerrar) no está verificado automáticamente. | Al menos 1 smoke test del flujo crítico con Selenium/Playwright |
| Baja | **Performance benchmarks** | No se evaluó tiempo de ejecución del suite. Con 344 tests, un regression en velocidad pasaría desapercibido. | Baseline < 30s total, regression threshold en CI |
| Baja | **Tests de templates** | `test_timeline.py` cubre rendering parcialmente, pero no hay tests dedicados a verificar que los templates rendericen correctamente con datos reales. | Templates críticos con tests de regression visual o snapshots |
| Baja | **Tests de views HTTP** | Las views de SFTP están cubiertas (`test_sftp.py`), pero otras views (dashboard, listados) no tienen tests HTTP dedicados fuera del lifecycle. | Cada view con al menos 1 test de status code + 1 test de permisos |

## 9. Documentos Relacionados

- [audit-template.md](audit-template.md) — Template utilizado para esta auditoría
- [00-ARQUITECTURA/00-REQUERIMIENTOS.md](../01-ARQUITECTURA/00-REQUERIMIENTOS.md) — Requisitos que las pruebas protegen
- Commits: `d72b876`, `f3414c0`, `da50a28`
