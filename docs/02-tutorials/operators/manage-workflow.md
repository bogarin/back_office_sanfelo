---
Title: Flujo de Trabajo Diario - Gestión de Múltiples Trámites
Role: operator
Time: 20 minutos
Level: beginner
Prerequisites: Haber completado el tutorial "Crear tu Primer Trámite" o tener experiencia básica con el sistema
---

## Resumen

Este tutorial te enseñará cómo gestionar múltiples trámites eficientemente durante tu día de trabajo. Aprenderás técnicas para organizar tu bandeja de trabajo, priorizar tareas, y mantener los trámites actualizados de manera efectiva.

## Lo que aprenderás

- Organizar tu vista de trámites según prioridad y estado
- Filtrar y buscar trámites rápidamente
- Actualizar el estado de múltiples trámites eficientemente
- Adjuntar documentos a trámites
- Manejar casos especiales o excepciones

## Requisitos previos

- ✅ Usuario y contraseña del sistema con permisos de operador
- ✅ Haber creado al menos un trámite previamente (tutorial recomendado)
- ✅ Navegador web moderno (Chrome, Firefox, Edge)
- ✅ Conexión a la intranet del Gobierno de San Felipe
- ❌ NO necesitas conocimientos técnicos avanzados

---

## Paso 1: Acceder y Organizar tu Vista de Trámites

### 1.1 Acceder a la Lista de Trámites

1. Accede al sistema: `http://<host>/admin/`
2. Ingresa tus credenciales
3. Navega a la sección **TRAMITES** en el panel principal

**Resultado esperado**: Verás la lista completa de trámites con los que tienes permiso de interactuar.

> **Nota**: Como operador, solo verás los trámites asignados a ti, no todos los trámites del sistema.

### 1.2 Entender la Interfaz de Lista

La lista de trámites tiene las siguientes columnas (o campos):

| Columna | Descripción | ¿Puedes ordenar? |
|----------|-------------|-------------------|
| **Número** | Número único del trámite (TRAM-AAAA-XXXXX) | ✅ Sí |
| **Tipo** | Tipo de trámite | ✅ Sí |
| **Descripción** | Breve descripción del trámite | ✅ Sí |
| **Estado** | Estado actual del trámite | ✅ Sí |
| **Prioridad** | Nivel de urgencia (Baja/Normal/Alta/Urgente) | ✅ Sí |
| **Creado** | Fecha de creación | ✅ Sí |
| **Asignado a** | Operador asignado (debe ser tú) | ✅ No (filtro) |
| **Acciones** | Botones para editar/ver | N/A |

**Ordenar la lista**:
1. Haz clic en el encabezado de cualquier columna para ordenar
2. El primer clic ordena ascendente (A→Z)
3. El segundo clic ordena descendente (Z→A)
4. Ejemplos de ordenamiento útiles:
   - **Por Prioridad**: Urgente primero
   - **Por Estado**: Primero trámites en proceso, luego pendientes
   - **Por Fecha de Creación**: Los más antiguos primero

> **Consejo**: Ordena por **Prioridad descendente** y **Fecha de Creación ascendente** para trabajar primero en lo más urgente y antiguo.

### 1.3 Filtrar la Lista

Usa los filtros disponibles para reducir la lista a lo relevante:

**Filtros comunes en Django Admin**:

1. **Barra de búsqueda** (arriba derecha)
   - Escribe texto para buscar
   - Busca en: número, tipo, descripción
   - Búsqueda sensible a mayúsculas/minúsculas

2. **Filtros en la barra lateral** (si disponibles):
   - **Por Estado**: Selecciona el estado específico
   - **Por Tipo**: Filtra por tipo de trámite
   - **Por Prioridad**: Solo urgentes, solo altas, etc.

**Resultado esperado**: La lista se reduce a mostrar solo los trámites que coinciden con tus criterios de búsqueda.

> **Consejo**: Usa filtros en combinación. Por ejemplo: "Estado: En Proceso" + "Prioridad: Alta" para ver solo los trabajos urgentes activos.

---

## Paso 2: Priorizar tu Trabajo

### 2.1 Identificar Trámites Urgentes

1. Ordena la lista por **Prioridad (descendente)**
2. Identifica todos los trámites marcados como **Urgente** o **Alta**
3. Estos deben ser tu primer prioridad del día

