---
Title: Configurar Usuarios - Tutorial para Administradores
Role: admin
Time: 20 minutos
Level: beginner
Prerequisites: Usuario administrativo con permisos de configuración de usuarios
---

## Resumen

Este tutorial te guiará paso a paso en la configuración de usuarios del sistema Backoffice de Trámites. Aprenderás a crear usuarios, asignarles permisos, agruparlos en grupos, y administrar el acceso de manera segura y efectiva.

## Lo que aprenderás

- Crear nuevos usuarios en el sistema
- Asignar permisos apropiados (Admin vs Operador)
- Crear y gestionar grupos de usuarios
- Activar/desactivar usuarios temporalmente
- Restablecer contraseñas de usuarios
- Verificar el historial de cambios en auditoría

## Requisitos previos

- ✅ Usuario administrativo con permisos completos
- ✅ Acceso a la intranet del Gobierno de San Felipe
- ✅ Conocimiento básico de los roles del sistema (Admin vs Operador)
- ✅ Navegador web moderno
- ❌ NO necesitas conocimientos técnicos de Django o bases de datos

---

## Paso 1: Acceder al Panel de Administración

### 1.1 Acceder al Django Admin

1. Abre tu navegador web
2. Ingresa a la URL:
   ```
   http://<host-del-sistema>/admin/
   ```
3. Ingresa tus credenciales de administrador
4. Haz clic en **"Acceder"**

**Resultado esperado**: Verás el panel principal de Django Admin con todas las aplicaciones disponibles.

> **Nota**: Como administrador, verás todas las secciones del sistema, incluyendo la de gestión de usuarios.

---

## Paso 2: Entender los Roles de Usuario

### 2.1 Tipos de Usuarios en el Sistema

El sistema tiene dos tipos principales de usuarios:

#### Rol: Admin (Administrador)

**Permisos completos**:
- ✅ Gestionar todos los usuarios del sistema (crear, editar, desactivar)
- ✅ Gestionar grupos y permisos
- ✅ Acceder a todos los catálogos (tipos, estatus, requisitos, peritos)
- ✅ Configurar costos por trámite
- ✅ Ver todos los trámites del sistema (no solo asignados)
- ✅ Ver el historial completo (bitácora) de todo el sistema
- ✅ Acceder a todas las configuraciones del sistema

**Cuándo usar**:
- Para personal de TI o soporte
- Para supervisores del sistema
- Para configuración inicial del sistema
- Para tareas de mantenimiento y administración

#### Rol: Operador

**Permisos limitados**:
- ✅ Ver solo los trámites asignados a sí mismo
- ✅ Crear nuevos trámites
- ✅ Editar el estado de trámites asignados
- ✅ Adjuntar documentos a trámites asignados
- ✅ Ver historial de cambios de sus propios trámites
- ❌ NO pueden ver trámites de otros operadores
- ❌ NO pueden gestionar usuarios o configurar catálogos
- ❌ NO pueden acceder a configuraciones globales

**Cuándo usar**:
- Para el personal que procesa trámites diariamente
- Para usuarios de departamentos específicos
- Para personal operativo (no administrativo)

> **Importante**: Los roles de usuario controlan el acceso a la información y funcionalidades. Asigna el rol apropiado según la responsabilidad del usuario.

---

## Paso 3: Crear un Nuevo Usuario

### 3.1 Acceder a la Sección de Usuarios

1. En el panel principal, busca la sección **Usuarios y grupos** (o "Users and Groups")
2. Haz clic en **Usuarios**

**Resultado esperado**: Verás la lista de usuarios existentes con sus roles y estados.

### 3.2 Iniciar la Creación de Usuario

1. Haz clic en el botón **"Añadir usuario"** (Add User) en la esquina superior derecha
2. Verás el formulario de creación de usuario

### 3.3 Llenar el Formulario de Usuario

#### Campos Obligatorios:

##### 3.3.1 Nombre de Usuario (Username)

- **Descripción**: Nombre único para identificar al usuario en el sistema
- **Cómo llenarlo**:
  - Usa el formato: `nombre.apellido` o `iniciales.apellido`
  - Ejemplo: `juan.perez`, `maria.garcia`, `jgarcia`
- Sin espacios ni caracteres especiales
- Máximo 150 caracteres

