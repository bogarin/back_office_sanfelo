"""
Test settings for sanfelipe project.

Extends base settings with test-specific overrides:
- Uses in-memory SQLite for all database operations (no PostgreSQL needed)
- Bypasses routing complexity for faster, more reliable test execution
- Simplified configuration for isolated test environments

The ModelBasedRouter is preserved to test routing logic when needed.
For most tests, using SQLite simplifies setup and execution while maintaining
adequate test coverage for core functionality.

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

# Override DATABASES to use in-memory SQLite for all models
# This provides fast, isolated test execution without external dependencies
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use ModelBasedRouter to test routing logic
# Set to empty list [] if you want to bypass routing entirely
DATABASE_ROUTERS = ['core.db_router.ModelBasedRouter']

# Explicitly use dummy cache (no side effects in tests)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Remove 'tests' app from INSTALLED_APPS (we don't need it anymore)
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'tests']