**Estrategia de priorización**:
- **Urgente** → Atender inmediatamente (primer 2 horas del día)
- **Alta** → Atender en la mañana
- **Normal** → Atender en la tarde
- **Baja** → Atender al final del día si hay tiempo

### 2.2 Identificar Trámites en Estado Crítico

Estados que requieren acción inmediata:
- **Esperando Documentos** → Solicitante debe aportar documentación
- **En Espera de Pago** → El solicitante debe pagar
- **Pendiente de Asignación** → (No debería aparecer, contactar a admin)

**Resultado esperado**: Una lista clara de qué trámites atender primero y por qué.

> **Importante**: No cambies la prioridad asignada manualmente. Si necesitas ajustar prioridad, contacta a tu supervisor o admin para aprobación.

---

## Paso 3: Actualizar el Estado de Trámites

### 3.1 Cambiar Estado de un Solo Trámite

1. Haz clic en el **número de trámite** que quieres actualizar
2. Verás la página de detalle del trámite
3. Busca el campo **Estado** (o "Status")
4. Selecciona el nuevo estado del menú desplegable
5. Llena **Observaciones** si el cambio requiere explicación
6. Haz clic en **"Guardar"** para aplicar el cambio

**Resultado esperado**: Verás un mensaje de confirmación verde "El trámite fue actualizado exitosamente".

### 3.2 Actualizar Múltiples Trámites (Acciones en Lote)

Si necesitas actualizar varios trámites con el mismo cambio:

1. En la lista de trámites, marca los trámites que quieres actualizar
   - Haz clic en las casillas de verificación (checkboxes) a la izquierda de cada trámite
2. En el menú de **Acciones** (arriba de la tabla), selecciona:
   - **Cambiar estado a: [nuevo estado]** si está disponible
   - O marca manualmente y edita uno por uno

**Resultado esperado**: Todos los trámites seleccionados se actualizan al nuevo estado.

> **Consejo**: Las acciones en lote solo están disponibles para cambios simples y consistentes. Para cambios complejos, actualiza cada trámite individualmente.

### 3.3 Estados Típicos y Cuándo Usarlos

| Estado | Cuándo usarlo | Qué significa |
|----------|---------------|---------------|
| **Registrado** | Trámite creado recientemente | Esperando ser procesado |
| **En Revisión** | Operador está revisando el trámite | En proceso de evaluación |
| **En Proceso** | Trámite está siendo atendido | Se están realizando las acciones necesarias |
| **Esperando Documentos** | Solicita documentos al solicitante | No puede avanzar sin documentación |
| **En Espera de Pago** | Requiere pago de derechos o costos | Trámite pausado hasta el pago |
| **En Espera de Perito** | Asignado a perito especializado | Esperando evaluación técnica |
| **Completado** | Trámite finalizado exitosamente | Cierre del caso |
| **Rechazado** | Trámite no aprobado | Caso cerrado sin éxito |
| **Cancelado** | Solicitud cancelada | Cierre administrativo |

> **Importante**: Solo cambia el estado cuando realmente se haya producido el cambio. No cambies el estado "por adelantar" el proceso real.

---

## Paso 4: Gestionar Documentos en Trámites

### 4.1 Acceder a la Sección de Documentos

1. Desde el detalle de un trámite, busca la sección **Documentos** (o "Files")
2. O haz clic en el número de trámite para ver todos los detalles relacionados

**Resultado esperado**: Verás la lista de documentos asociados al trámite.

### 4.2 Subir un Documento

1. Haz clic en **"Añadir documento"** (o "Add Document")
2. Selecciona el archivo desde tu computadora
3. Llena la descripción del documento (qué tipo de documento es)
4. Selecciona el estado del documento:
   - **Recibido**: Documento entregado por el solicitante
   - **En Revisión**: Documento siendo evaluado
   - **Aprobado**: Documento validado correctamente
5. Haz clic en **"Guardar"**

**Tipos de documentos comunes**:
- Identificación oficial (INE, pasaporte)
- Comprobante de domicilio
- Planos o croquis
- Escrituras
- Formularios de solicitud
- Constancias

> **Consejo**: Llena siempre la descripción del documento. Esto ayuda a identificar rápidamente qué es cada documento sin necesidad de abrirlo.

### 4.3 Ver y Descargar Documentos

1. Haz clic en el nombre del documento para verlo
2. O usa el botón de descarga (icono de descarga o enlace) para bajarlo a tu computadora

**Resultado esperado**: El documento se abre en tu navegador o se descarga a tu computadora.

