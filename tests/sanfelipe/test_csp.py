"""Tests for Content Security Policy configuration.

Validates that CSP is properly configured to protect against XSS,
plugin injection, and iframe embedding attacks.
"""

import pytest
from django.conf import settings
from django.utils.csp import CSP  # ty: ignore[unresolved-import]

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def csp_policy():
    """Return the active CSP policy dict, failing if not configured."""
    assert hasattr(settings, 'SECURE_CSP'), 'SECURE_CSP must be defined in settings'
    policy = settings.SECURE_CSP
    assert policy is not None, 'SECURE_CSP must not be None'
    return policy


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_csp_constants_defined():
    """CSP constants (SELF, NONE, NONCE, UNSAFE_INLINE) must exist."""
    assert hasattr(CSP, 'SELF')
    assert hasattr(CSP, 'NONE')
    assert hasattr(CSP, 'NONCE')
    assert hasattr(CSP, 'UNSAFE_INLINE')


def test_csp_has_required_directives(csp_policy):
    """CSP policy must include all required security directives."""
    required = ('default-src', 'script-src', 'style-src', 'object-src', 'frame-src')
    for directive in required:
        assert directive in csp_policy, f'CSP missing required directive: {directive}'


def test_csp_script_src_uses_self(csp_policy):
    """CSP script-src must include 'self' for same-origin scripts."""
    assert CSP.SELF in csp_policy['script-src']


def test_csp_blocks_plugins(csp_policy):
    """CSP object-src must block all plugins (None)."""
    object_sources = csp_policy.get('object-src', [])
    assert CSP.NONE in object_sources or "'none'" in object_sources


def test_csp_blocks_frames(csp_policy):
    """CSP frame-src must block all iframes (None)."""
    frame_sources = csp_policy.get('frame-src', [])
    assert CSP.NONE in frame_sources or "'none'" in frame_sources
