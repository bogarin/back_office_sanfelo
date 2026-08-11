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
    PeritoFactory,
    TramiteCatalogoFactory,
    TramiteEstatusFactory,
)
from tests.factories.tramites import (
    TramiteFactory,
    TramiteWithEstatusFactory,
)

__all__ = [
    'ActividadFactory',
    'AdminUserFactory',
    'ContentTypeFactory',
    'GroupFactory',
    'PeritoFactory',
    'PermissionFactory',
    'SuperUserFactory',
    # Catalog factories
    'TramiteCatalogoFactory',
    'TramiteEstatusFactory',
    # Tramites factories
    'TramiteFactory',
    'TramiteWithEstatusFactory',
    # Auth factories
    'UserFactory',
]
