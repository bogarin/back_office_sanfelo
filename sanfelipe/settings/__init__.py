"""
Django settings for sanfelipe project.

Microservice for San Felipe Government Backoffice.
Uses PostgreSQL with schema separation:
- backoffice schema: Django auth, admin, sessions, messages, staticfiles
- public schema: tramites, core (business data managed externally)
"""

from pathlib import Path

import environ
import importlib.util

from .security import configure_security, validate_secret_key
from .tenancy import configure_tenancy
from .jazzmin import configure_jazzmin
from .logging import configure_logging
from .sftp import configure_sftp

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# settings/ is now a package, so we need to go up 3 levels instead of 2
# From: sanfelipe/settings/__init__.py -> sanfelipe/ -> project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment configuration
env = environ.Env()

# Read environment variables from .env file
# Copy .env.example to .env and customize with your actual values
env_file = BASE_DIR / '.env'

if env_file.exists():
    environ.Env.read_env(env_file)
else:
    import warnings

    warnings.warn(
        f'Environment file not found: {env_file}. '
        f'Using environment variables directly. '
        f'Set DJANGO_* and POSTGRESQL_DB_URL environment variables for configuration.',
        RuntimeWarning,
        stacklevel=2,
    )

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# Configure security settings from dedicated security module
# This includes SECRET_KEY, DEBUG, ALLOWED_HOSTS, CSP, and production security headers
security_config = configure_security(env)

# Apply all security settings to the module namespace
for key, value in security_config.items():
    globals()[key] = value

# =============================================================================
# TENANCY SETTINGS
# =============================================================================

# Configure tenancy settings from dedicated tenancy module
# This includes site branding, content, and department-specific limits
tenancy_config = configure_tenancy(env)

# Apply all tenancy settings to the module namespace
for key, value in tenancy_config.items():
    globals()[key] = value

# =============================================================================
# JAZZMIN SETTINGS
# =============================================================================

# Configure Jazzmin settings from dedicated jazzmin module
# This includes admin UI customization, branding, and navigation
jazzmin_config = configure_jazzmin(tenancy_config)

# Apply Jazzmin settings to the module namespace
for key, value in jazzmin_config.items():
    globals()[key] = value

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================


INSTALLED_APPS = [
    # Django core apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Django Admin
    'jazzmin',
    'django.contrib.admin',
    # Third-party apps (only in DEBUG mode, not during tests, and only if installed)
    'debug_toolbar'
    if (DEBUG and not TESTING and importlib.util.find_spec('debug_toolbar'))
    else None,
    # Local apps (backend data in PostgreSQL, managed externally)
    'tramites',
    'core',
    # Test-only models for permission testing (only during tests)
    'tests' if TESTING else None,
]

# Filter out None values (conditional apps)
INSTALLED_APPS = [app for app in INSTALLED_APPS if app]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csp.ContentSecurityPolicyMiddleware',  # CSP middleware for XSS protection
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.CacheUserRolesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG and not TESTING and importlib.util.find_spec('debug_toolbar'):
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'sanfelipe.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # CSP context processor - provides csp_nonce for inline scripts/styles
                'django.template.context_processors.csp',
            ],
        },
    },
]

WSGI_APPLICATION = 'sanfelipe.wsgi.application'
ASGI_APPLICATION = 'sanfelipe.asgi.application'


# =============================================================================
# DATABASE
# =============================================================================

# Multi-database configuration with schema separation:
# - default (PostgreSQL, backoffice schema): Django auth, admin, sessions, messages, staticfiles, debug_toolbar
# - backend (PostgreSQL, public schema): tramites, core (business data)
#
# The database router (core.db_router.ModelBasedRouter) routes queries
# to the appropriate database based on the model's db_table attribute.
#
# Backend tables are managed externally (managed=False), so Django won't
# create or modify them - it only reads/writes to existing PostgreSQL tables.

db = env.db('POSTGRESQL_DB_URL')
backoffice_schema = env('BACKOFFICE_DB_SCHEMA', default='backoffice')
backend_schema = env('BACKEND_DB_SCHEMA', default='public')

DATABASES = {
    'default': {**db, 'OPTIONS': {'options': f'-c search_path={backoffice_schema}'}},
    'backend': {**db, 'OPTIONS': {'options': f'-c search_path={backend_schema}'}},
}

# Route backend apps to PostgreSQL
# Use the model-based router that respects db_table schema prefixes
DATABASE_ROUTERS = ['core.db_router.ModelBasedRouter']

# =============================================================================
# CACHE
# =============================================================================

# Cache configuration:
# Testing: DummyCache (no side effects in tests)
# Dev + Prod: LocMemCache for process-local caching.
#   - Used by TramiteManager for statistics caching (tramite_stats:*).
#   - Fast, in-memory storage per process.
#   - Requires consideration for multi-worker setups (each worker has its own cache).
#   - No additional setup required.
# Catalog models use CachedCatalogManager with @lru_cache (process memory,
# no Django cache involvement).
if TESTING:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================
# Usamos Argon2 por default
# https://docs.djangoproject.com/en/6.0/topics/auth/passwords/#using-argon2-with-django
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 10},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'es-ar'  # Spanish - Argentina (San Felipe)
TIME_ZONE = 'America/Argentina/San_Luis'  # San Felipe timezone

