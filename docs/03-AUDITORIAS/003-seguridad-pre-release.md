# AUDIT-003: seguridad-previa-al-release

> **Fecha:** 2026-05-05
> **Tipo:** Seguridad
> **Estado:** Completada

______________________________________________________________________

## 1. Objetivo

Evaluar la postura de seguridad del código de la aplicación Backoffice de Trámites previo al release a producción, identificando vulnerabilidades según OWASP Top 10 y mejores prácticas de seguridad Django.

## 2. Alcance

**Incluye:**

- Todo el código Python (models, views, admin, middleware, forms, SFTP service, settings)
- Configuración de nginx (`nginx/nginx.conf`) — template base (en producción se sobreescribe con config más restrictiva)
- Script de entrypoint Docker (`docker/entrypoint.sh`)
- Autenticación, autorización, RBAC
- Pipeline de descarga SFTP (prevención de path traversal, caché, X-Accel-Redirect)
- Configuración CSP y headers de seguridad
- Gestión de sesiones y CSRF
- Validación de inputs y sanitización
- Routing de base de datos y separación de schemas
- Manejo de errores y fuga de información

**Excluye:**

- Archivo `.env` (no accesible en el repositorio)
- `Dockerfile` (excluido por decisión del equipo)
- `docker-compose.yml` (excluido por decisión del equipo)
- Paquetes de terceros (se asumen confiables)
- Configuración de producción de `.env` (se asume HTTPS, ALLOWED_HOSTS, SECRET_KEY correctos)

**Suposiciones de producción:**

1. HTTPS habilitado via nginx/proxy externo
1. El `nginx.conf` se sobreescribe con configuración más restrictiva en producción
1. `DJANGO_SECRET_KEY` apropiado configurado
1. `ALLOWED_HOSTS` correctamente configurado (sin wildcard)
1. `DJANGO_DEBUG=False`
1. Variables de entorno correctamente protegidas
1. Credenciales de base de datos gestionadas apropiadamente

## 3. Metodología y Criterios de Evaluación

Evaluación manual del código fuente contra OWASP Top 10 (2021) y mejores prácticas de seguridad Django.

| Criterio | Umbral aceptable | Referencia |
|----------|-----------------|------------|
| Inyección (SQL, Command, Path Traversal) | 0 hallazgos | OWASP A03:2021 |
| Autenticación rota | 0 hallazgos críticos | OWASP A07:2021 |
| Exposición de datos sensibles | 0 hallazgos | OWASP A02:2021 |
| Control de acceso roto (IDOR) | 0 hallazgos | OWASP A01:2021 |
| Configuración de seguridad | Headers completos, CSP efectivo | OWASP A05:2021 |
| XSS | CSP sin unsafe-inline idealmente | OWASP A03:2021 |
| CSRF | Protección en todos los formularios | OWASP A01:2021 |

## 4. Hallazgos

### Críticos

> No se encontraron hallazgos críticos.

### Altos

> Los que degradan significativamente la seguridad o permiten explotación dirigida.

- **H-003-001:** ~~Open Redirect en `cancelar_tramite_view`~~ ✅ **Corregido**
  - **Severidad:** Alto
  - **Evidencia:** `tramites/views.py:127-130` — El parámetro `next` del query string se usaba como destino de redirección sin validación.
  - **Riesgo:** Robo de credenciales de personal del gobierno mediante redirección maliciosa.
  - **Corrección:** Agregada función `_safe_redirect_url()` que valida que `next` sea URL relativa (sin scheme ni netloc). Testeado con 12 casos.
  - **Tests:** `tests/sanfelipe/test_security_audit.py::TestSafeRedirectUrl` (12 tests)

### Medios

> Los que deberían corregirse en el corto plazo.

- **H-003-002:** CSP permite `unsafe-inline` para scripts — Protección XSS debilitada

  - **Severidad:** Medio
  - **Estado:** Pendiente — requiere migración gradual
  - **Evidencia:** `sanfelipe/settings/security.py:84` — `'script-src': [CSP.SELF, CSP.UNSAFE_INLINE]` neutraliza la protección XSS de CSP.
  - **Plan:** Migrar a NONCE-based CSP (código comentado en líneas 85-92 tiene el plan). Usar `DJANGO_CSP_REPORT_ONLY=True` primero para monitorear.
  - **Tests:** `tests/sanfelipe/test_security_audit.py::TestCSPSecurityDirectives` (6 tests validan directivas SÍ configuradas)

- **H-003-003:** ~~`assert` usado para verificación de seguridad~~ ✅ **Corregido**

  - **Severidad:** Medio
  - **Evidencia:** `tramites/sftp.py:225-227` — `assert '..' not in cache_path_for_nginx` se eliminaba con `PYTHONOPTIMIZE=1`.
  - **Corrección:** Reemplazado con `if '..' in cache_path_for_nginx: raise SFTPConnectionError(...)`.
  - **Tests:** `tests/sanfelipe/test_security_audit.py::TestPathTraversalDefenseInDepth` (3 tests)

