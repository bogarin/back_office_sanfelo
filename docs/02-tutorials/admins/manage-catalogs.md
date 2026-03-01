---
Title: Gestionar Catálogos - Tutorial para Administradores
Role: admin
Time: 25 minutos
Level: beginner
Prerequisites: Haber completado el tutorial "Configurar Usuarios" o tener usuario administrativo activo
---

## Resumen

Este tutorial te enseñará cómo gestionar los catálogos del sistema Backoffice de Trámites. Los catálogos son tablas maestras que definen los tipos, estatus, requisitos, peritos y otros valores configurables del sistema. Al final, podrás crear, editar y eliminar registros en todos los catálogos.

## Lo que aprenderás

- Navegar y acceder a cada uno de los catálogos disponibles
- Crear nuevos registros en los diferentes catálogos
- Editar registros existentes
- Eliminar registros que ya no son necesarios
- Comprender la relación entre los catálogos y los trámites
- Usar filtros y búsqueda para encontrar registros rápidamente

## Requisitos previos

- ✅ Usuario administrativo con permisos de gestión de catálogos
- ✅ Haber completado el tutorial "Configurar Usuarios" o tener rol de Admin asignado
- ✅ Navegador web moderno (Chrome, Firefox, Edge)
- ✅ Conexión a la intranet del Gobierno de San Felipe
- ❌ NO necesitas conocimientos técnicos de Django o bases de datos

---

## Paso 1: Acceder al Panel de Administración

### 1.1 Iniciar Sesión

1. Abre tu navegador web
2. Ingresa a la URL del sistema:
   ```
   http://<host-del-sistema>/admin/
   ```
   - Por ejemplo: `http://backoffice.intranet.gob.sanfelipe/admin/`

3. En el campo "Usuario", ingresa tu nombre de usuario administrativo
4. En el campo "Contraseña", ingresa tu contraseña
5. Haz clic en el botón "Acceder"

**Resultado esperado**: Serás redirigido al **Panel Principal de Django Admin** donde verás todas las aplicaciones disponibles.

> **Nota**: Si olvidaste tu contraseña, contacta a tu administrador del sistema. No intentes recuperarla por ti mismo.

### 1.2 Navegar a la Sección de Catálogos

1. En el panel principal, busca la sección **CATÁLOGOS** (o "Catalogs")
2. Verás una lista de aplicaciones de catálogo disponibles:
   - Tipos de Trámites
   - Estatus
   - Requisitos
   - Peritos
   - [Otros catálogos configurados]

3. Haz clic en **Tipos de Trámites** para comenzar

**Resultado esperado**: Verás la lista (tabla) de tipos de trámites existentes.

---

## Paso 2: Comprender los Tipos de Trámites

### 2.1 Estructura de la Lista

La lista de tipos de trámites muestra las siguientes columnas:

| Columna | Descripción | ¿Puedes ordenar? |
|----------|-------------|-------------------|
| **Código** | Identificador único del tipo de trámite (ej: "LIC-CONST") | ✅ Sí |
| **Nombre** | Descripción del tipo de trámite (ej: "Licencia de Construcción") | ✅ Sí |
| **Departamento** | Dependencia responsable del trámite | ✅ Sí |
| **Tiempo Estimado (Días)** | Días estimados para completar el trámite | ✅ Sí |
| **Costo en UMAs** | Valor base en UMAs para cálculo de costos | ✅ Sí |
| **Activo** | Indica si el tipo está disponible actualmente | ❌ No (solo activos) |
| **Acciones** | Botones para editar/eliminar | N/A |

### 2.2 Ver Detalle de un Tipo Existente

1. Haz clic en el **código** de cualquier tipo de trámite existente
2. Verás el formulario de edición con todos los detalles

**Resultado esperado**: Página de detalle con:
- Todos los campos del tipo de trámite
- Datos de configuración
- Relaciones con otros catálogos

---

## Paso 3: Crear un Nuevo Tipo de Trámite

### 3.1 Acceder al Formulario de Creación

