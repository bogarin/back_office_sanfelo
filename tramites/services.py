"""
Servicios para gestión de asignaciones de trámites.

Separados del modelo para facilitar testing y reutilización.
"""

from typing import TYPE_CHECKING

from .models import AsignacionTramite

if TYPE_CHECKING:
    from django.contrib.auth.models import User


def obtener_analista_asignado(tramite):
    """
    Obtiene el analista asignado a un trámite.

    Args:
        tramite: Instancia de Tramite

    Returns:
        User or None: El analista asignado, o None si no está asignado
    """
    try:
        asignacion = AsignacionTramite.objects.get(tramite_id=tramite.id)
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

    from tramites.models import AsignacionTramite

    User = get_user_model()

    # Count assignments using Subquery (cross-database safe)
    carga_subquery = (
        AsignacionTramite.objects.filter(analista=OuterRef('id'))
        .annotate(total=Count('id'))
        .values('total')[:1]
    )

    return (
        User.objects.filter(groups__name='Analista')
        .annotate(carga_tramites=Subquery(carga_subquery))
        .order_by('carga_tramites')
    )


# =============================================================================
# SFTP SERVICE
# =============================================================================

from dataclasses import dataclass


@dataclass
class PDFFile:
    """Representación de un archivo PDF."""

    nombre: str
    url: str
    tamaño: str


class SFTPService:
    """Servicio para interactuar con servidor SFTP."""

    def list_pdfs_for_tramite(self, folio: str) -> list[PDFFile]:
        """
        Lista PDFs relacionados con un trámite por folio.

        TODO: Implementar conexión real a SFTP usando django-storages.

        Args:
            folio: Folio del trámite para buscar PDFs

        Returns:
            Lista de objetos PDFFile con información de archivos
        """
        # Datos ficticios para testing
        return [
            PDFFile(nombre=f'PDF_{folio}_001.pdf', url=f'#pdf-{folio}-001', tamaño='1.2 MB'),
            PDFFile(nombre=f'PDF_{folio}_002.pdf', url=f'#pdf-{folio}-002', tamaño='0.8 MB'),
            PDFFile(nombre=f'PDF_{folio}_003.pdf', url=f'#pdf-{folio}-003', tamaño='2.1 MB'),
            PDFFile(nombre=f'PDF_{folio}_004.pdf', url=f'#pdf-{folio}-004', tamaño='0.5 MB'),
            PDFFile(nombre=f'PDF_{folio}_005.pdf', url=f'#pdf-{folio}-005', tamaño='1.5 MB'),
        ]
