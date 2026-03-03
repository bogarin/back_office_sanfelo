"""Factory-boy factories for all models."""

from tests.factories.auth import (
    AdminUserFactory,
    ContentTypeFactory,
    GroupFactory,
    OperadorUserFactory,
    PermissionFactory,
    SuperUserFactory,
    UserFactory,
)
from tests.factories.catalogos import (
    ActividadesFactory,
    CatActividadFactory,
    CatCategoriaFactory,
    CatEstatusFactory,
    CatIncisoFactory,
    CatPeritoFactory,
    CatRequisitoFactory,
    CatTipoFactory,
    CatTramiteFactory,
    CatUsuarioFactory,
    CobroFactory,
    RelTmtActividadFactory,
    RelTmtCategoriaFactory,
    RelTmtCateReqFactory,
    RelTmtIncisoFactory,
    RelTmtTipoReqFactory,
)
from tests.factories.costos import CostoFactory, UmaFactory
from tests.factories.tramites import TramiteFactory

__all__ = [
    # Auth factories
    'UserFactory',
    'SuperUserFactory',
    'AdminUserFactory',
    'OperadorUserFactory',
    'GroupFactory',
    'PermissionFactory',
    'ContentTypeFactory',
    # Catalogos factories
    'CatTramiteFactory',
    'CatEstatusFactory',
    'CatUsuarioFactory',
    'CatPeritoFactory',
    'CatActividadFactory',
    'CatCategoriaFactory',
    'CatIncisoFactory',
    'CatRequisitoFactory',
    'CatTipoFactory',
    'RelTmtCateReqFactory',
    'RelTmtCategoriaFactory',
    'RelTmtIncisoFactory',
    'RelTmtTipoReqFactory',
    'ActividadesFactory',
    'CobroFactory',
    'RelTmtActividadFactory',
    # Costos factories
    'CostoFactory',
    'UmaFactory',
    # Tramites factories
    'TramiteFactory',
]
