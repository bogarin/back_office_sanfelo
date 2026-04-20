"""
Excepciones customizadas para Tramite.
"""


class TramiteNoAsignableError(Exception):
    """El trámite no puede ser asignado (estado incorrecto)."""


class EstadoNoPermitidoError(Exception):
    """El trámite está en un estado que no permite asignación."""