**Ejemplos**:
- ✅ `juan.perez` - Bueno, claro, único
- ✅ `jgarcia.operaciones` - Muy bueno, incluye área
- ❌ `juan.perez.01` - Evita números, no es claro
- ❌ `user123` - Muy genérico, no profesional

> **Consejo**: Usa un formato consistente en toda tu organización. Esto facilita la identificación de usuarios.

##### 3.3.2 Nombre Completo

- **Descripción**: Nombre completo real de la persona
- **Cómo llenarlo**:
  - Escribe: `Nombre Apellido1 [Apellido2]` si aplica
  - Ejemplo: `Juan Pérez García`
  - Puedes incluir título si aplica: `Ing. Juan Pérez García`

**Resultado esperado**: El nombre completo aparecerá en las notificaciones y en el historial de cambios.

> **Importante**: Asegúrate de tener permiso para registrar y usar los nombres reales de las personas.

##### 3.3.3 Correo Electrónico (Email)

- **Descripción**: Dirección de correo electrónico del usuario
- **Cómo llenarlo**:
  - Usa el correo institucional si es posible: `nombre.apellido@sanfelipe.gob.mx`
  - Si es personal, usa correo personal
  - Verifica que el correo sea correcto antes de guardar

**Resultado esperado**: El correo se usará para notificaciones de cuenta y recuperación de contraseña.

> **Importante**: El correo debe ser único en el sistema. No puedes asignar el mismo correo a dos usuarios diferentes.

##### 3.3.4 Contraseña (Password)

