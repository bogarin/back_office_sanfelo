# 020: Mensajes de Error Orientados al Usuario

**Date:** 12 de mayo de 2026
**Status:** Accepted
**Related:** [RNF-06 Mensajes de Error](../01-ARQUITECTURA/00-REQUERIMIENTOS.md), [ADR-004 Logging y Monitoreo](004-logging-monitoreo.md), [RF-05 Auditoría Completa](../01-ARQUITECTURA/00-REQUERIMIENTOS.md)

## Contexto y Planteamiento del Problema

El backoffice es usado por personal administrativo del municipio (analistas, coordinadores) que no tiene formación técnica. Los mensajes de error que exponen detalles internos — IDs de estatus, rutas de archivos, excepciones Python, esquema de base de datos, terminología SSH/SFTP — generan confusión y desconfianza en los usuarios, y pueden revelar información sensible sobre la infraestructura a potenciales atacantes.

## Opciones Consideradas

- **Opción A:** Mensajes técnicos tal cual (status quo) — el usuario ve lo que el framework o la base de datos arrojan
- **Opción B:** Mensajes genéricos al usuario + detalles técnicos exclusivamente en bitácora
- **Opción C:** Mensajes genéricos al usuario + sistema de códigos de error rastreables (ej: "Error #ERR-0042, reporte este código")

## Resultado de la Decisión

Opción elegida: **"B — Mensajes limpios + bitácora"**, porque es la más simple de implementar y mantener sin requerir infraestructura adicional, y proporciona toda la información necesaria para debugging vía la bitácora existente.

### Reglas

1. **Prohibido en mensajes al usuario:** IDs internos, rutas de archivo, nombres de tabla, SQL, tracebacks, IPs, puertos, nombres de clase, términos de framework (Django, SFTP, SSH, ORM), códigos de estatus HTTP, o cualquier jerga técnica.
1. **Permitido en mensajes al usuario:** El folio del trámite (dato que el usuario ya conoce), instrucciones claras en español ("Verifica que el estatus sea correcto", "Intenta nuevamente más tarde").
1. **Obligatorio:** Cuando ocurre un error, el detalle técnico se registra en bitácora vía `logger.error()` con `exc_info=True` **antes** de mostrar el mensaje genérico al usuario. Las operaciones exitosas siguen el flujo de auditoría normal (RF-05).
1. **Excepciones custom:** Deben exponer un atributo `user_message` (texto amigable en español) separado del mensaje interno. Las vistas y admin actions usan `e.user_message`, nunca `str(e)`.
1. **Errores inesperados:** Los bloques `except Exception` siempre muestran un mensaje genérico ("Ocurrió un error inesperado. Por favor intenta nuevamente más tarde.") y registran el detalle completo en bitácora.

### Ejemplos

| Mal | Bien |
|-----|------|
| `"Error de base de datos al crear registro de actividad 202 para el tramite 123: connection refused"` | `"No se pudo registrar la acción. Por favor intenta nuevamente más tarde."` |
| `"Sftp connection error to 127.0.0.1:2222"` | `"Error al acceder a los archivos PDF. Por favor intenta nuevamente más tarde."` |
| `"Estatus de cierre inválido: 305. Debe ser uno de: (301, 302, 304)"` | `"El estatus de cierre seleccionado no es válido."` |
| `"Archivo de llave privada no encontrado: /home/app/.ssh/id_rsa"` | `"Error de configuración del servidor. Contacta al administrador."` |
| `"Tipo de host key no soportado: ssh-dss. Tipos soportados: ssh-rsa, ssh-ed25519"` | `"Error de configuración del servidor de archivos. Contacta al administrador del sistema."` |

## Consecuencias

- **Bueno, porque** los usuarios ven mensajes comprensibles y accionables, lo que reduce la frustación y el tiempo perdido intentando interpretar errores técnicos.
- **Bueno, porque** se elimina la exposición de detalles de infraestructura a potenciales atacantes.
- **Bueno, porque** la bitácora conserva toda la información necesaria para debugging con contexto completo (tracebacks, IDs, rutas).
- **Malo, porque** requiere disciplina constante: cada nuevo `messages.error(request, str(e))` o `raise Exception(f'...{detail}...')` debe seguir el patrón de separar mensaje de usuario y detalle interno.

## Ver también

- [ADR-004: Logging y Monitoreo](004-logging-monitoreo.md)
- [RF-05: Auditoría Completa](../01-ARQUITECTURA/00-REQUERIMIENTOS.md)
- [RNF-06: Mensajes de Error](../01-ARQUITECTURA/00-REQUERIMIENTOS.md)