> **Importante**: Los documentos son parte del registro permanente del trámite. No elimines documentos que puedan ser necesarios en el futuro.

---

## Paso 5: Manejar Casos Especiales

### 5.1 Solicitudes Incompletas

Si un solicitante olvida proporcionar información esencial:

1. Cambia el estado a **"Esperando Documentos"**
2. Agrega observación clara: "Falta [documento específico]"
3. Si es posible, contacta al solicitante por los canales oficiales
4. Registra la comunicación en observaciones del trámite

**Resultado esperado**: El trámite queda en espera hasta que el solicitante proporcione la información.

> **Consejo**: No rechaces trámites por información incompleta en primera instancia. Contacta primero para aclarar.

### 5.2 Casos Requieren Coordinación

Si un trámite requiere intervención de otros departamentos:

1. Cambia el estado a **"En Espera de Perito"** o **"En Coordinación"**
2. Agrega observación: "Enviado a [departamento] para evaluación"
3. Registra la fecha y departamento asignado
4. Programa seguimiento: recuerda verificar después de X días

**Departamentos comunes**:
- Perito arquitectónico
- Perito topográfico
- Dirección de obra pública
- Departamento jurídico
- Tesorería (para verificación de pagos)

**Resultado esperado**: El trámite se marca como en espera y el sistema muestra quién lo está atendiendo.

### 5.3 Casos que Requieren Anulación

Si necesitas anular un trámite:

1. Cambia el estado a **"Cancelado"**
2. Agrega observación detallada: "Cancelado por [razón específica]"
3. Registra quién autorizó la cancelación y cuándo

**Razones válidas para cancelación**:
- Solicitud retirada por el ciudadano
- Duplicado con otro trámite existente
- Error en el proceso de solicitud
- Falta de competencia (jurisdicción incorrecta)

**Resultado esperado**: El trámite se marca como cancelado y aparece en historial con esa nota.

> **Importante**: Solo los administradores pueden cancelar trámites después de ciertas fases del proceso. Como operador, consulta con tu admin antes de cancelar.

---

## Paso 6: Finalizar el Día de Trabajo

### 6.1 Revisar Trámites Completados

1. Al final del día, filtra por estado **"Completado"**
2. Verifica que todos tengan el cierre adecuado
3. Revisa observaciones para confirmar que están documentadas

**Resultado esperado**: Una lista de trámites que cerraste exitosamente hoy.

### 6.2 Identificar Trámites Pendientes para Mañana

1. Filtra por estados pendientes: **"Registrado"**, **"En Revisión"**, **"En Proceso"**
2. Prioriza estos trámites para mañana:
   - Urgentes primero
   - Luego por fecha de creación (más antiguos primero)

**Resultado esperado**: Una lista clara de qué esperar y priorizar mañana.

> **Consejo**: Mantén una lista mental o física de los trámites más importantes para mañana. Esto ayuda a empezar el siguiente día con claridad.

### 6.3 Verificar que Todo Está Actualizado

Antes de finalizar tu día:

1. Revisa que no hay trámites en estados intermedios injustificados
2. Verifica que todos los cambios de estado tengan observaciones
3. Confirma que todos los documentos requeridos estén adjuntados
4. Verifica que las prioridades sean correctas

**Resultado esperado**: Cierre del día con el trabajo bien organizado y documentado.

---

## Resumen

En este tutorial has aprendido:

✅ Cómo organizar tu vista de trámites efectivamente
✅ Cómo ordenar y filtrar la lista según tus necesidades
✅ Cómo priorizar el trabajo basado en urgencia y estado
✅ Cómo actualizar el estado de trámites individualmente y en lote
✅ Cómo gestionar documentos asociados a trámites
✅ Cómo manejar casos especiales y excepciones
✅ Cómo finalizar tu día de trabajo eficientemente

---

## ¿Qué sigue?

Ahora que puedes gestionar trámites eficientemente, puedes aprender:

### Tutoriales siguientes:
- 📋 [Cambiar Estado de un Trámite](../../03-guides/operators/change-status.md) - Tutorial más detallado sobre cambios de estado
- 📋 [Subir Documentos](../../03-guides/operators/upload-docs.md) - Tutorial completo sobre gestión de documentos
- 🔍 [Búsqueda Avanzada de Trámites](../../03-guides/operators/search-tramites.md) - Técnicas avanzadas de búsqueda

