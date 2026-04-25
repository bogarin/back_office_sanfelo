# Auditoría de Seguridad en Producción

Esta guía proporciona un checklist completo para realizar auditorías de seguridad antes de desplegar el Backoffice Trámites en producción. Es un **requisito obligatorio** completar esta auditoría y corregir cualquier hallazgo antes del primer deployment en producción.

## ✅ Pre-requisitos

Antes de iniciar la auditoría, asegúrese de:

- [ ] Entorno de producción listo (servidores, base de datos, SFTP)
- [ ] Archivos `.env` de producción configurados con valores seguros
- [ ] Backup de base de datos realizado
- [ ] Equipo de operaciones notificado del deployment

---

## 🔒️ Checklist de Seguridad Crítica

### 1. Validación de Contraseñas

**Ubicación:** `sanfelipe/settings/__init__.py:198`
**Severidad:** CRITICAL — Bloquea producción

**Verificación:**

```bash
# Ejecutar en servidor de producción
python manage.py shell

>>> from sanfelipe.settings import AUTH_PASSWORD_VALIDATORS
>>> print(AUTH_PASSWORD_VALIDATORS)
# Debe mostrar 4 validadores
```

**Resultado esperado:**
```python
[
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

**Si falla:**
- ❌ CRÍTICO: No se puede hacer deploy hasta habilitar validación de contraseñas
- **Fix:** Verificar Fase 1.1 del plan de seguridad

---

### 2. SECRET_KEY Segura

**Ubicación:** `sanfelipe/settings/__init__.py`, `.env`
**Severidad:** CRITICAL — Bloquea producción

**Verificación:**

```bash
# Ejecutar en servidor de producción
python manage.py shell

>>> from sanfelipe.settings import SECRET_KEY, DEBUG
>>> print(f'Longitud: {len(SECRET_KEY)}')
>>> print(f'Entra "insecure": {"insecure" in SECRET_KEY.lower()}')
>>> print(f'Entra "change": {"change" in SECRET_KEY.lower()}')
```

**Resultado esperado:**
- Longitud ≥ 50 caracteres
- NO contiene "insecure"
- NO contiene "change"
- Entropía > 3.0 bits/char (calculada automáticamente por `validate_secret_key`)

**Prueba de entropía:**

```bash
# Generar SECRET_KEY nueva y probar
DJANGO_DEBUG=False DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())") python manage.py check
# Debe cargar sin errores
```

**Si falla:**
- ❌ CRÍTICO: `ImproperlyConfigured` al iniciar Django
- **Fix:** Generar nueva SECRET_KEY con:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
  Y actualizar `.env` con el resultado

---

### 3. Autenticación en Vistas de Asignación de Roles

**Ubicación:** `core/views.py:43, 118`
**Severidad:** CRITICAL — Bloquea producción

**Verificación manual:**

1. Navegar a `/admin/auth/user/asignar-rol/` sin estar logueado
2. **Esperado:** Redirección a `/admin/login/` (no debe mostrar formulario)

**Si falla:**
- ❌ CRÍTICO: Endpoint accesible sin autenticación
- **Fix:** Verificar que `@staff_member_required` está decorando ambas vistas (Fase 1.2)

---

### 4. ALLOWED_HOSTS Configurado

**Ubicación:** `.env`, `sanfelipe/settings/security.py`
**Severidad:** HIGH — Bloquea producción

**Verificación:**

```bash
# Ejecutar en servidor de producción
python manage.py shell

>>> from sanfelipe.settings import ALLOWED_HOSTS, DEBUG
>>> print(f'DEBUG: {DEBUG}')
>>> print(f'ALLOWED_HOSTS: {ALLOWED_HOSTS}')
```

**Resultado esperado:**
- `DEBUG = False`
- `ALLOWED_HOSTS` = [`nombres-de-dominios-reales`, `IPs-del-load-balancer`]
- **NO** `['*']` o lista vacía `[]`

**Si falla:**
- ❌ CRÍTICO: `ImproperlyConfigured` al iniciar Django
- **Fix:** Configurar `DJANGO_ALLOWED_HOSTS` en `.env` con dominios/IPs reales

---

### 5. Rate Limiting en Login

**Ubicación:** `nginx/nginx.conf`
**Severidad:** HIGH — Bloquea producción

**Verificación:**

```bash
# Prueba de fuerza bruta simulada
for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8090/admin/login/ -X POST \
    -d "username=admin&password=wrong$i&csrfmiddlewaretoken=test"
done | sort | uniq -c

# Esperado: Varias respuestas 429 (Too Many Requests) después de 5 intentos
```

**Resultado esperado:**
- 429 aparece después de ~5-6 intentos
- Rate limit: 5 req/min con burst de 3

**Si falla:**
- ❌ HIGH: Ningún límite de rate en `/admin/login/`
- **Fix:** Verificar Fase 2.1 (agregó `limit_req_zone` y `location /admin/login/`)

**Verificación de configuración nginx:**

```bash
# En servidor de producción
docker exec backoffice_nginx cat /etc/nginx/nginx.conf | grep -A10 "location /admin/login/"
```

**Debe mostrar:**
```nginx
location /admin/login/ {
    limit_req zone=auth_limit burst=3 nodelay;
    limit_req_status 429;
    ...
}
```

---

### 6. Headers de Seguridad (Nosniff, XSS-Filter)

**Ubicación:** `sanfelipe/settings/security.py`
**Severidad:** MEDIUM

**Verificación:**

```bash
curl -I http://localhost:8090/admin/login/ 2>&1 | grep -E "(X-Content-Type-Options|X-XSS-Protection)"
```

**Resultado esperado:**
```
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

