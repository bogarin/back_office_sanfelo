---
Title: Cambiar Estado de un Trámite - Guía para Operadores
Role: operator
Related: [Concepto: Estados de Trámite](../../04-concepts/estados-de-tramite.md)
---

## Resumen

Esta guía te enseñará cómo cambiar el estado de un trámite existente. Aprenderás a navegar por el menú desplegable de estados, comprender qué implica cada estado y cómo realizar los cambios correctamente.

## ¿Cuándo usar esta guía?

- Cuando un trámite necesita avanzar al siguiente fase del proceso
- Cuando el solicitante proporcionó información adicional
- Cuando un perito requiere revisión del trabajo
- Cuando se corrigieron errores en información ingresada

---

## Casos de Uso

### Cambios de Estado Comunes

| Situación | Nuevo Estado |
|-----------|-------------|
| Trámite recién creado | En Revisión |
| Faltan documentos | Esperando Documentos |
| Revisión completa | En Proceso |
| Awaiting Perito | Esperando Revisión |
| Perito terminó revisión | En Proceso |
| Documentos completos | Completo |
| Error en trámite | Rechazado |

---

## Flujo de Estados

### Estados Típicos

1. **Registrado**: Trámite creado, esperando procesamiento
2. **En Revisión**: Operador revisa información ingresada
3. **En Proceso**: Trámite siendo atendido
4. **Esperando Documentos**: Esperando que el solicitante aporte información adicional
5. **Esperando Perito**: Asignado a perito para evaluación
6. **En Proceso (Perito)**: Perito revisando el trámite
7. **Completo**: Trámite finalizado exitosamente
8. **Rechazado**: Trámite no aprobado
9. **Cancelado**: Solicitud cancelada por el solicitante

---

## Pasos para Cambiar Estado

### Paso 1: Acceder al Trámite

1. Desde la lista de trámites, busca el trámite que quieres actualizar
2. Haz clic en el **número de trámite** (ej: TRAM-2026-00045)
3. Verás la página de detalle del trámite

**Resultado esperado**: Página de detalle con la información actual del trámite.

---

### Paso 2: Localizar el Campo de Estado

En la página de detalle del trámite, busca el campo **Estado** (o "Status").

**Localización**:
- Generalmente está en la parte superior derecha del formulario
- Puede ser un menú desplegable etiquetado como "Estado:" o "Status:"

> **Nota**: El campo puede tener diferentes nombres según la configuración, pero fácil de identificar.

---

### Paso 3: Seleccionar el Nuevo Estado

1. Haz clic en el campo de Estado
2. Se desplegará un menú con los estados disponibles
3. Selecciona el nuevo estado apropiado

**Estados disponibles**:
- Los estados dependen del tipo de trámite y configuración del sistema

> **Importante**: Solo muestra estados que son válidos para el trámite en su estado actual. No todos los estados aparecen para todos los trámites.

---

### Paso 4: (Opcional) Agregar Observaciones

Si el cambio de estado requiere explicación, usa el campo de **Observaciones**:

**Cuándo usar observaciones**:
- Para registrar información importante
- Para explicar por qué se cambió el estado
- Para documentar solicitudes del solicitante
- Para registrar correcciones necesarias

**Cómo llenar observaciones**:
- Sé específico y conciso
- Incluye fecha y hora
- Firma o inicial de tu nombre si es un cambio oficial

**Ejemplos de observaciones**:
- "Documentos incompletos enviados por solicitante el 2026-02-26"
- "Corrección solicitada: cambiar dirección de entrega"
- "Observación: Perito solicitó revisión adicional"

**Resultado esperado**: Las observaciones se guardan en la bitácora del trámite.

---

## Estados y Cuándo Usarlos

### Estado: En Revisión → En Proceso

**Cuándo usarlo**:
- El operador ha revisado y aprobado la información ingresada
- Los documentos requeridos están completos
- Listo para comenzar el trabajo

**Cómo cambiarlo**:
1. Cambia el estado a "En Proceso"
2. Agrega observación si es necesario

