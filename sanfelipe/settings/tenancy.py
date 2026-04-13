"""
Tenancy settings for sanfelipe project.

This module contains all tenancy-specific configuration that varies per department:
- Site branding (title, header, brand, logo)
- Site content (welcome sign, copyright)
- Department-specific limits (max trámites per analyst)
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
    tenancy_settings = {
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
        # =============================================================================
        # DEPARTMENT LIMITS
        # =============================================================================
        # Maximum number of trámites that can be assigned to an analyst
        # This limit varies per department based on workload and policies
        'BACKOFFICE_MAX_TRAMITES_POR_ANALISTA': env.int(
            'BACKOFFICE_MAX_TRAMITES_POR_ANALISTA', default=50
        ),
    }

    # =============================================================================
    # DJAZZO-JAZZMIN CONFIGURATION
    # =============================================================================

    # Configure Jazzmin branding from tenancy settings
    # This allows each department to have its own branding
    tenancy_settings['JAZZMIN_SETTINGS'] = {
        # title of the window (Will default to current_admin_site.site_title if absent or None)
        'site_title': tenancy_settings['BACKOFFICE_SITE_TITLE'],
        # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
        'site_header': tenancy_settings['BACKOFFICE_SITE_HEADER'],
        # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
        'site_brand': tenancy_settings['BACKOFFICE_SITE_BRAND'],
        # Logo to use for your site, must be present in static files, used for brand on top left
        'site_logo': tenancy_settings['BACKOFFICE_SITE_LOGO'] or None,
        # Welcome text on the login screen
        'welcome_sign': tenancy_settings['BACKOFFICE_WELCOME_SIGN'],
        # Copyright on the footer
        'copyright': tenancy_settings['BACKOFFICE_COPYRIGHT'],
        # Bootstrap theme with badge styles (solar has .badge, .badge-primary, etc.)
        'theme': 'vendor/bootswatch/solar/bootstrap.min.css',
        'custom_css': 'admin/css/backoffice.css',
        'show_sidebar': True,
        'navigation_expanded': False,
        'related_modal_active': True,
        'hide_apps': ['contenttypes', 'sessions', 'admin', 'tramites'],
        'hide_models': ['auth.group'],
        'custom_links': {
            'Trámites': [
                {
                    'name': 'Todos',
                    # url name e.g `admin:index`, relative urls e.g `/admin/index` or absolute urls e.g `https://domain.com/admin/index`
                    'url': 'admin:tramites_tramite_changelist',
                    # any font-awesome icon
                    'icon': 'fas fa-comments',
                    # a list of permissions of user must have to see this link (optional)
                    'permissions': ['books.view_book'],
                },
                {
                    'name': 'Sin asignar',
                    # url name e.g `admin:index`, relative urls e.g `/admin/index` or absolute urls e.g `https://domain.com/admin/index`
                    'url': 'make_messages',
                    # any font-awesome icon
                    'icon': 'fas fa-comments',
                    # a list of permissions of user must have to see this link (optional)
                    'permissions': ['books.view_book'],
                },
                {
                    'name': 'Asignados',
                    # url name e.g `admin:index`, relative urls e.g `/admin/index` or absolute urls e.g `https://domain.com/admin/index`
                    'url': 'make_messages',
                    # any font-awesome icon
                    'icon': 'fas fa-comments',
                    # a list of permissions of user must have to see this link (optional)
                    'permissions': ['books.view_book'],
                },
                {
                    'name': 'Finalizados',
                    # url name e.g `admin:index`, relative urls e.g `/admin/index` or absolute urls e.g `https://domain.com/admin/index`
                    'url': 'make_messages',
                    # any font-awesome icon
                    'icon': 'fas fa-comments',
                    # a list of permissions of user must have to see this link (optional)
                    'permissions': ['books.view_book'],
                },
                {
                    'name': 'Cancelados',
                    # url name e.g `admin:index`, relative urls e.g `/admin/index` or absolute urls e.g `https://domain.com/admin/index`
                    'url': 'make_messages',
                    # any font-awesome icon
                    'icon': 'fas fa-comments',
                    # a list of permissions of user must have to see this link (optional)
                    'permissions': ['books.view_book'],
                },
            ]
        },
    }

    return tenancy_settings