**Si falla:**
- ⚠️ MEDIUM: Headers faltantes o deshabilitados
- **Fix:** Verificar Fase 2.6 (`SECURE_CONTENT_TYPE_NOSNIFF` y `SECURE_BROWSER_XSS_FILTER` siempre en `True`)

---

### 7. Comando `simular_pago` Bloqueado en Producción

**Ubicación:** `core/management/commands/simular_pago.py`
**Severidad:** MEDIUM

**Verificación:**

```bash
# Intentar ejecutar con DEBUG=False
DJANGO_DEBUG=False python manage.py simular_pago TRM-12345
```

**Resultado esperado:**
```
CommandError: ❌ SEGURIDAD: Este comando SOLO puede ejecutarse en modo DEBUG.
Nunca debe usarse en producción...
```

**Si falla:**
- ⚠️ MEDIUM: Comando permite simular pagos en producción
- **Fix:** Verificar Fase 2.4 (guard de `if not settings.DEBUG`)

**Verificación con DEBUG=True (debe funcionar):**

```bash
DJANGO_DEBUG=True python manage.py simular_pago TRM-12345
# Debe pedir confirmación interactiva
```

---

### 8. Sesiones Backend (No Cookies)

**Ubicación:** `sanfelipe/settings/__init__.py:304`
**Severidad:** MEDIUM

**Verificación:**

```bash
python manage.py shell

>>> from sanfelipe.settings import SESSION_ENGINE
>>> print(SESSION_ENGINE)
```

**Resultado esperado:**
```python
'django.contrib.sessions.backends.db'
# NO debe ser 'django.contrib.sessions.backends.signed_cookies'
```

**Si falla:**
- ⚠️ MEDIUM: Sesiones almacenadas en cookies (exposición de datos internos)
- **Nota:** Cambiar a DB-backed sessions es parte de Fase 4 (no implementada aún)

---

## 🔍 Verificaciones Operativas

### 9. Verificar Logs de Seguridad

**Ubicación:** `/var/log/` (servidor), Docker logs

**Comandos:**

```bash
# Ver logs de errores recientes
tail -100 /var/log/nginx/error.log | grep -i "error\|forbidden\|deny"

# Ver logs de Django
docker logs backoffice_app --tail 100 | grep -i "warning\|error\|security"
```

**Qué buscar:**
- Intentos fallidos de login (`Login unsuccessful`)
- Bloqueos de IP por rate limiting (`limiting requests`)
- Errores de permisos (`PermissionDenied`, `403 Forbidden`)
- Accesso a endpoints no autorizados

---

### 10. Probar Flujo Completo de Autenticación

**Pasos de prueba:**

1. [ ] Login como superusuario → Dashboard visible
2. [ ] Intentar login con contraseña incorrecta 6 veces → 429 Too Many Requests
3. [ ] Intentar acceder a `/admin/auth/user/asignar-rol/` sin login → Redirección a login
4. [ ] Intentar ejecutar `simular_pago` con `DEBUG=False` → Error de seguridad
5. [ ] Verificar cookies de sesión → `sessionid` cookie presente con `Max-Age` correcto
6. [ ] Intentar asignar trámite a usuario sin rol Analista → Rechazado

---

## 📊 Registro de Auditoría

Completar esta sección como evidencia de la auditoría realizada:

| # | Verificación | Estado | Responsable | Fecha |
|---|--------------|--------|-------------|-------|
| 1 | Validación de contraseñas habilitada | ⬜ | | |
| 2 | SECRET_KEY segura (≥50 chars, sin patrones) | ⬜ | | |
| 3 | Vistas de asignación protegidas | ⬜ | | |
| 4 | ALLOWED_HOSTS configurado (no wildcard) | ⬜ | | |
| 5 | Rate limiting en `/admin/login/` activo | ⬜ | | |
| 6 | Headers nosniff/XSS-filter activos | ⬜ | | |
| 7 | Comando `simular_pago` bloqueado en prod | ⬜ | | |
| 8 | Sesiones DB (opcional) | ⬜ | | |
| 9 | Logs de seguridad revisados | ⬜ | | |
| 10 | Flujo de autenticación probado | ⬜ | | |

---

## 🚨 Pasos si Alguna Verificación Falla

### Si cualquier verificación CRITICAL (1-3) falla:

1. **DETENER deployment inmediatamente**
2. Corregir el problema según la fase indicada en este documento
3. Re-verificar la corrección
4. Documentar el fix en este registro
5. Continuar con la auditoría

### Si verificación MEDIUM falla:

1. Evaluar el riesgo de seguridad
2. Si es aceptable para el deployment inicial, crear ticket de mejora
3. Documentar la decisión de aceptar el riesgo

---

## 📚 Referencias

- [Plan de Seguridad - Fase 1 (Bloqueantes de Producción)](../../06-decisions/README.md)
- [Plan de Seguridad - Fase 2 (Alta Prioridad)](../../06-decisions/README.md)
- [Django Security Best Practices](https://docs.djangoproject.com/en/6.0/topics/security/)
- [OWASP Top 10](https://owasp.org/Top10)
- [Guía de Rate Limiting Nginx](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)

---

## ✅ Criterios de Aprobación

Antes de aprobar el deployment en producción, **todas** las verificaciones CRITICAL (1-3) deben estar en estado ✅.

Las verificaciones MEDIUM (6-8) pueden estar pendientes, pero con tickets de mejora documentados si no se cumplen al 100%.

---

**Estado Final:** [ ] Auditoría Aprobada
**Aprobado por:** ___________________________
**Fecha:** ______________________
**Firma:** _______________________
