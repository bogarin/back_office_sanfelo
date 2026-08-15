"""FSM declarativa del workflow de trámites.

Única fuente de verdad de transiciones, acciones y roles autorizados.
El modelo ``Tramite`` delega aquí la validación de transiciones
(``TRANSITIONS``), el cálculo de ``available_actions()`` y los destinos de
cierre de ``cancelar()``.

El estado de un trámite NO se persiste en el modelo (``Tramite`` mapea a la
vista read-only ``v_tramites_unificado``): cada acción registra una fila en
``Actividades`` (append-only) y la vista recalcula el estatus. Por eso este
módulo es puro: no toca ORM ni base de datos y es testeable sin BD.

Semántica de ``Transition.roles`` (visibilidad/ejecución por rol):

- Superuser / Administrador: siempre autorizados.
- Coordinador: autorizado si ``BackOfficeRole.COORDINADOR`` está en ``roles``.
- Analista: autorizado si ``BackOfficeRole.ANALISTA`` está en ``roles`` y
  además está asignado al trámite.
"""

from dataclasses import dataclass
from typing import Protocol

from django.conf import settings as django_settings

from core.rbac.constants import BackOfficeRole
from tramites.models.catalogos import TramiteEstatus

_Estatus = TramiteEstatus.Estatus
_Role = BackOfficeRole

# Roles con permiso de gestión de asignaciones (no aparecen en available_actions).
_ROLES_GESTION = frozenset({_Role.COORDINADOR, _Role.ADMINISTRADOR})
# Roles con permiso de ejecutar acciones de revisión sobre el trámite.
_ROLES_REVISION = frozenset({_Role.ANALISTA, _Role.COORDINADOR, _Role.ADMINISTRADOR})


