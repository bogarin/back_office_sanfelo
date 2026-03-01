---
Title: Crear tu Primer Trámite
Role: operator
Time: 15 minutos
Level: beginner
Prerequisites: Acceso a la intranet del Gobierno de San Felipe, usuario y contraseña
---

## Resumen

Este tutorial te mostrará paso a paso cómo crear tu primer trámite en el sistema Backoffice de Trámites. Al final, habrás registrado exitosamente un nuevo expediente con todos los datos básicos.

## Lo que aprenderás

- Acceder al sistema de Backoffice de Trámites
- Navegar por la interfaz de Django Admin
- Crear un nuevo trámite con información básica
- Asignar el trámite a ti mismo como operador
- Verificar que el trámite se haya creado correctamente

## Requisitos previos

- ✅ Usuario y contraseña del sistema (proporcionados por tu administrador)
- ✅ Acceso a la intranet del Gobierno de San Felipe
- ✅ Navegador web moderno (Chrome, Firefox, Edge)
- ✅ Conexión a internet (intranet)
- ❌ NO necesitas conocimientos técnicos de Django o bases de datos

---

## Paso 1: Acceder al Sistema

1. Abre tu navegador web
2. Ingresa a la URL del sistema:
   ```
   http://<host-del-sistema>/admin/
   ```
   - Por ejemplo: `http://backoffice.intranet.gob.sanfelipe/admin/`

3. Verás la página de **Login de Django Admin**

**Resultado esperado**: Deberías ver una pantalla con:
- Campo para "Usuario"
- Campo para "Contraseña"
- Botón "Acceder"

> **Nota**: Si no puedes acceder, verifica con tu administrador que tu usuario está activo y tiene los permisos correctos.

---

## Paso 2: Iniciar Sesión

1. En el campo "Usuario", escribe tu nombre de usuario
2. En el campo "Contraseña", escribe tu contraseña
3. Haz clic en el botón "Acceder"

**Resultado esperado**: Serás redirigido al **Panel Principal de Django Admin** donde verás todas las aplicaciones disponibles.

> **Nota**: Si olvidaste tu contraseña, contacta a tu administrador. No intentes recuperarla por ti mismo.

---

## Paso 3: Navegar a la Sección de Trámites

1. En el panel principal, busca la sección **TRAMITES**
2. Haz clic en "Trámites" o "Tramites"

**Resultado esperado**: Verás una lista (tabla) con los trámites existentes o un mensaje "No hay trámites disponibles".

> **Nota**: La sección de trámites puede aparecer con diferentes nombres según la configuración del sistema, como "Gestión de Trámites" o simplemente "Tramites".

---

## Paso 4: Crear un Nuevo Trámite

1. Haz clic en el botón **"Añadir trámite"** (o "Add Tramite") en la esquina superior derecha

**Resultado esperado**: Verás el **formulario de creación de trámite** con los siguientes campos:

### Campos Obligatorios (requeridos):

#### 1. Tipo de Trámite
- **Descripción**: Categoría o tipo de expediente que vas a crear
- **Cómo llenarlo**: Selecciona el tipo apropiado del menú desplegable
- **Ejemplos**:
  - "Licencia de Construcción"
  - "Licencia de Uso de Suelo"
  - "División de Linderos"
  - "Registro de Propiedad"

> **Importante**: El tipo de trámite define el flujo de trabajo, los requisitos necesarios, el tiempo estimado y los costos base. Selecciona el tipo correcto.

#### 2. Descripción del Trámite
- **Descripción**: Explicación breve del propósito o solicitud
- **Cómo llenarlo**: Escribe una descripción clara y concisa
- **Ejemplo**:
  - "Solicitud de licencia para construcción de vivienda unifamiliar en el lote X, manzana Y"
  - "División de linderos entre predios ubicados en calle ABC #123"

> **Consejo**: Sé específico pero conciso. Una buena descripción ayuda a entender rápidamente el propósito del trámite sin necesidad de leer documentos adicionales.

#### 3. Prioridad
- **Descripción**: Nivel de urgencia del trámite
- **Cómo llenarlo**: Selecciona del menú desplegable
- **Opciones comunes**:
  - Baja
  - Normal
  - Alta
  - Urgente

> **Importante**: La prioridad puede afectar el orden en que se procesan los trámites. Usa "Urgente" solo cuando sea realmente necesario.

#### 4. Observaciones
- **Descripción**: Notas adicionales o contexto relevante
- **Cómo llenarlo**: Escribe cualquier información adicional que sea útil
- **Ejemplo**:
  - "El solicitante tiene documentación incompleta, requiere seguimiento"
  - "Caso complejo que requiere revisión legal"
  - "Prioridad otorgada por dirección general"

> **Consejo**: Este campo es opcional pero muy útil. Registra información contextual que no encaja en otros campos.

### Campos Automáticos (no editable):

Los siguientes campos se llenan automáticamente por el sistema:

- **Número de Trámite**: Se genera automáticamente en formato `TRAM-AAAA-XXXXX`
- **Fecha de Creación**: Se registra automáticamente al crear el trámite
- **Estado Inicial**: Se asigna automáticamente el estado inicial según el tipo de trámite (ej: "Registrado")
- **Creado Por**: Se registra tu usuario automáticamente
- **Asignado A**: Se asigna automáticamente a tu usuario (operador actual)

---

## Paso 5: Guardar el Trámite

1. Revisa todos los campos llenados
2. Si todo está correcto, haz clic en el botón **"Guardar"** (o "Save") en la parte inferior del formulario
3. Si necesitas hacer cambios, puedes hacer clic en **"Guardar y continuar editando"** (Save and continue)

