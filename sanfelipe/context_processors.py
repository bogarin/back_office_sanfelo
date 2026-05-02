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
