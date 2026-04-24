"""
Servicios SFTP para el módulo de trámites.

Conexión, listing de archivos, descarga con caché y validación de folios.

Public API (classmethods — no instance creation needed):
    - ``SFTPService.serve_requisito_pdf(tramite, filename)`` → HttpResponse
    - ``SFTPService.fetch_requisito_files(folio)`` → (files, warning)
    - ``SFTPService.download_to_path(folio, filename, local_path)`` → None
    - ``SFTPService.ping()`` → None

Module-level validators:
    - ``validate_folio(folio)`` → str
    - ``validate_filename(filename)`` → str
"""

from __future__ import annotations

import base64
import logging
import os
import stat
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import paramiko
from django.conf import settings
from django.http import FileResponse, HttpResponse

from .constants import (
    FILE_COUNT_WARNING_THRESHOLD,
    FILENAME_REGEX,
    FOLIO_REGEX,
    FORBIDDEN_FILENAME_CHARS,
    FORBIDDEN_FOLIO_CHARS,
    MAX_DOWNLOAD_FILE_SIZE_BYTES,
)
from .exceptions import SFTPConnectionError
from .models import Requisito, RequisitoFile

if TYPE_CHECKING:
    from .models import Tramite

logger = logging.getLogger(__name__)

# =============================================================================
# SFTP SERVICE
# =============================================================================


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
        except (paramiko.SSHException, OSError) as exc:
            logger.debug('Failed to load key with %s: %s', label, exc)
            continue
    return None


# =============================================================================
# Folio Validation
# =============================================================================


def validate_folio(folio: str) -> str:
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


