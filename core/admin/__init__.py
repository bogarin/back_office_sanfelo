"""Django Admin global configuration.

Configures the admin interface for the backoffice with:
- Custom site headers and titles
- Dashboard modifications
- Admin actions and permissions
- Async audit trail using background tasks
"""

import logging

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User

from core.admin.base import BaseModelAdmin, ReadOnlyModelAdmin, ActionableReadOnlyMixin
from core.admin.actions import (
    mark_as_active,
    mark_as_inactive,
    mark_urgent,
    mark_not_urgent,
    mark_as_paid,
    mark_as_unpaid,
    asignar_rol,
)
from core.admin.user_admin import BackofficeUserAdmin
from core.admin.site import BackofficeAdminSite
from core.admin.mixins import RoleBasedAccessMixin
from core.admin.user_admin import BackofficeUserAdmin
from core.admin.site import BackofficeAdminSite
from core.admin.mixins import RoleBasedAccessMixin

logger = logging.getLogger(__name__)

# Admin Site Configuration
admin.site.site_header = 'Backoffice San Felipe'
admin.site.site_title = 'Backoffice San Felipe'
admin.site.index_title = 'Panel de Administración'


# =============================================================================
# Register Custom User Admin
# =============================================================================

# Unregister default User admin and register our custom version
admin.site.unregister(User)
admin.site.register(User, BackofficeUserAdmin)


__all__ = [
    # Base classes
    'BaseModelAdmin',
    'ReadOnlyModelAdmin',
    'ActionableReadOnlyMixin',
    # Actions
    'mark_as_active',
    'mark_as_inactive',
    'mark_urgent',
    'mark_not_urgent',
    'mark_as_paid',
    'mark_as_unpaid',
    'asignar_rol',
    # User admin
    'BackofficeUserAdmin',
    # Admin site
    'BackofficeAdminSite',
    # Mixins
    'RoleBasedAccessMixin',
]
