"""
Excepciones customizadas para el módulo de trámites.

Cada excepción de negocio expone ``user_message``: texto en español,
amigable para el usuario final, sin detalles técnicos.

Uso en modelos/servicios::

    raise EstadoNoPermitidoError(
        f'Transición inválida: tramite={folio} {from_s} → {to_s}',
        user_message='No es posible realizar esta acción en el estatus '
                     f'actual del trámite {folio}.',
    )

Uso en vistas/admin::

    except BackofficeError as e:
        messages.error(request, e.user_message)
"""

from __future__ import annotations


class BackofficeError(Exception):
    """Base class para todas las excepciones de negocio del backoffice.

    Provee ``user_message`` (seguro para usuarios) y preserva los
    argumentos originales para la bitácora.
    """

    user_message: str = 'Ocurrió un error inesperado. Por favor intenta nuevamente más tarde.'

    def __init__(self, *args: object, user_message: str | None = None) -> None:
        super().__init__(*args)
        if user_message is not None:
            self.user_message = user_message

    def __str__(self) -> str:
        """Return the user-facing message.

        When constructed with a positional arg (backward compatible),
        returns that arg.  When constructed with only ``user_message=``,
        returns the user message.
        """
        if self.args and self.args[0]:
            return str(self.args[0])
        return self.user_message


class TramiteNoAsignableError(BackofficeError):
    """El trámite no puede ser asignado (estado incorrecto)."""

    user_message = 'El trámite ya no se encuentra activo.'


class EstadoNoPermitidoError(BackofficeError):
    """El trámite está en un estado que no permite la acción solicitada."""

    user_message = 'No es posible realizar esta acción en el estatus actual del trámite.'


class SFTPConnectionError(BackofficeError):
    """Error de conexión con el servidor de archivos."""

    user_message = (
        'Error de conexión al servidor de archivos. Contacta al administrador del sistema.'
    )

    # TODO: __init__ acopla positional args a user_message, inconsistente con
    # el contrato del parent (BackofficeError) donde args es para bitácora y
    # user_message es para el usuario. Actualmente seguro porque todos los
    # raises en sftp.py usan mensajes limpios como positional args, pero si
    # alguien pasa un mensaje técnico como positional arg, se filtraría al
    # usuario vía e.user_message. Para resolver: migrar los 35 raises en
    # sftp.py a usar user_message= explícitamente y eliminar este override.
    def __init__(self, *args: object, user_message: str | None = None) -> None:
        if user_message is None and args:
            user_message = str(args[0])
        super().__init__(*args, user_message=user_message)
