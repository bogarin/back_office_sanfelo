"""Timeline building logic for tramite detail view.

This module contains pure functions for building timeline entries,
separate from Django admin to avoid circular imports and enable
unit testing without Django test mode.
"""

from tramites.models.actividades import ActividadFile, RequisitoFile, TimelineEntry
from tramites.models.catalogos import TramiteEstatus


def build_timeline_entries(
    historial,
    actividades_files,
    requisitos,
    users,
):
    """Build timeline entries for tramite detail view.

    Groups actividad files by actividad_id, finds first PENDIENTE_PAGO
    activity, and matches them to timeline entries.

    Args:
        historial: List of Actividades from tramite.historial_actividades.
        actividades_files: List of ActividadFile from SFTP.
        requisitos: List of RequisitoFile from SFTP.
        users: Dict mapping user_id -> User (from batch lookup).

    Returns:
        List of TimelineEntry objects ready for template rendering.
    """
    files_by_act = {}
    for f in actividades_files:
        files_by_act.setdefault(f.actividad_id, []).append(f)

    first_pendiente_pago = next(
        (a for a in reversed(historial)
         if a.estatus_id == TramiteEstatus.Estatus.PENDIENTE_PAGO),
        None,
    )

    file_estados = {TramiteEstatus.Estatus.REQUERIMIENTO, TramiteEstatus.Estatus.SUBSANADO}

    timeline_entries = []
    for act in historial:
        timeline_entries.append(
            TimelineEntry(
                actividad=act,
                actividad_files=(
                    files_by_act.get(act.id, []) if act.estatus_id in file_estados else []
                ),
                requisito_files=(
                    requisitos if first_pendiente_pago and act.id == first_pendiente_pago.id else []
                ),
                user=users.get(act.backoffice_user_id),
            )
        )

    return timeline_entries