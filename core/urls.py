"""
URL configuration for core application.

This module contains URL routing for custom admin views.
"""

from django.urls import path

from core.views import asignar_rol

app_name = 'core'

urlpatterns = [
    # Admin role assignment
    path('admin/auth/user/asignar-rol/', asignar_rol, name='asignar-rol'),
]
