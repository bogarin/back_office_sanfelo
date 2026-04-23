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

# Regex for parsing requisito_id from filename (path traversal defense)
# Example: DAU-260420-AAAE-B-19.pdf → requisito_id=19
# Anchored with ^ and $ to prevent partial matches (security hardening)
FILENAME_REGEX = re.compile(r'^[A-Z]+-\d{6}-[A-Z]{4}-[A-Z]-(?P<requisito_id>\d+)\.pdf$')

# Characters that must NEVER appear in a filename (path traversal vectors)
# Note: '.' is NOT forbidden here (needed for .pdf extension)
FORBIDDEN_FILENAME_CHARS = frozenset('/\\\x00')
