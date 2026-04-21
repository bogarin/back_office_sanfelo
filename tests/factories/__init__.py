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
]
