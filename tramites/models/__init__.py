from .actividades import Actividades
from .catalogos import (
    Actividad,
    Categoria,
    Perito,
    Requisito,
    RequisitoFile,
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
    'Tipo',
    # Transaccional
    'Actividades',
    # Relaciones (pivotes)
    'TramiteCatalogoCategoria',
    'TramiteCatalogoRequisito',
    'TramiteCatalogoTipoRequisito',
    'TramiteCatalogoActividad',
]
