from .actividades import (
    ActividadFile,
    Actividades,
    RequisitoFile,
    TimelineEntry,
)
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
from .tramite import Buzon, Cerrado, Disponible, Tramite

__all__ = [
    # Core
    'Tramite',
    'Buzon',
    'Disponible',
    'Cerrado',
    # Catálogos
    'TramiteCatalogo',
    'TramiteEstatus',
    'Perito',
    'Actividad',
    'Categoria',
    'Requisito',
    'RequisitoFile',
    'ActividadFile',
    'Tipo',
    # Transaccional
    'Actividades',
    'TimelineEntry',
    # Relaciones (pivotes)
    'TramiteCatalogoCategoria',
    'TramiteCatalogoRequisito',
    'TramiteCatalogoTipoRequisito',
    'TramiteCatalogoActividad',
]
