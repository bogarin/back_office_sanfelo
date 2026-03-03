"""
Generic admin tests for model registration.

This module contains parametrized tests that verify all models are registered in admin.
"""

import pytest


@pytest.mark.django_db
class TestAdminRegistration:
    """Test that all models are registered with admin."""

    @pytest.mark.parametrize(
        'app_label,model_name',
        [
            ('tramites', 'Tramite'),
            ('costos', 'Costo'),
            ('costos', 'Uma'),
            ('catalogos', 'CatTramite'),
            ('catalogos', 'CatEstatus'),
            ('catalogos', 'CatPerito'),
            ('catalogos', 'CatActividad'),
            ('catalogos', 'CatCategoria'),
            ('catalogos', 'CatInciso'),
            ('catalogos', 'CatRequisito'),
            ('catalogos', 'CatTipo'),
            ('catalogos', 'Actividades'),
            ('catalogos', 'Cobro'),
        ],
    )
    def test_model_registered_in_admin(self, app_label, model_name):
        """Test that a model is registered in admin site."""
        from django.contrib import admin
        from django.apps import apps

        Model = apps.get_model(app_label, model_name)

        registered = False
        for model, model_admin in admin.site._registry.items():
            if model._meta.model_name == Model._meta.model_name:
                registered = True
                break

        assert registered, f'{model_name} should be registered in admin'
