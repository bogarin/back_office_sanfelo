"""
Security settings for sanfelipe project.

This module contains all security-related configuration including:
- Core security settings (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
- Production security headers
- Content Security Policy (CSP) configuration
"""

import math
from collections import Counter

from django.utils.csp import CSP
from environ import Env


def configure_security(env: Env) -> dict:
    """
    Configure and return all security-related settings.

    Args:
        env: Environ instance for reading environment variables

    Returns:
        Dictionary containing all security settings
    """
    security_settings = {
        # =============================================================================
        # CORE SECURITY SETTINGS
        # =============================================================================
        'SECRET_KEY': env('DJANGO_SECRET_KEY'),
        'DEBUG': env.bool('DJANGO_DEBUG', default=False),
        'TESTING': env.bool('TESTING', default=False),
        'ALLOWED_HOSTS': env.list('DJANGO_ALLOWED_HOSTS', default=[]),
        # =============================================================================
        # PRODUCTION SECURITY HEADERS
        # =============================================================================
        # Security settings for intranet (relaxed, no SSL needed)
        # In DEBUG mode, use 'SAMEORIGIN' instead of None to allow dev tools
        'SECURE_CONTENT_TYPE_NOSNIFF': True,
        'SECURE_BROWSER_XSS_FILTER': True,
        'X_FRAME_OPTIONS': 'SAMEORIGIN',
        'SECURE_SSL_REDIRECT': False,
        'SESSION_COOKIE_SECURE': False,
        'CSRF_COOKIE_SECURE': False,
    }

    # Production-only security settings
    if not security_settings['DEBUG']:
        security_settings.update(
            {
                'X_FRAME_OPTIONS': 'DENY',
                'SECURE_SSL_REDIRECT': env.bool('DJANGO_SECURE_SSL_REDIRECT', default=False),
                'SESSION_COOKIE_SECURE': env.bool('DJANGO_SESSION_COOKIE_SECURE', default=False),
                'CSRF_COOKIE_SECURE': env.bool('DJANGO_CSRF_COOKIE_SECURE', default=False),
            }
        )

    # =============================================================================
    # CONTENT SECURITY POLICY (CSP) - Django 6.0 Native Support
    # =============================================================================

    # CSP is a powerful security feature that helps prevent XSS attacks and other
    # content injection attacks by defining which content sources are trusted.
    #
    # Security Benefits:
    # - Prevents execution of unauthorized scripts (XSS mitigation)
    # - Controls which external resources can be loaded (scripts, styles, images, fonts)
    # - Blocks unauthorized content injection
    # - Provides violation reporting for monitoring and debugging
    #
    # For initial deployment, use REPORT_ONLY mode to identify any issues without
    # breaking functionality. After confirming everything works, switch to enforced mode.
    csp_report_mode = env.bool('DJANGO_CSP_REPORT_ONLY', default=False)

    # Define common CSP policy (used in both report-only and enforced modes)
    csp_policy = {
        # Default fallback for all content types
        # 'self' allows resources from the same origin only
        'default-src': [CSP.SELF],
        # Script sources: Only allow scripts from same origin with nonce support
        # NONCE allows inline scripts with a valid nonce attribute
        # This is more secure than 'unsafe-inline' as it explicitly whitelists scripts
        'script-src': [CSP.NONCE, CSP.SELF, 'strict-dynamic'],
        # Style sources: Allow styles from same origin and inline styles
        # Note: Django admin uses some inline styles, so UNSAFE_INLINE is needed
        # For better security, consider using NONCE for inline styles
        'style-src': [CSP.SELF, CSP.UNSAFE_INLINE, 'https://fonts.googleapis.com'],
        # Image sources: Allow images from same origin and data: URIs
        # data: URIs are commonly used for base64-encoded images in Django admin
        'img-src': [CSP.SELF, 'data:'],
        # Font sources: Only allow fonts from same origin
        # Django admin loads fonts from static files
        'font-src': [CSP.SELF, 'https://fonts.gstatic.com'],
        # Connect sources: Restrict AJAX/Fetch requests to same origin
        'connect-src': [CSP.SELF],
        # Object sources: Block all plugins (Flash, Java, etc.)
        # This prevents plugin-based XSS attacks
        'object-src': [CSP.NONE],
        # Media sources: Restrict audio/video to same origin
        'media-src': [CSP.SELF],
        # Frame sources: Block all iframes unless explicitly needed
        # Prevents clickjacking attacks
        'frame-src': [CSP.NONE],
        # Frame ancestors: Prevent page from being embedded in frames
        # Works with X-Frame-Options middleware for clickjacking protection
        'frame-ancestors': [CSP.SELF],
        # Base URI: Restrict base tag to same origin
        'base-uri': [CSP.SELF],
        # Form action: Restrict form submissions to same origin
        'form-action': [CSP.SELF],
        # Manifest: Restrict app manifests to same origin
        'manifest-src': [CSP.SELF],
        # Report violations to this endpoint (optional, for monitoring)
        # Uncomment and configure if you want to collect CSP violation reports
        # "report-uri": ["/csp-violation-report/"],
        # "report-to": ["csp-endpoint"],
    }

    # Apply CSP based on report mode
    if csp_report_mode:
        # Report-only mode: Monitor violations without blocking content
        # This is recommended for initial deployment to identify any issues
        security_settings['SECURE_CSP_REPORT_ONLY'] = csp_policy
        security_settings['SECURE_CSP'] = None
    else:
        # Enforced mode: Actively block non-compliant content
        # Use this after confirming no issues in report-only mode
        security_settings['SECURE_CSP'] = csp_policy
        security_settings['SECURE_CSP_REPORT_ONLY'] = None

    # Note: The resulting CSP header will look like:
    # Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-SECRET'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; media-src 'self'; frame-src 'none'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'; manifest-src 'self'

    return security_settings