**Resultado esperado**: Serás redirigido a la **lista de trámites** y verás un mensaje de confirmación verde que dice "El trámite fue agregado exitosamente".

> **Nota**: Si aparece un mensaje de error en rojo, verifica:
- Todos los campos obligatorios estén llenados
- Los datos tengan el formato correcto
- No hay caracteres especiales inválidos

---

## Paso 6: Verificar que el Trámite se Creó Correctamente

1. En la lista de trámites, busca el trámite que acabas de crear
2. Haz clic en el **número de trámite** generado (ej: `TRAM-2026-00001`)

**Resultado esperado**: Verás la **página de detalle del trámite** con toda la información que ingresaste.

Verifica que:
- ✅ El número de trámite está en el formato correcto `TRAM-AAAA-XXXXX`
- ✅ El tipo de trámite es el correcto
- ✅ La descripción está correctamente escrita
- ✅ La prioridad es la correcta
- ✅ Tu usuario aparece como "Creado por"
- ✅ El estado actual es el inicial apropiado (ej: "Registrado")

> **Felicitaciones!** 🎉 Has creado exitosamente tu primer trámite.

---

## Resumen

En este tutorial has aprendido:

✅ Cómo acceder al sistema Backoffice de Trámites
✅ Cómo navegar por la interfaz de Django Admin
✅ Cómo crear un nuevo trámite paso a paso
✅ Qué campos son obligatorios y qué significa cada uno
✅ Cómo guardar y verificar que el trámite se creó correctamente

---

## ¿Qué sigue?

Ahora que has creado tu primer trámite, puedes aprender:

### Tutoriales siguientes:
- 📖 [Flujo de Trabajo Diario](./manage-workflow.md) - Aprende a gestionar múltiples trámites eficientemente
- 📋 [Cambiar Estado de un Trámite](../../03-guides/operators/change-status.md) - Aprende a actualizar el estado de trámites existentes
- 📋 [Subir Documentos](../../03-guides/operators/upload-docs.md) - Aprende a adjuntar documentos a trámites

### Guías relacionadas:
- 🔍 [Búsqueda Avanzada de Trámites](../../03-guides/operators/search-tramites.md) - Aprende a buscar y filtrar trámites

---

## Problemas Comunes

| Problema | Posible Causa | Solución |
|----------|-----------------|----------|
| No puedo acceder a /admin/ | URL incorrecta o usuario inactivo | Verifica la URL con tu administrador; solicita que reactive tu usuario |
| "Acceso denegado" | Usuario sin permisos de operador | Contacta a tu administrador para verificar tus permisos |
| Error al guardar: "Campo obligatorio" | No llenaste todos los campos requeridos | Revisa que Tipo de Trámite y Descripción estén llenados |
| Error al guardar: "Formato inválido" | Datos con formato incorrecto | Verifica que no haya caracteres especiales en descripción |
| No veo el botón "Guardar" | El formulario está muy abajo | Desplázate hacia abajo o usa el scroll del navegador |
| El trámite no aparece en la lista | Se guardó pero no se muestra | Haz clic en "Recargar" o presiona F5 |

---

## Consejos y Mejores Prácticas

### Para una Gestión Efectiva de Trámites

1. **Sé específico en las descripciones**
   - Una descripción clara ahorra tiempo a todos los que revisan el trámite
   - Incluye información clave: tipo de solicitud, ubicación, solicitante

2. **Usa las observaciones efectivamente**
   - Registra información contextual importante
   - Documenta casos especiales o excepciones
   - Ayuda a recordar detalles importantes

3. **Selecciona la prioridad correctamente**
   - No uses "Urgente" para todos los trámites
   - Usa "Urgente" solo cuando realmente lo requieras
   - Esto ayuda a priorizar el trabajo del equipo

4. **Verifica antes de guardar**
   - Revisa que todos los campos estén correctos
   - Un minuto de revisión ahorra tiempo de corrección posterior

5. **Documenta procesos especiales**
   - Si un trámite requiere manejo especial, regístralo en observaciones
   - Esto ayuda a mantener la continuidad si otro operador toma el caso

---

## Preguntas Frecuentes

**P: ¿Puedo cambiar el tipo de trámite después de crearlo?**
R: No, el tipo de trámite no debería cambiar después de la creación porque define el flujo de trabajo. Si necesitas un tipo diferente, crea un nuevo trámite y archiva el anterior.

**P: ¿Cuánto tiempo toma crear un trámite típico?**
R: Un trámite básico toma 5-10 minutos si tienes toda la información a mano. Trámites más complejos pueden tomar 15-20 minutos.

**P: ¿Qué pasa si creo un trámite por error?**
R: No puedes eliminar trámites directamente. En su lugar, cambia el estado a "Cancelado" y explica en observaciones por qué se canceló.

**P: ¿Puedo crear múltiples trámites a la vez?**
R: No, debes crearlos uno por uno. Esto asegura que cada trámite tenga la información correcta y completa.

---

## Referencias Adicionales

- [Glosario de Términos](../01-onboarding/glossary.md) - Para entender términos como "trámite", "tipo de trámite", "prioridad"
- [Overview del Proyecto](../01-onboarding/overview.md) - Para entender mejor el sistema
- [Tutorial: Flujo de Trabajo Diario](./manage-workflow.md) - El siguiente paso recomendado

---

**¿Necesitas ayuda?**
- Consulta las [Guías de Troubleshooting](../../03-guides/operators/)
- Contacta a tu administrador del sistema

---

*Última actualización: 26 de Febrero de 2026*
