"""
Views for core application.

This module contains the main views for the Backoffice San Felipe.
Following Django's best practices with proper separation of concerns.
"""

from typing import Dict, Any
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


def home(request: HttpRequest) -> HttpResponse:
    """
    Render the home page.

    This view displays the main landing page of the Backoffice San Felipe
    with a link to the Django admin interface.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Rendered home page template.
    """
    context: Dict[str, Any] = {
        "title": "Backoffice San Felipe",
        "subtitle": "Sistema de Gestión de Trámites",
    }
    return render(request, "core/home.html", context)
