"""Factory-boy factories for all models."""

from tests.factories.auth import (
    AdminUserFactory,
    ContentTypeFactory,
    GroupFactory,
    PermissionFactory,
    SuperUserFactory,
    UserFactory,
)
from tests.factories.catalogos import (
    ActividadFactory,
    ActividadesFactory,
    PeritoFactory,
    TramiteCatalogoFactory,
    TramiteEstatusFactory,
)
from tests.factories.tramites import TramiteFactory, TramiteWithEstatusFactory

__all__ = [
    # Auth factories
    'UserFactory',
    'SuperUserFactory',
    'AdminUserFactory',
    'GroupFactory',
    'PermissionFactory',
    'ContentTypeFactory',
    # Catalog factories
    'TramiteCatalogoFactory',
    'TramiteEstatusFactory',
    'PeritoFactory',
    'ActividadFactory',
    'ActividadesFactory',
    # Tramites factories
    'TramiteFactory',
    'TramiteWithEstatusFactory',
]
