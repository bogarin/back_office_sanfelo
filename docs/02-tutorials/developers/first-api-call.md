---
Title: Primera Llamada a la API - Tutorial para Desarrolladores
Role: developer
Time: 20 minutos
Level: beginner
Prerequisites: Acceso al proyecto, entorno de desarrollo configurado, conocimientos básicos de Django y REST APIs
---

## Resumen

Este tutorial te mostrará cómo hacer tu primera llamada exitosa a la API del Backoffice de Trámites. Aprenderás a configurar autenticación, hacer solicitudes HTTP, y recibir respuestas en formato JSON. Al final, tendrás creado tu primer trámite a través de la API.

## Lo que aprenderás

- Entender la arquitectura de la API
- Configurar autenticación (JWT tokens)
- Hacer diferentes tipos de solicitudes (GET, POST, PUT, DELETE)
- Manejar códigos de estado HTTP
- Procesar respuestas JSON correctamente
- Manejar errores comunes

## Requisitos previos

- ✅ Entorno de desarrollo local configurado (ver: [Tutorial: Setup de Desarrollo](../local-dev-setup.md))
- ✅ Base de datos PostgreSQL corriendo con esquema inicial aplicado
- ✅ Usuario de prueba creado (ver: [Tutorial: Setup de Desarrollo](../local-dev-setup.md))
- ✅ Cliente HTTP o herramienta para hacer solicitudes (curl, Postman, Insomnia, etc.)
- ❌ NO necesitas interfaz de usuario (Django Admin)

---

## Paso 1: Entender la Arquitectura de la API

### 1.1 Vista General

La API del Backoffice de Trámites sigue una arquitectura RESTful con autenticación JWT vía Kong.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                  │
│           ┌──────────────────────────────────┐          │
│           │   Kong Gateway (Auth Provider)    │          │
│           │   - Token Validation               │          │
│           │   - JWT Verification             │          │
│           └──────────────────────────────────┘          │
│                      │                         │         │
│                      ▼                         ▼         │
│              ┌─────────────────────────────┐        │
│              │  Django REST API              │        │
│              │  - Endpoints                │        │
│              │  - Business Logic            │        │
│              │  - PostgreSQL (Business DB)     │        │
│              │  - Models                  │        │
│              │  └───────────────────────────┘        │
└───────────────────────────────────────────────────────────┘
```

### 1.2 Flujo de Solicitud

```
Cliente ──► Kong ──► Django API ──► PostgreSQL (Business DB)
  │              │              │
  │              │              └──────────────► Models (Guardar en DB)
  │              │              │                 │
  └──────────────┴─────────────────────────────────────► Usuario (Bitácora)
```

### 1.3 Importante: Base de Datos Dual

El sistema usa **dos bases de datos**:
- **SQLite (Django)**: Almacena usuarios, sesiones, metadatos
- **PostgreSQL (Business)**: Almacena trámites, catálogos, costos, bitácora

Para más información: [Concepto: Dual Database](../../04-concepts/dual-database.md)

---

## Paso 2: Configurar Autenticación

### 2.1 Obtener Token de Acceso

La API usa autenticación JWT vía Kong Gateway. Necesitas un token válido.

#### 2.1.1 Método: Usar credenciales de prueba

**Opción A: Usuario de prueba de desarrollo**
```bash
# Usar el usuario de prueba creado en el setup local
curl -X POST http://localhost:8090/admin/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Respuesta esperada**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "1",
    "username": "admin",
    "email": "admin@sanfelipe.gob.mx",
    "roles": ["admin", "user"]
  }
}
```

**Opción B: Token JWT directamente**
Si tienes acceso directo a Kong, puedes generar un token JWT:
```json
{
  "sub": "user123",
  "realm_access": "backoffice",
  "name": "Juan Pérez",
  "email": "juan.perez@sanfelipe.gob.mx",
  "groups": ["backoffice-admin", "backoffice-user"]
}
```

> **Nota**: Para producción, obtén el token a través de Kong con tus credenciales reales.

#### 2.1.2 Estructura del Token

**Propiedades principales del token**:
```
{
  "access_token": "eyJhbGc..."  // Token de acceso (expira en X minutos)
  "expires_in": 3600,        // Tiempo de expiración en segundos (1 hora)
  "refresh_token": "eyJhbGc...",  // Token para refrescar (expira en 7 días)
  "user": {...}                    // Información del usuario
}
```

**Tiempos de expiración**:
- `access_token`: 3600 segundos (1 hora)
- `refresh_token`: 604800 segundos (7 días)

> **Importante**: Los tiempos pueden variar según configuración de Kong. Respeta siempre los tiempos devueltos en `expires_in`.

### 2.2 Guardar el Token

Guarda el token en una variable de entorno o archivo para reutilizarlo:

```bash
# Guardar en variable
export TOKEN="eyJhbGciOiJIUzI1NiIs..."
export REFRESH_TOKEN="eyJhbGciOiJIUzI1NiIs..."
export USER_ID="1"