1. Desde la lista de tipos de trámites, haz clic en el botón **"Añadir tipo de trámite"** (o "Add TipoTramite") en la esquina superior derecha
2. Verás el formulario en blanco

**Resultado esperado**: Formulario vacío listo para llenar.

### 3.2 Llenar los Campos del Formulario

#### 3.2.1 Código (Obligatorio)

**Descripción**: Identificador único del tipo de trámite.

**Cómo llenarlo**:
- Usa un código corto y descriptivo
- Formato: 3-5 letras mayúsculas
- Ejemplos: "LIC-CONST", "L-USE-OCC", "DIV-LIN", "REG-PROP"

**Reglas**:
- ✅ Debe ser único en el sistema
- ✅ Solo letras mayúsculas y guiones
- ✅ Máximo 10 caracteres
- ❌ No espacios ni caracteres especiales

> **Consejo**: Usa códigos que sean fáciles de recordar y escribir. Los operadores necesitarán seleccionar este código frecuentemente.

#### 3.2.2 Nombre (Obligatorio)

**Descripción**: Descripción clara del tipo de trámite.

**Cómo llenarlo**:
- Ejemplo: "Licencia de Construcción"
- Sé específico pero conciso
- Máximo 200 caracteres

> **Consejo**: Usa nombres que los ciudadanos reconozcan fácilmente. Evita tecnicismos o abreviaturas.

#### 3.2.3 Departamento (Obligatorio)

**Descripción**: Dependencia gubernamental responsable del trámite.

**Cómo llenarlo**:
- Selecciona del menú desplegable
- Ejemplos: "Obras Públicas", "Desarrollo Urbano", "Catastro"

> **Importante**: Este campo define qué departamento será responsable de los trámites de este tipo. Asegúrate de seleccionar el correcto.

#### 3.2.4 Tiempo Estimado en Días (Obligatorio)

**Descripción**: Días que toma procesar el trámite en condiciones normales.

**Cómo llenarlo**:
- Ingresa un número entero positivo
- Ejemplos: 15, 30, 60, 90

**Rango típico**:
- Trámites sencillos: 5-15 días
- Trámites complejos: 30-90 días
- Trámites muy complejos: 90-180 días

> **Consejo**: Usa tiempos realistas basados en tu experiencia. Los tiempos muy optimistas causan frustración a los ciudadanos.

#### 3.2.5 Costo en UMAs (Obligatorio)

**Descripción**: Valor base en UMAs (Unidad de Medida Actualizada) para cálculo de costos.

**Cómo llenarlo**:
- Ingresa un número decimal
- Ejemplos: 0.5, 1.0, 2.5, 5.0

**Explicación**:
- 1.0 UMA = valor de UMA oficial vigente
- El costo final del trámite = (Valor en UMAs) × (Valor UMA en MXN)

> **Nota**: La UMA oficial se actualiza periódicamente. El sistema debe mantenerse sincronizado con el valor oficial más reciente.

#### 3.2.6 Activo (Obligatorio)

**Descripción**: Indica si el tipo de trámite está disponible actualmente.

**Cómo llenarlo**:
- Marca la casilla "Activo" (Is Active) si el tipo está disponible
- No marques si no se debe usar temporalmente

**Resultado esperado**:
- ✅ Marcado: El tipo aparecerá en la lista y podrá seleccionarse al crear trámites
- ❌ No marcado: El tipo no estará disponible

> **Importante**: No elimines tipos de trámite cuando dejen de usarse. En su lugar, desactívalos marcando "Activo" = No. Esto mantiene el historial.

### 3.3 Guardar el Nuevo Tipo de Trámite

1. Revisa todos los campos llenados
2. Haz clic en el botón **"Guardar"** (o "Save") en la parte inferior del formulario

**Resultado esperado**:
- Verás un mensaje verde de confirmación
- Serás redirigido a la lista de tipos de trámites
- El nuevo tipo de trámite aparecerá en la lista

> **Consejo**: Si aparece un error en rojo, revisa los campos marcados. Los mensajes de error suelen indicar específicamente qué está mal.