**Resultados esperados**:
- Trámite aparece en la lista de trabajos de los operadores
- El solicitante puede ver el progreso

### Estado: En Proceso → Completo

**Cuándo usarlo**:
- El trámite ha completado exitosamente todos los pasos
- Todos los documentos requeridos están adjuntos
- Perito ha aprobado el trabajo

**Cómo cambiarlo**:
1. Cambia el estado a "Completo"
2. Agrega observación de cierre si es necesario

**Resultados esperados**:
- Trámite se marca como completado
- Solicitante recibe notificación de finalización
- Archivos de documentos quedan disponibles para descarga

### Estado: En Proceso → Esperando Documentos

**Cuándo usarlo**:
- El operador ha realizado todos los pasos posibles
- Pero falta información del solicitante para continuar

**Cómo cambiarlo**:
1. Cambia el estado a "Esperando Documentos"
2. Contacta al solicitante para solicitar la información faltante

**Resultados esperados**:
- Trámite queda en espera hasta recibir la información
- El sistema marca el trámite para mostrar como pendiente

### Estado: Esperando Documentos → En Revisión

**Cuándo usarlo**:
- El solicitante ha enviado documentos o información adicional
- El trámite requiere revisión del operador

**Cómo cambiarlo**:
1. Cambia el estado a "En Revisión"
2. Asigna el trámite a ti mismo (o solicita cambio de asignación)
3. Coordina con el solicitante para las revisiones

**Resultados esperados**:
- El operador verá el trámite en su lista de trabajos de revisión
- El solicitante puede ver las observaciones

### Estado: En Revisión → En Proceso

**Cuándo usarlo**:
- El operador ha revisado y aprobado la información
- El trámite vuelve al proceso activo

**Cómo cambiarlo**:
1. Cambia el estado a "En Proceso"
2. Comunica al solicitante (si aplica) que continúe el trabajo

**Resultados esperados**:
- El trámite avanza en el proceso de atención
- El solicitante puede monitorear el progreso

---

## Reglas Importantes

### Regla 1: Cambios de Estado Solo Permitidos

**✅ PERMITIDO:**
- Avanzar en el flujo de trabajo establecido
- Cambiar de estado lógico según el progreso real
- Seguir los procedimientos establecidos por el departamento

**❌ NO PERMITIDO:**
- Saltar estados (ej: de "Registrado" directo a "Completo")
- Cambiar a "Rechazado" sin aprobación del solicitante
- Cambiar a "Cancelado" sin notificar al solicitante

**Ejemplos de cambios NO permitidos**:
- ❌ De "Registrado" → "Completo" (no hubo revisión)
- ❌ De "En Revisión" → "Completo" (sin aprobación del solicitante)
- ❌ De "En Proceso" → "Registrado" (no se completó el trabajo)

> **Consecuencia**: Estos cambios no cumplen con los procedimientos del departamento y pueden causar problemas de calidad y cumplimiento.

---

### Regla 2: Autorización para Cambios Irreversibles

**Si necesitas hacer un cambio irreversible**:
1. Consulta primero con tu supervisor o administrador
2. Documenta la razón del cambio en observaciones
3. Obtener aprobación antes de ejecutar el cambio

**Cambios irreversibles**:
- Cambiar de "Completo" → "En Revisión" o "En Proceso"
- Cambiar de "Rechazado" → "Completo"
- Eliminar un trámite (puede requerir aprobación especial)

> **Nota**: Los cambios en estados quedan registrados permanentemente en la bitácora. Asegúrate de tener una justificación válida.

---

### Regla 3: Uso de Observaciones

**Cuándo usar observaciones**:
- Para registrar información importante del solicitante
- Para documentar correcciones necesarias
- Para registrar cambios de dirección u prioridad
- Para registrar aprobaciones o rechazos

**Cómo llenar bien**:
- Sé específico y conciso
- Incluye fecha, hora y tu identificación
- Usa lenguaje profesional y respetuoso
- Evita culpas o lenguaje subjetivo