# O guardar en archivo JSON
cat > token.json <<EOF
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": "1",
  "username": "admin"
  "expires_at": "2026-02-26T16:00:00Z"
}
EOF
```

---

## Paso 3: Hacer tu Primera Solicitud GET

### 3.1 Listar Trámites

Obten la lista de trámites existentes para verificar que todo funciona.

```bash
# Ejemplo de solicitud GET con autenticación
curl -X GET http://localhost:8090/api/tramites/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

**Respuesta esperada**:
```json
{
  "count": 25,
  "next": "http://localhost:8090/api/tramites/?page=2",
  "previous": null,
  "results": [
    {
      "numero": "TRAM-2026-00045",
      "tipo_codigo": "LIC-CONST",
      "tipo_nombre": "Licencia de Construcción",
      "descripcion": "Solicitud de licencia...",
      "estado": "Registrado",
      "prioridad": "Normal",
      "creado_por_user_id": "1",
      "creado_por_username": "admin",
      "creado_por_username": "admin",
      "fecha_creacion": "2026-02-15T10:30:00Z",
      "asignado_a_user_id": null,
      "asignado_a_username": null,
      "observaciones": ""
    }
  ]
}
```

**Explicación de campos**:

| Campo | Descripción |
|--------|-------------|
| `numero` | Número único del trámite (TRAM-AAAA-XXXXX) |
| `tipo_codigo` | Código del tipo de trámite |
| `tipo_nombre` | Nombre del tipo de trámite |
| `estado` | Estado actual del trámite |
| `prioridad` | Prioridad del trámite (Normal, Alta, Urgente) |
| `creado_por_user_id` | ID del usuario que creó el trámite |
| `asignado_a_user_id` | ID del usuario asignado |
| `observaciones` | Notas adicionales |

**Paginación**:
- La API devuelve resultados paginados: `?page=1`, `?page=2`, etc.
- Cada página devuelve hasta 25 trámites por defecto
- Ver campos `next` y `previous` para navegación

---

## Paso 4: Crear un Trámite con POST

### 4.1 Preparar el Payload

Prepara el objeto JSON con los datos del nuevo trámite:

```json
{
  "tipo_codigo": "LIC-CONST",
  "descripcion": "Solicitud de licencia de construcción para vivienda unifamiliar",
  "prioridad": "Normal",
  "observaciones": "Cliente: Juan Pérez García, Dirección: Av. Principal #123, Tel: 555-1234"
}
```

**Campos requeridos**:

| Campo | Tipo | Requerido | Descripción |
|--------|------|-----------|-------------|
| `tipo_codigo` | string | ✅ Sí | Código válido del tipo de trámite |
| `descripcion` | string | ✅ Sí | Descripción clara del trámite |
| `prioridad` | string | ✅ No | Prioridad ("Normal", "Alta", "Urgente", Default: "Normal") |
| `observaciones` | string | ❌ No | Notas adicionales |

### 4.2 Crear el Trámite

