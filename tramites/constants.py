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


# =============================================================================
# Estatus range constants
# =============================================================================


ESTATUS_INICIO_RANGE = range(100, 200)
ESTATUS_PROCESO_RANGE = range(200, 300)
ESTATUS_FINALIZADO_RANGE = range(300, 400)

ESTATUS_PROCESO_LOWER = 201
ESTATUS_PROCESO_UPPER = 301
ESTATUS_FINALIZADO_LOWER = 301

# Specific status IDs (used in managers and queries)
ESTATUS_EN_DILIGENCIA = 205
ESTATUS_PRESENTADO = 201

_STATUS_GROUPS = {
    1: 'inicio',
    2: 'proceso',
    3: 'finalizado',
}


def get_status_group(estatus_id: int | None) -> str:
    """Return the status group name for a given estatus ID.

    Maps estatus IDs to their family:
      - 100-199 → 'inicio'
      - 200-299 → 'proceso'
      - 300-399 → 'finalizado'
      - anything else → 'otro'
    """
    if estatus_id is None:
        return 'otro'
    return _STATUS_GROUPS.get(estatus_id // 100) or 'otro'


def get_status_badge_class(estatus_id: int | None) -> str:
    """Return the CSS badge class for a given estatus ID.

    Format: '{group}-{estatus_id}' (e.g. 'proceso-202').
    Returns 'otro' for None or out-of-range values.
    """
    if estatus_id is None:
        return 'otro'
    if estatus_id in ESTATUS_INICIO_RANGE:
        return f'inicio-{estatus_id}'
    if estatus_id in ESTATUS_PROCESO_RANGE:
        return f'proceso-{estatus_id}'
    if estatus_id in ESTATUS_FINALIZADO_RANGE:
        return f'finalizado-{estatus_id}'
    return 'otro'
