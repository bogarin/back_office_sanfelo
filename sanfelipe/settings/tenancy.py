"""
Tenancy settings for sanfelipe project.

This module contains all tenancy-specific configuration that varies per department:
- Site branding (title, header, brand, logo)
- Site content (welcome sign, copyright)
- Department-specific limits (max trámites per analyst)

Note: Jazzmin configuration is handled separately in jazzmin.py
"""

from django.core.exceptions import ImproperlyConfigured
from environ import Env


def configure_tenancy(env: Env) -> dict:
    """
    Configure and return all tenancy-related settings.

    These settings vary per department/deployment and are configured
    via environment variables, allowing a single Docker image to serve
    multiple departments with different branding and configurations.

    Args:
        env: Environ instance for reading environment variables

    Returns:
        Dictionary containing all tenancy settings
    """
    # =============================================================================
    # Department configuration
    # =============================================================================
    # Used for conditional template rendering and department-specific behavior.
    BACKOFFICE_DEPARTMENT = env('BACKOFFICE_DEPARTMENT', default='DAU').strip().upper()
    if BACKOFFICE_DEPARTMENT not in {'DAU', 'SEC', 'TES'}:
        raise ImproperlyConfigured(
            'BACKOFFICE_DEPARTMENT must be one of '
            f"{{'DAU', 'SEC', 'TES'}}, got '{BACKOFFICE_DEPARTMENT}'"
        )
    return {
        'BACKOFFICE_DEPARTMENT': BACKOFFICE_DEPARTMENT,
        # =============================================================================
        # SITE BRANDING (UI Customization)
        # =============================================================================
        # Title of the window (defaults to current_admin_site.site_title if absent or None)
        'BACKOFFICE_SITE_TITLE': env('BACKOFFICE_SITE_TITLE', default='Ventanilla Urbana Digital'),
        # Title on the login screen (19 chars max)
        # (defaults to current_admin_site.site_header if absent or None)
        'BACKOFFICE_SITE_HEADER': env('BACKOFFICE_SITE_HEADER', default='San Felipe'),
        # Title on the brand (19 chars max)
        # (defaults to current_admin_site.site_header if absent or None)
        'BACKOFFICE_SITE_BRAND': env('BACKOFFICE_SITE_BRAND', default='Ventanilla Urbana Digital'),
        # Logo to use for your site, must be present in static files
        'BACKOFFICE_SITE_LOGO': env('BACKOFFICE_SITE_LOGO', default='/static/logo.svg'),
        # =============================================================================
        # SITE CONTENT
        # =============================================================================
        # Welcome text on the login screen
        'BACKOFFICE_WELCOME_SIGN': env(
            'BACKOFFICE_WELCOME_SIGN', default='Ventanilla Urbana Digital - Municipio de San Felipe'
        ),
        # Copyright on the footer
        'BACKOFFICE_COPYRIGHT': env(
            'BACKOFFICE_COPYRIGHT',
            default='Municipio de San Felipe - Todos los derechos reservados',
        ),
        # =============================================================================
        # TRAMITES SETTINGS
        # =============================================================================
        'BACKOFFICE_TRAMITES_PER_PAGE': env.int('BACKOFFICE_TRAMITES_PER_PAGE', default=25),
        # Transitions disabled per department (comma-separated estatus IDs).
        # SEC example: BACKOFFICE_DISABLED_TRANSITIONS=205 (disables EN_DILIGENCIA).
        # Values are converted to int at load time for correct comparison with TRANSITIONS keys.
        'BACKOFFICE_DISABLED_TRANSITIONS': [
            int(x) for x in env.list('BACKOFFICE_DISABLED_TRANSITIONS', default=[]) if x.strip()
        ],
    }
