"""
URL configuration for sanfelipe project.

San Felipe Government Backoffice URL routing.
Microservice architecture with Django Admin for backoffice UI.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

from core.views import home


def health_check(request: HttpResponse) -> HttpResponse:
    """Health check endpoint for monitoring."""
    return HttpResponse("OK", status=200)


urlpatterns = [
    # Home page
    path("", home, name="home"),
    # Health check
    path("health/", health_check, name="health-check"),
    # Django Admin
    path("admin/", admin.site.urls),
    # Future APIs can be added here
    # path('api/reportes/', include('reportes.urls')),
]

# Debug configuration - only in development
if settings.DEBUG:
    # Django Debug Toolbar URLs
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
        *urlpatterns
    ]

    # Static files serving in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
