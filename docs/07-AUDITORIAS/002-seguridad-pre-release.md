# AUDIT-002: seguridad-previa-al-release

> **Fecha:** 2026-05-04
> **Tipo:** Seguridad
> **Estado:** En Progreso

---

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
2. El `nginx.conf` se sobreescribe con configuración más restrictiva en producción
3. `DJANGO_SECRET_KEY` apropiado configurado
4. `ALLOWED_HOSTS` correctamente configurado (sin wildcard)
5. `DJANGO_DEBUG=False`
6. Variables de entorno correctamente protegidas
7. Credenciales de base de datos gestionadas apropiadamente

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

- **H-002-001:** Open Redirect en `cerrar_tramite_view`
  - **Severidad:** Alto
  - **Evidencia:** `tramites/views.py:127-130` — El parámetro `next` del query string se usa como destino de redirección sin validación. Un atacante puede crear `?next=https://evil.com` para redirigir a un usuario autenticado a un sitio de phishing.
  - **Riesgo:** Robo de credenciales de personal del gobierno mediante redirección maliciosa.
  - **Recomendación:** Validar que `next` sea una URL relativa (sin scheme ni netloc).

### Medios

> Los que deberían corregirse en el corto plazo.

- **H-002-002:** CSP permite `unsafe-inline` para scripts — Protección XSS debilitada
  - **Severidad:** Medio
  - **Evidencia:** `sanfelipe/settings/security.py:84` — `'script-src': [CSP.SELF, CSP.UNSAFE_INLINE]` neutraliza la protección XSS de CSP.
  - **Recomendación:** Migrar a NONCE-based CSP (el código comentado en líneas 85-92 ya tiene el plan). Usar `DJANGO_CSP_REPORT_ONLY=True` primero para monitorear.

- **H-002-003:** `assert` usado para verificación de seguridad (eliminado en modo optimizado)
  - **Severidad:** Medio
  - **Evidencia:** `tramites/sftp.py:225-227` — `assert '..' not in cache_path_for_nginx`. Si se ejecuta con `PYTHONOPTIMIZE=1`, este check desaparece.
  - **Recomendación:** Reemplazar con `if/raise` explícito.

- **H-002-004:** Nginx location blocks sobreescriben headers de seguridad para archivos estáticos
  - **Severidad:** Medio
  - **Evidencia:** `nginx/nginx.conf:147-151, 159-163` — Los bloques `/static/` y `/media/` usan `add_header Cache-Control`, lo que hace que nginx NO herede los headers de seguridad del bloque `server`.
  - **Nota:** En producción el nginx.conf se sobreescribe, pero el template base debería ser correcto.
  - **Recomendación:** Re-agregar `X-Content-Type-Options nosniff always` y `X-Frame-Options DENY always` en cada location block.

### Bajos

> Mejoras deseables pero no urgentes.

- **H-002-005:** Race condition (TOCTOU) en transiciones de estado del workflow
  - **Severidad:** Bajo
  - **Evidencia:** `tramites/models/tramite.py:359-395` — Las acciones de workflow siguen un patrón check-then-act sin locking a nivel base de datos.
  - **Recomendación:** Aceptable para un backoffice gubernamental con baja concurrencia. Considerar `select_for_update()` si escala.

- **H-002-006:** Vista `asignar_rol` carece de verificación explícita de permisos
  - **Severidad:** Bajo
  - **Evidencia:** `core/views.py:46` — Solo usa `@staff_member_required`, no verifica que el usuario tenga permisos de gestión de roles.
  - **Recomendación:** Agregar verificación de `is_superuser or is_administrador`.

- **H-002-007:** `X-Forwarded-For` confiado sin validación de proxy
  - **Severidad:** Bajo
  - **Evidencia:** `tramites/views.py:209-226` — `_get_client_ip` confía en el header sin validar que la request vino a través de un proxy confiable.
  - **Recomendación:** Gunicorn escucha en `127.0.0.1`, mitigando el riesgo. Considerar usar `REMOTE_ADDR` directamente.

- **H-002-008:** Excepción no manejada en `modificar_asignacion` para ID de analista inválido
  - **Severidad:** Bajo
  - **Evidencia:** `tramites/admin.py:408` — `User.objects.get(id=analista_id)` sin try/except.
  - **Recomendación:** Envolver en try/except con `User.DoesNotExist, ValueError`.

