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

    Custom links in the sidebar use role-based permissions to control visibility:
    - Auth links: Only visible to Administrador role
    - Tramites links: Visible based on specific role permissions

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
            'navigation_expanded': True,
            'related_modal_active': True,
            # Hide 'contenttypes', 'sessions', 'admin', 'tramites' apps
            # Auth app visibility is controlled via auth.view_user permission
            # Tramites app is controlled via custom_links below
            'hide_apps': ['contenttypes', 'sessions', 'admin', 'tramites'],
            'hide_models': ['auth.group'],
            'custom_links': {
                # Auth group: User and group management (only Administrador)
                'auth': [
                    {
                        'name': 'Usuarios',
                        'url': 'admin:auth_user_changelist',
                        'icon': 'fas fa-users',
                        # Requires auth permission to view (only Administrador has this)
                        'permissions': ['auth.view_user'],
                    },
                ],
                # Trámites group: Role-based visibility via custom permissions
                'Trámites': [
                    {
                        'name': 'Mis trámites',
                        # URL with query parameter to filter trámites assigned to logged-in user
                        'url': 'admin:tramites_buzon_changelist',
                        'icon': 'fas fa-user',
                        # Solo los analistas deberían ver este enlace
                        'permissions': ['tramites.acceso_analista'],
                    },
                    {
                        'name': 'Disponibles',
                        'url': 'admin:tramites_disponible_changelist',
                        'icon': 'fas fa-inbox',
                        # Solo los analistas deberían ver este enlace
                        'permissions': ['tramites.acceso_analista'],
                    },
                    {
                        'name': 'Trámites',
                        'url': 'admin:tramites_tramite_changelist',
                        'icon': 'fas fa-list',
                        # No es para analistas
                        'permissions': ['tramites.acceso_coordinador'],
                    },
                ],
            },
        }
    }
