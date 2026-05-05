# AUDIT-002: Limpieza de Código — Antipatrones y Mantenibilidad

> **Fecha:** 2026-05-04
> **Tipo:** Calidad
> **Estado:** Completada

---

## 1. Objetivo

Evaluar la calidad estructural del código del Backoffice de Trámites buscando antipatrones, código sucio y violaciones a las buenas prácticas de Django que dificulten el mantenimiento, la testabilidad y la evolución del sistema.

## 2. Alcance

**Incluye:**
- Modelos (`tramites/models/`, `core/models/`)
- Vistas y URLs (`tramites/views.py`, `core/views.py`, `sanfelipe/urls.py`, `tramites/urls.py`)
- Capa de servicios/utilidades (`tramites/sftp.py`, `tramites/timeline.py`, `core/rbac/`, `core/admin_utils.py`)
- Admin (`tramites/admin.py`, `core/admin.py`)
- Forms (`tramites/forms.py`, `core/forms.py`)
- Configuración (`sanfelipe/settings/`, `*/apps.py`, `core/middleware.py`)
- Templates (`templates/`) y archivos estáticos (`static/`)

**Excluye:**
- Tests (cubiertos en AUDIT-001)
- Corrección funcional (no se evalúa si el código hace lo correcto, sino cómo está escrito)
- Rendimiento en producción (no se midieron tiempos de respuesta)

## 3. Metodología y Criterios de Evaluación

Auditoría automatizada mediante análisis estático de 5 subagentes examinando simultáneamente todas las capas del proyecto. Criterios basados en:

- [Django Coding Style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x) — patrones service layer
- [PEP 8](https://peps.python.org/pep-0008/) y convenciones del proyecto (skill Django)
- Principios SOLID aplicados a Django

| Criterio | Umbral aceptable | Referencia |
|----------|-----------------|------------|
| Funciones > 30 líneas | 0 god functions | Single Responsibility |
| `transaction.atomic()` en writes múltiples | 100% de operaciones batch | Integridad de datos |
| Sin lógica de negocio en vistas/modelos | Service layer para orquestación | Two Scoops |
| Sin código muerto | 0 archivos/clases sin referencia | Clean Code |
| i18n en strings visibles | `{% trans %}` / `gettext_lazy` | Django i18n |
| Sin URLs hardcodeadas | `reverse()` / `{% url %}` | Django URL resolution |
| Type hints en APIs públicas | 100% funciones públicas | PEP 484 |

## 4. Hallazgos

> Total: **131 hallazgos** consolidados de 5 auditorías paralelas.

### Críticos

> Los que comprometen la integridad de datos o bloquean la evolución arquitectónica.

- **H-002-001:** God Model `Tramite` — 481 líneas, 18 métodos, orquestación completa de workflow
  - **Severidad:** Crítico
  - **Evidencia:** `tramites/models/tramite.py:53-481`. Contiene 5 acciones de workflow (`asignar`, `requerir_documentos`, `en_diligencia`, `cerrar`, `registrar_actividad`), 5 checks de permisos, validación de transiciones, y generación de observaciones. No existe `services.py` en todo el proyecto.
  - **Impacto:** Imposible testear workflow sin instanciar modelo. Lógica de negocio atrapada en ORM.

- **H-002-002:** Sin capa de servicios — toda la lógica de negocio vive en modelos y vistas
  - **Severidad:** Crítico
  - **Evidencia:** No existe `tramites/services.py` ni `core/services.py`. El workflow de trámites, la asignación de roles, y la manipulación de grupos de usuario están en modelos (`tramite.py:279-451`) y vistas (`core/views.py:93-108`).
  - **Impacto:** Código duplicado entre `core/views.py` y `core/admin.py` para asignación de roles. Imposible reutilizar lógica desde management commands sin acoplamiento.

- **H-002-003:** Ausencia de `transaction.atomic()` en escrituras batch de usuarios
  - **Severidad:** Crítico
  - **Evidencia:** `core/views.py:93-108` — loop que modifica `groups`, `is_superuser`, `is_staff`, y llama `user.save()` para múltiples usuarios sin transacción. Si falla en el usuario 3 de 5, los primeros 2 quedan modificados.
  - **Impacto:** Estado inconsistente de permisos de usuario. Un administrador puede quedar sin grupo o con permisos parciales.

- **H-002-004:** Ausencia de `transaction.atomic()` en acción batch de trámites
  - **Severidad:** Crítico
  - **Evidencia:** `tramites/admin.py:382-433` — `modificar_asignacion` procesa múltiples trámites en loop, creando registros de `Actividades` para cada uno sin transacción.
  - **Impacto:** Asignación parcial de trámites. Algunos trámites quedan asignados y otros no.

### Altos

> Los que degradan significativamente la mantenibilidad o seguridad.

- **H-002-005:** God Method `TramiteBaseAdmin.change_view` — 122 líneas
  - **Severidad:** Alto
  - **Evidencia:** `tramites/admin.py:463-585` — maneja POST routing, fetching SFTP (3 try/except), construcción de timeline, lookup de usuarios, y ensamblaje de contexto en un solo método.

- **H-002-006:** God Method `SFTPService._create_sftp_connection` — 105 líneas
  - **Severidad:** Alto
  - **Evidencia:** `tramites/sftp.py:551-656` — maneja carga de clave, validación, política de host key, autenticación por clave y por contraseña en un solo método.

- **H-002-007:** N+1 Queries en `historial_actividades` — sin `select_related`
  - **Severidad:** Alto
  - **Evidencia:** `tramites/models/tramite.py:148` — el property retorna queryset sin `.select_related('estatus')`. Cada acceso a `act.estatus.estatus` dispara query adicional. También en `tramites/sftp.py:857,870`.
  - **Impacto:** Escalado O(n) en consultas al mostrar historial.

- **H-002-008:** `on_delete=models.DO_NOTHING` en 10 ForeignKey de modelos de relación
  - **Severidad:** Alto
  - **Evidencia:** `tramites/models/relaciones.py` líneas 36,43,73,80,87,119,126,133,167,174. Todos los FK de tablas pivot usan `DO_NOTHING`.
  - **Impacto:** Sin integridad referencial desde Django. Orphans si se eliminan registros padres fuera de Django.

- **H-002-009:** Inline `onclick` en `403_csrf.html` — violación CSP
  - **Severidad:** Alto
  - **Evidencia:** `templates/403_csrf.html:18` — `onclick="history.back(); return false;"` en conflicto con `django.middleware.csp.ContentSecurityPolicyMiddleware`.

- **H-002-010:** i18n cargado pero `{% trans %}` nunca usado — 4 templates con ~82+ strings hardcodeados
  - **Severidad:** Alto
  - **Evidencia:** `tramite_detail.html` (~40 strings), `tramite_cerrar.html` (~15), `modificar_asignacion.html` (~15), `asignar_tramites.html` (~12). Todas cargan `{% load i18n %}` pero usan cero tags `{% trans %}`.

- **H-002-011:** Acoplamiento core → tramites — 7 imports directos
  - **Severidad:** Alto
  - **Evidencia:** `core/views.py:18-26` importa `Actividad, Categoria, Perito, Requisito, Tipo, TramiteCatalogo, TramiteEstatus` desde `tramites.models`. `core/management/commands/sftp.py` y `simular_pago.py` también importan de tramites.
  - **Impacto:** `core` no es reusable. Management commands de tramites están en app equivocada.

- **H-002-012:** Ausencia de `transaction.atomic()` en `core/admin.py` `save_model`
  - **Severidad:** Alto
  - **Evidencia:** `core/admin.py:196-227` — `save_model` hace `obj.save()` seguido de `groups.remove/add` sin transacción. Si la modificación de grupos falla, el usuario queda con `is_staff=True` pero sin grupo asignado.

### Medios

> Los que deberán corregirse en el corto plazo.

- **H-002-013:** Lógica de estado duplicada entre `admin_utils.py` y `admin_extras.py`
  - **Severidad:** Medio
  - **Evidencia:** Rangos de estatus (100-199=inicio, 200-299=proceso, 300-399=finalizado) duplicados en `core/admin_utils.py:40-47` y `tramites/templatetags/admin_extras.py:25-31`.

- **H-002-014:** Patrón de check de rol duplicado en 4 admin classes
  - **Severidad:** Medio
  - **Evidencia:** `tramites/admin.py:613,654,700,744` — `obj is None and (user.is_analista or user.is_coordinador or user.is_administrador)` repetido en 4 clases.

- **H-002-015:** Filtro de queryset duplicado en 3 admin classes
  - **Severidad:** Medio
  - **Evidencia:** `tramites/admin.py:621-629,673-681,717-724` — filtro `ultima_actividad_estatus_id__gte/__lt` copiado 3 veces.

- **H-002-016:** `CharField(null=True)` en 28+ campos — dos estados vacíos
  - **Severidad:** Medio
  - **Evidencia:** `tramites/models/tramite.py` (12 campos), `tramites/models/catalogos.py` (16 campos). Genera ambigüedad `None` vs `''`.

- **H-002-017:** URLs hardcodeadas en Python y templates
  - **Severidad:** Medio
  - **Evidencia:** `tramites/views.py:129` usa `f'/admin/tramites/tramite/{pk}/change/'`. Templates usan `../..` y `/admin/` en vez de `{% url %}`.

- **H-002-018:** Código muerto — `core/urls.py` nunca incluido
  - **Severidad:** Medio
  - **Evidencia:** Todo el archivo `core/urls.py` (16 líneas) define rutas que nunca se incluyen en `sanfelipe/urls.py`.

- **H-002-019:** Template muerto — `asignar_tramites.html` (102 líneas)
  - **Severidad:** Medio
  - **Evidencia:** `templates/admin/asignar_tramites.html` — nunca renderizado por ninguna vista. Acción `asignar_seleccionados` no existe.

- **H-002-020:** Variable undefined — `queryset_count` en `modificar_asignacion.html`
  - **Severidad:** Medio
  - **Evidencia:** `templates/admin/modificar_asignacion.html:17` usa `{{ queryset_count }}` pero el admin action pasa `queryset`, no `queryset_count`. Se renderiza vacío.

- **H-002-021:** `Session` con cookies firmadas + listas de usuarios en sesión = riesgo de overflow
  - **Severidad:** Medio
  - **Evidencia:** `settings:345` usa `signed_cookies` y `core/admin.py:233` guarda `selected_user_ids` (lista) en sesión. Selecciones grandes pueden exceder 4KB.

- **H-002-022:** Branding duplicado/conflictivo del admin site
  - **Severidad:** Medio
  - **Evidencia:** `core/admin.py:29-31` setea `'Backoffice San Felipe'` y `sanfelipe/apps.py:16-20` setea `'San Felipe Backoffice'`. El valor efectivo depende del orden de carga.

- **H-002-023:** Middleware sin manejo de excepciones en query DB
  - **Severidad:** Medio
  - **Evidencia:** `core/middleware.py:33-35` — `request.user.groups.values_list(...)` sin try/except. Si la DB no está disponible, error 500 en cada request.

- **H-002-024:** God functions adicionales (5 funciones > 80 líneas)
  - **Severidad:** Medio
  - **Evidencia:** `modificar_asignacion` (96 líneas), `_cleanup_cache` (139 líneas), `_list_files` (91 líneas), `asignar_rol` (80 líneas).

- **H-002-025:** Type hints ausentes en APIs públicas
  - **Severidad:** Medio
  - **Evidencia:** `core/admin_utils.py` (3 funciones), `tramites/timeline.py:12-16` (`build_timeline_entries`), múltiples métodos en `tramites/admin.py` y `core/admin.py`.

- **H-002-026:** `except Exception` amplio sin `exc_info=True` en 3 vistas
  - **Severidad:** Medio
  - **Evidencia:** `tramites/views.py:153-155`, `tramites/admin.py:512-518`, `tramites/admin.py:393,420,458`. Los catch-all pierden stack traces.

- **H-002-027:** Strings hardcodeados sin `gettext`/`gettext_lazy` en modelos
  - **Severidad:** Medio
  - **Evidencia:** Todos los modelos — strings como `f'El trámite {self.folio} ya no se encuentra activo'` y todos los `verbose_name`/`help_text` sin envolver en `_()`.

- **H-002-028:** Validación ausente en `CerrarTramiteForm.observacion`
  - **Severidad:** Medio
  - **Evidencia:** `tramites/forms.py:53-63` — `observacion` es `required=True` pero acepta 1 carácter o solo whitespace.

- **H-002-029:** Inline CSS en templates — violación CSP y duplicación
  - **Severidad:** Medio
  - **Evidencia:** `tramite_detail.html:5-14` (bloque `<style>` inline), `dashboard_cards.html:6,10,20` (3 inline `style=` con colores dinámicos), `modificar_asignacion.html:35` y `asignar_tramites.html:32` (style duplicado).

- **H-002-030:** CSS sin minificar (24 KB) y sin cache-busting
  - **Severidad:** Medio
  - **Evidencia:** `static/admin/css/backoffice.css` — 866 líneas sin minificar. No hay `ManifestStaticFilesStorage` configurado.

- **H-002-031:** Templates de error duplican estructura de `base_error.html`
  - **Severidad:** Medio
  - **Evidencia:** `templates/errors/base_error.html` define bloque content parametrizado, pero `403.html`, `404.html`, `500.html`, `403_csrf.html` sobreescriben completamente el bloque. El base es código muerto.

### Bajos

> Mejoras deseables pero no urgentes.

- **H-002-032:** Código muerto: `CachedCatalogManager` (52 líneas nunca usadas)
  - **Severidad:** Bajo
  - **Evidencia:** `tramites/models/managers.py:47-98`

- **H-002-033:** `CharField` en vez de `EmailField`/`URLField`
  - **Severidad:** Bajo
  - **Evidencia:** `catalogos.py:164` (`correo`), `tramite.py:91` (`solicitante_correo`), `catalogos.py:47` (`url`)

- **H-002-034:** `verbose_name` ausente en 22 campos de `Tramite`
  - **Severidad:** Bajo
  - **Evidencia:** `tramites/models/tramite.py:59-133` — inconsistentes con `catalogos.py` que sí los define.

- **H-002-035:** `ordering` inconsistente — tuples vs lists
  - **Severidad:** Bajo
  - **Evidencia:** `tramite.py:140` usa `('nombre',)` pero `actividades.py:101` usa `['actividad']`.

- **H-002-036:** Constante `ERROR_TEMPLATE_MAP` definida pero nunca usada
  - **Severidad:** Bajo
  - **Evidencia:** `core/views.py:187`

- **H-002-037:** `reverse_lazy()` en cuerpos de funciones (debería ser `reverse()`)
  - **Severidad:** Bajo
  - **Evidencia:** `core/views.py:65,89,115,163`

- **H-002-038:** f-strings en llamadas a logger (11+ instancias)
  - **Severidad:** Bajo
  - **Evidencia:** `core/rbac/__init__.py` (9 instancias), `tramites/admin.py:394,421`, `core/signals.py:18`

- **H-002-039:** `logging.error()` vs `logger.error()` inconsistente
  - **Severidad:** Bajo
  - **Evidencia:** `tramites/models/tramite.py:300` usa `logging.error()` en vez del `logger` del módulo.

- **H-002-040:** Estilo inconsistente de declaración de admin actions
  - **Severidad:** Bajo
  - **Evidencia:** `tramites/admin.py` usa decorador `@admin.action()` (moderno), `core/admin.py` usa atributo `action.short_description =` (legacy).

- **H-002-041:** `delete_model` sin `super()` ni documentación del intento
  - **Severidad:** Bajo
  - **Evidencia:** `core/admin.py:270-273` — soft-delete sin documentar que se omite `super()` intencionalmente.

- **H-002-042:** `ready()` vacío en `TramitesConfig`
  - **Severidad:** Bajo
  - **Evidencia:** `tramites/apps.py:7-9`

- **H-002-043:** `default_auto_field` ausente en `CoreConfig` y `TramitesConfig`
  - **Severidad:** Bajo
  - **Evidencia:** Ninguno define `default_auto_field`; dependen de `SanfelipeConfig`.

- **H-002-044:** `TRAMITE_ESTADOS` y `TRAMITE_PRIORIDADES` en settings — código muerto
  - **Severidad:** Bajo
  - **Evidencia:** `sanfelipe/settings/__init__.py:368-383` — definidos pero nunca usados.

- **H-002-045:** Templates de test en producción (630 líneas)
  - **Severidad:** Bajo
  - **Evidencia:** `test_errors.html`, `test_rendering.html`, `csp_example.html` — rutas protegidas por DEBUG pero archivos presentes en deployment.

- **H-002-046:** `csp_example.html` extiende `base.html` inexistente
  - **Severidad:** Bajo
  - **Evidencia:** `templates/csp_example.html:1` — si se renderiza, causa `TemplateDoesNotExist`. Nunca renderizada.

- **H-002-047:** `BooleanField(null=True)` — tri-state no documentado
  - **Severidad:** Bajo
  - **Evidencia:** `catalogos.py:46,48` — `pago_inicial` y `activo` admiten `None`.

- **H-002-048:** Números mágicos en rangos de estatus
  - **Severidad:** Bajo
  - **Evidencia:** `core/admin_utils.py:40-47` — rangos 100, 200, 300, 400 sin constantes nombradas.

- **H-002-049:** Código comentado en `core/admin.py:331`
  - **Severidad:** Bajo
  - **Evidencia:** Línea con `# return format_html(...)` que debería eliminarse.

- **H-002-050:** Middleware no setea `roles` para usuarios anónimos
  - **Severidad:** Bajo
  - **Evidencia:** `core/middleware.py:33-35` — `request.user.roles` solo se define si `is_authenticated`. Código downstream necesita `getattr(user, 'roles', set())`.

## 5. Acciones Correctivas

> Priorizadas por impacto. Las acciones de prioridad P0 y P1 deben completarse antes del próximo deploy.

| Hallazgo | Acción | Prioridad | Estado | Fecha límite |
|----------|--------|-----------|--------|--------------|
| H-002-001, H-002-002 | Crear `tramites/services/workflow.py` y extraer lógica de workflow del modelo Tramite | P0 | Pendiente | 2026-05-11 |
| H-002-003 | Agregar `transaction.atomic()` en `core/views.py:asignar_rol` POST loop | P0 | Pendiente | 2026-05-06 |
| H-002-004 | Agregar `transaction.atomic()` en `tramites/admin.py:modificar_asignacion` batch loop | P0 | Pendiente | 2026-05-06 |
| H-002-012 | Agregar `transaction.atomic()` en `core/admin.py:save_model` | P0 | Pendiente | 2026-05-06 |
| H-002-005 | Extraer helper methods de `change_view`: `_handle_post_action()`, `_fetch_sftp_files()`, `_build_timeline()` | P1 | Pendiente | 2026-05-11 |
| H-002-006 | Dividir `_create_sftp_connection` en `_connect_with_key()` y `_connect_with_password()` | P1 | Pendiente | 2026-05-11 |
| H-002-007 | Agregar `.select_related('estatus')` a `historial_actividades` y query en `sftp.py` | P1 | Pendiente | 2026-05-08 |
| H-002-009 | Reemplazar inline `onclick` con nonce-based script en `403_csrf.html` | P1 | Pendiente | 2026-05-08 |
| H-002-010 | Envolver strings en `{% trans %}` en 4 templates principales | P1 | Pendiente | 2026-05-15 |
| H-002-017 | Reemplazar URLs hardcodeadas con `reverse()` y `{% url %}` | P2 | Pendiente | 2026-05-15 |
| H-002-018 | Eliminar `core/urls.py` muerto | P2 | Pendiente | 2026-05-08 |
| H-002-019 | Eliminar `asignar_tramites.html` muerto | P2 | Pendiente | 2026-05-08 |
| H-002-020 | Corregir `queryset_count` en context de `modificar_asignacion` | P2 | Pendiente | 2026-05-08 |
| H-002-022 | Consolidar branding en un solo lugar (`core/admin.py`) | P2 | Pendiente | 2026-05-15 |
| H-002-023 | Agregar try/except en `CacheUserRolesMiddleware` | P2 | Pendiente | 2026-05-11 |
| H-002-013 | Extraer `get_status_group()` a `tramites/constants.py` compartido | P2 | Pendiente | 2026-05-15 |
| H-002-014, H-002-015 | Crear mixin `_can_execute_actions()` y `Tramite.objects.en_proceso()` | P2 | Pendiente | 2026-05-15 |
| H-002-025 | Agregar type hints a APIs públicas (`admin_utils`, `timeline`, `admin` filters) | P3 | Pendiente | 2026-05-22 |
| H-002-027 | Envolver strings en `gettext_lazy()` en modelos | P3 | Pendiente | 2026-05-22 |
| H-002-029 | Extraer CSS inline a `backoffice.css` | P3 | Pendiente | 2026-05-22 |
| H-002-038 | Migrar f-strings en logger a `%s` lazy formatting | P3 | Pendiente | 2026-05-22 |

## 6. Métricas

| Métrica | Baseline | Post-corrección | Delta |
|---------|----------|----------------|-------|
| God functions (>30 líneas) | 8 | — | Pendiente |
| Operaciones batch sin `transaction.atomic()` | 4 | — | Pendiente |
| Templates con código muerto | 5 | — | Pendiente |
| Strings sin i18n (modelos + templates) | ~120+ | — | Pendiente |
| URLs hardcodeadas | 8 | — | Pendiente |
| Type hints ausentes en APIs públicas | ~25 funciones | — | Pendiente |
| Líneas de código muerto | ~250+ | — | Pendiente |
| N+1 queries documentados | 3 | — | Pendiente |
| Archivos Python con antipatrones | 15 | — | Pendiente |
| Archivos template con antipatrones | 12 | — | Pendiente |

## 7. Decisiones Derivadas

- **ADR pendiente:** Evaluar adopción de librería de state machine (e.g., `django-fsm`) para el workflow de trámites. La complejidad del modelo `Tramite` lo justifica.
- **ADR pendiente:** Decidir estrategia i18n — si el backoffice será solo español, eliminar `{% load i18n %}` y `gettext_lazy` para reducir ruido. Si se necesita multiidioma, aplicar consistentemente.

## 8. Documentos Relacionados

- [AUDIT-001](001-calidad-de-pruebas.md) — Calidad de pruebas (complementaria)
- [Skill Django](/.agents/skills/django/SKILL.md) — Convenciones de código del proyecto
- [Template de auditoría](audit-template.md) — Formato utilizado

---

### Positivos Destacados

El código no es todo problemas. Se identificaron prácticas sólidas:

- **Jerarquía de excepciones custom** — `TramiteNoAsignableError`, `EstadoNoPermitidoError`, `SFTPConnectionError` bien definidas
- **Sin `print()`, sin `except:` bare, sin `import *`, sin mutables como defaults** — lo básico está limpio
- **SFTPService bien documentado** — docstrings con Args/Returns/Raises
- **Constantes nombradas en `tramites/constants.py`** — `CACHE_TIMEOUT`, `FILE_COUNT_WARNING_THRESHOLD`, `MAX_DOWNLOAD_FILE_SIZE_BYTES`
- **DTOs con dataclasses** — `RequisitoFile`, `ActividadFile`, `TimelineEntry` para transferencia limpia
- **Patrón de registro de modelos** — `@register_model` para routing multi-DB
- **Validación de SECRET_KEY con entropía Shannon** — práctica de seguridad above-average
- **Todos los formularios con `{% csrf_token %}`** — sin excepciones
- **Patrón de máquinas de estado explícito** — `TRANSITIONS` dict con validación