- **H-003-004:** ~~Nginx location blocks sobreescriben headers de seguridad~~ ✅ **Corregido**

  - **Severidad:** Medio
  - **Evidencia:** `nginx/nginx.conf:147-151, 159-163` — Los bloques `/static/` y `/media/` usaban `add_header Cache-Control` sin re-incluir headers de seguridad.
  - **Corrección:** Agregados `X-Content-Type-Options nosniff always` y `X-Frame-Options DENY always` en ambos location blocks.
  - **Nota:** En producción el nginx.conf se sobreescribe, pero el template base ahora es correcto.

### Bajos

> Mejoras deseables pero no urgentes.

- **H-003-005:** Race condition (TOCTOU) en transiciones de estado del workflow

  - **Severidad:** Bajo
  - **Estado:** Riesgo aceptado
  - **Evidencia:** `tramites/models/tramite.py:359-395` — Las acciones de workflow siguen un patrón check-then-act sin locking a nivel base de datos.
  - **Justificación:** Aceptable para un backoffice gubernamental con baja concurrencia. Considerar `select_for_update()` si escala.

- **H-003-006:** Vista `asignar_rol` carece de verificación explícita de permisos

  - **Severidad:** Bajo
  - **Estado:** Pendiente
  - **Evidencia:** `core/views.py:46` — Solo usa `@staff_member_required`, no verifica que el usuario tenga permisos de gestión de roles.
  - **Mitigación actual:** La vista es inofensiva sin datos de sesión (cookies firmadas), que solo se establecen via la admin action con permisos.
  - **Tests:** `tests/sanfelipe/test_security_audit.py::TestAsignarRolPermissionCheck` (1 test)

- **H-003-007:** `X-Forwarded-For` confiado sin validación de proxy

  - **Severidad:** Bajo
  - **Estado:** Mitigado por arquitectura
  - **Evidencia:** `tramites/views.py:209-226` — `_get_client_ip` confía en el header sin validar que la request vino a través de un proxy confiable.
  - **Mitigación:** Gunicorn escucha en `127.0.0.1`, haciendo acceso directo muy difícil.
  - **Tests:** `tests/sanfelipe/test_security_audit.py::TestGetClientIP` (4 tests)

- **H-003-008:** ~~Excepción no manejada en `modificar_asignacion` para ID de analista inválido~~ ✅ **Corregido**

  - **Severidad:** Bajo
  - **Evidencia:** `tramites/admin.py:408` — `User.objects.get(id=analista_id)` sin try/except generaba 500.
  - **Corrección:** Agregado try/except con `User.DoesNotExist, ValueError` → redirect con mensaje de error.
  - **Tests:** `tests/sanfelipe/test_security_audit.py::TestModificarAsignacionErrorHandling` (1 test)

- **H-003-009:** ~~`SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` por defecto en `False` incluso en producción~~ ✅ **Corregido**

  - **Severidad:** Bajo
  - **Evidencia:** `sanfelipe/settings/security.py:53-55` — Los defaults eran `False` en producción.
  - **Corrección:** Cambiados defaults a `True` para producción.
  - **Tests:** `tests/sanfelipe/test_security_audit.py::TestProductionCookieDefaults` (3 tests)

## 5. Acciones Correctivas

| Hallazgo | Acción | Responsable | Estado | Fecha límite |
|----------|--------|-------------|--------|--------------|
| H-003-001 | Agregar `_safe_redirect_url()` para validar parámetro `next` | dev | ✅ Resuelto | 2026-05-05 |
| H-003-002 | Migrar CSP a NONCE-based (primero en report-only) | dev | Pendiente | 2026-05-15 |
| H-003-003 | Reemplazar `assert` con `if/raise` en sftp.py | dev | ✅ Resuelto | 2026-05-05 |
| H-003-004 | Re-agregar headers de seguridad en location blocks de nginx | dev | ✅ Resuelto | 2026-05-05 |
| H-003-005 | Riesgo aceptado (baja concurrencia) | dev | Aceptado | — |
| H-003-006 | Agregar verificación de permisos en `asignar_rol` | dev | Pendiente | 2026-05-10 |
| H-003-007 | Mitigado por arquitectura (gunicorn 127.0.0.1) | dev | Aceptado | — |
| H-003-008 | Agregar try/except para `User.DoesNotExist` en admin | dev | ✅ Resuelto | 2026-05-05 |
| H-003-009 | Cambiar defaults de cookies seguras a `True` en producción | dev | ✅ Resuelto | 2026-05-05 |

### Archivos Modificados

