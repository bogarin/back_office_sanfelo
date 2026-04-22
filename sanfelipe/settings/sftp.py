"""
SFTP Storage settings for sanfelipe project.

This module contains all SFTP-related configuration including:
- Connection settings (host, port, username, password)
- Remote directory paths for PDF storage
- Django-storages SFTP backend configuration
"""

from environ import Env


def configure_sftp(env: Env) -> dict:
    """
    Configure and return all SFTP storage-related settings.

    These settings are used by django-storages[sftp] backend to access
    PDF files stored on a remote SFTP server.

    Args:
        env: Environ instance for reading environment variables

    Returns:
        Dictionary containing all SFTP settings
    """
    sftp_settings = {
        # =============================================================================
        # SFTP CONNECTION SETTINGS
        # =============================================================================
        # Hostname or IP address of SFTP server
        'SFTP_HOST': env('SFTP_HOST', default=''),
        # Port number for SFTP connection (default: 22)
        'SFTP_PORT': env.int('SFTP_PORT', default=22),
        # Username for SFTP authentication
        'SFTP_USERNAME': env('SFTP_USERNAME', default=''),
        # Password for SFTP authentication
        'SFTP_PASSWORD': env('SFTP_PASSWORD', default=''),
        # Path to SSH private key file (alternative to password authentication)
        # Leave empty if using password authentication
        'SFTP_PRIVATE_KEY_PATH': env('SFTP_PRIVATE_KEY_PATH', default=''),
        # Passphrase for SSH private key (only used with SFTP_PRIVATE_KEY_PATH)
        # Leave empty if private key has no passphrase
        'SFTP_PRIVATE_KEY_PASSPHRASE': env('SFTP_PRIVATE_KEY_PASSPHRASE', default=''),
        # Timeout en segundos para operaciones SFTP
        # None = default de paramiko (aprox. 30 segundos)
        'SFTP_TIMEOUT': env.int('SFTP_TIMEOUT', default=None),
        # SSH host key for server verification (MITM protection)
        # Format: "ssh-rsa AAAAB3Nza..." or "ssh-ed25519 AAAA..."
        # Obtain with: ssh-keyscan -t rsa,ed25519 <host>
        # Required in production (DEBUG=False). Optional in development.
        'SFTP_HOST_KEY': env('SFTP_HOST_KEY', default=''),
        # =============================================================================
        # REMOTE DIRECTORY PATHS
        # =============================================================================
        # Base directory where tramites PDFs are stored on SFTP server
        # Leave empty if not using SFTP storage
        'SFTP_BASE_DIR': env('SFTP_BASE_DIR', default=''),
        # Subdirectory for uploaded/received PDF files
        'SFTP_PDF_DIR': env('SFTP_PDF_DIR', default='pdfs'),
    }

    # DO NOT overwrite STORAGES - return separate config for merge
    sftp_settings['SFTP_STORAGE_CONFIG'] = {
        'BACKEND': 'storages.backends.sftp.SFTPStorage',
        'OPTIONS': {
            'host': lambda: env('SFTP_HOST'),
            'port': env.int('SFTP_PORT', default=22),
            'username': lambda: env('SFTP_USERNAME'),
            'password': lambda: env('SFTP_PASSWORD'),
            'private_key': lambda: env('SFTP_PRIVATE_KEY_PATH', default=None),
        },
    }

    return sftp_settings