- **H-002-009:** `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` por defecto en `False` incluso en producción
  - **Severidad:** Bajo
  - **Evidencia:** `sanfelipe/settings/security.py:53-55` — Los defaults son `False` en producción.
  - **Recomendación:** Cambiar defaults a `True` para producción.

## 5. Acciones Correctivas

| Hallazgo | Acción | Responsable | Estado | Fecha límite |
|----------|--------|-------------|--------|--------------|
| H-002-001 | Validar que `next` sea URL relativa (sin scheme/netloc) | dev | Pendiente | 2026-05-05 |
| H-002-002 | Migrar CSP a NONCE-based (primero en report-only) | dev | Pendiente | 2026-05-15 |
| H-002-003 | Reemplazar `assert` con `if/raise` en sftp.py | dev | Pendiente | 2026-05-05 |
| H-002-004 | Re-agregar headers de seguridad en location blocks de nginx | dev | Pendiente | 2026-05-05 |
| H-002-005 | Documentar como riesgo aceptado (baja concurrencia) | dev | Pendiente | 2026-05-10 |
| H-002-006 | Agregar verificación de permisos en `asignar_rol` | dev | Pendiente | 2026-05-10 |
| H-002-007 | Usar `REMOTE_ADDR` directamente en auditoría | dev | Pendiente | 2026-05-10 |
| H-002-008 | Agregar try/except para `User.DoesNotExist` en admin | dev | Pendiente | 2026-05-10 |
| H-002-009 | Cambiar defaults de cookies seguras a `True` en producción | dev | Pendiente | 2026-05-10 |

## 6. Métricas

| Métrica | Baseline | Post-corrección | Delta |
|---------|----------|----------------|-------|
| Hallazgos Críticos | 0 | — | — |
| Hallazgos Altos | 1 | Pendiente | — |
| Hallazgos Medios | 3 | Pendiente | — |
| Hallazgos Bajos | 5 | Pendiente | — |
| Total hallazgos | 9 | Pendiente | — |
| Protección IDOR | 100% views cubiertas | — | — |
| SQL Injection | 0 (ORM exclusivo) | — | — |
| Path Traversal SFTP | 5 capas de defensa | — | — |
| Validación SECRET_KEY | Shannon entropy + patterns | — | — |

## 7. Decisiones Derivadas

- Ninguna. Las correcciones se implementan dentro de la arquitectura existente.

## 8. Documentos Relacionados

- [`audit-template.md`](audit-template.md) — Template utilizado para esta auditoría
- [`001-calidad-de-pruebas.md`](001-calidad-de-pruebas.md) — Auditoría de calidad de pruebas (344 tests, 100% pass rate)

---

## Hallazgos Positivos (Fortalezas de Seguridad)

1. **Defensa SFTP Path Traversal ejemplar** — Regex anclado, caracteres prohibidos, `O_NOFOLLOW`, `_is_within_cache()`, archivos atómicos, límite de tamaño, verificación de host key.
2. **Protección IDOR completa** — Todas las views validan permisos a nivel objeto (`can_view`, `can_download`, `can_execute_action`).
3. **Protección de superusuarios en admin** — Non-superusers no pueden editar, eliminar ni cambiar passwords de superusuarios.
4. **Validación de SECRET_KEY con entropía Shannon** — Impide que la app arranque con clave débil en producción.
5. **Zero raw queries** — Todo el acceso a BD usa Django ORM (SQL injection imposible).
6. **Verificación de host key SFTP** — `RejectPolicy` obligatorio en producción.
7. **Rate limiting en nginx** — Login (5 req/min) y tramites (10 req/min).
8. **Sesiones con cookies firmadas** — Sin almacenamiento server-side, 1 hora de expiración, HttpOnly + SameSite=Lax.
9. **Argon2 como hasher primario** — Ganador del Password Hashing Competition, mínimo 10 caracteres.
10. **Máquina de estados de workflow** — `TRANSITIONS` dict valida todas las transiciones de estado.
11. **Gunicorn como non-root** — Entrypoint ejecuta gunicorn como `appuser`.
12. **Headers Content-Disposition seguros** — Filename validado por regex estricto.
13. **Páginas de error sin fuga de información** — Custom handlers sin stack traces.
14. **Logging de auditoría** — Descargas y acciones de workflow registradas con user, tramite, IP, estado.
