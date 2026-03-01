---
Title: Configurar Costos por Trámite - Guía para Administradores
Role: admin
Related: [Glosario: UMA](../../01-onboarding/glossary.md#uma-unidad-de-medida-actualizada)
---

## Resumen

Esta guía te enseñará cómo configurar y gestionar los costos por tipo de trámite en el sistema Backoffice de Trámites. Los costos se calculan usando UMA (Unidad de Medida Actualizada), que es un estándar oficial del gobierno mexicano.

## ¿Cuándo usar esta guía?

- Cuando necesitas actualizar los costos base de un tipo de trámite
- Cuando se actualiza el valor oficial de UMA y deben ajustarse los precios
- Cuando creas un nuevo tipo de trámite y defines sus costos
- Cuando necesitas agregar costos adicionales (honorarios de peritos, etc.)
- Cuando investigas un problema de cálculo de costos

---

## Conceptos Fundamentales

### ¿Qué es UMA?

**Definición**: UMA (Unidad de Medida Actualizada) es un estándar oficial del gobierno mexicano para medir el valor monetario. La UMA se actualiza periódicamente por el CONEVAL.

**Por qué usar UMA**:
- Permite ajustes automáticos por inflación
- Es un estándar legal transparente
- Facilita comparaciones entre diferentes servicios
- Se actualiza oficialmente, evitando arbitrariedades

**Cálculo básico**:
```
Costo del Trámite (MXN) = (Valor en UMAs) × (Valor UMA actual en MXN)
```

**Ejemplo**:
- Costo base en UMAs: 2.5
- Valor actual de UMA: $103.74 MXN
- **Costo final**: 2.5 × $103.74 = $259.35 MXN

---

### ¿Cómo Funciona el Sistema de Costos?

El sistema gestiona costos en tres niveles:

#### 1. Costos Base por Tipo de Trámite
- Definido al crear el tipo de trámite
- Valor en UMAs
- Aplica a todos los trámites de ese tipo

#### 2. Costos Adicionales
- Honorarios de peritos
- Costos por servicios especiales
- Cargos adicionales por complejidad

#### 3. Descuentos y Exenciones
- Descuentos por ciudadanía
- Exenciones por tipo de solicitante
- Promociones temporales

---

## Pasos para Configurar Costos Base

### Paso 1: Acceder al Catálogo de Tipos de Trámite

1. Ingresa al panel de administración:
   ```
   http://<host-del-sistema>/admin/
   ```
2. Ve a la sección **CATÁLOGOS**
3. Haz clic en **"Tipos de Trámite"**

**Resultado esperado**: Lista de tipos de trámite con sus costos actuales en UMAs.

---

### Paso 2: Editar el Costo de un Tipo de Trámite

1. Haz clic en el código del tipo de trámite que quieres actualizar
2. Busca el campo **"Costo en UMAs"**
3. Actualiza el valor

**Ejemplos de actualización**:
- De `1.0` a `1.5` (aumento del 50%)
- De `2.0` a `2.0` (sin cambio)
- De `5.0` a `4.5` (reducción del 10%)

---

### Paso 3: Guardar y Justificar el Cambio

1. Haz clic en el botón **"Guardar"**
2. Agrega observación explicando el cambio:
   ```
   Costo actualizado de 1.0 a 1.5 UMAs.
   Justificación: Aumento aprobado por dirección general el 27-02-2026.
   Referencia: Acta de consejo #123.
   ```

**Resultado esperado**:
- El costo se actualiza inmediatamente
- El cambio queda registrado en la bitácora
- Los trámites nuevos usarán el nuevo costo

> **Importante**: Los trámites ya creados mantienen su costo original. El cambio solo aplica a trámites nuevos.

---

## Actualización Masiva de Costos

### ¿Cuándo Hacer Actualización Masiva?

**Causas comunes**:
- Actualización oficial del valor de UMA por CONEVAL
- Aumento general de costos aprobado por dirección
- Inflación acumulada por período prolongado

**Consideraciones importantes**:
- ¿Qué porcentaje de aumento es apropiado?
- ¿Qué tipos de trámite deben actualizarse?
- ¿Hay excepciones que deben mantener el costo actual?

---

### Pasos para Actualización Masiva

#### Opción A: Actualización Manual (Recomendada para pocos tipos)

1. Lista los tipos de trámite que necesitan actualización
2. Para cada tipo:
   - Haz clic en el código
   - Calcula el nuevo costo:
     ```
     Nuevo Costo = Costo Actual × (1 + % de aumento)
     ```
   - Actualiza el valor
   - Agrega observación con justificación
3. Guardar

**Ejemplo de cálculo**:
- Costo actual: 1.5 UMAs
- Aumento del 10%
- Nuevo costo: 1.5 × 1.10 = 1.65 UMAs

#### Opción B: Actualización por Script (Requiere desarrollo)

Para actualizaciones masivas de muchos tipos de trámite:

1. Solicita a equipo de desarrollo un script de actualización
2. El script debe:
   - Actualizar todos los costos en proporción especificada
   - Registrar cada cambio en la bitácora
   - Permitir rollback si hay error
3. Prueba en ambiente de desarrollo primero
4. Ejecuta en producción con respaldo previo

> **Nota**: Esta opción requiere aprobación y supervisión del equipo de desarrollo.

---

## Configuración de Costos de Peritos

### Agregar Costo de Perito a Tipo de Trámite

**Cuándo agregar**: Cuando un tipo de trámite requiere perito obligatoriamente.

**Pasos**:
1. Desde el detalle del tipo de trámite, busca la sección "Peritos Asignados"
2. Haz clic en el botón para asignar peritos
3. Selecciona el perito especializado
4. Define el costo en UMAs específico para este tipo de trámite

**Ejemplo**:
```
Tipo: Licencia de Construcción
Perito: Ing. Juan Pérez (Arquitectónico)
Costo: 0.8 UMAs
```

**Resultado esperado**: Cuando se asigne este perito a este tipo de trámite, se agregará el costo al total.

---

### Costos Variables por Perito

Los peritos pueden tener diferentes costos según su experiencia y especialidad.

**Ejemplo de estructura**:
| Perito | Especialidad | Costo Base UMAs | Recargo % |
|--------|-------------|------------------|-----------|
| Ing. Juan Pérez | Arquitectónico | 0.8 | 0% |
| Arq. María García | Arquitectónico | 1.0 | +25% |
| Ing. Carlos López | Topógrafo | 0.7 | 0% |

**Lógica de cálculo**:
```
Costo Perito = (Costo Base UMAs) × (1 + Recargo % / 100)
```

---

## Gestión de Descuentos y Exenciones

### Crear un Tipo de Descuento

**Cuándo crear**: Para aplicar descuentos a grupos específicos de ciudadanos.

**Pasos**:
1. Navega a la sección **Descuentos** en catálogos
2. Haz clic en "Añadir descuento"
3. Llena los campos:
   - **Nombre**: Ej: "Descuento a adultos mayores"
   - **Porcentaje**: Ej: 50% (50% de descuento)
   - **Condición**: Ej: "Solicitante mayor de 60 años"
4. Guardar

**Resultado esperado**: El descuento estará disponible para aplicarse a trámites.

---

### Aplicar un Descuento a un Trámite

**Pasos**:
1. Al crear o editar un trámite, busca el campo "Descuento"
2. Selecciona el descuento apropiado del menú
3. El sistema calculará automáticamente el precio final

**Cálculo**:
```
Precio Final = (Costo Base - Descuento)
            = (Costo Base × (1 - % Descuento))
```

**Ejemplo**:
- Costo base: $500 MXN
- Descuento: 50%
- Precio final: $500 × 0.50 = $250 MXN

---

## Configuración del Valor de UMA

### ¿Quién Actualiza el Valor de UMA?

**Responsable**: El equipo de desarrollo o el administrador del sistema.

**Frecuencia**: Cada vez que CONEVAL actualiza oficialmente el valor de UMA (generalmente anual).

**Fuente oficial**: [Portal de CONEVAL](https://www.coneval.org.mx/Medicion/Paginas/Pobreza-Ingresos.aspx)

---

### Pasos para Actualizar el Valor de UMA

1. Verificar el nuevo valor oficial en portal de CONEVAL
2. Solicitar a equipo de desarrollo la actualización:
   ```
   Nuevo valor de UMA: [valor en MXN]
   Fecha de vigencia: [fecha]
   Referencia: Resolución [número]
   ```
3. El equipo de desarrollo actualizará la configuración
4. Verificar que los cálculos de costos sean correctos

> **Nota**: Esta actualización afecta el cálculo de costos para todos los trámites nuevos. Los trámites existentes mantienen su costo en el momento de creación.

---

## Reglas Importantes

### Regla 1: Costos Deben Ser Justificados

**✅ REQUERIDO**:
- Documentar el por qué de cada cambio de costo
- Referenciar aprobaciones oficiales
- Mantener registro de resoluciones o actas

**❌ NO PERMITIDO**:
- Cambios de costos sin justificación
- Aumentos arbitrarios
- Modificaciones no autorizadas

> **Consecuencia**: Los cambios sin justificación pueden ser cuestionados en auditorías o por el público.

---

### Regla 2: Actualización de UMA es Obligatoria

**Cuando CONEVAL actualiza el valor de UMA**:
- Debes actualizar el valor en el sistema dentro de un periodo razonable
- Verificar que el cálculo de costos refleje el nuevo valor
- Documentar la actualización con referencia oficial

**Tiempo recomendado**: Dentro de los 30 días posteriores a la actualización oficial.

---

### Regla 3: Trámites Antiguos Mantienen su Costo

**Regla**: Los trámites ya creados mantienen el costo calculado en el momento de su creación.

**Por qué**:
- El solicitante conoció y aceptó un precio específico
- Cambios retroactivos causarían confusión y posibles reclamos
- Es justo mantener la tarifa acordada

**Excepciones**:
- Si hay error de cálculo documentado y aprobado
- Si el solicitante solicita explícitamente la actualización

---

### Regla 4: Costos Deben Ser Transparentes

**Requisito**: Los costos deben ser públicos y comprensibles.

**Qué hacer**:
- Publicar tablas de costos (tipo de trámite → costo en MXN)
- Explicar cómo se calculan (UMA × valor actual)
- Incluir costos de peritos y adicionales
- Mantener la información actualizada

**Dónde publicar**:
- Sitio web de la dependencia
- En la oficina de atención al público
- En el sistema (si está disponible al público)

---

## Solución de Problemas

| Problema | Posible Causa | Solución |
|----------|----------------|----------|
| Costo incorrecto en trámite | Valor de UMA desactualizado | Actualizar valor de UMA |
| Costo no se calcula | Falta valor en UMAs | Llenar campo de costo base |
| Trámite tiene costo diferente | Trámite creado antes de actualización | Es normal, mantener costo original |
| Error en cálculo de perito | Costo de perito no configurado | Asignar costo al perito para ese tipo |
| Descuento no se aplica | Tipo no configurado | Crear tipo de descuento |

---

## Solución de Problemas Específicos

### Problema: Costo de Trámite Incorrecto por Error

**Situación**: Un trámite tiene un costo incorrecto por error de configuración.

**Pasos**:
1. Verificar si el trámite ya fue pagado
   - **Si no pagado**: Corregir el costo
     - Editar el trámite
     - Corregir el valor de UMAs
     - Documentar el error y corrección
   - **Si ya pagado**: No corregir retroactivamente
     - El solicitante ya pagó un precio
     - Corregir solo para trámites futuros
     - Si el error es significativo, consultar con dirección para compensación

**Resultado esperado**: Trámites futuros tendrán el costo correcto. Trámites ya pagados mantienen su costo.

---

### Problema: Valor de UMA Desactualizado

**Situación**: El sistema está usando un valor antiguo de UMA.

**Pasos**:
1. Verificar el valor actual en portal de CONEVAL
2. Comparar con el valor configurado en el sistema
3. Si está desactualizado:
   - Solicitar actualización al equipo de desarrollo
   - Documentar la solicitud con referencia oficial
   - Verificar actualización una vez implementada

**Resultado esperado**: El sistema usa el valor actualizado de UMA.

---

### Problema: Diferencia de Costo Mismo Tipo de Trámite

**Situación**: Dos trámites del mismo tipo tienen costos diferentes.

**Causas posibles y soluciones**:

1. **Creados en fechas diferentes**:
   - Normal: costos pueden cambiar con el tiempo
   - Cada trámite mantiene el costo de su fecha de creación

2. **Tienen diferentes peritos asignados**:
   - Normal: peritos pueden tener diferentes costos
   - Verificar que los costos de peritos estén configurados correctamente

3. **Uno tiene descuento aplicado**:
   - Normal: descuentos varían según situación del solicitante
   - Verificar en el detalle del trámite qué descuento se aplicó

4. **Error en configuración**:
   - Si ninguna de las anteriores aplica, investigar:
     - Verificar bitácora del trámite
     - Revisar costos configurados para ese tipo
     - Consultar con equipo si hay configuración especial

---

## Resumen

En esta guía has aprendido:

✅ Qué es UMA y por qué se usa
✅ Cómo funciona el sistema de costos
✅ Cómo configurar costos base por tipo de trámite
✅ Cómo hacer actualizaciones masivas de costos
✅ Cómo configurar costos de peritos
✅ Cómo gestionar descuentos y exenciones
✅ Cómo actualizar el valor de UMA
✅ Reglas importantes para gestión de costos
✅ Cómo resolver problemas comunes de costos

---

## ¿Qué sigue?

Ahora que puedes gestionar costos, puedes aprender:

### Guías siguientes:
- 📋 [Agregar Peritos](./add-peritos.md) - Tutorial para gestionar peritos especializados
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