- **Descripción**: Contraseña inicial del usuario
- **Cómo llenarlo**:
  - Opción A: Deja el campo vacío para que el sistema genere automáticamente una contraseña segura
  - Opción B: Ingresa una contraseña temporal
  - Requisitos si ingresas manualmente:
    - Mínimo 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial (!@#$%&*)

**Ejemplos**:
- ✅ `SanF3l1p3!2026` - Fuerte, cumple requisitos
- ❌ `12345678` - Muy débil, no cumple requisitos
- ❌ `password` - Muy débil, no cumple requisitos

> **Mejor práctica**: Deja el campo vacío para que el sistema genere una contraseña segura. Proporciona la contraseña al usuario a través de canales seguros (no por email).

##### 3.3.5 Estado (Is Active)

- **Descripción**: Si el usuario puede iniciar sesión inmediatamente
- **Cómo llenarlo**: Marca la casilla "Activo" (Is Active)
- **Valor por defecto**: ✅ Activo (marcado)

**Resultado esperado**:
- ✅ Marcado: El usuario puede acceder inmediatamente
- ❌ No marcado: El usuario existe pero no puede acceder

> **Consejo**: Crea usuarios con estado "Activo" para usuarios que deben acceder inmediatamente. Usa "Inactivo" solo cuando necesites preparar el acceso antes de la fecha de inicio.

#### Campos Opcionales:

##### 3.3.6 Primer Nombre y Apellido

- **Descripción**: Separación del nombre completo en dos campos
- **Cómo llenarlo**:
  - `Primer nombre`: Juan
  - `Apellidos`: Pérez García

**Resultado esperado**: El sistema combina estos campos para mostrar el nombre completo en la interfaz.

##### 3.3.7 Is Staff (Is Staff)

- **Descripción**: Indica si el usuario tiene acceso al Django Admin
- **Cómo llenarlo**: Marca la casilla "Es personal" (Is Staff)
- **Recomendación**:
  - ✅ Marcar para Administradores
  - ❌ NO marcar para Operadores

> **Importante**: Esta casilla controla el acceso al panel de administración. Solo los usuarios marcados como "Is Staff" pueden acceder a `/admin/`.

##### 3.3.8 Is Superuser (Is Superuser)

- **Descripción**: Usuario con permisos de superadministrador (todas las acciones permitidas sin restricciones)
- **Cómo llenarlo**: Marca la casilla "Es superusuario" (Is Superuser)
- **Recomendación**:
  - ❌ NO marcar para usuarios normales
  - ✅ Marcar solo para 1-2 administradores principales del sistema
  - ❌ Crear múltiples superusuarios

> **CRÍTICO**: Los superusuarios tienen control total sobre el sistema, incluyendo todos los datos y configuraciones. Usa con extrema precaución.

---

## Paso 4: Asignar Permisos y Grupos

### 4.1 Entender los Grupos de Usuarios

El sistema utiliza grupos de Django para gestionar permisos colectivamente:

**Grupos comunes**:
- `admin_users` - Usuarios con permisos de administración
- `operadores` - Usuarios que gestionan trámites
- `peritos` - Peritos especializados (si aplica)
- `auditores` - Usuarios que revisan trámites (si aplica)

### 4.2 Asignar Grupos al Usuario

En el formulario de creación de usuario (o al editar):

1. Busca la sección **Grupos** (Groups)
2. Haz clic en el campo de grupos para ver todos los disponibles
3. Selecciona el grupo apropiado (puedes seleccionar múltiples con Ctrl+Clic)
4. Haz clic en el botón derecho para mover los grupos seleccionados al cuadro de grupos asignados

**Asignación por rol**:
| Rol del Usuario | Grupo(s) a Asignar |
|-----------------|----------------------|
| **Administrador** | `admin_users` (opcionalmente también `operadores` si necesita ver operaciones) |
| **Operador** | `operadores` (solo este grupo) |
| **Perito** | `peritos` |
| **Auditor** | `auditores` |

> **Importante**: Los grupos determinan qué permisos tiene el usuario. Asigna los grupos correctos para dar el acceso apropiado.

### 4.3 Ver Permisos de Usuario

Los permisos se derivan de los grupos asignados:

**Permisos de Admin (grupo `admin_users`)**:
- ✅ add_user / change_user / delete_user / view_user
- ✅ add_group / change_group / delete_group / view_group
- ✅ add_tramite / change_tramite / delete_tramite / view_tramite
- ✅ add_documento / change_documento / delete_documento / view_documento
- ✅ All permissions for all models

**Permisos de Operador (grupo `operadores`)**:
- ✅ view_tramite (solo asignados a sí mismo)
- ✅ add_tramite
- ✅ change_tramite (estado y campos específicos)
- ✅ add_documento
- ✅ change_documento (estado de documento)
- ❌ NO permisos de usuarios, grupos, configuración global

> **Nota**: Como administrador, puedes ver y modificar los permisos directamente si necesitas configuración especial.

---

## Paso 5: Editar Usuarios Existentes

### 5.1 Acceder a un Usuario

1. Desde la lista de usuarios, haz clic en el **nombre de usuario** que quieres editar
2. Verás el formulario de edición con todos los campos del usuario

**Resultado esperado**: Formulario de edición pre-llenado con la información actual del usuario.

### 5.2 Modificar Información

Puedes modificar cualquiera de los campos:

**Cambios comunes**:

1. **Cambiar rol (grupo)**:
   - Si un usuario cambia de departamento, actualiza sus grupos
   - Ejemplo: De `operadores` a `peritos`
   - Esto cambia automáticamente sus permisos

2. **Cambiar estado (activar/desactivar)**:
   - Desmarca "Is Active" para desactivar temporalmente
   - Útil cuando un empleado está de vacaciones o licencia
   - El usuario no podrá iniciar sesión pero su cuenta permanece intacta

3. **Cambiar nombre o email**:
   - Si hay cambio legal en nombre o correo
   - Actualiza la información en el sistema
   - Esto mantiene consistencia con registros institucionales

4. **Cambiar contraseña manualmente**:
   - Usa el botón "Cambiar contraseña" si está disponible
   - O elimina la contraseña actual e ingresa una nueva
   - Recomendado cuando un usuario olvida su contraseña

**Resultado esperado**: Los cambios se aplican al guardar.

> **Consejo**: Cuando cambies grupos o permisos de un usuario, verifica que estos cambios sean apropiados para sus nuevas responsabilidades.

---

## Paso 6: Gestión de Usuarios Desactivados

### 6.1 Desactivar Usuarios Temporalmente

**Cuándo desactivar**:
- Usuario de vacaciones o licencia
- Personal transferido temporalmente
- Cuenta comprometida (necesita cambio de contraseña)
- Suspensión temporal por cualquier razón

**Cómo desactivar**:
1. Busca al usuario en la lista
2. Haz clic en el nombre de usuario para editar
3. Desmarca la casilla **"Is Active"** (Activo)
4. Haz clic en **"Guardar"**

**Resultado esperado**: El usuario figura en la lista como inactivo y no puede iniciar sesión.

> **Importante**: Los usuarios desactivados todavía aparecen en el sistema con su historial completo. Esto mantiene el registro incluso cuando el acceso está suspendido.

### 6.2 Reactivar Usuarios

**Cómo reactivar**:
1. Busca al usuario inactivo en la lista
2. Haz clic en el nombre de usuario para editar
3. Marca la casilla **"Is Active"** (Activo)
4. Haz clic en **"Guardar"**

**Resultado esperado**: El usuario puede iniciar sesión nuevamente.

> **Nota**: Considera cambiar la contraseña al reactivar un usuario que estuvo desactivado por seguridad.

---

## Paso 7: Eliminar Usuarios (Precaución)

### 7.1 Cuándo Eliminar Usuarios

**Situaciones apropiadas para eliminación**:
- ✅ Usuario que ya no trabaja en la organización
- ✅ Cuenta duplicada creada por error
- ✅ Cuenta de prueba que ya no es necesaria
- ✅ Solicitante explícitamente solicitó eliminación de sus datos

### 7.2 Eliminar un Usuario

1. Busca al usuario en la lista
2. Haz clic en el nombre de usuario
3. Haz clic en el botón **"Eliminar usuario"** (Delete User)
4. **CONFIRMA** que quieres eliminar al usuario
5. **OBSERVA**: Esta acción es irreversible

**Resultado esperado**: El usuario es eliminado permanentemente del sistema.

> **ADVERTENCIA**: La eliminación de un usuario también elimina su historial y todas sus asignaciones de trámites. Antes de eliminar, considera:
- Si hay trámites activos asignados a este usuario
- Si necesitas conservar el historial del usuario
- Si debes reasignar los trámites a otro operador

**Alternativa recomendada**:
- Desactiva al usuario en lugar de eliminarlo
- Esto mantiene el historial y las asignaciones
- Usa eliminación solo para casos justificados

---

## Paso 8: Auditoría de Cambios de Usuarios

### 8.1 Ver el Historial de Cambios

Como administrador, puedes ver todos los cambios en la bitácora:

1. Navega a la sección **Bitácora** (o "Audit Log")
2. Filtra por:
   - `usuario_user_id`: El usuario que sufrió el cambio
   - `acción`: Tipo de acción (crear_usuario, eliminar_usuario, cambiar_grupo, etc.)
   - `tabla`: Filtra por "auth_user" para ver solo cambios de usuarios
3. Revisa los cambios de usuarios en el historial

**Información registrada**:
- Qué usuario realizó el cambio
- Cuándo se realizó
- Qué acción se ejecutó
- Qué campos se modificaron
- Valores anteriores y nuevos

### 8.2 Uso de la Bitácora

**Investigaciones**:
- Si necesitas investigar un problema de seguridad
- Para verificar quién activó/desactivó un usuario
- Para rastrear cambios no autorizados

**Compliance**:
- Para auditorías de seguridad periódicas
- Para demostrar quién tiene acceso y cuándo se otorgó
- Para mantener trazabilidad completa

---

## Resumen

En este tutorial has aprendido:

✅ Cómo acceder al panel de administración de usuarios
✅ La diferencia entre roles Admin y Operador
✅ Cómo crear nuevos usuarios paso a paso
✅ Cómo asignar permisos y grupos apropiadamente
✅ Cómo editar usuarios existentes
✅ Cómo activar/desactivar usuarios temporalmente
✅ Cuándo y cómo eliminar usuarios (con precauciones)
✅ Cómo usar la bitácora para auditoría de cambios

---

## ¿Qué sigue?

Ahora que puedes gestionar usuarios, puedes aprender:

### Tutoriales siguientes:
- 📋 [Gestión de Catálogos](./manage-catalogs.md) - Tutorial para configurar tipos, estatus, requisitos
- 📋 [Agregar Peritos](../../03-guides/admins/add-peritos.md) - Tutorial para gestionar peritos especializados
- 📋 [Configurar Costos](../../03-guides/admins/configure-costs.md) - Tutorial para configurar costos por trámite

### Conceptos útiles:
- 🧠 [Permisos y Roles](../../04-concepts/) - Para entender la teoría detrás de los permisos
- 🧠 [Sistema de Auditoría](../../04-concepts/audit-system.md) - Para entender cómo funciona la bitácora

---

## Problemas Comunes

| Problema | Causa | Solución |
|----------|---------|----------|
| No puedo crear usuario: "Nombre ya existe" | Username duplicado | Cambia el username para que sea único |
| El usuario no puede iniciar sesión | "Is Active" no marcado o contraseña incorrecta | Marca "Is Active" y cambia contraseña si es necesario |
| Usuario no ve el panel de admin | No es "Is Staff" | Marca "Is Staff" si es administrador; si es operador, esto es normal |
| Permisos incorrectos | Grupo equivocado asignado | Edita el usuario y asigna el grupo correcto |
| No puedo eliminar usuario | Usuario tiene trámites activos | Primero reasigna o marca como inactivo, luego elimina |
| El historial no muestra cambios | Bitácora no se está registrando | Contacta a desarrollador para revisar configuración de auditoría |

---

## Mejores Prácticas de Gestión de Usuarios

### Para Seguridad del Sistema

1. **Principio de menor privilegio**
   - Da el mínimo de permisos necesarios para cada función
   - Usa roles de operador, no admin, cuando sea posible
   - Esto reduce el riesgo en caso de cuenta comprometida

2. **Rotación de contraseñas**
   - Establece política de cambio de contraseña periódicamente
   - Recomienda cambiar cada 90 días
   - Fuerza cambio al reactivar un usuario desactivado

3. **Revisión periódica de usuarios activos**
   - Desactiva usuarios que ya no trabajan en la organización
   - Esto mantiene la seguridad y reduce riesgos

4. **Auditoría regular de permisos**
   - Revisa que los usuarios tengan solo los permisos necesarios
   - Revoca permisos cuando cambian de rol
   - Registra estos cambios con justificación

### Para Efectividad Operativa

1. **Estándariza nombres de usuario**
   - Usa un formato consistente: `nombre.apellido` o `iniciales.apellido.departamento`
   - Esto facilita la identificación y gestión de usuarios

2. **Documenta roles y responsabilidades**
   - Mantén un registro interno de qué rol tiene qué usuario
   - Actualiza cuando cambian las responsabilidades

3. **Comunica cambios a los usuarios**
   - Notifica a los usuarios cuando cambias sus permisos
   - Explica el por qué de los cambios
   - Proporciona entrenamiento si cambia significativamente su rol

4. **Uso apropiado de superusuarios**
   - Solo 1-2 superusuarios para situaciones de emergencia
   - Usa administradores normales para tareas diarias
   - Esto reduce el riesgo de acceso total no controlado

---

## Preguntas Frecuentes

**P: ¿Puedo tener dos usuarios con el mismo correo?**
R: No, el correo electrónico debe ser único en el sistema. Usa correos institucionales diferentes.

**P: ¿Cuántos usuarios administradores debo tener?**
R: Mínimo 1 superusuario para recuperación de emergencias. Recomendado 2-3 administradores normales según el tamaño de la organización.

**P: ¿Qué pasa si elimino un usuario que tiene trámites activos?**
R: Los trámites quedan sin asignado. Primero reasigna a otro operador o marca como inactivo antes de eliminar.

**P: ¿Los usuarios pueden cambiar su propia contraseña?**
R: Depende de la configuración. Si está habilitado, sí. Si no, solo los administradores pueden cambiar contraseñas.

**P: ¿Cómo verifico qué permisos tiene un usuario específico?**
R: En el detalle del usuario, verás los grupos asignados y una lista de permisos derivados de esos grupos.

---

## Referencias Adicionales

- [Glosario de Términos](../01-onboarding/glossary.md) - Para entender términos como "usuario", "permisos", "grupo"
- [Overview del Proyecto](../01-onboarding/overview.md) - Para entender mejor el sistema
- [ADR-006: Permisos de Admin y Operador](../../06-decisions/006-permisos-admin-operador.md) - Documento sobre decisiones de permisos

---

**¿Necesitas ayuda?**
- Consulta las [Guías de Administradores](../../03-guides/admins/)
- Contacta a tu equipo de desarrollo si hay errores técnicos
- Revisa el [Troubleshooting](../../03-guides/admins/)

---

*Última actualización: 26 de Febrero de 2026*