**Ejemplo de observación bien escrita**:
```
El solicitante solicitó agregar nuevo documento (contrato) para trámite.
Observación: Se recibido documento adicional el 2026-02-26 a las 14:30 hrs.
Registrado por: María García, Operador
Aprobado por: Juan Pérez, Administrador
Estado: Trámite regresado a estado "Esperando Documentos" hasta recibir documento.
```

**Ejemplo de observación mal escrita**:
```
El cliente me dijo que quiere cambiar el trámite de urgente.
Observación: Cambio de prioridad solicitado.
```
```

> **Nota**: Las observaciones son parte del registro permanente del trámite y pueden ser consultadas en cualquier momento por auditoría.

---

## Problemas Comunes

| Problema | Posible Causa | Solución |
|----------|----------------|----------|
| No encuentro el campo de Estado | Campo ubicado en diferente lugar | Busca en la página de detalle, puede estar en sección diferente |
| No veo el estado que necesito | El estado puede no estar disponible para este trámite | Contacta a tu supervisor para verificar permisos |
| Estado no se actualiza | Cambio no se guardó correctamente | Presiona "Guardar" nuevamente y verifica que se actualice |
| Error: "No puedes cambiar estado" | Permiso insuficiente o cambio de estado no válido | Consulta con tu supervisor sobre el permisos necesarios |
| Cambie el estado por error | Si fue un error, cambia al estado anterior y notifica el error |

---

## Solución de Problemas Específicos

### Problema: Trámite en estado incorrecto

**Situación**: El trámite está en un estado que no corresponde a su situación actual.

**Pasos para solucionar**:
1. Verifica qué estado actual tiene el trámite
2. Identifica en qué estado debería estar según el flujo real
3. Consulta con solicitante si hay duda sobre el estado correcto
4. Cambia al estado correcto con observación explicativa

**Ejemplo**:
```
Situación: Trámite marcado como "Completo" pero el solicitante pidió cambios.

Pasos:
1. Cambia estado a "En Revisión" o "En Proceso"
2. Observación: "Solicitante solicitó cambios adicionales. Esperando aprobación del trámite actual. 2026-02-27 por María García."
3. Comunica con solicitante para explicar la situación

Resultado esperado: Trámite vuelve al estado correcto con la información del solicitante.
```

---

## Resumen

En esta guía has aprendido:

✅ Cómo acceder al detalle de un trámite
✅ Cómo localizar el campo de estado
✅ Cómo seleccionar un nuevo estado desde el menú desplegable
✅ Cuándo agregar observaciones (y por qué)
✅ Reglas de cambios de estado permitidos y prohibidos
✅ Los estados típicos y cuándo usar cada uno
✅ Cómo solucionar problemas comunes de cambios de estado

---

## ¿Qué sigue?

Ahora que puedes cambiar estados de trámites, puedes aprender:

### Tutoriales siguientes:
- 📖 [Tutorial: Subir Documentos](./upload-docs.md) - Aprende a adjuntar documentos a trámites
- 🔍 [Tutorial: Búsqueda Avanzada de Trámites](./search-tramites.md) - Encontrar trámites eficientemente
- 📋 [Tutorial: Flujo de Trabajo Diario](../manage-workflow.md) - Gestionar múltiples trámites diariamente

### Conceptos útiles:
- 🧠 [Concepto: Estados de Trámite](../../04-concepts/estados-de-tramite.md) - Para entender la teoría detrás de los estados
- 🧠 [Concepto: Sistema de Auditoría](../../04-concepts/audit-system.md) - Para entender cómo se registran los cambios

### Guías relacionadas:
- 📋 [Guía: Operadores - Gestionar Catálogos](../admins/manage-catalogs.md) - Para aprender a gestionar catálogos (si aplica permisos)
- 📋 [Guía: Operadores - Agregar Peritos](../admins/add-peritos.md) - Para asignar peritos (si aplica permisos)

---

**¿Necesitas ayuda?**
- Consulta las [Guías de Operadores](../03-guides/operators/)
- Contacta a tu administrador del sistema
- Revisa el [Troubleshooting](../03-guides/operators/)

---

*Última actualización: 26 de Febrero de 2026*
