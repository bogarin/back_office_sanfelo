"""
Django settings for sanfelipe project.

Microservice for San Felipe Government Backoffice.
Uses Django's built-in auth system with SQLite.
Business data (tramites, buzon) uses PostgreSQL.
"""

from pathlib import Path

import environ

from .security import configure_security
from .tenancy import configure_tenancy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# settings/ is now a package, so we need to go up 3 levels instead of 2
# From: sanfelipe/settings/__init__.py -> sanfelipe/ -> project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment configuration
env = environ.Env()

# Read environment variables from .env file
# Copy .env.example to .env and customize with your actual values
env_file = BASE_DIR / '.env'

try:
    environ.Env.read_env(env_file)
except FileNotFoundError:
    raise FileNotFoundError(
        f'Environment file not found: {env_file}. '
        f'Please copy .env.example to .env and customize it with your actual values.'
    ) from None

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
    # Third-party apps (only in DEBUG mode, not during tests)
    'debug_toolbar' if (DEBUG and not TESTING) else None,
    # Local apps (business data in PostgreSQL, managed externally)
    'tramites',
    'core',
    'buzon',  # Buzón de Trámites - gestiona asignaciones de trámites a analistas
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
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG and not TESTING:
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

# Multi-database configuration:
# - default (SQLite): Django auth, admin, sessions, messages, staticfiles, debug_toolbar
# - business (PostgreSQL): tramites, buzon, core (business data)
#
# The database router (core.db_router.MultiDatabaseRouter) routes queries
# to the appropriate database based on the app label.
#
# Business tables are managed externally (managed=False), so Django won't
# create or modify them - it only reads/writes to existing PostgreSQL tables.

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(env.path('DJANGO_SQLITE_DB_PATH', default=str(BASE_DIR / 'db' / 'db.sqlite3'))),
    },
    'business': env.db(
        'DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/backoffice'
    ),
}

# Route business apps to PostgreSQL
# Use the comprehensive multi-database router
DATABASE_ROUTERS = ['core.db_router.MultiDatabaseRouter']

# =============================================================================
# CACHE
# =============================================================================

# Cache only in production for performance
# Development: No cache (simple, fast development)
# Testing: Dummy cache (no side effects in tests)
# Production: LocMemCache (fast, simple, no external dependencies)
if DEBUG or TESTING:
    # Development and testing - no cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
else:
    # Production - use built-in local memory cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-sanfelipe-cache',
        }
    }

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = []

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
    INTERNAL_IPS = env.list('DJANGO_INTERNAL_IPS', default=['127.0.0.1', '0.0.0.0'])

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: not TESTING,
    }

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = env('DJANGO_LOG_LEVEL', default='INFO' if not DEBUG else 'DEBUG')
DEBUG_SQL = env.bool('DJANGO_DEBUG_SQL', default=False)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG_SQL else 'WARNING',
            'propagate': False,
        },
        'django.utils.autoreload': {
            'handlers': ['console'],
            'level': 'WARNING',  # Reduce autoreload noise in development
            'propagate': False,
        },
        'django.template': {
            'handlers': ['console'],
            'level': 'WARNING',  # Reduce template noise in development
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO',  # Show only important request info
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',  # Only show security warnings
            'propagate': False,
        },
        'sanfelipe': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'tramites': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

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

# Role-based access control groups
ADMINISTRADOR_GROUP_NAME = 'Administrador'
COORDINADOR_GROUP_NAME = 'Coordinador'
ANALISTA_GROUP_NAME = 'Analista'

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = env.list(
    'DJANGO_CSRF_TRUSTED_ORIGINS', default=['http://localhost', 'http://127.0.0.1']
)

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

if not SECRET_KEY and DEBUG:
    import warnings

    warnings.warn('Using insecure SECRET_KEY. Only do this in development!', RuntimeWarning)
