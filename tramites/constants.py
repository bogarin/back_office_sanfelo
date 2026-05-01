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

# Regex for parsing actividad_id from ACT filename (path traversal defense)
# Example: ACT-145-2026-04-30T02-54-49.pdf → actividad_id=145
# Anchored with ^ and $ to prevent partial matches (security hardening)
ACTIVIDAD_FILENAME_REGEX = re.compile(
    r'^ACT-(?P<actividad_id>\d+)-(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})\.pdf$',
)

# Characters that must NEVER appear in a filename (path traversal vectors)
# Note: '.' is NOT forbidden here (needed for .pdf extension)
FORBIDDEN_FILENAME_CHARS = frozenset('/\\\x00')

# Warning threshold for file count
FILE_COUNT_WARNING_THRESHOLD = 100

# Maximum file size allowed for download (50 MB)
MAX_DOWNLOAD_FILE_SIZE_BYTES = 50 * 1024 * 1024