---

## Paso 4: Editar un Tipo de Trámite Existente

### 4.1 Acceder al Formulario de Edición

1. Desde la lista de tipos de trámites, busca el tipo que quieres editar
2. Haz clic en el botón de edición (ícono de lápiz) en la columna de "Acciones"

**Resultado esperado**: Formulario pre-llenado con la información actual del tipo de trámite.

### 4.2 Modificar los Campos

1. Actualiza los campos que necesites cambiar
2. Puedes modificar:
   - Código (si es seguro que no se usa en trámites)
   - Nombre
   - Departamento
   - Tiempo estimado
   - Costo en UMAs
   - Estado activo/inactivo

> **Advertencia**: Si cambias el **Código** de un tipo que ya tiene trámites creados, esto puede causar problemas en los trámites existentes. Solo cambia el código si es absolutamente necesario y conoce el impacto.

### 4.3 Guardar los Cambios

1. Haz clic en el botón **"Guardar"** (o "Save")

**Resultado esperado**:
- Mensaje verde de confirmación
- La lista muestra los valores actualizados
- El historial de cambios es registrado automáticamente

---

## Paso 5: Eliminar un Tipo de Trámite

### 5.1 Verificar que el Tipo no se Está Usando

**⚠️ ANTES DE ELIMINAR**, verifica:

1. ¿Existen trámites creados con este tipo?
2. Si existen, elimínalos primero o cámbialos de tipo
3. ¿Hay trámites en proceso activo con este tipo?

> **Importante**: No puedes eliminar un tipo de trámite que tiene trámites asociados. Debes primero eliminar o reasignar esos trámites.

**Cómo verificar**:
1. Haz clic en el código del tipo de trámite
2. En la página de detalle, verifica la sección de trámites relacionados
3. Si hay trámites, toma nota del problema y solución

### 5.2 Eliminar el Tipo

**Si es seguro eliminar**:

1. Desde la lista de tipos de trámites, haz clic en el botón de eliminación (ícono de papelera) en la columna de "Acciones"
2. El sistema pedirá confirmación

### 5.3 Confirmar la Eliminación

1. Lee el mensaje de confirmación cuidadosamente
2. Haz clic en **"Sí, eliminar"** para confirmar
3. O haz clic en **"Cancelar"** si cambias de opinión

**Resultado esperado**:
- El tipo de trámite es eliminado permanentemente
- Ya no aparecerá en la lista
- No se podrá seleccionar este tipo al crear trámites nuevos

> **ADVERTENCIA**: Esta acción es irreversible. No hay opción de "deshacer". Si necesitas el tipo en el futuro, tendrás que recrearlo.

---

## Paso 6: Gestionar Otros Catálogos

Los siguientes catálogos funcionan de manera similar:

### 6.1 Estatus

1. Desde el panel principal, haz clic en **"Estatus"**
2. Verás la lista de estados posibles
3. Ejemplos: "Registrado", "En Revisión", "En Proceso", "Completo", "Rechazado"

**Cómo gestionar**:
- **Crear**: Añade nuevos estados según el flujo de trabajo
- **Editar**: Modifica nombres o descripciones
- **Eliminar**: Elimina estados que ya no se usan

> **Consejo**: Los estados definen el flujo de trabajo. Los nuevos estados deben ser consistentes con el flujo existente.

### 6.2 Requisitos

1. Desde el panel principal, haz clic en **"Requisitos"**
2. Verás la lista de documentos requeridos

**Ejemplos**:
- Identificación oficial (INE)
- Comprobante de domicilio
- Planos arquitectónicos
- Escrituras públicas

**Cómo gestionar**:
- Asocia requisitos a tipos de trámites específicos
- Define cuáles son obligatorios u opcionales
- Puedes agregar o quitar requisitos

> **Consejo**: Los requisitos ayudan a los operadores a verificar que el solicitante tiene toda la documentación necesaria.

### 6.3 Peritos

1. Desde el panel principal, haz clic en **"Peritos"**
2. Verás la lista de peritos especializados disponibles