def validate_filename(filename: str) -> str:
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
    """Facade for SFTP operations with internally-managed connection lifecycle.

    All public methods are **classmethods** — no instance creation needed.
    Connection lifecycle (open/close) is handled internally via
    ``try/finally`` blocks.

    Public API::

        SFTPService.serve_requisito_pdf(tramite, filename) -> HttpResponse
        SFTPService.fetch_requisito_files(folio) -> (files, warning)
        SFTPService.download_to_path(folio, filename, local_path) -> None
        SFTPService.ping() -> None
    """

    # ------------------------------------------------------------------
    # High-level use-case methods (classmethods)
    # ------------------------------------------------------------------

    @classmethod
    def serve_requisito_pdf(
        cls,
        tramite: Tramite,
        filename: str,
    ) -> HttpResponse:
        """Full download pipeline: validate → cache → download → build response.

        Validates folio and filename, checks the local cache, downloads from
        SFTP if needed, and returns an appropriate HTTP response (dev:
        ``FileResponse``, prod: ``X-Accel-Redirect``).  Connection lifecycle
        is managed internally.

        Args:
            tramite: Tramite instance.
            filename: PDF filename.

        Returns:
            HttpResponse ready to return from a Django view.

        Raises:
            SFTPConnectionError: On validation, connection, or download failure.
        """
        validate_folio(tramite.folio)
        validate_filename(filename)

        service = cls()
        try:
            final_path = service._download_with_cache(tramite, filename)
            cache_path_for_nginx = f'{tramite.folio}/{filename}'

            # Defense-in-depth: reject any path traversal in the nginx header.
            # Both folio and filename are already validated, but this is a cheap
            # output-boundary guard against future regressions.
            assert '..' not in cache_path_for_nginx, (
                f'Path traversal detected in cache path: {cache_path_for_nginx!r}'
            )

            return cls.build_file_response(
                final_path=final_path,
                cache_path_for_nginx=cache_path_for_nginx,
                filename=filename,
            )
        except SFTPConnectionError:
            raise
        except Exception as exc:
            logger.error(
                'Error inesperado al servir archivo %s para folio %s: %s',
                filename,
                tramite.folio,
                exc,
                exc_info=True,
            )
            raise SFTPConnectionError(
                'Error al descargar el archivo. Por favor intenta nuevamente más tarde.'
            ) from exc
        finally:
            service.close_connection()

    @classmethod
    def fetch_requisito_files(
        cls,
        folio: str,
    ) -> tuple[list[RequisitoFile], str | None]:
        """List requisito PDFs with catalog names from the database.

        Validates the folio, fetches the file listing from SFTP, and enriches
        each entry with the requisito name from the database catalog.
        Connection lifecycle is managed internally.

        Args:
            folio: Folio of the tramite.

        Returns:
            ``(files, warning_message)`` — *warning_message* is ``None``
            when everything is normal.

        Raises:
            SFTPConnectionError: On validation or SFTP failure.
        """
        validate_folio(folio)

        service = cls()
        try:
            return service._list_requisito_files(folio)
        except SFTPConnectionError:
            raise
        except Exception as exc:
            logger.error(
                'Error inesperado al listar requisitos para folio %s: %s',
                folio,
                exc,
                exc_info=True,
            )
            raise SFTPConnectionError(
                'Ocurrió un error inesperado al cargar los archivos. '
                'Por favor contacta al administrador del sistema.'
            ) from exc
        finally:
            service.close_connection()

    @classmethod
    def download_to_path(
        cls,
        folio: str,
        filename: str,
        local_path: Path,
    ) -> None:
        """Download a file from SFTP to an arbitrary local path.

        Validates folio and filename, then downloads the file. Connection
        lifecycle is managed internally.  Intended for CLI use.

        Args:
            folio: Folio of the tramite.
            filename: Name of the PDF file to download.
            local_path: Local path where the file should be saved.

        Raises:
            SFTPConnectionError: On validation, connection, or download failure.
        """
        validate_folio(folio)
        validate_filename(filename)

        service = cls()
        try:
            service._download_file(folio=folio, filename=filename, local_path=local_path)
        except SFTPConnectionError:
            raise
        except Exception as exc:
            logger.error(
                'Error inesperado descargando archivo %s para folio %s: %s',
                filename,
                folio,
                exc,
                exc_info=True,
            )
            raise SFTPConnectionError(
                'Error al descargar el archivo. Por favor intenta nuevamente más tarde.'
            ) from exc
        finally:
            service.close_connection()

    @classmethod
    def ping(cls) -> None:
        """Test SFTP connectivity by connecting and listing the base directory.

        Raises:
            SFTPConnectionError: If the connection or listing fails.
        """
        service = cls()
        try:
            client = service.get_sftp_client()
            sftp = client.open_sftp()
            try:
                sftp.listdir(settings.SFTP_BASE_DIR)
            except FileNotFoundError:
                raise SFTPConnectionError(
                    f'El directorio base {settings.SFTP_BASE_DIR} no existe en el servidor.'
                ) from None
            except (OSError, paramiko.SSHException, EOFError) as exc:
                logger.error('Error en ping SFTP al listar %s: %s', settings.SFTP_BASE_DIR, exc)
                raise SFTPConnectionError(
                    'Error al conectar al servidor SFTP. Intenta nuevamente más tarde.'
                ) from exc
            finally:
                sftp.close()
        except SFTPConnectionError:
            raise
        except Exception as exc:
            logger.error('Error inesperado en ping SFTP: %s', exc, exc_info=True)
            raise SFTPConnectionError(
                'Error al conectar al servidor SFTP. Intenta nuevamente más tarde.'
            ) from exc
        finally:
            service.close_connection()

    # ------------------------------------------------------------------
    # Connection lifecycle (internal)
    # ------------------------------------------------------------------

    def get_sftp_client(self) -> paramiko.SSHClient:
        """Create and return a connected SFTP client.

        A new connection is created each time.  Callers are responsible
        for calling :meth:`close_connection` when done (typically in a
        ``finally`` block).
        """
        self._sftp_client = self._create_sftp_connection()
        return self._sftp_client

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
        """Close the SFTP connection (if one was opened by this instance).

        Silently ignores socket-level errors during close to avoid
        suppressing the original exception in ``finally`` blocks.
        """
        client = getattr(self, '_sftp_client', None)
        if client is not None:
            self._safe_close(client)
            self._sftp_client = None

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
    # Cached catalog lookups (internal)
    # ------------------------------------------------------------------

    def _get_cached_requisitos(self) -> dict[int, Requisito]:
        """Return ``{pk: Requisito}`` dict from Django cache."""
        return Requisito.objects.all_cached_as_dict()

    # ------------------------------------------------------------------
    # File listing (internal)
    # ------------------------------------------------------------------

    def _list_files_for_tramite(self, folio: str) -> list[tuple[str, float]]:
        """List PDF files for a tramite using optimised ``listdir_attr()``.

        Args:
            folio: Folio of the tramite.

        Returns:
            List of ``(file_name, size_mb)`` tuples (PDF files only).

        Raises:
            SFTPConnectionError: On connection / listing failure.
        """
        validate_folio(folio)
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

    def _list_requisito_files(
        self,
        folio: str,
    ) -> tuple[list[RequisitoFile], str | None]:
        """List requisito PDFs with catalog names from the database.

        Internal method — callers should use the ``fetch_requisito_files``
        classmethod instead.

        Args:
            folio: Folio of the tramite.

        Returns:
            ``(files, warning_message)`` — *warning_message* is ``None``
            when everything is normal.

        Raises:
            SFTPConnectionError: On SFTP failure.
        """
        try:
            files = self._list_files_for_tramite(folio)
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
    # File download (internal)
    # ------------------------------------------------------------------

    def _download_file(
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
        validate_folio(folio)
        validate_filename(filename)

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
    # Warning helpers (internal)
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

    # ------------------------------------------------------------------
    # Cache helpers (internal)
    # ------------------------------------------------------------------

    @staticmethod
    def _is_cache_hit(path: Path) -> bool:
        """Check if a cached file exists and is valid.

        Uses O_NOFOLLOW to prevent symlink attacks and checks file size > 0.

        Args:
            path: Path to the cached file.

        Returns:
            True if file exists and is valid, False otherwise.
        """
        try:
            fd = os.open(str(path), os.O_NOFOLLOW | os.O_RDONLY)
        except OSError:
            return False

        try:
            st = os.fstat(fd)
            return stat.S_ISREG(st.st_mode) and st.st_size > 0
        finally:
            os.close(fd)

    @staticmethod
    def _is_within_cache(path: Path, cache_dir: Path) -> bool:
        """Check if a path is safely within the cache directory.

        Resolves both paths and uses is_relative_to for containment check.

        Args:
            path: Path to check.
            cache_dir: Cache directory path.

        Returns:
            True if path is within cache_dir, False otherwise.
        """
        resolved = path.resolve()
        resolved_cache = cache_dir.resolve()
        return resolved.is_relative_to(resolved_cache)

    # ------------------------------------------------------------------
    # Response builder (internal)
    # ------------------------------------------------------------------

    @staticmethod
    def build_file_response(
        final_path: Path,
        cache_path_for_nginx: str,
        filename: str,
    ) -> FileResponse | HttpResponse:
        """Build HTTP response for file download.

        In dev mode, serves file directly via FileResponse.
        In prod mode, delegates to nginx via X-Accel-Redirect.

        Args:
            final_path: Local path to the file (dev mode only).
            cache_path_for_nginx: Path for nginx X-Accel-Redirect (prod mode only).
            filename: Original filename for Content-Disposition header.

        Returns:
            HttpResponse with appropriate headers.
        """
        if settings.DEBUG:
            # Dev mode: serve file directly with FileResponse
            response = FileResponse(
                final_path.open('rb'),
                content_type='application/pdf',
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
        else:
            # Production: delegate to nginx via X-Accel-Redirect
            response = HttpResponse()
            response['X-Accel-Redirect'] = f'/sftp-cache/{cache_path_for_nginx}'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'

        return response

    # -------------------------------------------------------------------------
    # Cache download (internal)
    # -------------------------------------------------------------------------

    def _download_with_cache(
        self,
        tramite: Tramite,
        filename: str,
    ) -> Path:
        """Download file to cache with atomic operations and temp file management.

        Internal method — callers should use the ``serve_requisito_pdf``
        classmethod instead.

        Args:
            tramite: Tramite instance.
            filename: PDF filename.

        Returns:
            Path to the final cached file.
        """
        folio = tramite.folio
        cache_dir = Path(settings.SFTP_CACHE_DIR)
        folio_cache_dir = cache_dir / folio
        final_path = folio_cache_dir / filename

        # Cache hit check
        if self._is_within_cache(final_path, cache_dir) and self._is_cache_hit(final_path):
            return final_path

        # Cache miss - download from SFTP with atomic rename
        pid = os.getpid()
        uuid_suffix = uuid.uuid4().hex[:8]
        temp_filename = f'.{filename}.{pid}.{uuid_suffix}.downloading'
        temp_path = folio_cache_dir / temp_filename

        try:
            folio_cache_dir.mkdir(parents=True, exist_ok=True)

            self._download_file(
                folio=folio,
                filename=filename,
                local_path=temp_path,
            )

            # Atomic rename: .downloading -> final name
            temp_path.rename(final_path)
            return final_path

        except BaseException:
            # Cleanup temp file on any failure (download, rename, etc.)
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass
            raise