| Archivo | Cambio | Hallazgo |
|---------|--------|----------|
| `tramites/views.py` | Agregada `_safe_redirect_url()`, usada en `cancelar_tramite_view` | H-003-001 |
| `tramites/sftp.py` | `assert` → `if/raise` en path traversal check | H-003-003 |
| `nginx/nginx.conf` | Headers de seguridad en `/static/` y `/media/` | H-003-004 |
| `tramites/admin.py` | try/except para `User.DoesNotExist` en `modificar_asignacion` | H-003-008 |
| `sanfelipe/settings/security.py` | Cookies seguras default `True` en producción | H-003-009 |
| `tests/sanfelipe/test_security_audit.py` | 30 tests de regresión de seguridad (nuevo) | Todos |
| `tests/tramites/test_sftp.py` | Actualizado nombre de test (assertion→check) | H-003-003 |

## 6. Métricas

| Métrica | Baseline | Post-corrección | Delta |
|---------|----------|----------------|-------|
| Hallazgos Críticos | 0 | 0 | — |
| Hallazgos Altos | 1 | 0 | -1 |
| Hallazgos Medios | 3 | 1 | -2 |
| Hallazgos Bajos | 5 | 2 | -3 |
| Total hallazgos | 9 | 3 pendientes | -6 resueltos |
| Tests de seguridad | 0 | 30 | +30 |
| Tests totales suite | 344 | 374 | +30 |
| Pass rate | 100% | 100% | — |
| Protección IDOR | 100% views cubiertas | 100% | — |
| SQL Injection | 0 (ORM exclusivo) | 0 | — |
| Path Traversal SFTP | 5 capas de defensa | 5 capas | — |
| Validación SECRET_KEY | Shannon entropy + patterns | Igual | — |

### Cobertura de tests por hallazgo

| Hallazgo | Tests | Clase de test |
|----------|-------|---------------|
| SEC-001 Open Redirect | 12 | `TestSafeRedirectUrl` |
| SEC-002 CSP Config | 6 | `TestCSPSecurityDirectives` |
| SEC-003 Path Traversal | 3 | `TestPathTraversalDefenseInDepth` |
| SEC-006 asignar_rol | 1 | `TestAsignarRolPermissionCheck` |
| SEC-007 X-Forwarded-For | 4 | `TestGetClientIP` |
| SEC-008 Admin exception | 1 | `TestModificarAsignacionErrorHandling` |
| SEC-009 Cookie defaults | 3 | `TestProductionCookieDefaults` |
| **Total** | **30** | — |

## 7. Decisiones Derivadas

- **H-003-005 (Race condition):** Riesgo aceptado. El backoffice gubernamental tiene baja concurrencia (5-10 usuarios simultáneos). Si la aplicación escala, considerar `select_for_update()` con `transaction.atomic()`.
- **H-003-007 (X-Forwarded-For):** Riesgo aceptado. Gunicorn escucha en `127.0.0.1` y nginx es el único proxy. Si la arquitectura cambia (ej. load balancer separado), reconsiderar.
- **H-003-002 (CSP unsafe-inline):** Pendiente migración gradual a NONCE. Se recomienda habilitar `DJANGO_CSP_REPORT_ONLY=True` en producción primero para identificar inline scripts necesarios.

## 8. Documentos Relacionados

- [`audit-template.md`](audit-template.md) — Template utilizado para esta auditoría
- [`001-calidad-de-pruebas.md`](001-calidad-de-pruebas.md) — Auditoría de calidad de pruebas (344 tests, 100% pass rate)
- [`tests/sanfelipe/test_security_audit.py`](../../tests/sanfelipe/test_security_audit.py) — Tests de regresión de seguridad (30 tests)

______________________________________________________________________

## Hallazgos Positivos (Fortalezas de Seguridad)

1. **Defensa SFTP Path Traversal ejemplar** — Regex anclado, caracteres prohibidos, `O_NOFOLLOW`, `_is_within_cache()`, archivos atómicos, límite de tamaño, verificación de host key.
1. **Protección IDOR completa** — Todas las views validan permisos a nivel objeto (`can_view`, `can_download`, `can_execute_action`).
1. **Protección de superusuarios en admin** — Non-superusers no pueden editar, eliminar ni cambiar passwords de superusuarios.
1. **Validación de SECRET_KEY con entropía Shannon** — Impide que la app arranque con clave débil en producción.
1. **Zero raw queries** — Todo el acceso a BD usa Django ORM (SQL injection imposible).
1. **Verificación de host key SFTP** — `RejectPolicy` obligatorio en producción.
1. **Rate limiting en nginx** — Login (5 req/min) y tramites (10 req/min).
1. **Sesiones con cookies firmadas** — Sin almacenamiento server-side, 1 hora de expiración, HttpOnly + SameSite=Lax.
1. **Argon2 como hasher primario** — Ganador del Password Hashing Competition, mínimo 10 caracteres.
1. **Máquina de estados de workflow** — `TRANSITIONS` dict valida todas las transiciones de estado.
1. **Gunicorn como non-root** — Entrypoint ejecuta gunicorn como `appuser`.
1. **Headers Content-Disposition seguros** — Filename validado por regex estricto.
1. **Páginas de error sin fuga de información** — Custom handlers sin stack traces.
1. **Logging de auditoría** — Descargas y acciones de workflow registradas con user, tramite, IP, estado.
