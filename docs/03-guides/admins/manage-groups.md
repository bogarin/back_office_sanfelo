---
Title: Gestionar Grupos de Usuarios - Guía para Administradores
Role: admin
Related: [Glosario: Admin y Operador](../../01-onboarding/glossary.md#admin-administrador)
---

## Resumen

Esta guía te enseñará cómo crear, editar y gestionar grupos de usuarios en el sistema Backoffice de Trámites. Los grupos permiten asignar permisos de manera colectiva a usuarios con roles similares.

## ¿Cuándo usar esta guía?

- Cuando necesitas crear un nuevo grupo de usuarios
- Cuando debes agregar o quitar permisos de un grupo
- Cuando un usuario cambia de rol y necesita moverse de grupo
- Cuando necesitas reorganizar la estructura de permisos
- Cuando debes auditor quién tiene qué permisos

---

## Conceptos Fundamentales

### ¿Qué es un Grupo de Usuarios?

**Definición**: Un grupo es una colección de usuarios que comparten el mismo conjunto de permisos. En lugar de asignar permisos individualmente a cada usuario, se asignan al grupo.

**Ventajas de usar grupos**:
- **Eficiencia**: Asigna permisos una vez y afecta a todos los usuarios del grupo
- **Consistencia**: Asegura que usuarios del mismo rol tengan los mismos permisos
- **Mantenimiento**: Más fácil actualizar permisos (cambia en el grupo, afecta a todos)
- **Auditoría**: Más fácil revisar quién tiene qué tipo de acceso

**Ejemplo**:
- Grupo `operadores` tiene 20 usuarios
- Si agregas un permiso nuevo al grupo, automáticamente los 20 usuarios lo tienen
- Sin grupos, tendrías que agregar el permiso a 20 usuarios individualmente

---

### Relación entre Grupos y Permisos

```
Usuario ─► Grupo ─► Permisos
```

**Flujo**:
1. Crea un grupo (ej: `operadores`)
2. Asigna permisos al grupo (ej: `view_tramite`, `add_tramite`)
3. Agrega usuarios al grupo
4. Los usuarios heredan todos los permisos del grupo

**Un usuario puede estar en múltiples grupos**:
```
Usuario: Juan Pérez
├── Grupo: operadores (permisos básicos)
└── Grupo: auditores (permisos adicionales)
```

---

## Grupos Predeterminados del Sistema

### Grupo: admin_users

**Descripción**: Usuarios con permisos administrativos completos.

**Permisos típicos**:
- ✅ Todos los permisos de tramites (add, change, delete, view)
- ✅ Todos los permisos de catalogos (tipos, estatus, requisitos, peritos)
- ✅ Todos los permisos de usuarios (add, change, delete, view)
- ✅ Todos los permisos de grupos (add, change, delete, view)
- ✅ Todos los permisos de bitácora (view completo)
- ✅ Acceso completo a configuración del sistema

**Quién debería estar en este grupo**:
- Administradores del sistema
- Personal de TI con permisos de configuración
- Supervisores que necesitan acceso completo

---

### Grupo: operadores

**Descripción**: Usuarios que gestionan trámites diariamente.

**Permisos típicos**:
- ✅ view_tramite (solo asignados a sí mismos)
- ✅ add_tramite (crear nuevos trámites)
- ✅ change_tramite (estado y campos específicos)
- ✅ add_documento (adjuntar documentos)
- ✅ change_documento (estado de documento)
- ✅ view_documento (ver documentos)
- ❌ NO permisos de usuarios, grupos o configuración global
- ❌ NO pueden ver trámites de otros operadores

**Quién debería estar en este grupo**:
- Operadores que procesan trámites
- Personal de departamentos específicos
- Usuarios de atención al público

---

### Grupo: peritos

**Descripción**: Peritos especializados que participan en trámites.

**Permisos típicos**:
- ✅ view_tramite (solo asignados)
- ✅ change_tramite (solo campos que peritos pueden modificar)
- ✅ view_documento (ver documentos de trámites asignados)
- ✅ add_observaciones (agregar notas técnicas)

**Quién debería estar en este grupo**:
- Peritos arquitectónicos
- Peritos topógrafos
- Peritos ingenieros
- Otros especialistas

---

### Grupo: auditores

**Descripción**: Usuarios que revisan trámites para auditoría.

**Permisos típicos**:
- ✅ view_tramite (todos, no solo asignados)
- ✅ view_bitacora (historial completo de auditoría)
- ✅ view_documento (todos los documentos)
- ❌ NO permisos de modificación (no pueden cambiar nada)

**Quién debería estar en este grupo**:
- Auditores internos
- Personal de control de calidad
- Supervisores que solo revisan

---

## Pasos para Crear un Nuevo Grupo

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

### Paso 2: Navegar a la Sección de Grupos

1. En el panel principal, busca la sección **Usuarios y grupos**
2. Haz clic en **"Grupos"** (Groups)

**Resultado esperado**: Lista de grupos existentes con sus permisos.

---

### Paso 3: Crear Nuevo Grupo

1. Haz clic en el botón **"Añadir grupo"** (Add Group)
2. Verás el formulario de creación de grupo

---

### Paso 4: Llenar los Campos

#### 4.1 Nombre del Grupo (Obligatorio)

**Descripción**: Nombre único del grupo.

**Cómo llenarlo**:
- Usa nombres cortos y descriptivos
- Usa guiones bajos en lugar de espacios
- Usa minúsculas para consistencia

**Ejemplos**:
- ✅ `operadores_urbanismo`
- ✅ `auditores_internos`
- ✅ `peritos_arquitectonicos`
- ❌ `Grupo de Operadores de Urbanismo` - Demasiado largo
- ❌ `OPERADORES` - Mayúsculas rompen consistencia

> **Consejo**: Usa un estándar de nomenclatura en toda tu organización.

---

#### 4.2 Permisos (Obligatorio)

**Descripción**: Permisos que tendrá este grupo.

**Cómo seleccionar permisos**:

1. El sistema muestra dos columnas:
   - **Permisos disponibles**: Permisos que PUEDES asignar
   - **Permisos seleccionados**: Permisos YA asignados

2. Selecciona los permisos apropiados:
   - Haz clic en un permiso para seleccionarlo
   - Usa Ctrl+Clic para seleccionar múltiples
   - Usa Shift+Clic para seleccionar un rango

3. Mueve los permisos seleccionados a la columna de "Permisos seleccionados":
   - Usa el botón de flecha derecha (►) para agregar
   - Usa el botón de flecha izquierda (◄) para quitar

**Formato de permisos**:
- `[app]_[acción]_[modelo]`
- Ejemplo: `add_tramite`, `view_tramite`, `change_tramite`

**Acciones disponibles**:
- `add` - Crear nuevos registros
- `view` - Ver registros
- `change` - Editar registros
- `delete` - Eliminar registros

---

### Paso 5: Guardar el Nuevo Grupo

1. Revisa que el nombre del grupo sea claro
2. Verifica que los permisos sean los apropiados
3. Haz clic en el botón **"Guardar"** (Save)

**Resultado esperado**:
- Verás un mensaje verde de confirmación
- El nuevo grupo aparecerá en la lista
- Ya puedes asignar usuarios a este grupo

---

## Asignar Usuarios a un Grupo

### Método 1: Desde el Perfil del Usuario

1. Ve a la sección **Usuarios**
2. Haz clic en el nombre del usuario que quieres editar
3. Busca la sección **"Grupos"** (Groups)
4. Haz clic en el campo de grupos
5. Selecciona el grupo o grupos deseados
6. Haz clic en el botón derecho para mover los grupos seleccionados
7. Guardar

**Resultado esperado**: El usuario ahora tiene todos los permisos del grupo asignado.

---

### Método 2: Desde el Perfil del Grupo

1. Ve a la sección **Grupos**
2. Haz clic en el nombre del grupo que quieres editar
3. Busca la sección **"Usuarios"**
4. Agrega usuarios al grupo:
   - Selecciona usuarios de la lista disponible
   - Mueve a la lista de usuarios seleccionados
5. Guardar

**Resultado esperado**: Los usuarios seleccionados ahora tienen los permisos del grupo.

> **Nota**: Un usuario puede estar en múltiples grupos. En ese caso, tiene la combinación de permisos de todos sus grupos.

---

## Editar un Grupo Existente

### Agregar Permisos a un Grupo

**Cuándo agregar**:
- Cuando el sistema tiene nueva funcionalidad que requiere permisos
- Cuando un grupo necesita acceso adicional
- Cuando una política cambia y requieres más permisos

**Pasos**:
1. Desde la lista de grupos, haz clic en el nombre del grupo
2. En la sección de permisos, selecciona los nuevos permisos
3. Muévelos a la columna de permisos seleccionados
4. Guardar

**Resultado esperado**: Todos los usuarios del grupo ahora tienen los nuevos permisos.

> **Importante**: El cambio afecta a TODOS los usuarios del grupo simultáneamente.

---

### Quitar Permisos de un Grupo

**⚠️ IMPORTANTE**: Revocar permisos puede afectar el trabajo de los usuarios.

**Cuándo quitar**:
- Cuando un permiso se asignó por error
- Cuando un rol cambia y requiere menos permisos
- Por razones de seguridad o compliance

**Pasos**:
1. Desde la lista de grupos, haz clic en el nombre del grupo
2. En la sección de permisos, selecciona los permisos a quitar
3. Muévelos a la columna de permisos disponibles
4. Guardar

**Resultado esperado**: Los usuarios del grupo ya no tienen esos permisos.

> **Advertencia**: Antes de quitar permisos, verifica que:
> - Ningún usuario está usando esos permisos activamente
> - No hay trámites en proceso que requieran esos permisos
> - Los usuarios han sido notificados del cambio

---

## Cambiar de Grupo a un Usuario

### Cuándo Cambiar de Grupo

**Situaciones comunes**:
- **Promoción**: Operador → Administrador
- **Transferencia**: Usuario cambia de departamento
- **Rol especial**: Usuario temporalmente necesita permisos adicionales

---

### Pasos para Cambiar de Grupo

**Opción A: Reemplazar grupos (recomendado)**

1. Ve al perfil del usuario
2. En la sección "Grupos", desmarca todos los grupos actuales
3. Marca el/los nuevos grupos
4. Agrega observación explicando el cambio
5. Guardar

**Ejemplo de observación**:
```
Usuario: María González
Cambio: De 'operadores' a 'admin_users'
Motivo: Promoción a administrador del sistema
Fecha: 2026-02-27
Aprobado por: Juan Pérez, Director
```

**Opción B: Agregar grupos (permisos acumulativos)**

1. Ve al perfil del usuario
2. En la sección "Grupos", marca el nuevo grupo
3. Mantén los grupos existentes marcados
4. Agrega observación explicando
5. Guardar

**Resultado esperado**: El usuario ahora tiene la combinación de permisos de todos sus grupos.

> **Nota**: La Opción A es más clara. La Opción B solo se usa cuando el usuario genuinamente necesita permisos de múltiples roles simultáneamente.

---

## Eliminar un Grupo

### Cuándo Eliminar un Grupo

**Situaciones apropiadas**:
- ✅ Grupo vacío que nunca se usó
- ✅ Grupo duplicado creado por error
- ✅ Grupo que ya no corresponde a ninguna estructura organizacional

**⚠️ ANTES DE ELIMINAR**, verifica:
1. ¿Hay usuarios en este grupo?
   - Si hay, reasigna a otro grupo
2. ¿Hay trámites en proceso que dependen de estos permisos?
   - Si hay, espera hasta que se completen
3. ¿Es el grupo crítico para alguna operación?
   - Si es crítico, no lo elimines, renómbralo

---

### Pasos para Eliminar un Grupo

1. Reasigna todos los usuarios a otro grupo
2. Desde la lista de grupos, haz clic en el botón de eliminación (papelera)
3. El sistema pedirá confirmación
4. Lee el mensaje de confirmación
5. Haz clic en **"Sí, eliminar"** si estás seguro

**Resultado esperado**: El grupo es eliminado permanentemente.

> **ADVERTENCIA**: Esta acción es irreversible. No hay opción de "deshacer".

---

## Reglas Importantes

### Regla 1: Principio de Menor Privilegio

**Concepto**: Da a cada usuario SOLO los permisos necesarios para cumplir con sus responsabilidades.

**Por qué aplicar**:
- Reduce el riesgo de acceso no autorizado
- Limita el daño si una cuenta es comprometida
- Facilita la auditoría de quién puede hacer qué

**Ejemplo**:
- Un operador NO necesita permisos para gestionar usuarios
- Un perito NO necesita permisos para configurar catálogos
- Un auditor NO necesita permisos para modificar datos

---

### Regla 2: Documentar Cambios de Permisos

**✅ REQUERIDO**:
- Documentar en bitácora todos los cambios de permisos
- Incluir razón del cambio
- Registrar quién aprobó el cambio (si aplica)

**Qué documentar**:
```
Fecha: 2026-02-27
Usuario: Juan Pérez (admin)
Cambio: Agregado permiso 'delete_tramite' al grupo 'operadores'
Justificación: Necesario para que operadores puedan eliminar trámites rechazados
Aprobado por: María García, Directora
```

> **Consecuencia**: Los cambios sin documentación pueden ser cuestionados en auditorías.

---

### Regla 3: Revisar Permisos Periódicamente

**Frecuencia recomendada**: Cada 6 meses o anualmente.

**Qué revisar**:
- ¿Todos los grupos tienen permisos actuales?
- ¿Hay permisos obsoletos que se pueden quitar?
- ¿Hay permisos faltantes que se deben agregar?
- ¿Hay usuarios en grupos que ya no corresponden?

**Resultado esperado**: Grupos actualizados y alineados con las necesidades actuales.

---

### Regla 4: No Dar Permisos Directos a Usuarios

**Recomendación**: Siempre usa grupos en lugar de asignar permisos directamente a usuarios.

**Por qué**:
- Más fácil mantener
- Consistencia entre usuarios del mismo rol
- Auditoría más simple

**Excepciones**:
- Un solo usuario necesita un permiso especial y temporal
- El usuario es superusuario (raro caso)
- Situaciones de emergencia (debe documentarse)

---

## Solución de Problemas

| Problema | Posible Causa | Solución |
|----------|----------------|----------|
| Usuario no puede ver trámites | No tiene permisos apropiados | Agregar permisos 'view_tramite' al grupo |
| Usuario no puede crear trámites | Falta permiso 'add_tramite' | Agregar permiso al grupo |
| Usuario ve trámites de otros | Tiene permisos demasiado amplios | Revisar grupo y quitar permisos |
| Permisos no se aplican | Usuario no tiene sesión activa | Cerrar y volver a abrir sesión |
| No puedo eliminar grupo | Grupo tiene usuarios asignados | Primero reasigna los usuarios |

---

## Solución de Problemas Específicos

### Problema: Usuario Permite Más de lo Necesario

**Situación**: Un usuario tiene permisos que no corresponden a su rol.

**Pasos**:
1. Revisar qué grupos tiene el usuario
   - Ir al perfil del usuario
   - Ver la sección "Grupos"
2. Identificar grupos inapropiados
   - ¿Está en 'admin_users' cuando no debería?
   - ¿Está en grupos de otros departamentos?
3. Quitar los grupos inapropiados
   - Desmarcar los grupos
   - Mantener solo los que correspondan
4. Agregar observación documentando el cambio

**Resultado esperado**: Usuario ahora tiene solo los permisos apropiados.

---

### Problema: Grupo con Permisos Demasiados Amplios

**Situación**: Un grupo tiene permisos que exceden lo que sus usuarios deberían tener.

**Ejemplo**: El grupo 'operadores' puede eliminar trámites (permiso 'delete_tramite').

**Pasos**:
1. Verificar si el permiso se está usando actualmente
   - Revisar bitácora para ver acciones recientes
2. Si no se usa, quitar el permiso:
   - Editar el grupo
   - Quitar el permiso 'delete_tramite'
   - Documentar la razón
3. Si se usa, investigar:
   - ¿Quién está usando el permiso y para qué?
   - ¿Es realmente necesario o hay alternativa?
   - ¿Debería crearse un grupo especial para esa función?

**Resultado esperado**: Grupo con permisos apropiados a su rol.

---

### Problema: Necesidad de Permiso Especial para Un Usuario

**Situación**: Un solo usuario necesita un permiso que nadie más necesita.

**Opciones**:

**Opción A: Crear grupo especial** (recomendada)
1. Crear un nuevo grupo (ej: `operadores_especiales`)
2. Agregar el permiso especial al grupo
3. Asignar al usuario a este nuevo grupo
4. El usuario mantiene sus grupos originales + este nuevo

**Opción B: Asignar permiso directo al usuario** (no recomendada, pero posible)
1. Ir al perfil del usuario
2. Agregar el permiso directamente
3. Documentar extensivamente el por qué

> **Consejo**: La Opción A es mejor porque mantiene el principio de grupos y facilita auditoría.

---

## Resumen

En esta guía has aprendido:

✅ Qué son los grupos de usuarios y por qué usarlos
✅ Qué grupos predeterminados existen en el sistema
✅ Cómo crear un nuevo grupo
✅ Cómo asignar usuarios a grupos
✅ Cómo agregar y quitar permisos de grupos
✅ Cómo cambiar de grupo a un usuario
✅ Cuándo y cómo eliminar grupos
✅ Reglas importantes para gestión de grupos
✅ Cómo resolver problemas comunes

---

## ¿Qué sigue?

Ahora que puedes gestionar grupos, puedes aprender:

### Guías siguientes:
- 📋 [Configurar Usuarios](../../02-tutorials/admins/setup-users.md) - Tutorial fundamental de usuarios
- 📋 [Agregar Peritos](./add-peritos.md) - Tutorial para gestionar peritos especializados
- 📋 [Configurar Costos](./configure-costs.md) - Tutorial para definir costos

### Tutoriales relacionados:
- 📋 [Gestión de Catálogos](../../02-tutorials/admins/manage-catalogs.md) - Tutorial para gestionar catálogos

---

**¿Necesitas ayuda?**
- Consulta las [Guías de Administradores](../03-guides/admins/)
- Contacta a tu equipo de desarrollo si hay errores técnicos
- Revisa el [Troubleshooting](../03-guides/admins/)

---

*Última actualización: 27 de Febrero de 2026*
