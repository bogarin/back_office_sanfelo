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
from core.views import (
    asignar_rol,
    health_check,
    invalidate_catalog_cache,
    pwa_manifest,
    serviceworker,
    test_errors,
    test_rendering,
)

# PWA head (manifest + icons) on the login page, which uses
# registration/base.html instead of admin/base_site.html
admin.site.login_template = 'admin/pwa_login.html'

urlpatterns = [
    # Health check
    path('health/', health_check, name='health-check'),
    # PWA manifest
    path('manifest.json', pwa_manifest, name='pwa-manifest'),
    # PWA service worker (root path = root scope)
    path('sw.js', serviceworker, name='serviceworker'),
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

# Custom error handlers
handler403 = 'core.views.custom_permission_denied'
handler404 = 'core.views.custom_page_not_found'
handler500 = 'core.views.custom_server_error'

# Debug configuration - only in development
if settings.DEBUG:
    import importlib.util

    if importlib.util.find_spec('debug_toolbar'):
        import debug_toolbar

        urlpatterns = [path('__debug__/', include(debug_toolbar.urls)), *urlpatterns]

    urlpatterns += [path('test_rendering/', test_rendering, name='test-rendering')]
    urlpatterns += [path('test_errors/', test_errors, name='test-errors')]
    # Static files serving in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
