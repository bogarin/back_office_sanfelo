"""
Servicios para gestión de asignaciones de trámites.

Separados del modelo para facilitar testing y reutilización.
"""

from django.core.exceptions import ValidationError

from .models import AsignacionTramite


class AsignacionError(Exception):
    """Base exception para errores de asignación."""


class TramiteNoAsignableError(AsignacionError):
    """El trámite no puede ser asignado (estado incorrecto)."""


class AnalistaConMuchasAsignacionesError(AsignacionError):
    """El analista ya tiene demasiados trámites asignados."""


class EstadoNoPermitidoError(AsignacionError):
    """El trámite está en un estado que no permite asignación."""


def asignar_tramite(tramite, analista, asignado_por=None, observacion=''):
    """
    Asigna un trámite a un analista.

    Args:
        tramite: Instancia de Tramite (de BD legacy)
        analista: Instancia de User
        asignado_por: Instancia de User (opcional)
        observacion: Texto opcional

    Returns:
        AsignacionTramite: La nueva asignación

    Raises:
        TramiteNoAsignableError: Si el trámite no puede ser asignado
        EstadoNoPermitidoError: Si el trámite está en estado incorrecto
        ValidationError: Si hay validaciones falladas
    """
    try:
        return AsignacionTramite.asignar(
            tramite=tramite, analista=analista, asignado_por=asignado_por, observacion=observacion
        )
    except ValidationError as e:
        error_msg = str(e).lower()

        if (
            'estatus' in error_msg
            or 'proceso' in error_msg
            or 'estado' in error_msg
            or 'borrador' in error_msg
        ):
            raise EstadoNoPermitidoError(str(e))
        if (
            'limite' in error_msg
            or 'límite' in error_msg
            or 'asignaciones' in error_msg
            or 'trámites' in error_msg
            or 'demasiados' in error_msg
        ):
            raise AnalistaConMuchasAsignacionesError(str(e))
        raise TramiteNoAsignableError(str(e))


def liberar_tramite(tramite):
    """
    Libera un trámite.

    Args:
        tramite: Instancia de Tramite
    """
    AsignacionTramite.liberar(tramite)


def reasignar_tramite(tramite, nuevo_analista, reasignado_por=None, observacion=''):
    """
    Reasigna un trámite a otro analista.

    Esencialmente lo mismo que asignar, pero más explícito en el nombre.

    Args:
        tramite: Instancia de Tramite
        nuevo_analista: Instancia de User
        reasignado_por: Instancia de User (opcional)
        observacion: Texto opcional

    Returns:
        AsignacionTramite: La nueva asignación
    """
    return asignar_tramite(tramite, nuevo_analista, reasignado_por, observacion)


def obtener_analista_asignado(tramite):
    """
    Obtiene el analista asignado a un trámite.

    Args:
        tramite: Instancia de Tramite

    Returns:
        User or None: El analista asignado, o None si no está asignado
    """
    try:
        asignacion = AsignacionTramite.objects.get(tramite=tramite)
        return asignacion.analista
    except AsignacionTramite.DoesNotExist:
        return None


def obtener_carga_analistas():
    """
    Obtiene lista de analistas ordenados por carga de trámites.

    Útil para el Coordinador al balancear carga.

    Returns:
        QuerySet: Analistas ordenados por carga (ascendente)
    """
    from django.contrib.auth import get_user_model
    from django.db.models import Count, OuterRef, Subquery

    from buzon.models import AsignacionTramite

    User = get_user_model()

    # Count assignments using Subquery (cross-database safe)
    carga_subquery = (
        AsignacionTramite.objects.filter(analista_id=OuterRef('id'))
        .annotate(total=Count('id'))
        .values('total')[:1]
    )

    return (
        User.objects.filter(groups__name='Analista')
        .annotate(carga_tramites=Subquery(carga_subquery))
        .order_by('carga_tramites')
    )
