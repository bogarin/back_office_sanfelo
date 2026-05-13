"""
Context processors for sanfelipe project.

Provides global variables to all template contexts.
"""

from django.conf import settings


def image_tag(request):
    """Expose IMAGE_TAG_BACKOFFICE to all templates."""
    return {
        'IMAGE_TAG_BACKOFFICE': getattr(settings, 'IMAGE_TAG_BACKOFFICE', 'dev'),
    }


def active_department(request):
    """Expose ACTIVE_DEPARTMENT to all templates for conditional rendering."""
    return {
        'ACTIVE_DEPARTMENT': getattr(settings, 'ACTIVE_DEPARTMENT', 'DAU'),
    }
