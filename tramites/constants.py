"""Shared constants for the tramites module.

Public constants used across services, models, and management commands
to ensure consistent validation without circular imports.
"""

import re

# Regex for validating folio format (path traversal defense)
# Example: DAU-260420-AAAE-B
FOLIO_REGEX = re.compile(r'^[A-Z]+-\d{6}-[A-Z]{4}-[A-Z]$')

# Characters that must NEVER appear in a folio (path traversal vectors)
FORBIDDEN_FOLIO_CHARS = frozenset('/\\\x00.')
