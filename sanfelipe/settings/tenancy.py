"""
Tenancy settings for sanfelipe project.

This module contains all tenancy-specific configuration that varies per department:
- Site branding (title, header, brand, logo)
- Site content (welcome sign, copyright)
- Department-specific limits (max trámites per analyst)

Note: Jazzmin configuration is handled separately in jazzmin.py
"""

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
    return {
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
        'BACKOFFICE_SITE_LOGO': env('BACKOFFICE_SITE_LOGO', default=''),
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
    }

