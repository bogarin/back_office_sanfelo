"""
Tests for Content Security Policy configuration.

This module contains tests for:
- CSP constants
- CSP configuration structure
- External script blocking
- Plugin blocking
"""

from django.conf import settings
from django.test import TestCase
from django.utils.csp import CSP


class TestContentSecurityPolicy(TestCase):
    """Test suite for CSP security configuration."""

    def test_csp_constants_defined(self) -> None:
        """Test that CSP constants are defined in settings."""
        self.assertTrue(hasattr(CSP, 'SELF'))
        self.assertTrue(hasattr(CSP, 'NONE'))
        self.assertTrue(hasattr(CSP, 'NONCE'))
        self.assertTrue(hasattr(CSP, 'UNSAFE_INLINE'))

    def test_csp_configuration_structure(self) -> None:
        """Test that CSP configuration is properly structured."""
        # Check that CSP settings exist
        self.assertTrue(
            hasattr(settings, 'SECURE_CSP') or hasattr(settings, 'SECURE_CSP_REPORT_ONLY')
        )

        # If SECURE_CSP is not None, verify its structure
        if hasattr(settings, 'SECURE_CSP') and settings.SECURE_CSP is not None:
            csp = settings.SECURE_CSP
            self.assertIn('default-src', csp)
            self.assertIn('script-src', csp)
            self.assertIn('style-src', csp)
            self.assertIn('object-src', csp)
            self.assertIn('frame-src', csp)

    def test_csp_blocks_external_scripts(self) -> None:
        """Test that CSP configuration blocks external scripts."""
        if hasattr(settings, 'SECURE_CSP') and settings.SECURE_CSP is not None:
            csp = settings.SECURE_CSP
            script_sources = csp.get('script-src', [])

            # Should include SELF and NONCE (not 'unsafe-inline')
            self.assertTrue(CSP.SELF in script_sources or 'self' in script_sources)
            # NONCE is included as a CSP directive object
            self.assertTrue(CSP.NONCE in script_sources)

    def test_csp_blocks_plugins(self) -> None:
        """Test that CSP configuration blocks all plugins."""
        if hasattr(settings, 'SECURE_CSP') and settings.SECURE_CSP is not None:
            csp = settings.SECURE_CSP
            object_sources = csp.get('object-src', [])

            # Should block all plugins
            self.assertTrue(CSP.NONE in object_sources or "'none'" in object_sources)

    def test_csp_blocks_frames(self) -> None:
        """Test that CSP configuration blocks iframes."""
        if hasattr(settings, 'SECURE_CSP') and settings.SECURE_CSP is not None:
            csp = settings.SECURE_CSP
            frame_sources = csp.get('frame-src', [])

            # Should block iframes
            self.assertTrue(CSP.NONE in frame_sources or "'none'" in frame_sources)
