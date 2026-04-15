"""
Logging settings for sanfelipe project.

This module contains all logging-related configuration including:
- Log level configuration
- Console and file handlers
- Rotating file handler with size limits
- Specific logger configurations for Django apps
"""

from pathlib import Path
from environ import Env


def configure_logging(env: Env, BASE_DIR: Path, DEBUG: bool) -> dict:
    """
    Configure and return all logging-related settings.

    Args:
        env: Environ instance for reading environment variables
        BASE_DIR: Base directory path for the project
        DEBUG: Debug mode flag for conditional handler configuration

    Returns:
        Dictionary containing all logging settings
    """
    log_level = env('DJANGO_LOG_LEVEL', default='INFO' if not DEBUG else 'DEBUG')
    debug_sql = env.bool('DJANGO_DEBUG_SQL', default=False)

    # Determine handlers based on DEBUG mode
    django_handlers = ['console', 'file'] if not DEBUG else ['console']
    app_handlers = ['console', 'file'] if not DEBUG else ['console']

    logging_settings = {
        'LOG_LEVEL': log_level,
        'DEBUG_SQL': debug_sql,
        'LOGGING': {
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
                    'maxBytes': 1024 * 1024 * 10,
                    'backupCount': 10,
                    'formatter': 'verbose',
                },
            },
            'root': {
                'handlers': ['console'],
                'level': log_level,
            },
            'loggers': {
                'django': {
                    'handlers': django_handlers,
                    'level': log_level,
                    'propagate': False,
                },
                'django.db.backends': {
                    'handlers': ['console'],
                    'level': 'DEBUG' if debug_sql else 'WARNING',
                    'propagate': False,
                },
                'django.utils.autoreload': {
                    'handlers': ['console'],
                    'level': 'WARNING',
                    'propagate': False,
                },
                'django.template': {
                    'handlers': ['console'],
                    'level': 'WARNING',
                    'propagate': False,
                },
                'django.request': {
                    'handlers': ['console'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'django.security': {
                    'handlers': ['console'],
                    'level': 'WARNING',
                    'propagate': False,
                },
                'sanfelipe': {
                    'handlers': app_handlers,
                    'level': log_level,
                    'propagate': False,
                },
                'tramites': {
                    'handlers': app_handlers,
                    'level': log_level,
                    'propagate': False,
                },
            },
        },
    }

    return logging_settings
