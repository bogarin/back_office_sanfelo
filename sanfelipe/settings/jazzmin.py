"""
Jazzmin settings for sanfelipe project.

This module contains all Jazzmin-specific configuration for the Django admin.
Jazzmin branding is derived from tenancy settings, allowing each department
to have its own branding while maintaining consistent admin UI structure.
"""

from typing import Any


def configure_jazzmin(tenancy_settings: dict[str, Any]) -> dict[str, Any]:
    """
    Configure and return Jazzmin settings based on tenancy configuration.

    Jazzmin branding values (site_title, site_header, site_brand, site_logo,
    welcome_sign, copyright) are populated from tenancy settings, allowing
    different departments to have their own branding.

    Args:
        tenancy_settings: Dictionary containing tenancy configuration,
            including BACKOFFICE_SITE_TITLE, BACKOFFICE_SITE_HEADER, etc.

    Returns:
        Dictionary containing JAZZMIN_SETTINGS configuration
    """
    return {
        'JAZZMIN_SETTINGS': {
            # Title of the window (defaults to current_admin_site.site_title if absent or None)
            'site_title': tenancy_settings['BACKOFFICE_SITE_TITLE'],
            # Title on the login screen (19 chars max)
            # (defaults to current_admin_site.site_header if absent or None)
            'site_header': tenancy_settings['BACKOFFICE_SITE_HEADER'],
            # Title on the brand (19 chars max)
            # (defaults to current_admin_site.site_header if absent or None)
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
                        'name': 'Mis trámites',
                        # url with ?current_user=True query parameter to filter
                        # trámites assigned to the logged-in user
                        'url': '/admin/tramites/asignados/?analista=_user',
                        # any font-awesome icon
                        'icon': 'fas fa-user',
                        # a list of permissions of user must have to see this link (optional)
                        'permissions': ['books.view_book'],
                    },
                    {
                        'name': 'Todos',
                        # url name e.g `admin:index`, relative urls e.g `/admin/index`
                        # or absolute urls e.g `https://domain.com/admin/index`
                        'url': 'admin:tramites_abiertos_changelist',
                        # any font-awesome icon
                        'icon': 'fas fa-list',
                        # a list of permissions of user must have to see this link (optional)
                        'permissions': ['books.view_book'],
                    },
                    {
                        'name': 'Sin asignar',
                        # url name e.g `admin:index`, relative urls e.g `/admin/index`
                        # or absolute urls e.g `https://domain.com/admin/index`
                        'url': 'tramites:sin-asignar',
                        # any font-awesome icon
                        'icon': 'fas fa-inbox',
                        # a list of permissions of user must have to see this link (optional)
                        'permissions': ['books.view_book'],
                    },
                    {
                        'name': 'Asignados',
                        # url name e.g `admin:index`, relative urls e.g `/admin/index`
                        # or absolute urls e.g `https://domain.com/admin/index`
                        'url': 'admin:tramites_asignados_changelist',
                        # any font-awesome icon
                        'icon': 'fas fa-user-check',
                        # a list of permissions of user must have to see this link (optional)
                        'permissions': ['books.view_book'],
                    },
                    {
                        'name': 'Finalizados',
                        # url name e.g `admin:index`, relative urls e.g `/admin/index`
                        # or absolute urls e.g `https://domain.com/admin/index`
                        'url': 'admin:tramites_finalizados_changelist',
                        # any font-awesome icon
                        'icon': 'fas fa-check-circle',
                        # a list of permissions of user must have to see this link (optional)
                        'permissions': ['books.view_book'],
                    },
                ]
            },
        }
    }
