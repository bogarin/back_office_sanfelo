"""
Django settings for sanfelipe project.

Microservice for San Felipe Government Backoffice.
Uses Keycloak for authentication via django-allauth (OpenID Connect).
Database schema is managed externally (no Django migrations).
"""

from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment configuration
env = environ.Env()
ENVIRONMENT = env("ENVIRONMENT", default="development")
env_file = BASE_DIR / f".env.{ENVIRONMENT}"

try:
    environ.Env.read_env(env_file)
except FileNotFoundError:
    raise FileNotFoundError(
        f"Environment file not found: {env_file}. "
        f"Please create .env.{ENVIRONMENT} or check ENVIRONMENT variable."
    )

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)

# Intranet deployment - adjust ALLOWED_HOSTS accordingly
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

# Security settings for intranet (relaxed, no SSL needed)
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
        "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
    )
    SECURE_BROWSER_XSS_FILTER = env.bool(
        "DJANGO_SECURE_BROWSER_XSS_FILTER", default=True
    )
    X_FRAME_OPTIONS = "DENY"

    # Intranet - may not have SSL
    SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
    SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=False)
    CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=False)

# =============================================================================
# DJANGO-ALLAUTH + KEYCLOAK (OpenID Connect) SETTINGS
# =============================================================================

# Keycloak OpenID Connect provider configuration
# Using OIDC provider with Keycloak as per django-allauth 65.x docs
SOCIALACCOUNT_PROVIDERS = {
    "openid_connect": {
        "APPS": [
            {
                "provider_id": "keycloak",
                "name": "Keycloak",
                "client_id": env("KEYCLOAK_CLIENT_ID"),
                "secret": env("KEYCLOAK_CLIENT_SECRET"),
                "settings": {
                    "server_url": env("KEYCLOAK_SERVER_URL", default=""),
                },
            }
        ]
    }
}

# django-allauth settings
AUTHENTICATION_BACKENDS = (
    # django-allauth backends
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "allauth.socialaccount.auth_backends.OpenIDConnectBackend",
)

# IMPORTANT: We're NOT managing users locally in Django
# All user data comes from Keycloak via OIDC
SOCIALACCOUNT_AUTO_SIGNUP = False  # Disable auto sign-up
ACCOUNT_ADAPTER = "core.account_adapter.CustomAccountAdapter"

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    # Django core apps
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Django Admin
    "django.contrib.admin",
    # Third-party apps
    "debug_toolbar" if DEBUG else None,
    # django-allauth - core apps
    "django.contrib.sites",
    "django.contrib.auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.openid_connect",
    # Local apps
    "tramites",
    "catalogos",
    "bitacora",
    "costos",
    "core",
]

# Filter out None values (conditional apps)
INSTALLED_APPS = [app for app in INSTALLED_APPS if app]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # django-allauth middleware
]

if DEBUG:
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "sanfelipe.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "allauth.socialaccount.context_processors.socialaccount",  # Keycloak user info
            ],
        },
    },
]

WSGI_APPLICATION = "sanfelipe.wsgi.application"
ASGI_APPLICATION = "sanfelipe.asgi.application"

# =============================================================================
# DATABASE
# =============================================================================

DATABASES = {
    "default": env.db(default="sqlite:///db.sqlite3"),
}

# =============================================================================
# CACHE
# =============================================================================

TESTING = env.bool("TESTING", default=False)

if TESTING:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        }
    }

# =============================================================================
# PASSWORD VALIDATION (Not used with Keycloak, but kept for compatibility)
# =============================================================================

AUTH_PASSWORD_VALIDATORS = []

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "es-ar"  # Spanish - Argentina (San Felipe)
TIME_ZONE = "America/Argentina/San_Luis"  # San Felipe timezone

USE_I18N = True
USE_L10N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# =============================================================================
# MEDIA FILES
# =============================================================================

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# DEBUG TOOLBAR
# =============================================================================

if DEBUG:
    INTERNAL_IPS = env.list("DJANGO_INTERNAL_IPS", default=["127.0.0.1", "0.0.0.0"])

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: not TESTING,
    }

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO" if not DEBUG else "DEBUG")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"] if not DEBUG else ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "sanfelipe": {
            "handlers": ["console", "file"] if not DEBUG else ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "tramites": {
            "handlers": ["console", "file"] if not DEBUG else ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

# =============================================================================
# AUTHENTICATION (Keycloak via django-allauth OIDC)
# =============================================================================

# django-allauth settings
ACCOUNT_EMAIL_REQUIRED = False  # Email not required, comes from Keycloak
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_UNIQUE_EMAIL = False  # Allow duplicate emails (Keycloak uniqueness)

# Custom adapter to save Keycloak user info to our models
ACCOUNT_ADAPTER = "core.account_adapter.CustomAccountAdapter"
SOCIALACCOUNT_ADAPTER = "core.account_adapter.CustomSocialAccountAdapter"

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = env.list(
    "DJANGO_CSRF_TRUSTED_ORIGINS", default=["http://localhost", "http://127.0.0.1"]
)

# =============================================================================
# SESSION SETTINGS
# =============================================================================

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_COOKIE_AGE = env.int("DJANGO_SESSION_COOKIE_AGE", default=3600)  # 1 hour
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# =============================================================================
# EMAIL SETTINGS (for notifications)
# =============================================================================

EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("DJANGO_EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("DJANGO_EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("DJANGO_EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL", default="noreply@sanfelipe.gob.ar"
)

# =============================================================================
# TRAMITES SETTINGS
# =============================================================================

TRAMITE_ESTADOS = (
    ("borrador", "Borrador"),
    ("pendiente", "Pendiente"),
    ("en_proceso", "En Proceso"),
    ("aprobado", "Aprobado"),
    ("rechazado", "Rechazado"),
    ("completado", "Completado"),
)

TRAMITE_PRIORIDADES = (
    ("baja", "Baja"),
    ("media", "Media"),
    ("alta", "Alta"),
    ("urgente", "Urgente"),
)

# Pagination
DEFAULT_PAGE_SIZE = env.int("DJANGO_DEFAULT_PAGE_SIZE", default=25)

# =============================================================================
# MIGRATIONS DISABLED
# =============================================================================

# Migrations are handled externally via SQL scripts from another repository
# This setting prevents Django from trying to run migrations
MIGRATION_MODULES = {
    "contenttypes": None,
    "allauth": None,
    "allauth.account": None,
    "allauth.socialaccount": None,
    "allauth.socialaccount.providers.openid_connect": None,
    "tramites": None,
    "catalogos": None,
    "bitacora": None,
    "costos": None,
    "core": None,
}

# =============================================================================
# SANITY CHECK
# =============================================================================

if not SECRET_KEY and DEBUG:
    import warnings

    warnings.warn(
        "Using insecure SECRET_KEY. Only do this in development!", RuntimeWarning
    )
