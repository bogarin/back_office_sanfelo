"""
URL configuration for sanfelipe project.

San Felipe Government Backoffice URL routing.
Microservice architecture with Django Admin for backoffice UI.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

import tramites.urls
from core.views import asignar_rol, health_check, invalidate_catalog_cache

urlpatterns = [
    # Health check
    path('health/', health_check, name='health-check'),
    # Custom admin views - must be before admin.site.urls
    path('admin/auth/user/asignar-rol/', asignar_rol, name='asignar-rol'),
    # Maintenance: invalidate catalog cache (Administrador only)
    path(
        'admin/maintenance/invalidate-cache/',
        invalidate_catalog_cache,
        name='invalidate-catalog-cache',
    ),
    path(
        'admin/tramites/',
        include(tramites.urls, namespace='tramites'),
    ),
    # Django admin (uses custom admin/index.html template override)
    path('admin/', admin.site.urls),
    # Redirect root to admin dashboard
    path('', RedirectView.as_view(url='/admin/', permanent=True), name='admin-home'),
]

# Debug configuration - only in development
if settings.DEBUG:
    # Django Debug Toolbar URLs
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls)), *urlpatterns]

    # Static files serving in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
