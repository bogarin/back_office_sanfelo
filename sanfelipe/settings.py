"""
Django settings for sanfelipe project.

Microservice for San Felipe Government Backoffice.
Uses Django's built-in auth system with SQLite.
Business data (tramites, catalogos, costos, bitacora) uses PostgreSQL.
"""

from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

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
    )

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env.bool('DJANGO_DEBUG', default=False)

# Intranet deployment - adjust ALLOWED_HOSTS accordingly
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['*'])

# Security settings for intranet (relaxed, no SSL needed)
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = env.bool('DJANGO_SECURE_CONTENT_TYPE_NOSNIFF', default=True)
    SECURE_BROWSER_XSS_FILTER = env.bool('DJANGO_SECURE_BROWSER_XSS_FILTER', default=True)
    X_FRAME_OPTIONS = 'DENY'

    # Intranet - may not have SSL
    SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=False)
    SESSION_COOKIE_SECURE = env.bool('DJANGO_SESSION_COOKIE_SECURE', default=False)
    CSRF_COOKIE_SECURE = env.bool('DJANGO_CSRF_COOKIE_SECURE', default=False)

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
    'django.contrib.admin',
    # Third-party apps
    'debug_toolbar' if DEBUG else None,
    # Local apps (business data in PostgreSQL, managed externally)
    'tramites',
    'catalogos',
    'bitacora',
    'costos',
    'core',
]

# Filter out None values (conditional apps)
INSTALLED_APPS = [app for app in INSTALLED_APPS if app]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG:
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
# - default (SQLite): Django auth, admin, sessions
# - business (PostgreSQL): tramites, catalogos, costos, bitacora (legacy tables)
#
# Business tables are managed externally (managed=False), so Django won't
# create or modify them - it only reads/writes to existing PostgreSQL tables.

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': env.path('DJANGO_SQLITE_DB_PATH', default=BASE_DIR / 'db.sqlite3'),
    },
    'business': env.db(
        'DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/backoffice'
    ),
}

# Route business apps to PostgreSQL
DATABASE_ROUTERS = ['sanfelipe.routers.BusinessDatabaseRouter']

# =============================================================================
# CACHE
# =============================================================================

TESTING = env.bool('TESTING', default=False)

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

# =============================================================================
# SANITY CHECK
# =============================================================================

if not SECRET_KEY and DEBUG:
    import warnings

    warnings.warn('Using insecure SECRET_KEY. Only do this in development!', RuntimeWarning)
