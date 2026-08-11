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


def active_department(request):
    """Expose ACTIVE_DEPARTMENT to all templates for conditional rendering."""
    return {
        'ACTIVE_DEPARTMENT': getattr(settings, 'ACTIVE_DEPARTMENT', 'DAU'),
    }
