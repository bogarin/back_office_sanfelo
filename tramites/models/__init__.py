"""Tramites models package.

All models are in submodules for organization, but re-exported here
for convenient importing: ``from tramites.models import Tramite``.
"""

from .actividades import Actividades
from .catalogos import (
    Actividad,
    Categoria,
    Perito,
    Requisito,
    Tipo,
    TramiteCatalogo,
    TramiteEstatus,
)
from .relaciones import (
    TramiteCatalogoActividad,
    TramiteCatalogoCategoria,
    TramiteCatalogoRequisito,
    TramiteCatalogoTipoRequisito,
)
from .tramite import Tramite

__all__ = [
    # Core
    'Tramite',
    # Catálogos
    'TramiteCatalogo',
    'TramiteEstatus',
    'Perito',
    'Actividad',
    'Categoria',
    'Requisito',
    'Tipo',
    # Transaccional
    'Actividades',
    # Relaciones (pivotes)
    'TramiteCatalogoCategoria',
    'TramiteCatalogoRequisito',
    'TramiteCatalogoTipoRequisito',
    'TramiteCatalogoActividad',
]
