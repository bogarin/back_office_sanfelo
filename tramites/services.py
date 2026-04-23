"""
Servicios SFTP para el módulo de trámites.

Conexión, listing de archivos y validación de folios.
"""

import base64
import logging
import re
import threading
from pathlib import Path

import paramiko
from django.conf import settings

from .constants import (
    FOLIO_REGEX,
    FORBIDDEN_FOLIO_CHARS,
    FILENAME_REGEX,
    FORBIDDEN_FILENAME_CHARS,
)
from .exceptions import SFTPConnectionError
from .models import Requisito, RequisitoFile

logger = logging.getLogger(__name__)

# =============================================================================
# SFTP SERVICE
# =============================================================================

# Thread-local storage for SFTP connection
_local = threading.local()

# Warning threshold for file count
FILE_COUNT_WARNING_THRESHOLD = 100

# Maximum file size allowed for download (50 MB)
MAX_DOWNLOAD_FILE_SIZE_BYTES = 50 * 1024 * 1024


# =============================================================================
# SFTP Key Loading
# =============================================================================

# SSH key types to try, in order of preference
_SSH_KEY_TYPES: list[tuple[type[paramiko.PKey], str]] = [
    (paramiko.RSAKey, 'RSA'),
    (paramiko.Ed25519Key, 'Ed25519'),
    (paramiko.ECDSAKey, 'ECDSA'),
]


def _try_load_key(
    key_path_str: str,
    passphrase: str | None = None,
) -> tuple[paramiko.PKey, str] | None:
    """Try loading an SSH key by probing each supported type.

    Args:
        key_path_str: Path to the private key file.
        passphrase: Optional passphrase for encrypted keys.

    Returns:
        ``(key, label)`` on success, ``None`` if no type matched.
    """
    for key_class, label in _SSH_KEY_TYPES:
        try:
            match passphrase:
                case str():
                    key = key_class.from_private_key_file(key_path_str, password=passphrase)
                case _:
                    key = key_class.from_private_key_file(key_path_str)
            return key, (label if passphrase is None else f'{label} (passphrase)')
        except (paramiko.SSHException, OSError):
            continue
    return None


# =============================================================================
# Folio Validation
# =============================================================================


def _validate_folio(folio: str) -> str:
    """Validate folio format to prevent SFTP path traversal.

    Args:
        folio: The folio string to validate.

    Returns:
        The validated folio string.

    Raises:
        SFTPConnectionError: If the folio contains forbidden characters
            or doesn't match the expected format.
    """
    if not folio:
        raise SFTPConnectionError('Folio no puede estar vacío.')

    # Reject path traversal characters FIRST (defense-in-depth)
    if any(c in FORBIDDEN_FOLIO_CHARS for c in folio):
        logger.error('Seguridad: folio rechazado por caracteres no permitidos: %r', folio)
        raise SFTPConnectionError(
            'Folio contiene caracteres no permitidos. Verifica que el folio sea correcto.'
        )

    # Enforce expected format
    if not FOLIO_REGEX.match(folio):
        logger.error('Seguridad: folio no coincide formato esperado: %r', folio)
        raise SFTPConnectionError('Formato de folio inválido. Verifica que el folio sea correcto.')

    return folio


def _validate_filename(filename: str) -> str:
    """Validate PDF filename format to prevent SFTP path traversal.

    Args:
        filename: The filename string to validate.

    Returns:
        The validated filename string.

    Raises:
        SFTPConnectionError: If filename contains forbidden characters
            or doesn't match the expected format.
    """
    if not filename:
        raise SFTPConnectionError('Nombre de archivo no puede estar vacío.')

    # Reject path traversal characters FIRST (defense-in-depth)
    # Note: Use FORBIDDEN_FILENAME_CHARS (without '.') for filenames
    if any(c in FORBIDDEN_FILENAME_CHARS for c in filename):
        logger.error('Seguridad: archivo rechazado por caracteres no permitidos: %r', filename)
        raise SFTPConnectionError(
            'El nombre de archivo contiene caracteres no permitidos. '
            'Verifica que el archivo sea correcto.'
        )

    # Enforce expected format (anchored regex)
    if not FILENAME_REGEX.match(filename):
        logger.error('Seguridad: archivo no coincide formato esperado: %r', filename)
        raise SFTPConnectionError(
            'Formato de nombre de archivo inválido. Verifica que el archivo sea correcto.'
        )

    return filename


