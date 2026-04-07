"""
URL configuration for sanfelipe project.

San Felipe Government Backoffice URL routing.
Microservice architecture with Django Admin for backoffice UI.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import health_check, admin_home

urlpatterns = [
    # Health check
    path('health/', health_check, name='health-check'),
    # Auth (Django admin auth)
    path('admin/', admin.site.urls, name='admin'),
    # Custom home
    path('', admin_home, name='admin-home'),
]

# Debug configuration - only in development
if settings.DEBUG:
    # Django Debug Toolbar URLs
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls)), *urlpatterns]

    # Static files serving in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