class WorkflowUser(Protocol):
    """Contrato de rol que este módulo requiere del usuario."""

    @property
    def is_superuser(self) -> bool: ...

    @property
    def is_administrador(self) -> bool: ...

    @property
    def is_coordinador(self) -> bool: ...

    @property
    def is_analista(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class Transition:
    """Transición válida del workflow.

    Attributes:
        action: Nombre público de la acción (lo que consume
            ``available_actions()`` y los templates).
        source: Estatus origen.
        target: Estatus destino (igual a ``source`` en self-loops).
        label: Etiqueta legible para UI y documentación.
        roles: Roles autorizados a ejecutar la transición.
        requires_assignment: El trámite debe estar asignado al usuario que
            ejecuta la acción (guarda ``_assert_asignado_a``).
        requires_note: La observación es obligatoria.
        changes_status: ``False`` para self-loops que registran actividad
            sin cambiar de estatus.
        offers_action: ``False`` para acciones de gestión (asignar, liberar)
            que se ofrecen vía admin, no vía ``available_actions()``.
    """

    action: str
    source: int
    target: int
    label: str
    roles: frozenset[str]
    requires_assignment: bool = True
    requires_note: bool = False
    changes_status: bool = True
    offers_action: bool = True


WORKFLOW: tuple[Transition, ...] = (
    # -- Gestión de asignaciones (Coordinador/Administrador, vía admin) --
    Transition(
        'asignar',
        _Estatus.PRESENTADO,
        _Estatus.EN_REVISION,
        'Asignar analista',
        _ROLES_GESTION,
        requires_assignment=False,
        offers_action=False,
    ),
    Transition(
        'reasignar',
        _Estatus.EN_REVISION,
        _Estatus.EN_REVISION,
        'Reasignar analista',
        _ROLES_GESTION,
        requires_assignment=False,
        offers_action=False,
    ),
    Transition(
        'liberar',
        _Estatus.EN_REVISION,
        _Estatus.PRESENTADO,
        'Liberar al pool',
        _ROLES_GESTION,
        requires_assignment=False,
        offers_action=False,
    ),
    # -- Revisión (Analista asignado) --
    Transition(
        'requerir_documentos',
        _Estatus.EN_REVISION,
        _Estatus.REQUERIMIENTO,
        'Requerir documentos',
        _ROLES_REVISION,
    ),
    Transition(
        'enviar_a_firma',
        _Estatus.EN_REVISION,
        _Estatus.EN_DILIGENCIA,
        'Enviar a firma',
        _ROLES_REVISION,
    ),
    Transition(
        'cancelar',
        _Estatus.EN_REVISION,
        _Estatus.POR_RECOGER,
        'Cerrar trámite',
        _ROLES_REVISION,
        requires_note=True,
    ),
    Transition(
        'cancelar',
        _Estatus.EN_REVISION,
        _Estatus.RECHAZADO,
        'Cerrar trámite',
        _ROLES_REVISION,
        requires_note=True,
    ),
    Transition(
        'cancelar',
        _Estatus.EN_REVISION,
        _Estatus.CANCELADO,
        'Cerrar trámite',
        _ROLES_REVISION,
        requires_note=True,
    ),
    Transition(
        'cancelar',
        _Estatus.REQUERIMIENTO,
        _Estatus.POR_RECOGER,
        'Cerrar trámite',
        _ROLES_REVISION,
        requires_note=True,
    ),
    Transition(
        'cancelar',
        _Estatus.REQUERIMIENTO,
        _Estatus.RECHAZADO,
        'Cerrar trámite',
        _ROLES_REVISION,
        requires_note=True,
    ),
    Transition(
        'cancelar',
        _Estatus.REQUERIMIENTO,
        _Estatus.CANCELADO,
        'Cerrar trámite',
        _ROLES_REVISION,
        requires_note=True,
    ),
    # -- Cierre desde diligencia: solo Coordinador/Administrador --
    Transition(
        'cancelar',
        _Estatus.EN_DILIGENCIA,
        _Estatus.POR_RECOGER,
        'Cancelar trámite',
        _ROLES_GESTION,
        requires_assignment=False,
        requires_note=True,
    ),
    Transition(
        'cancelar',
        _Estatus.EN_DILIGENCIA,
        _Estatus.RECHAZADO,
        'Cancelar trámite',
        _ROLES_GESTION,
        requires_assignment=False,
        requires_note=True,
    ),
    Transition(
        'cancelar',
        _Estatus.EN_DILIGENCIA,
        _Estatus.CANCELADO,
        'Cancelar trámite',
        _ROLES_GESTION,
        requires_assignment=False,
        requires_note=True,
    ),
)

# Vista derivada (compatibilidad): los tests y ``_validate_transition``
# consumen este dict. No editar a mano — se deriva de ``WORKFLOW``.
TRANSITIONS: dict[tuple[int, int], bool] = {(t.source, t.target): True for t in WORKFLOW}


def get_disabled_transitions() -> set[int]:
    """Return disabled destination status IDs from settings (read at call time).

    Values are coerced to ``int`` as defense-in-depth: settings converts
    at load time, but ``override_settings()`` in tests may pass raw strings.
    """
    return {int(x) for x in getattr(django_settings, 'BACKOFFICE_DISABLED_TRANSITIONS', [])}


def transitions_from(source: int | None) -> tuple[Transition, ...]:
    """Transiciones cuyo estatus origen es *source*, en orden de tabla."""
    return tuple(t for t in WORKFLOW if t.source == source)


def user_may(user: WorkflowUser, transition: Transition, *, assigned: bool) -> bool:
    """Whether *user* is authorized for *transition*.

    - Superuser / Administrador: always ``True``.
    - Coordinador: ``True`` if the role is in ``transition.roles``.
    - Analista: ``True`` if the role is in ``transition.roles`` AND the
      analyst is assigned to the trámite.
    """
    if user.is_superuser or user.is_administrador:
        return True
    if user.is_coordinador:
        return _Role.COORDINADOR in transition.roles
    if user.is_analista:
        return _Role.ANALISTA in transition.roles and assigned
    return False


def offered_actions(
    *,
    user: WorkflowUser,
    source: int | None,
    assigned: bool,
    disabled: set[int],
) -> list[str]:
    """Action names offered to *user* from status *source*.

    An action is offered when at least one of its transitions from *source*
    has an enabled destination and the user's role allows it (``any``
    semantics: if a department disables only some closure destinations, the
    ``cancelar`` action remains visible while at least one survives).
    """
    actions: list[str] = []
    for transition in transitions_from(source):
        if not transition.offers_action or transition.action in actions:
            continue
        if transition.target in disabled:
            continue
        if not user_may(user, transition, assigned=assigned):
            continue
        actions.append(transition.action)
    return actions


def closure_destinations() -> tuple[int, ...]:
    """Estatus de cierre aceptados por ``cancelar()``, de cualquier origen."""
    destinations = {t.target for t in WORKFLOW if t.action == 'cancelar'}
    return tuple(sorted(destinations))
