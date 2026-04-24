# ¿Qué es el Backoffice de Trámites?

## Resumen

El **Backoffice de Trámites** es un sistema de gestión de trámites municipales para el Gobierno de San Felipe. Permite a los funcionarios gestionar el ciclo de vida completo de los trámites — desde que ingresan hasta que se finalicen — con auditoría completa de todas las operaciones.

---

## ¿Para qué sirve?

El sistema resuelve tres necesidades principales:

1. **Gestión de trámites:** Ver, filtrar, asignar y dar seguimiento a trámites municipales
2. **Control de acceso:** Roles diferenciados (Administrador, Coordinador, Analista) con permisos granulares
3. **Auditoría:** Historial completo de cambios de estatus, asignaciones y observaciones

---

## ¿Quiénes lo usan?

| Rol | Qué hace en el sistema |
|-----|----------------------|
| **Administrador** | Gestiona usuarios, tiene acceso completo a todas las funciones |
| **Coordinador** | Asigna trámites a analistas, monitorea el flujo de trabajo |
| **Analista** | Toma trámites disponibles, procesa y cambia estatus |

---

## ¿Cómo se accede?

El sistema es una **aplicación web** accesible desde el navegador. No requiere instalación en la computadora del usuario.

- **URL:** `https://backoffice.sanfelipe.gob.mx/admin/`
- **Autenticación:** Usuario y contraseña propios del sistema
- **Requisito:** El usuario debe estar en un grupo de rol (Administrador, Coordinador o Analista)

---

## ¿Qué puedo hacer en el sistema?

### Si soy Analista

- Ver los trámites **asignados a mí** (Mi Buzón)
- Ver trámites **disponibles** para tomar
- **Tomar** un trámite disponible
- **Cambiar el estatus** de un trámite (en revisión, requerimiento, etc.)
- Agregar **observaciones** a un trámite
- Ver y descargar **requisitos** (PDFs) de un trámite

### Si soy Coordinador

Todo lo de Analista, más:
- Ver **todos los trámites** activos
- **Asignar** trámites a analistas específicos
- **Reasignar** trámites entre analistas
- Ver trámites **finalizados** y **cancelados**

### Si soy Administrador

Todo lo de Coordinador, más:
- **Gestionar usuarios** (crear, editar, asignar roles)
- **Gestionar grupos** de permisos
- Acceso completo al panel de administración

---

## ¿De dónde vienen los datos?

Los trámites **no se crean** en este sistema. Son creados por otro microservicio (el portal ciudadano) y almacenados en PostgreSQL. El Backoffice **lee** esos datos y permite gestionar su procesamiento.

```
Portal Ciudadano → PostgreSQL ← Backoffice de Trámites
(crea trámites)     (BD)         (gestiona procesamiento)
```

Los catálogos (tipos de trámite, estatus, peritos, requisitos) también son gestionados externamente. El Backoffice los consume en modo **solo lectura**.

---

## ¿Qué información tiene un trámite?

Cada trámite contiene:

- **Datos del trámite:** Folio, tipo, categoría, monto, urgencia
- **Datos del solicitante:** Nombre, teléfono, correo, comentarios
- **Perito asignado:** Si aplica al tipo de trámite
- **Estatus actual:** Dónde está en el flujo (presentado → en revisión → finalizado)
- **Asignación:** Qué analista lo está procesando
- **Requisitos:** Archivos PDF subidos por el solicitante

---

## Estados de un trámite

Los trámites siguen un flujo con códigos numéricos agrupados:

| Rango | Estado | Ejemplos |
|-------|--------|---------|
| **1xx** | Inicio | Borrador (101), Pendiente de pago (102) |
| **2xx** | Proceso | Presentado (201), En revisión (202), Requerimiento (203), En diligencia (205) |
| **3xx** | Finalizado | Finalizado (303), Rechazado (302), Cancelado (304) |

Ver: [Referencia de estados](../05-reference/estados-tramites.md)

---

## Tecnología (para curiosos)

| Componente | Tecnología |
|------------|------------|
| Framework | Django 6.0.2 (Python 3.14) |
| Base de datos | PostgreSQL 16 |
| Interfaz | Django Admin (tema jazzmin) |
| Despliegue | Docker (Nginx + Gunicorn) |

**¿Quieres saber más?** Lee [Arquitectura detallada](architecture-overview.md)

---

## Ver también

- [Arquitectura detallada](architecture-overview.md)
- [Glosario de términos](glossary.md)
- [Tutorial para desarrolladores](../02-tutorials/developers/local-dev-setup.md)
- [Guía de despliegue](../03-guides/sysadmins/deploy-production.md)
