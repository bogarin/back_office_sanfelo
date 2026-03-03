"""
Test settings for sanfelipe project.

Extends base settings with test-specific overrides:
- Routes all databases to SQLite (no PostgreSQL needed)
- Enables managed=True for business models during tests
- Simplified configuration for faster, reliable testing

Usage:
    DJANGO_SETTINGS_MODULE=sanfelipe.settings_test TESTING=1 uv run manage.py test core
    just test --settings=sanfelipe.settings_test
"""

from .settings import *

# =============================================================================
# TEST-SPECIFIC OVERRIDES
# =============================================================================

# Ensure test mode is active
TESTING = True

# Override DATABASES to use only SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db' / 'test_db.sqlite3'),
    }
}

# Use TestRouter - instantiate directly (no singleton)
DATABASE_ROUTERS = ['core.db_router.TestRouter']

# Explicitly use dummy cache (no side effects in tests)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Remove 'tests' app from INSTALLED_APPS (we don't need it anymore)
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'tests']