**Información típica de peritos**:
- Nombre completo
- Especialidad (ej: Arquitectónico, Topógrafo, Ingeniero Civil)
- Datos de contacto
- Honorarios (si aplica)

**Cómo gestionar**:
- Crea nuevos peritos cuando se incorporan especialistas
- Actualiza información de peritos existentes
- Elimina peritos que ya no trabajan con el gobierno

> **Importante**: Los peritos se pueden asignar a diferentes tipos de trámites según su especialidad. Los operadores pueden seleccionar peritos específicos para cada trámite.

---

## Paso 7: Usar Filtros y Búsqueda

### 7.1 Búsqueda de Registros

**Barra de búsqueda**:
1. Ubica la barra de búsqueda arriba de la tabla
2. Escribe el texto que quieres buscar (código, nombre, etc.)
3. Presiona Enter o haz clic en el botón de búsqueda

**Resultado esperado**: La lista se filtra para mostrar solo los registros que coinciden con tu búsqueda.

**Búsqueda sensible a mayúsculas/minúsculas**:
- Por defecto, no distingue mayúsculas (juan = JUAN)
- Para búsqueda exacta con mayúsculas/minúsculas, usa comillas: "Juan Pérez"

### 7.2 Filtros Específicos

**Filtros disponibles**:
- **Por Activo**: Solo tipos activos o todos
- **Por Departamento**: Filtra tipos por departamento específico
- **Por Rango de Tiempo**: Tipos con tiempo estimado entre X y Y días

**Cómo usar filtros**:
1. Haz clic en el botón de filtros (icono de embudo)
2. Selecciona los criterios deseados
3. Aplicar filtros

**Resultado esperado**: La lista se reduce para mostrar solo los registros que cumplen con los filtros.

> **Consejo**: Los filtros son muy útiles cuando hay muchos registros. Combinar búsqueda con filtros para encontrar exactamente lo que necesitas.

---

## Paso 8: Ver el Historial de Cambios

### 8.1 Acceder a la Bitácora

1. Desde la lista de catálogos, haz clic en el código de un tipo de trámite
2. En la página de detalle, busca la sección **"Historial"** o **"Bitácora"**

**Resultado esperado**: Verás una tabla con todos los cambios realizados en este tipo de trámite.

### 8.2 Interpretar el Historial

**Información en la bitácora**:
- **Usuario**: Quién hizo el cambio
- **Fecha y Hora**: Cuándo se realizó
- **Acción**: Tipo de acción (crear, editar, eliminar)
- **Campo**: Campo que se modificó (si aplica)
- **Valor Anterior**: Valor antes del cambio
- **Valor Nuevo**: Valor después del cambio

**Ejemplo de registro**:
```
Usuario: admin.garcia
Fecha: 2026-02-26 15:30:00
Acción: editar
Campo: tiempo_estimado_dias
Valor Anterior: 15
Valor Nuevo: 20
```

> **Importante**: La bitácora es un registro permanente de todos los cambios. Esto ayuda a mantener la trazabilidad y resolver disputas o problemas.

---

## Resumen

En este tutorial has aprendido:

✅ Cómo navegar a la sección de catálogos
✅ Cómo crear un nuevo tipo de trámite
✅ Cómo editar tipos de trámites existentes
✅ Cómo eliminar tipos de trámites (con precauciones)
✅ Cómo gestionar otros catálogos (estatus, requisitos, peritos)
✅ Cómo usar filtros y búsqueda eficientemente
✅ Cómo revisar el historial de cambios en la bitácora

---

## ¿Qué sigue?

Ahora que puedes gestionar los catálogos, puedes aprender:

### Tutoriales siguientes:
- 📋 [Agregar Peritos](../../03-guides/admins/add-peritos.md) - Tutorial para gestionar peritos especializados
- 📋 [Configurar Costos por Trámite](../../03-guides/admins/configure-costs.md) - Tutorial para definir costos

