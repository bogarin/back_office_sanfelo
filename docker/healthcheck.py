#!/usr/bin/env python3
"""
Health check script for San Felipe backoffice container.

This script performs health checks for the container services:
1. Nginx health check: Checks if nginx is responding on port 8080
2. Django health check: Checks if Django app is responding on port 8081

Note: SFTP connectivity is NOT checked. SFTP is an external dependency
and the container should remain healthy even if SFTP is temporarily
unavailable.

Exit codes:
- 0: All checks passed
- 1: Health check failed
"""

import sys
from http.client import HTTPConnection, HTTPException
from urllib.error import URLError
from urllib.request import urlopen

# Configuration
NGINX_HEALTH_URL = 'http://127.0.0.1:8080/healthz'
DJANGO_HEALTH_URL = 'http://127.0.0.1:8081/admin/'
TIMEOUT_SECONDS = 5


def check_url(url: str, name: str) -> bool:
    """Check if a URL is responding with a 200 OK status.

    Args:
        url: The URL to check.
        name: Descriptive name for the service being checked.

    Returns:
        True if the URL responds with 200 OK, False otherwise.
    """
    try:
        response = urlopen(url, timeout=TIMEOUT_SECONDS)
        return response.status == 200
    except (HTTPException, URLError, ConnectionError, TimeoutError) as exc:
        print(f'❌ {name} failed: {exc}', file=sys.stderr)
        return False


def check_nginx() -> bool:
    """Check if nginx is responding on port 8080.

    Returns:
        True if nginx is healthy, False otherwise.
    """
    return check_url(NGINX_HEALTH_URL, 'Nginx')


def check_django() -> bool:
    """Check if Django app is responding on port 8081.

    Returns:
        True if Django is healthy, False otherwise.
    """
    return check_url(DJANGO_HEALTH_URL, 'Django')


def main() -> int:
    """Run all health checks and return appropriate exit code.

    Returns:
        0 if all checks pass, 1 otherwise.
    """
    print('🏥 Running health checks...', file=sys.stderr)

    nginx_healthy = check_nginx()
    django_healthy = check_django()

    if nginx_healthy:
        print('✅ Nginx: healthy', file=sys.stderr)
    else:
        print('❌ Nginx: unhealthy', file=sys.stderr)

    if django_healthy:
        print('✅ Django: healthy', file=sys.stderr)
    else:
        print('❌ Django: unhealthy', file=sys.stderr)

    # Overall health
    if nginx_healthy and django_healthy:
        print('✅ All health checks passed', file=sys.stderr)
        return 0
    else:
        print('❌ Health checks failed', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