```bash
curl -X POST http://localhost:8090/api/tramites/create/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_codigo": "LIC-CONST",
    "descripcion": "Solicitud de licencia de construcción para vivienda unifamiliar",
    "prioridad": "Normal",
    "observaciones": "Cliente: Juan Pérez García, Dirección: Av. Principal #123"
  }'
```

**Respuesta esperada**:
```json
{
  "numero": "TRAM-2026-00046",
  "tipo_codigo": "LIC-CONST",
  "tipo_nombre": "Licencia de Construcción",
  "estado": "Registrado",
  "prioridad": "Normal",
  "creado_por_user_id": "1",
  "creado_por_username": "admin",
  "fecha_creacion": "2026-02-26T15:45:22Z",
  "observaciones": ""
}
```

**Resultado esperado**: Trámite creado con número único autogenerado y estado "Registrado".

> **Importante**: El campo `numero` se genera automáticamente en formato `TRAM-AAAA-XXXXX` donde:
- `TRAM` es prefijo constante
- `AAAA` es el año actual
- `XXXXX` es número secuencial único

---

## Paso 5: Actualizar un Trámite con PUT

### 5.1 Actualizar Información Básica

```bash
curl -X PUT http://localhost:8090/api/tramites/TRAM-2026-00046/update/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Solicitud actualizada: ahora se incluye plano arquitectónico",
    "observaciones": "Cliente agregó plano arquitectónico el 2026-02-26"
  }'
```

**Respuesta esperada**:
```json
{
  "numero": "TRAM-2026-00046",
  "tipo_codigo": "LIC-CONST",
  "tipo_nombre": "Licencia de Construcción",
  "estado": "Registrado",
  "descripcion": "Solicitud actualizada",
  "actualizado_por_user_id": "1",
  "actualizado_por_username": "admin",
  "fecha_actualizacion": "2026-02-26T16:20:30Z"
}
```

### 5.2 Actualizar Estado

```bash
# Cambiar estado a "En Proceso"
curl -X POST http://localhost:8090/api/tramites/TRAM-2026-00046/status/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "En Proceso"
  }'
```

### 5.3 Asignar Trámite a Usuario

```bash
# Asignar a operador específico (cambia ID según tus datos reales)
curl -X POST http://localhost:8090/api/tramites/TRAM-2026-00046/assign/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "asignado_a_user_id": "5",
    "asignado_a_username": "operador1"
  }'
```

**Respuesta esperada**:
```json
{
  "numero": "TRAM-2026-00046",
  "estado": "Asignado",
  "asignado_a_user_id": "5",
  "asignado_a_username": "operador1",
  "fecha_asignacion": "2026-02-26T16:25:00Z"
}
```

> **Nota**: Los IDs de usuario son de Keycloak (sub claim del JWT).

---

## Paso 6: Manejar Códigos de Estado HTTP

### 6.1 Códigos de Éxito Comunes

| Código | Significado | Cómo manejar |
|--------|----------|---------------|
| 200 OK | Solicitud exitosa | ✅ Todo bien, procesar la respuesta JSON |
| 201 Created | Recurso creado exitosamente | ✅ Leer el header `Location` para obtener el URL del nuevo recurso |
| 204 No Content | Solicitud exitosa pero sin retorno | ✅ No hacer nada, éxito |
| 400 Bad Request | Error en la solicitud | ❌ Revisar el payload y mensaje de error |
| 401 Unauthorized | Token inválido o expirado | ❌ Obtener nuevo token con `REFRESH_TOKEN` |
| 403 Forbidden | Permisos insuficientes | ❌ Verifica que el usuario tiene el rol necesario |
| 404 Not Found | Recurso no encontrado | ❌ Verifica la URL y el ID |
| 409 Conflict | Conflicto con estado actual | ❌ Trámite ya modificado por otro |
| 422 Unprocessable Entity | Payload mal formateado | ❌ Revisa la estructura del JSON |
| 500 Internal Server | Error interno del servidor | ❌ Contacta soporte técnico |

### 6.2 Códigos de Error y Soluciones

#### Error 400 Bad Request
**Causas comunes**:
- JSON mal formateado
- Campo requerido faltante
- Tipo de dato incorrecto
- Validación fallida

