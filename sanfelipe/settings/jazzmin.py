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
            'site_logo': 'logo_dark.svg',
            'login_logo': 'logo.svg',
            # Welcome text on the login screen
            'welcome_sign': tenancy_settings['BACKOFFICE_WELCOME_SIGN'],
            # Copyright on the footer
            'copyright': tenancy_settings['BACKOFFICE_COPYRIGHT'],
            'custom_css': 'admin/css/backoffice.css',
            'show_sidebar': True,
            'navigation_expanded': True,
            'related_modal_active': True,
            # Hide 'contenttypes', 'sessions', 'admin', 'tramites' apps
            # Auth app visibility is controlled via auth.view_user permission
            # Tramites app is controlled via custom_links below
            'hide_apps': ['contenttypes', 'sessions', 'admin', 'tramites', 'core'],
            'hide_models': ['auth.group'],
            'custom_links': {
                # Auth group: User and group management (only Administrador)
                'Administración': [
                    {
                        'name': 'Usuarios',
                        'url': 'admin:core_user_changelist',
                        'icon': 'fas fa-users',
                        # Requires auth permission to view (only Administrador has this)
                        'permissions': ['core.view_user'],
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
                        'name': 'Trámites en curso',
                        'url': 'admin:tramites_tramite_changelist',
                        'icon': 'fas fa-inbox',
                        # No es para analistas
                        'permissions': ['tramites.acceso_coordinador'],
                    },
                    {
                        'name': 'Trámites finalizados',
                        'url': 'admin:tramites_cerrado_changelist',
                        'icon': 'fas fa-flag-checkered',
                        # No es para analistas
                        'permissions': ['tramites.acceso_coordinador'],
                    },
                ],
            },
        },
        'JAZZMIN_UI_TWEAKS': {
            "theme": "united",
            "default_theme_mode": "light",
            "footer_small_text": True,
            "brand_small_text": True,
            "sidebar_nav_flat_style": True,
            'brand_colour': 'green'
        }
    }
