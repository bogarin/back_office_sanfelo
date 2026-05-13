"""Middleware for the backoffice application.

Provides middleware that resolves user roles once per request and caches
them on ``request.user.roles`` as a ``set[str]``, eliminating repeated
database queries for group membership checks within a single request.

Also provides error logging middleware that ensures unhandled exceptions
are logged with request context before Django's default 500 handler.
"""

import logging

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class CacheUserRolesMiddleware:
    """Resolve user group membership once per request.

    After ``AuthenticationMiddleware`` has set ``request.user``, this
    middleware fetches all group names in a single query and stores them
    on ``request.user.roles`` (a ``set[str]``).

    Downstream code can then check membership with plain set operations::

        BackOfficeRole.COORDINADOR in request.user.roles

    No database query is needed for the rest of the request lifecycle.

    For anonymous users, ``request.user.roles`` is set to an empty ``set()``
    so downstream code can safely access ``request.user.roles`` without
    ``getattr()`` guards.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.user.roles = set(request.user.groups.values_list('name', flat=True))
        elif hasattr(request, 'user'):
            request.user.roles = set()
        return self.get_response(request)


class ErrorLoggingMiddleware:
    """Log unhandled exceptions with request context.

    Ensures every unhandled exception is logged with the user, URL, and
    request method for easier debugging.  Returns ``None`` so Django
    continues to its default error handling (handler500 → 500.html).

    Must be registered AFTER ``CacheUserRolesMiddleware`` so
    ``request.user.roles`` is available.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> None:
        """Log the exception with full request context.

        Returns ``None`` so Django continues to its default error handling.
        """
        user = getattr(request, 'user', None)
        username = getattr(user, 'username', 'anonymous')

        logger.error(
            'Excepción no manejada: %s user=%s method=%s path=%s',
            exception,
            username,
            request.method,
            request.get_full_path(),
            exc_info=True,
        )