USE_I18N = True
USE_L10N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# =============================================================================
# MEDIA FILES
# =============================================================================

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# DEBUG TOOLBAR
# =============================================================================

if DEBUG:
    INTERNAL_IPS = env.list('DJANGO_INTERNAL_IPS', default=['127.0.0.1'])

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: not TESTING,
    }

# =============================================================================
# LOGGING
# =============================================================================

# Configure logging settings from dedicated logging module
# This includes log level configuration, console and file handlers,
# and specific logger configurations for Django apps
logging_config = configure_logging(env, BASE_DIR, DEBUG)

# Apply all logging settings to the module namespace
for key, value in logging_config.items():
    globals()[key] = value

# =============================================================================
# SFTP STORAGE SETTINGS
# =============================================================================

# Configure SFTP storage settings from dedicated SFTP module
# This includes connection settings, remote directory paths,
# and django-storages SFTP backend configuration
sftp_config = configure_sftp(env, debug=DEBUG)

# Apply all SFTP settings to the module namespace
for key, value in sftp_config.items():
    if key != 'SFTP_STORAGE_CONFIG':
        globals()[key] = value

# Merge SFTP storage into STORAGES without overwriting existing backends
if 'STORAGES' not in globals():
    from django.conf.global_settings import STORAGES as DEFAULT_STORAGES

    globals()['STORAGES'] = DEFAULT_STORAGES.copy()

globals()['STORAGES']['sftp'] = sftp_config.get('SFTP_STORAGE_CONFIG')

# =============================================================================
# AUTHENTICATION (Django built-in)
# =============================================================================

# Use Django's default auth backend
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# URLs de autenticación
# LOGIN_URL: URL a la que redirige el decorador @login_required cuando no hay usuario autenticado
LOGIN_URL = 'admin:login'

# LOGIN_REDIRECT_URL: URL a la que redirige después de login exitoso
LOGIN_REDIRECT_URL = 'admin:index'

# LOGOUT_REDIRECT_URL: URL a la que redirige después de logout
LOGOUT_REDIRECT_URL = 'admin:login'

# Role-based access control is managed by core.rbac.constants.BackOfficeRole

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = env.list('DJANGO_CSRF_TRUSTED_ORIGINS', default=[])

# =============================================================================
# SESSION SETTINGS
# =============================================================================

# Use signed cookies - perfect for minimal session data (auth, CSRF, messages)
# No server-side storage needed, fast and simple
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_AGE = env.int('DJANGO_SESSION_COOKIE_AGE', default=3600)  # 1 hour
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# =============================================================================
# EMAIL SETTINGS (for notifications)
# =============================================================================

EMAIL_BACKEND = env(
    'DJANGO_EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = env('DJANGO_EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('DJANGO_EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('DJANGO_EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('DJANGO_EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('DJANGO_EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DJANGO_DEFAULT_FROM_EMAIL', default='noreply@sanfelipe.gob.ar')

# =============================================================================
# TRAMITES SETTINGS
# =============================================================================

TRAMITE_ESTADOS = (
    ('borrador', 'Borrador'),
    ('pendiente', 'Pendiente'),
    ('en_proceso', 'En Proceso'),
    ('aprobado', 'Aprobado'),
    ('rechazado', 'Rechazado'),
    ('completado', 'Completado'),
)

TRAMITE_PRIORIDADES = (
    ('baja', 'Baja'),
    ('media', 'Media'),
    ('alta', 'Alta'),
    ('urgente', 'Urgente'),
)

# Pagination
DEFAULT_PAGE_SIZE = env.int('DJANGO_DEFAULT_PAGE_SIZE', default=25)

# Statistics cache timeout (in seconds)
# Reduces round-trip queries to external database
# Default: 5 minutes (300 seconds)
TRAMITE_STATS_CACHE_TIMEOUT = env.int(
    'TRAMITE_STATS_CACHE_TIMEOUT',
    default=300,  # 5 minutes
)

# =============================================================================
# SANITY CHECK
# =============================================================================

from sanfelipe.settings.security import validate_secret_key

is_valid, reason = validate_secret_key(SECRET_KEY)
if not is_valid:
    if not DEBUG:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured(reason)
    import warnings

    warnings.warn(f'INSECURE SECRET_KEY: {reason}', RuntimeWarning)

# Validate ALLOWED_HOSTS in production
if not DEBUG and (not ALLOWED_HOSTS or ALLOWED_HOSTS == ['*']):
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured(
        'ALLOWED_HOSTS must be explicitly set in production. '
        'Wildcard "*" or empty list is not allowed.'
    )