**Diagnóstico**:
```bash
# Ver el mensaje de error en la respuesta
curl -v -X POST ... | jq '.'
```

**Ejemplo de respuesta 400**:
```json
{
  "error": {
    "tipo_codigo": "VALIDATION_ERROR",
    "mensaje": "El campo 'descripcion' es obligatorio"
  }
}
```

**Solución**:
- Revisa que todos los campos requeridos estén incluidos
- Verifica que el formato de los datos sea correcto

---

#### Error 401 Unauthorized
**Causa**: Token expirado o inválido

**Diagnóstico**:
```bash
# Verifica si el token está expirado
curl -X GET http://localhost:8090/api/tramites/ \
  -H "Authorization: Bearer $TOKEN"
```

**Solución**:
- Si el token expiró, usa el `refresh_token`
- Si el token es inválido, obtén un nuevo token con credenciales

**Cómo usar el refresh_token**:
```bash
curl -X POST http://localhost:8090/admin/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "$REFRESH_TOKEN"
  }'
```

---

## Paso 7: Procesar Respuestas JSON

### 7.1 Parsear JSON con jq

`jq` es una herramienta CLI para procesar JSON:

```bash
# Extraer información específica
curl -s http://localhost:8090/api/tramites/ | jq '.results[0].numero'
# Output: "TRAM-2026-00045"

# Extraer múltiples campos
curl -s http://localhost:8090/api/tramites/ | jq '.results | .[] | {numero, tipo_codigo, estado, descripcion}'

# Filtrar resultados
curl -s http://localhost:8090/api/tramites/?estado=Registrado | jq '.results | .[] | select(.numero, .tipo_codigo)'

# Extraer nested objects
curl -s http://localhost:8090/api/tramites/TRAM-2026-00046 | jq '.asignado_a'
# Output: {"user_id": 5, "username": "operador1", ...}
```

### 7.2 Manejar Errores HTTP

```bash
# Ver código de estado HTTP y mensaje
curl -i -X POST http://localhost:8090/api/tramites/create/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}' \
  -w "%{http_code}\n%{status_code}\n%{message}\n%{error}\n}" | jq -r @input
```

**Ejemplo de manejo de errores**:
```bash
# Manejo básico de errores
if [ $http_code -eq 200 ]; then
  echo "✅ Éxito"
  jq '.message' <<< "$RESPONSE"
elif [ $http_code -eq 400 ]; then
  echo "❌ Error de solicitud"
  jq '.error' <<< "$RESPONSE"
elif [ $http_code -eq 401 ]; then
  echo "❌ Error de autenticación"
  echo "⚠️ Obteniendo nuevo token..."
else
  echo "❌ Error no esperado: $http_code"
fi
```

---

## Resumen

En este tutorial has aprendido:

✅ Entender la arquitectura de la API REST
✅ Configurar autenticación JWT con Kong Gateway
✅ Obtener y guardar tokens de acceso
✅ Hacer solicitud GET para listar trámites
✅ Crear nuevo trámite con POST
✅ Actualizar información de trámite con PUT
✅ Cambiar estado de trámite con POST
✅ Manejar códigos de estado HTTP (200, 201, 400, 401, 403, 404, 500)
✅ Procesar respuestas JSON con jq
✅ Manejar errores comunes

---

## ¿Qué sigue?

Ahora que puedes hacer tu primera llamada a la API, puedes aprender:

### Tutoriales siguientes:
- 📖 [Tutorial: Crear Trámite](../operators/create-tramite.md) - Tutorial completo de creación de trámite
- 📋 [Tutorial: Flujo de Trabajo Diario](../operators/manage-workflow.md) - Cómo gestionar múltiples trámites
- 📋 [Tutorial: Subir Documentos](../operators/upload-docs.md) - Cómo adjuntar documentos
- 📋 [Tutorial: Búsqueda Avanzada](../operators/search-tramites.md) - Encontrar trámites eficientemente