### Guías relacionadas:
- 🔍 [Búsqueda Avanzada de Trámites](../../03-guides/operators/search-tramites.md) - Aunque es para operadores, te ayuda a entender cómo funcionan los catálogos
- 🧠 [Estados de Trámites](../../04-concepts/) - Concepto sobre los estados y su significado

---

## Problemas Comunes

| Problema | Posible Causa | Solución |
|----------|-----------------|----------|
| No puedo guardar: "Código ya existe" | Código duplicado | Usa un código diferente o verifica que el tipo no exista |
| No aparece en la lista | Tipo no está activo | Marca "Activo" = Sí al crear el tipo |
| Error al eliminar: "Tiene trámites relacionados" | Tipo está en uso | Primero elimina o reasigna los trámites asociados |
| No encuentro el tipo | Filtro activo | Limpia los filtros o haz una búsqueda más amplia |
| "Permisos insuficientes" | Usuario sin acceso de admin | Contacta a tu administrador para verificar tus permisos |
| Error de validación: "Formato inválido" | Caracteres especiales | Usa solo letras mayúsculas y guiones en el código |

---

## Consejos y Mejores Prácticas

### Para una Gestión Eficiente de Catálogos

1. **Usa códigos memorables**
   - Fáciles de recordar y escribir
   - Cortos pero descriptivos
   - Evita abreviaturas confusas

2. **Mantén consistencia en nombres**
   - Usa formato similar en todos los tipos
   - Sé específico pero profesional
   - Evita tecnicismos innecesarios

3. **Revisa tiempos estimados regularmente**
   - Ajusta según la experiencia real
   - Considera variaciones por complejidad
   - Actualiza si los procesos cambian

4. **Documenta razones de cambios**
   - Usa la bitácora para registrar "por qué" cambió algo
   - Esto ayuda en el futuro a entender decisiones

5. **No elimines, desactiva**
   - Mantén el historial completo
   - Usa el campo "Activo" para controlar disponibilidad
   - Esto ayuda a entender la evolución del sistema

6. **Coordina con otros departamentos**
   - Verifica que los departamentos coincidan en sus nombres
   - Asegúrate de que las asignaciones sean correctas

7. **Realiza auditorías periódicas**
   - Verifica que todos los catálogos estén actualizados
   - Elimina registros duplicados o desactualizados
   - Verifica que las relaciones sean correctas

---

## Preguntas Frecuentes

**P: ¿Puedo crear un tipo de trámite sin código único?**
R: No, el código es obligatorio y debe ser único en todo el sistema. Usa el código sugerido o crea uno único.

**P: ¿Qué pasa si elimino un tipo que todavía necesito?**
R: Si lo eliminaste por error, tendrás que crear un nuevo tipo con el mismo código (si aún está disponible) o coordinar con el equipo de desarrollo para recuperarlo.

**P: ¿Puedo cambiar el código de un tipo existente?**
R: No es recomendado porque los códigos se usan para referencia en los trámites. Si es absolutamente necesario, primero verifica que no haya trámites creados con ese código.

**P: ¿Los cambios se aplican inmediatamente a los trámites existentes?**
R: Depende. Algunos cambios (como nombre) se reflejan inmediatamente. Otros (como código) requieren que los trámites sean actualizados manualmente.

**P: ¿Cómo sé qué departamentos debo seleccionar?**
R: Consulta con los departamentos correspondientes. Cada departamento debe proporcionarte una lista de los tipos de trámite que gestionan.

---

## Referencias Adicionales

- [Glosario de Términos](../01-onboarding/glossary.md) - Para entender términos como "catálogo", "tipo de trámite"
- [Tutorial: Configurar Usuarios](./setup-users.md) - Tutorial fundamental si no lo has completado aún
- [Tutorial: Flujo de Trabajo Diario](../../02-tutorials/operators/manage-workflow.md) - Para entender cómo los operadores usan los catálogos

---

**¿Necesitas ayuda?**
- Consulta las [Guías de Administradores](../../03-guides/admins/)
- Contacta a tu administrador del sistema
- Revisa el [Troubleshooting](../../03-guides/admins/)

---

*Última actualización: 26 de Febrero de 2026*