# =============================================================================
# SFTPService
# =============================================================================


class SFTPService:
    """Servicio para interactuar con servidor SFTP con caching de conexión."""

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def get_sftp_client(self) -> paramiko.SSHClient:
        """Return a connected SFTP client for the current thread.

        Reuses the same client within a thread until
        :meth:`close_connection` is called.  Stale connections
        (e.g. after a server restart) are detected and replaced
        automatically.
        """
        if hasattr(_local, 'sftp_client'):
            client = _local.sftp_client
            transport = client.get_transport()
            if transport is not None and transport.is_active():
                return client
            # Dead connection — close and reconnect
            self._safe_close(client)
            del _local.sftp_client

        client = self._create_sftp_connection()
        _local.sftp_client = client
        return client

    @staticmethod
    def _safe_close(client: paramiko.SSHClient) -> None:
        """Close an SSH client, logging any failure.

        Only catches socket/SSH-level errors — never suppresses
        ``MemoryError``, ``KeyboardInterrupt`` or ``SystemExit``.
        """
        try:
            client.close()
        except (paramiko.SSHException, OSError, EOFError):
            logger.debug('Error closing SFTP client (expected during cleanup)', exc_info=True)

    def close_connection(self) -> None:
        """Close the SFTP connection for the current thread (if any).

        Silently ignores socket-level errors during close to avoid
        suppressing the original exception in ``finally`` blocks.
        """
        if hasattr(_local, 'sftp_client'):
            self._safe_close(_local.sftp_client)
            del _local.sftp_client

    def _configure_host_key_policy(self, client: paramiko.SSHClient) -> None:
        """Set the SSH host key verification policy.

        Graduated approach:

        - If ``SFTP_HOST_KEY`` is configured → use ``RejectPolicy``
          (strict verification, recommended for production).
        - If ``settings.DEBUG`` is ``True`` and no key → use ``WarningPolicy``
          (logs a warning but allows connection).
        - If ``settings.DEBUG`` is ``False`` and no key → raise
          ``SFTPConnectionError`` (refuse unverified connections in prod).

        Args:
            client: The :class:`paramiko.SSHClient` to configure.
        """
        host_key_str = getattr(settings, 'SFTP_HOST_KEY', '')

        if host_key_str:
            self._load_known_host_key(client, host_key_str)
            return

        # No host key configured
        if settings.DEBUG:
            logger.warning(
                'SFTP_HOST_KEY no configurado. Usando WarningPolicy '
                '(acepta cualquier host key). CONFIGURA SFTP_HOST_KEY '
                'para producción. Ver: docs/sftp-host-key.md'
            )
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
        else:
            raise SFTPConnectionError(
                'SFTP_HOST_KEY no está configurado. '
                'La verificación de host key es obligatoria en producción. '
                'Obtén la llave con: ssh-keyscan -t rsa,ed25519 <host>'
            )

    @staticmethod
    def _load_known_host_key(client: paramiko.SSHClient, host_key_str: str) -> None:
        """Parse and load a known host key for strict verification.

        Args:
            client: The SSH client to configure.
            host_key_str: Host key in OpenSSH format
                (e.g. ``"ssh-rsa AAAAB3Nza..."``).
        """
        host = settings.SFTP_HOST
        port = settings.SFTP_PORT

        parts = host_key_str.strip().split(None, 1)
        if len(parts) != 2:
            logger.error('SFTP_HOST_KEY formato inválido (esperado: "ssh-rsa AAAA...")')
            raise SFTPConnectionError(
                'SFTP_HOST_KEY tiene formato inválido. '
                'Formato esperado: "ssh-rsa AAAA..." o "ssh-ed25519 AAAA..."'
            )

        key_type_raw, key_data = parts

        # Map short aliases to SSH-standard names for paramiko's host keys dict
        _KEY_TYPE_NORMALIZE: dict[str, str] = {
            'rsa': 'ssh-rsa',
            'ed25519': 'ssh-ed25519',
            'ecdsa': 'ecdsa-sha2-nistp256',
        }
        key_type = _KEY_TYPE_NORMALIZE.get(key_type_raw, key_type_raw)

        host_key: paramiko.PKey | None = None
        try:
            match key_type_raw:
                case 'ssh-rsa' | 'rsa':
                    host_key = paramiko.RSAKey(data=base64.b64decode(key_data))
                case 'ssh-ed25519' | 'ed25519':
                    host_key = paramiko.Ed25519Key(data=base64.b64decode(key_data))
                case 'ecdsa-sha2-nistp256' | 'ecdsa':
                    host_key = paramiko.ECDSAKey(data=base64.b64decode(key_data))
        except Exception as exc:
            logger.error('SFTP_HOST_KEY parse error: %s', exc)
            raise SFTPConnectionError(
                'SFTP_HOST_KEY contiene datos inválidos. '
                'Verifica que el formato sea correcto (ej: "ssh-rsa AAAA...")'
            ) from exc

        if host_key is None:
            logger.error('SFTP_HOST_KEY tipo no soportado: %s', key_type_raw)
            raise SFTPConnectionError(
                f'Tipo de host key no soportado: {key_type_raw}. '
                'Tipos soportados: ssh-rsa, ssh-ed25519, ecdsa-sha2-nistp256'
            )

        client.get_host_keys().add(
            f'[{host}]:{port}' if port != 22 else host,
            key_type,
            host_key,
        )
        client.set_missing_host_key_policy(paramiko.RejectPolicy())

    def _create_sftp_connection(self) -> paramiko.SSHClient:
        """Create and return a connected :class:`paramiko.SSHClient`.

        Authentication priority: private key > password.

        Raises:
            SFTPConnectionError: On authentication or connection failure.
        """
        host = settings.SFTP_HOST
        port = settings.SFTP_PORT
        username = settings.SFTP_USERNAME
        password = settings.SFTP_PASSWORD
        key_passphrase = settings.SFTP_PRIVATE_KEY_PASSPHRASE
        timeout = settings.SFTP_TIMEOUT

        # --- SSH key auth ---
        if settings.SFTP_PRIVATE_KEY_PATH:
            key_path = Path(settings.SFTP_PRIVATE_KEY_PATH).expanduser()

            # Fail fast with a clear message if the key file doesn't exist
            if not key_path.exists():
                raise SFTPConnectionError(f'Archivo de llave privada no encontrado: {key_path}')

            # Reject relative paths BEFORE resolve (resolve always produces absolute)
            if not key_path.is_absolute():
                logger.error('SFTP_PRIVATE_KEY_PATH no es absoluta: %s', key_path)
                raise SFTPConnectionError('La ruta de la llave privada debe ser absoluta.')

            # Canonicalize .. and symlinks, then check forbidden dirs
            key_path = key_path.resolve()
            key_path_str = str(key_path)

            if len(key_path.parts) > 1 and key_path.parts[1] in ('etc', 'root', 'sys'):
                logger.error('SFTP_PRIVATE_KEY_PATH en ubicación no permitida: %s', key_path)
                raise SFTPConnectionError(
                    'La ruta de la llave privada no está en una ubicación permitida.'
                )

            # Try without passphrase first, then with (only if passphrase configured)
            key_result = _try_load_key(key_path_str)
            if key_result is None and key_passphrase:
                key_result = _try_load_key(key_path_str, key_passphrase)
            if key_result is None:
                raise SFTPConnectionError(
                    'No se pudo cargar la llave privada SSH. '
                    'Verifica el tipo (RSA, Ed25519, ECDSA) y passphrase.'
                )

            key, _auth_label = key_result
            client = paramiko.SSHClient()
            self._configure_host_key_policy(client)
            try:
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    pkey=key,
                    timeout=timeout,
                )
            except paramiko.AuthenticationException as exc:
                raise SFTPConnectionError(
                    'Autenticación fallida. Verifica la llave privada SSH.'
                ) from exc
            except OSError as exc:
                logger.error('Error de red al conectar por llave SSH: %s', exc)
                raise SFTPConnectionError(
                    'No se pudo conectar al servidor SFTP. '
                    'Verifica la dirección y la conexión de red.'
                ) from exc
            except paramiko.SSHException as exc:
                raise SFTPConnectionError(
                    'Error al conectar al servidor SFTP. Intenta nuevamente más tarde.'
                ) from exc
            return client

        # --- Password auth ---
        if password:
            client = paramiko.SSHClient()
            self._configure_host_key_policy(client)
            try:
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=timeout,
                )
            except paramiko.AuthenticationException as exc:
                raise SFTPConnectionError(
                    'Autenticación fallida. Verifica usuario y contraseña.'
                ) from exc
            except OSError as exc:
                logger.error('Error de red al conectar por password: %s', exc)
                raise SFTPConnectionError(
                    'No se pudo conectar al servidor SFTP. '
                    'Verifica la dirección y la conexión de red.'
                ) from exc
            except paramiko.SSHException as exc:
                raise SFTPConnectionError(
                    'Error al conectar al servidor SFTP. Intenta nuevamente más tarde.'
                ) from exc
            return client

        raise SFTPConnectionError(
            'No hay método de autenticación disponible (password o llave privada)'
        )

    # ------------------------------------------------------------------
    # Cached catalog lookups
    # ------------------------------------------------------------------

    def _get_cached_requisitos(self) -> dict[int, Requisito]:
        """Return ``{pk: Requisito}`` dict from Django cache."""
        return Requisito.objects.all_cached_as_dict()

    # ------------------------------------------------------------------
    # File listing
    # ------------------------------------------------------------------

    def list_files_for_tramite(self, folio: str) -> list[tuple[str, float]]:
        """List PDF files for a tramite using optimised ``listdir_attr()``.

        Args:
            folio: Folio of the tramite.

        Returns:
            List of ``(file_name, size_mb)`` tuples (PDF files only).

        Raises:
            SFTPConnectionError: On connection / listing failure.
        """
        _validate_folio(folio)
        folio_dir = f'{settings.SFTP_BASE_DIR}/{folio}'

        client = self.get_sftp_client()
        sftp = client.open_sftp()

        # Single network call: names + metadata
        try:
            entries = sftp.listdir_attr(folio_dir)
        except FileNotFoundError:
            entries = []
        except (OSError, paramiko.SSHException, EOFError) as exc:
            logger.error('Error al listar archivos en %s: %s', folio_dir, exc)
            raise SFTPConnectionError(
                'Error al obtener la lista de archivos. Por favor intenta nuevamente más tarde.'
            ) from exc
        finally:
            sftp.close()

        # Warn if unusually many files
        pdf_count = sum(1 for e in entries if e.filename.endswith('.pdf'))
        if pdf_count > FILE_COUNT_WARNING_THRESHOLD:
            logger.warning('Tramite %s tiene demasiados archivos: %d!!', folio, pdf_count)

        return [
            (e.filename, (e.st_size or 0) / (1024 * 1024))
            for e in entries
            if e.filename.endswith('.pdf')
        ]

    def list_requisito_files(
        self,
        folio: str,
    ) -> tuple[list[RequisitoFile], str | None]:
        """List requisito PDFs with catalog names from the database.

        Args:
            folio: Folio of the tramite.

        Returns:
            ``(files, warning_message)`` — *warning_message* is ``None``
            when everything is normal.

        Raises:
            SFTPConnectionError: On SFTP failure.
        """
        try:
            files = self.list_files_for_tramite(folio)
            requisitos_dict = self._get_cached_requisitos()

            resultado: list[RequisitoFile] = []
            for file_name, size_mb in files:
                match = FILENAME_REGEX.match(file_name)
                if not match:
                    continue

                requisito_id = int(match.group('requisito_id'))
                requisito = requisitos_dict.get(requisito_id)

                resultado.append(
                    RequisitoFile(
                        requisito_id=requisito_id,
                        requisito_nombre=requisito.requisito if requisito else None,
                        file_name=file_name,
                        size_mb=size_mb,
                    )
                )

            warning = self._check_file_count_warning(len(resultado), folio)
            return resultado, warning

        except SFTPConnectionError:
            raise
        except Exception as exc:
            logger.error(
                'Error inesperado al listar requisitos para folio %s: %s',
                folio,
                exc,
            )
            raise SFTPConnectionError(
                'Ocurrió un error inesperado al cargar los archivos. '
                'Por favor contacta al administrador del sistema.'
            ) from exc

    # ------------------------------------------------------------------
    # File download
    # ------------------------------------------------------------------

    def download_file(
        self,
        folio: str,
        filename: str,
        local_path: Path,
    ) -> None:
        """Download a PDF file from SFTP server to local cache.

        Args:
            folio: Folio of the tramite.
            filename: Name of the PDF file to download.
            local_path: Local path where the file should be saved.

        Raises:
            SFTPConnectionError: On SFTP failure or validation error.
        """
        # Validate inputs to prevent path traversal
        _validate_folio(folio)
        _validate_filename(filename)

        # Ensure local_path parent directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Remote path on SFTP server
        remote_path = f'{settings.SFTP_BASE_DIR}/{folio}/{filename}'

        client = self.get_sftp_client()
        sftp = client.open_sftp()

        try:
            # Check file size before download (security: enforce max size)
            file_stat = sftp.stat(remote_path)
            file_size = file_stat.st_size or 0
            if file_size > MAX_DOWNLOAD_FILE_SIZE_BYTES:
                logger.error(
                    'Archivo excede tamaño máximo: %s (%d bytes > %d bytes)',
                    filename,
                    file_size,
                    MAX_DOWNLOAD_FILE_SIZE_BYTES,
                )
                raise SFTPConnectionError(
                    'El archivo es demasiado grande para descargar. El tamaño máximo es 50 MB.'
                )
                raise SFTPConnectionError(
                    'El archivo es demasiado grande para descargar. El tamaño máximo es 50 MB.'
                )

            # Download file to local path
            sftp.get(remote_path, str(local_path))
            logger.info('Archivo descargado exitosamente: %s', filename)

        except FileNotFoundError:
            logger.error('Archivo no encontrado en SFTP: %s', remote_path)
            raise SFTPConnectionError(
                'El archivo solicitado no existe. Por favor verifica que el trámite sea correcto.'
            ) from None
        except (OSError, paramiko.SSHException, EOFError) as exc:
            logger.error('Error al descargar archivo %s: %s', filename, exc)
            raise SFTPConnectionError(
                'Error al descargar el archivo. Por favor intenta nuevamente más tarde.'
            ) from exc
        finally:
            sftp.close()

    # ------------------------------------------------------------------
    # Warning helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_file_count_warning(
        count: int,
        folio: str,
    ) -> str | None:
        """Return a warning message if *count* exceeds the threshold."""
        if count <= FILE_COUNT_WARNING_THRESHOLD:
            return None

        return (
            f'Se encontraron {count} archivos PDF en el trámite {folio}. '
            'Esto es inusual y puede afectar el rendimiento. '
            'Por favor verifica que todos los archivos sean necesarios.'
        )