### Guías relacionadas:
- 📋 [Guía: Debug Schema Validator](../developers/debug-schema.md) - Para depurar problemas con el esquema SQL
- 📋 [Guía: Ejecutar Tests](../developers/run-tests.md) - Para probar tu código

### Conceptos útiles:
- 🧠 [Concepto: Dual Database](../../04-concepts/dual-database.md) - Entender por qué dos BD
- 🧠 [Concepto: No Migrations](../../04-concepts/no-migrations.md) - Por qué no usar migraciones Django
- 🧠 [Concepto: Sistema de Auditoría](../../04-concepts/audit-system.md) - Cómo funciona la bitácora

---

## Problemas Comunes

| Problema | Posible Causa | Solución |
|----------|-----------------|----------|
| Token expirado | `expires_in` menor a fecha actual | Usar `refresh_token` para obtener nuevo token |
| 401 Unauthorized | Token inválido o no proporcionado | Obtener nuevo token con credenciales |
| 403 Forbidden | No tienes permisos | Verifica que tu usuario tiene el rol necesario |
| 404 Not Found | URL incorrecta o trámite no existe | Verifica URL e ID del trámite |
| 500 Internal Server | Error en servidor | Contacta soporte técnico |
| 400 Bad Request | Payload mal formateado | Revisa la estructura del JSON y mensaje de error |
| 409 Conflict | Trámite ya modificado | Consulta el estado actual antes de actualizar |

---

## Consejos de Mejores Prácticas

### Para Desarrollo

1. **Usa variables de entorno**
   ```bash
   export API_BASE_URL="http://localhost:8090/api"
   export TOKEN="your-token-here"
   ```

2. **Envuelve tokens y credenciales en .env.local**
   ```bash
   # .gitignore para no commitear tokens
   echo ".env.local" >> .gitignore
   echo ".token.json" >> .gitignore
   ```

3. **Usa scripts de ayuda**
   - Crea scripts en `scripts/` para operaciones comunes
   - Documenta tus scripts en un README

4. **Prueba endpoints con diferentes herramientas**
   - Usa Postman, Insomnia, o curl
   - Compara respuestas para verificar consistencia

5. **Documenta tus tests de integración**
   - Guarda ejemplos de requests/respuestas exitosas
   - Crea casos de prueba para edge cases

6. **Manejo de errores robusto**
   - Implementa reintentos automáticos
   - Log errores para diagnóstico posterior

---

## Preguntas Frecuentes

**P: ¿Cómo obtengo un token de producción?**
R: Contacta al equipo de DevOps o admin del sistema para obtener credenciales y URLs de Kong en producción.

**P: ¿Cuál es el formato del token JWT?**
R: El token sigue el estándar OpenID Connect. Contiene `access_token`, `refresh_token`, `user` con información del usuario.

**P: ¿El token expira?**
R: Sí, en 1 hora por defecto. Usa `refresh_token` antes de que expire.

**P: ¿Puedo usar el mismo token para múltiples llamadas?**
R: Sí, mientras no expira. Usa el mismo `access_token` para todas las solicitudes.

**P: ¿Cómo manejo paginación?**
R: Usa el parámetro `?page` y sigue los campos `next` y `previous`.

**P: ¿Cómo manejo timeouts?**
R: La API tiene timeouts configurados. Usa `timeout` en peticiones que puedan tardar más.

---

## Referencias Adicionales

- [Documentación de la API completa](../../05-reference/api/endpoints.md) - Referencia completa de todos los endpoints
- [Variables de Entorno](../../05-reference/configuration/environment-vars.md) - Configuración completa
- [Model Reference](../../05-reference/models/data-models.md) - Estructura de datos
- [Troubleshooting](../developers/troubleshoot.md) - Solución de problemas comunes

---

**¿Necesitas ayuda?**
- Consulta las [Guías de desarrolladores](../03-guides/developers/)
- Contacta a tu supervisor o equipo técnico
- Revisa el [Glosario](../01-onboarding/glossary.md) para términos técnicos

---

*Última actualización: 26 de Febrero de 2026*
