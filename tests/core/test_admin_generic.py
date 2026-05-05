"""Tests for Django admin model registration.

Ensures every model that should appear in the admin site is actually
registered, preventing accidental removal or misconfiguration.
"""

import pytest
from django.apps import apps
from django.contrib import admin


# ---------------------------------------------------------------------------
# All models registered via @admin.register() in core/admin.py and
# tramites/admin.py.  If a new model is added to admin, update this list.
# ---------------------------------------------------------------------------

ADMIN_REGISTERED_MODELS = [
    ('core', 'User'),
    ('tramites', 'Tramite'),
    ('tramites', 'Buzon'),
    ('tramites', 'Disponible'),
    ('tramites', 'Cerrado'),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'app_label, model_name',
    ADMIN_REGISTERED_MODELS,
    ids=[f'{app}.{name}' for app, name in ADMIN_REGISTERED_MODELS],
)
def test_model_registered_in_admin(app_label, model_name):
    """Every model in ADMIN_REGISTERED_MODELS must be in Django admin."""
    Model = apps.get_model(app_label, model_name)
    assert Model in admin.site._registry, (
        f'{app_label}.{model_name} is not registered in admin site'
    )