# =============================================================================
# SECRET KEY VALIDATION
# =============================================================================

FORBIDDEN_PATTERNS = (
    'django-insecure',
    'change',
    'changeme',
    'secret',
    'password',
    'example',
    'test',
    'dev-key',
)


def validate_secret_key(key: str) -> tuple[bool, str]:
    """
    Validate DJANGO_SECRET_KEY entropy and security.

    This function performs multiple security checks:
    - Minimum length (32 characters)
    - Forbidden patterns (e.g., 'django-insecure', 'change-me')
    - Character diversity (at least 10 unique characters)
    - Shannon entropy (minimum 3.0 bits per character)

    Args:
        key: The DJANGO_SECRET_KEY value to validate

    Returns:
        Tuple of (is_valid, reason):
            - is_valid: True if the key passes all checks
            - reason: Empty string if valid, otherwise error message explaining why

    Note:
        Shannon entropy measures the randomness/unpredictability of data.
        For a truly random 50-character key with 64 possible characters:
        - Expected entropy: ~5.9 bits per character
        - A repetitive key like 'aaaaaaaa...' has ~0.0 bits per character
        - A key like 'abcabcabc...' has ~1.6 bits per character
        - Our threshold of 3.0 rejects obviously weak keys while allowing
          slight repetition in human-generated keys
    """
    if not key:
        return False, 'DJANGO_SECRET_KEY is empty or not set.'

    # Check minimum length (Django generates 50 by default)
    if len(key) < 32:
        return False, f'DJANGO_SECRET_KEY is too short ({len(key)} chars, minimum 32).'

    # Check for forbidden patterns
    lower = key.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in lower:
            return False, f'DJANGO_SECRET_KEY contains forbidden pattern: "{pattern}".'

    # Check character diversity (avoid repetitive keys)
    char_counts = Counter(key)
    unique_chars = len(char_counts)
    if unique_chars < 10:
        return False, f'DJANGO_SECRET_KEY has only {unique_chars} unique characters (minimum 10).'

    # Calculate Shannon entropy
    # Higher entropy = more randomness = harder to brute force
    total = len(key)
    entropy = -sum((count / total) * math.log2(count / total) for count in char_counts.values())

    if entropy < 3.0:
        return False, f'DJANGO_SECRET_KEY has low entropy ({entropy:.2f} bits/char, minimum 3.0).'

    return True, ''
