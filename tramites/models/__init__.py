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
from .tramite import Tramite, Buzon, Disponible


__all__ = [
    # Core
    'Tramite',
    'Buzon',
    'Disponible',
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
