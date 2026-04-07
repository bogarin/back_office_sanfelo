"""
Views for core application.

This module contains main views for Backoffice San Felipe.
Following Django's best practices with proper separation of concerns.
"""

from django.http import HttpRequest, HttpResponse


def health_check(request: HttpRequest) -> HttpResponse:
    """
    Health check endpoint for monitoring.

    This endpoint returns a simple 'OK' response for health checks.
    It's commonly used by load balancers, monitoring systems, and orchestration tools.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Simple 'OK' response with status 200.
    """
    return HttpResponse('OK', status=200)
