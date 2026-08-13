"""
Context processors for sanfelipe project.

Provides global variables to all template contexts.
"""

from django.conf import settings


def version(request):
    """Expose BACKOFFICE_VERSION (from pyproject.toml) to all templates."""
    return {
        'BACKOFFICE_VERSION': getattr(settings, 'VERSION', 'dev'),
    }


def BACKOFFICE_DEPARTMENT(request):
    """Expose BACKOFFICE_DEPARTMENT to all templates for conditional rendering."""
    return {
        'BACKOFFICE_DEPARTMENT': getattr(settings, 'BACKOFFICE_DEPARTMENT', 'DAU'),
    }