### Conceptos útiles:
- 🧠 [Estados de Trámite](../../04-concepts/) - Para entender la teoría detrás de los estados
- 🧠 [Sistema de Auditoría](../../04-concepts/audit-system.md) - Para entender cómo se registran los cambios

---

## Problemas Comunes

| Problema | Causa | Solución |
|----------|---------|----------|
| No encuentro un trámite que acabo de crear | Filtro activo | Limpia los filtros o verifica que el estado incluya a nuevos trámites |
| El estado no se actualiza | Error de conexión o permisos | Recarga la página; verifica que tengas permisos de modificación |
| No puedo subir documentos | Archivo muy grande o formato no soportado | Comprime el archivo (ZIP) o usa formato soportado (PDF, JPG, PNG) |
| La lista está muy larga | Demasiados trámites en tu bandeja | Usa filtros para reducir la vista |
| No puedo ordenar por una columna | Columna no ordenable | Usa la búsqueda o filtra por otro criterio |

---

## Mejores Prácticas de Gestión de Trámites

### Para Eficiencia Operativa

1. **Empieza el día con urgencias**
   - Revisa primero todos los trámites marcados como "Urgente"
   - Atiéndelos inmediatamente al iniciar tu jornada

2. **Usa los filtros activamente**
   - Cambia los filtros según la tarea que estás realizando
   - No mantengas filtros que no necesitas

3. **Documenta tus acciones**
   - Agrega observaciones claras cuando cambias el estado
   - Esto ayuda a otros operadores y a ti mismo en el futuro

4. **Prioriza la calidad sobre la cantidad**
   - Es mejor hacer bien 5 trámites que mal 10 trámites
   - Toma tiempo necesario para hacer el trabajo correctamente

5. **Mantén la consistencia en observaciones**
   - Usa un formato estándar para tus observaciones
   - Esto hace que los trámites sean fáciles de buscar y revisar

---

## Consejos de Organización del Tiempo

### Estructura Recomendada del Día

| Hora del Día | Actividad Principal | Objetivo |
|----------------|----------------------|-----------|
| **Inicio (8:00-9:00)** | Revisión de urgencias y priorización | Identificar qué atender primero |
| **Mañana (9:00-12:00)** | Atención de trámites urgentes y altos | Completar prioridades principales |
| **Medio día (12:00-13:00)** | Descanso/almuerzo | Reenergizarse |
| **Tarde (13:00-17:00)** | Trámites de prioridad normal y baja | Reducir pendientes |
| **Final (17:00-18:00)** | Revisión y organización | Preparar el día siguiente |

> **Ajusta estos horarios según tu turno real. La estructura es adaptable.**

---

## Preguntas Frecuentes

**P: ¿Cómo veo solo los trámites asignados a mí?**
R: El sistema automáticamente filtra para que solo veas los trámites donde tú eres el operador asignado. Si ves trámites de otros operadores, reporta esto a tu administrador.

**P: ¿Puedo cambiar la prioridad de un trámite?**
R: Como operador, no deberías cambiar la prioridad asignada manualmente. Si necesitas ajustar prioridad, contacta a tu supervisor o admin para aprobación del cambio.

**P: ¿Puedo trabajar con múltiples trámites simultáneamente?**
R: Sí, puedes abrir múltiples pestañas en tu navegador para tener varios trámites abiertos al mismo tiempo. Solo asegúrate de guardar los cambios en cada uno.

**P: ¿Qué pasa si un solicitante llega físicamente a la oficina?**
R: Registra esta visita en las observaciones del trámite. Esto mantiene un historial completo de todas las interacciones con el solicitante.

---

## Referencias Adicionales

- [Tutorial: Crear tu Primer Trámite](./create-tramite.md) - Tutorial fundamental si no lo has completado aún
- [Tutorial: Cambiar Estado de un Trámite](../../03-guides/operators/change-status.md) - Guía detallada sobre cambios de estado
- [Tutorial: Subir Documentos](../../03-guides/operators/upload-docs.md) - Guía completa sobre gestión de documentos
- [Glosario de Términos](../01-onboarding/glossary.md) - Definiciones de términos usados

---

**¿Necesitas ayuda?**
- Consulta las [Guías de Operadores](../../03-guides/operators/)
- Contacta a tu administrador del sistema
- Revisa el [Troubleshooting](../../03-guides/operators/)

---

*Última actualización: 26 de Febrero de 2026*
