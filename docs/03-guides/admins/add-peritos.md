---
Title: Agregar Peritos Especializados - Guía para Administradores
Role: admin
Related: [Glosario: Perito](../../01-onboarding/glossary.md#perito)
---

## Resumen

Esta guía te enseñará cómo agregar y gestionar peritos especializados en el sistema Backoffice de Trámites. Los peritos son profesionales que participan en el proceso de trámites, proporcionando evaluaciones técnicas especializadas.

## ¿Cuándo usar esta guía?

- Cuando incorporas un nuevo perito al sistema
- Cuando necesitas actualizar la información de un perito existente
- Cuando debes desactivar peritos que ya no trabajan con el gobierno
- Cuando modificas los honorarios de un perito
- Cuando asignas peritos a tipos de trámites específicos

---

## Casos de Uso Comunes

| Situación | Acción |
|-----------|--------|
| Nuevo perito arquitectónico se incorpora | Crear perfil de perito con especialidad |
| Perito cambia de teléfono | Editar información de contacto |
| Perito se retira | Desactivar perito (no eliminar) |
| Honorarios de perito aumentan | Actualizar tarifa en perfil |
| Perito puede atender más tipos de trámite | Asignar perito a tipos adicionales |

---

## Tipos de Peritos Comunes

### Perito Arquitectónico

**Especialidad**: Evalúa proyectos arquitectónicos, planos y diseños de construcción.

**Trámites típicos**:
- Licencias de Construcción
- Licencias de Uso de Suelo
- Regularizaciones

**Habilidades requeridas**:
- Lectura e interpretación de planos
- Conocimiento de normativas de construcción
- Capacidad de identificar violaciones

---

### Perito Topógrafo

**Especialidad**: Mide y delimita terrenos, realiza divisiones de linderos.

**Trámites típicos**:
- División de Linderos
- Regularización de Predios
- Reubicación de mojones

**Habilidades requeridas**:
- Uso de equipos topográficos
- Lectura de planos catastrales
- Conocimiento de leyes de propiedad

---

### Perito Ingeniero Civil

**Especialidad**: Evalúa aspectos estructurales y de ingeniería de proyectos.

**Trámites típicos**:
- Licencias de Construcción (aspectos estructurales)
- Dictámenes de seguridad estructural
- Evaluación de riesgos

**Habilidades requeridas**:
- Conocimiento de cálculo estructural
- Evaluación de materiales
- Identificación de riesgos sísmicos

---

### Perito Valuador

**Especialidad**: Determina el valor de inmuebles y predios.

**Trámites típicos**:
- Avalúos para préstamos
- Actualización de valores catastrales
- Determinación de derechos

**Habilidades requeridas**:
- Conocimiento del mercado inmobiliario
- Métodos de valuación
- Análisis comparativo

---

## Pasos para Agregar un Nuevo Perito

### Paso 1: Acceder al Panel de Administración

1. Abre tu navegador web
2. Ingresa a la URL:
   ```
   http://<host-del-sistema>/admin/
   ```
3. Ingresa tus credenciales de administrador
4. Haz clic en **"Acceder"**

**Resultado esperado**: Panel principal de Django Admin.

---

### Paso 2: Navegar al Catálogo de Peritos

1. En el panel principal, busca la sección **CATÁLOGOS**
2. Haz clic en **"Peritos"**

**Resultado esperado**: Lista de peritos existentes.

---

### Paso 3: Crear Nuevo Perito

1. Haz clic en el botón **"Añadir perito"** (Add Perito)
2. Verás el formulario de creación de perito

---

### Paso 4: Llenar los Campos Obligatorios

#### 4.1 Nombre Completo (Obligatorio)

**Descripción**: Nombre completo real del perito.

**Cómo llenarlo**:
- Escribe: `Nombre Apellido1 [Apellido2]`
- Ejemplo: `Ing. Juan Carlos Pérez García`
- Incluye título profesional si aplica

> **Importante**: Este nombre aparecerá en los reportes y asignaciones. Asegúrate de que sea el nombre oficial del perito.

---

#### 4.2 Especialidad (Obligatorio)

**Descripción**: Área de especialización del perito.

**Cómo llenarlo**: Selecciona del menú desplegable:

- **Arquitectónico**: Para peritos que evalúan proyectos arquitectónicos
- **Topógrafo**: Para peritos que miden y delimitan terrenos
- **Ingeniero Civil**: Para evaluaciones estructurales
- **Valuador**: Para determinación de valores
- **Otro**: Para especialidades no listadas

**Resultado esperado**: El perito será asignable a trámites de tipos relacionados con su especialidad.

---

#### 4.3 Cédula Profesional (Obligatorio)

**Descripción**: Número de cédula profesional del perito.

**Cómo llenarlo**:
- Ingresa el número completo
- Ejemplo: `12345678` o `MX-12345678`

**Formatos válidos**:
- Solo números
- Con prefijo de país (ej: MX-12345678)

> **Importante**: La cédula profesional debe ser válida y vigente. Esta información puede ser solicitada para auditorías.

---

#### 4.4 Teléfono de Contacto (Obligatorio)

**Descripción**: Número telefónico para comunicarse con el perito.

**Cómo llenarlo**:
- Incluye código de área si es necesario
- Ejemplo: `+52 55 1234 5678` o `5512345678`

**Formatos recomendados**:
- `+52 [lada] [número]` - Internacional
- `[lada] [número]` - Nacional sin código de país

> **Nota**: Este teléfono se usa cuando operadores o administradores necesitan contactar al perito. Asegúrate de que sea un teléfono que responda durante horas laborales.

---

#### 4.5 Correo Electrónico (Obligatorio)

**Descripción**: Dirección de correo electrónico del perito.

**Cómo llenarlo**:
- Usa un correo profesional si es posible
- Ejemplo: `juan.perez@peritos-profesionales.com.mx`

**Requisitos**:
- Debe ser un correo válido
- Preferiblemente de dominio profesional
- No usar correos personales temporales

> **Importante**: El correo se usa para notificaciones oficiales y comunicaciones importantes. Verifica que sea correcto.

---

#### 4.6 Activo (Obligatorio)

**Descripción**: Indica si el perito está disponible actualmente.

**Cómo llenarlo**:
- Marca la casilla "Activo" (Is Active) si el perito puede recibir asignaciones
- No marques si está temporalmente no disponible

**Resultado esperado**:
- ✅ Marcado: El perito aparecerá en la lista para asignación
- ❌ No marcado: El perito no será asignable a nuevos trámites

> **Consejo**: Usa "Inactivo" cuando un perito está de vacaciones, en licencia médica, o temporalmente no disponible. No elimines peritos.

---

### Paso 5: Llenar Campos Opcionales

#### 5.1 Honorarios Base

**Descripción**: Tarifa base por servicio del perito (en UMAs).

**Cómo llenarlo**:
- Ingresa un número decimal
- Ejemplo: `0.5`, `1.0`, `2.5`

**Explicación**:
- El costo final se calcula como: (Honorarios en UMAs) × (Valor UMA actual)
- Si se deja vacío, se usa un valor predeterminado

> **Nota**: Los honorarios pueden variar según el tipo de trámite. Este es un valor base que puede ajustarse por asignación.

---

#### 5.2 Observaciones

**Descripción**: Notas adicionales sobre el perito.

**Cuándo usarlo**:
- Para registrar información relevante sobre el perito
- Para documentar restricciones o condiciones especiales
- Para agregar contexto útil para operadores

**Ejemplos**:
- "Solo disponible los martes y jueves"
- "Especialista en proyectos residenciales"
- "Requiere 48 horas de anticipación para asignaciones"

> **Consejo**: Usa observaciones para información que ayuda a operadores a seleccionar al perito apropiado.

---

### Paso 6: Asignar Tipos de Trámite

**Descripción**: Define a qué tipos de trámite puede ser asignado este perito.

**Cómo hacerlo**:
1. En el formulario, busca la sección "Tipos de Trámite"
2. Haz clic en el campo para ver todos los tipos disponibles
3. Selecciona los tipos que corresponden a la especialidad del perito
4. Usa Ctrl+Clic para seleccionar múltiples tipos

**Asignación por especialidad**:

| Especialidad | Tipos de Trámite Recomendados |
|-------------|------------------------------|
| **Arquitectónico** | Licencia de Construcción, Licencia de Uso de Suelo |
| **Topógrafo** | División de Linderos, Regularización de Predios |
| **Ingeniero Civil** | Licencia de Construcción, Dictámenes Estructurales |
| **Valuador** | Avalúos, Actualización Catastral |

> **Importante**: Solo asigna tipos de trámite que correspondan a la especialidad real del perito. Asignar tipos inapropiados puede causar problemas de calidad.

---

### Paso 7: Guardar el Nuevo Perito

1. Revisa todos los campos llenados
2. Haz clic en el botón **"Guardar"** (Save)

**Resultado esperado**:
- Verás un mensaje verde de confirmación
- El nuevo perito aparecerá en la lista
- El perito ya puede ser asignado a trámites

---

## Editar un Perito Existente

### Cambiar Información de Contacto

**Cuándo cambiar**:
- Cuando el perito cambia de teléfono o correo
- Cuando se actualiza información de contacto

**Pasos**:
1. Desde la lista, haz clic en el nombre del perito
2. Actualiza los campos necesarios (teléfono, correo)
3. Agrega observación del cambio: "Teléfono actualizado el [fecha]"
4. Guardar

**Resultado esperado**: La información se actualiza y queda registrada en la bitácora.

---

### Actualizar Honorarios

**Cuándo cambiar**:
- Cuando el perito actualiza sus tarifas
- Cuando se acuerda un cambio en los honorarios

**Pasos**:
1. Desde la lista, haz clic en el nombre del perito
2. Actualiza el campo de honorarios base
3. Agrega observación: "Honorarios actualizados de X a Y UMAs. Justificación: [razón]"
4. Guardar

> **Nota**: Los cambios en honorarios pueden afectar trámites futuros pero no deberían afectar trámites ya asignados.

---

### Desactivar un Perito

**Cuándo desactivar**:
- Perito de vacaciones o licencia temporal
- Perito enfermo o incapacidad temporal
- Perito temporalmente no disponible por cualquier razón

**Cuándo NO desactivar**:
- Perito que solo atiende ciertos días (usa observaciones en su lugar)

**Pasos**:
1. Desde la lista, haz clic en el nombre del perito
2. Desmarca la casilla "Activo" (Is Active)
3. Agrega observación con fecha de reactivación esperada
4. Guardar

**Resultado esperado**: El perito ya no aparecerá para nuevas asignaciones, pero su historial se mantiene.

> **Importante**: Los peritos desactivados mantienen su historial de asignaciones. No pierden información de trámites anteriores.

---

### Reactivar un Perito

**Cuándo reactivar**:
- Cuando el perito regresa de vacaciones
- Cuando la licencia o incapacidad termina
- Cuando el perito está nuevamente disponible

**Pasos**:
1. Desde la lista, haz clic en el nombre del perito inactivo
2. Marca la casilla "Activo" (Is Active)
3. Agrega observación: "Reactivado el [fecha]"
4. Guardar

**Resultado esperado**: El perito nuevamente aparece disponible para asignaciones.

---

## Reglas Importantes

### Regla 1: No Eliminar Peritos con Historial

**⚠️ IMPORTANTE**: Nunca elimines un perito que tiene trámites asignados.

**Por qué**:
- Eliminar un perito puede causar problemas en el historial de trámites
- Pierde información importante sobre quién evaluó qué trámite
- Causa inconsistencias en la bitácora

**Qué hacer en su lugar**:
- **Si el perito se retira definitivamente**: Desactívalo
- **Si hay un error**: Corrige la información
- **Si creaste un perito duplicado**: Eliminalo solo si no tiene asignaciones

---

### Regla 2: Especialidades Deben Ser Reales

**❌ NO PERMITIDO**:
- Asignar especialidades que el perito no tiene
- Cambiar especialidades por conveniencia
- Crear peritos con especialidades no existentes

**✅ RECOMENDADO**:
- Verificar cédula profesional antes de asignar especialidad
- Solicitar documentación que certifique la especialidad
- Mantener actualizados los registros de especialidades

> **Consecuencia**: Asignar especialidades incorrectas puede causar evaluaciones deficientes y problemas legales.

---

### Regla 3: Contacto Siempre Actualizado

**Requisito**: Mantén siempre actualizada la información de contacto.

**Por qué**:
- Operadores necesitan contactar peritos para coordinaciones
- Los trámites pueden retrasarse si no se puede contactar al perito
- Los ciudadanos pueden afectarse negativamente

**Cómo mantener**:
- Solicita actualización de contacto anualmente
- Verifica que teléfonos y correos funcionen
- Actualiza inmediatamente cuando el perito notifique cambios

---

## Solución de Problemas

| Problema | Posible Causa | Solución |
|----------|----------------|----------|
| No puedo asignar perito a trámite | Perito no está activo | Marca "Activo" o verifica estado |
| Perito no aparece en lista | Tipo de trámite no asignado | Asigna el tipo de trámite al perito |
| Cédula profesional duplicada | Ya existe perito con esa cédula | Verifica si es el mismo perito o hay error |
| Error al guardar: "Cédula inválida" | Formato incorrecto | Ingresa solo números o formato válido |
| Perito no responde al contacto | Datos desactualizados | Actualiza teléfono y correo |

---

## Solución de Problemas Específicos

### Problema: Perito Duplicado

**Situación**: Creaste dos peritos para la misma persona (por error).

**Pasos**:
1. Verifica qué perito tiene asignaciones:
   - Haz clic en cada perito para ver sus asignaciones
2. Si uno no tiene asignaciones:
   - Elimina el perito duplicado
3. Si ambos tienen asignaciones:
   - Desactiva uno
   - Reasigna sus trámites al otro perito
   - Documenta el cambio en observaciones

**Resultado esperado**: Solo queda un registro del perito con todas sus asignaciones.

---

### Problema: Perito con Cédula Incorrecta

**Situación**: Te das cuenta de que ingresaste mal el número de cédula profesional.

**Pasos**:
1. Accede al perfil del perito
2. Corrige el número de cédula
3. Agrega observación: "Cédula corregida de [antiguo] a [nuevo]. Motivo: [razón]"
4. Guardar

**Resultado esperado**: La cédula se corrige y queda registrado el cambio en la bitácora.

---

## Resumen

En esta guía has aprendido:

✅ Qué es un perito y qué tipos existen
✅ Cómo crear un nuevo perito con todos los campos requeridos
✅ Cómo asignar especialidades y tipos de trámite
✅ Cómo editar información de peritos existentes
✅ Cómo activar y desactivar peritos
✅ Reglas importantes para gestionar peritos
✅ Cómo resolver problemas comunes

---

## ¿Qué sigue?

Ahora que puedes gestionar peritos, puedes aprender:

### Guías siguientes:
- 📋 [Configurar Costos por Trámite](./configure-costs.md) - Tutorial para definir costos
- 📋 [Gestionar Grupos de Usuarios](./manage-groups.md) - Tutorial para gestionar grupos
- 📋 [Gestión de Catálogos](../../02-tutorials/admins/manage-catalogs.md) - Tutorial para gestionar todos los catálogos

### Tutoriales relacionados:
- 📋 [Configurar Usuarios](../../02-tutorials/admins/setup-users.md) - Tutorial fundamental de usuarios

---

**¿Necesitas ayuda?**
- Consulta las [Guías de Administradores](../03-guides/admins/)
- Contacta a tu equipo de desarrollo si hay errores técnicos
- Revisa el [Troubleshooting](../03-guides/admins/)

---

*Última actualización: 27 de Febrero de 2026*
