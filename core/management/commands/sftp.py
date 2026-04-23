"""
Django management command for SFTP operations.

Usage:
    python manage.py sftp ping
    python manage.py sftp list <folio>
    python manage.py sftp cleanup_cache
"""

import importlib.metadata
import logging
import os
import time
from pathlib import Path

import django
import paramiko
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tramites.constants import FORBIDDEN_FOLIO_CHARS, FORBIDDEN_FILENAME_CHARS
from tramites.exceptions import SFTPConnectionError
from tramites.services import SFTPService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """SFTP management command with ping, list, cleanup_cache, and download subcommands."""

    help = 'Test SFTP connection, list files, cleanup cache, and download PDF files'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['ping', 'list', 'cleanup_cache', 'download'],
            help='Action to perform: ping (test connection), list (list files for tramite), cleanup_cache (clean cached PDF files), or download (download PDF file from SFTP)',
        )
        parser.add_argument(
            'folio',
            type=str,
            nargs='?',
            help='Folio del trámite (requerido para acciones list y download)',
        )
        parser.add_argument(
            'filename',
            type=str,
            nargs='?',
            help='Nombre del archivo PDF a descargar (solo para acción download)',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='.',
            help='Directorio de destino para descargar archivos (default: directorio actual)',
        )

    def handle(self, *args, **options):
        action = options['action']
        folio = options.get('folio')
        filename = options.get('filename')
        output_dir = options.get('output_dir')

        match action:
            case 'ping':
                self._ping()
            case 'list':
                if not folio:
                    raise CommandError(
                        'Error: Se requiere el parámetro <folio> para la acción list.'
                    )
                self._list_files(folio)
            case 'cleanup_cache':
                self._cleanup_cache()
            case 'download':
                if not folio or not filename:
                    raise CommandError(
                        'Error: Se requieren los parámetros <folio> y <filename> para la acción download.'
                    )
                self._download(folio, filename, output_dir)

    def _print_versions(self):
        """Imprime versiones de dependencias críticas."""
        self.stdout.write('📦 Versiones de dependencias:')
        self.stdout.write(f'  Django: {".".join(map(str, django.VERSION))}')
        self.stdout.write(f'  django-storages: {importlib.metadata.version("django-storages")}')
        self.stdout.write(f'  paramiko: {paramiko.__version__}')
        self.stdout.write('')

    def _validate_sftp_config(self):
        """Valida configuración SFTP e imprime warnings/errores."""

        errors = []
        warnings = []

        # Validaciones críticas
        if not settings.SFTP_HOST:
            errors.append('SFTP_HOST no está configurado')

        if not settings.SFTP_USERNAME:
            errors.append('SFTP_USERNAME no está configurado')

        # Validar que haya al menos un método de autenticación
        has_password = bool(settings.SFTP_PASSWORD)
        has_key = bool(settings.SFTP_PRIVATE_KEY_PATH)

        if not has_password and not has_key:
            errors.append('No hay método de autenticación configurado (password o llave privada)')

        # Validaciones con warnings
        if ' ' in settings.SFTP_HOST:
            warnings.append('SFTP_HOST contiene espacios (posible error)')

        if not 1 <= settings.SFTP_PORT <= 65535:
            warnings.append(f'SFTP_PORT ({settings.SFTP_PORT}) debe estar entre 1 y 65535')

        if has_password and len(settings.SFTP_PASSWORD) < 4:
            warnings.append('SFTP_PASSWORD parece muy corta (< 4 caracteres)')

        if not settings.SFTP_BASE_DIR.startswith('/'):
            warnings.append(f'SFTP_BASE_DIR ({settings.SFTP_BASE_DIR}) debe empezar con /')

        if not settings.SFTP_BASE_DIR:
            warnings.append(
                'SFTP_BASE_DIR no está definido. '
                'El comando SFTP requiere un directorio base en el servidor.'
            )

        # Validar llave privada si está configurada
        if has_key:
            key_path_for_validation = Path(settings.SFTP_PRIVATE_KEY_PATH).expanduser()
            if not key_path_for_validation.exists():
                msg = f'SFTP_PRIVATE_KEY_PATH existe pero archivo no encontrado: {key_path_for_validation}'
                warnings.append(msg)
            else:
                # Validar permisos de llave (esperados: 600)
                file_mode = oct(key_path_for_validation.stat().st_mode)[-3:]
                if file_mode != '600':
                    warnings.append(
                        f'Permisos de llave SSH incorrectos ({file_mode}, esperados: 600). '
                        f'Ejecuta: chmod 600 {key_path_for_validation}'
                    )

        # Imprimir warnings
        for warning in warnings:
            self.stdout.write(self.style.WARNING(f'⚠ {warning}'))

        if warnings:
            self.stdout.write('')

        # Lanzar errores si existen
        if errors:
            for error in errors:
                self.stdout.write(self.style.ERROR(f'✗ {error}'))
            raise CommandError(
                'Configuración SFTP inválida. Por favor revisa las variables de entorno.'
            )

    def _ping(self):
        """Prueba conexión SFTP con validación completa."""
        self._print_versions()
        self._validate_sftp_config()

        # Warn if host key verification is not enforced
        if not getattr(settings, 'SFTP_HOST_KEY', ''):
            if settings.DEBUG:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠ SFTP_HOST_KEY no configurado. '
                        'La conexión NO está protegida contra ataques MITM. '
                        'Configura SFTP_HOST_KEY para producción. '
                        'Ver: docs/sftp-host-key.md'
                    )
                )
                self.stdout.write('')
            else:
                # RejectPolicy will be enforced by the service — this is informational
                pass

        self.stdout.write('Probando conexión SFTP...')

        service = SFTPService()

        try:
            client = service.get_sftp_client()
            sftp = client.open_sftp()
            sftp.listdir(settings.SFTP_BASE_DIR)

        except SFTPConnectionError as e:
            self.stdout.write(self.style.ERROR(f'✗ {e}'))
            raise CommandError(str(e)) from None

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'✗ Directorio no encontrado: {settings.SFTP_BASE_DIR}')
            )
            raise CommandError(
                f'El directorio base {settings.SFTP_BASE_DIR} no existe en el servidor.'
            ) from None

        except Exception as e:
            logger.error('Error inesperado en ping SFTP: %s', e)
            self.stdout.write(self.style.ERROR('✗ Error al conectar al servidor SFTP.'))
            raise CommandError('Error inesperado. Revisa los logs del servidor.') from None

        finally:
            service.close_connection()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ Conexión SFTP exitosa'))

    def _list_files(self, folio: str):
        """Lista archivos de un trámite usando el servicio SFTP."""
        # Early rejection of path traversal characters
        if any(c in folio for c in FORBIDDEN_FOLIO_CHARS):
            raise CommandError(f'Folio contiene caracteres no permitidos: {folio!r}')

        self._validate_sftp_config()

        self.stdout.write(f'Listando archivos para trámite: {folio}')
        self.stdout.write('')

        service = SFTPService()

        try:
            # Obtener archivos desde el servicio
            files, warning_message = service.list_requisito_files(folio)

            # Mostrar advertencia si existe
            if warning_message:
                self.stdout.write(self.style.WARNING(f'⚠ {warning_message}'))
                self.stdout.write('')

            if not files:
                self.stdout.write('  No se encontraron archivos')
            else:
                # Imprimir cabecera de tabla
                self.stdout.write(
                    f'  {"Requisito ID":<14} {"Nombre":<40} {"Archivo":<35} {"Tamaño":<10}'
                )
                self.stdout.write(f'  {"-" * 99}')

                for f in files:
                    requisito_nombre = f.requisito_nombre or '—'
                    self.stdout.write(
                        f'  {f.requisito_id:<14} {requisito_nombre:<40} '
                        f'{f.file_name:<35} {f.size_mb:.2f} MB'
                    )

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'✓ {len(files)} archivos listados'))

        except SFTPConnectionError as e:
            self.stdout.write(self.style.ERROR(f'✗ {e}'))
            raise CommandError(str(e)) from None

        except Exception as e:
            logger.error('Error inesperado listando archivos para folio %s: %s', folio, e)
            self.stdout.write(self.style.ERROR('✗ Error inesperado. Revisa los logs del servidor.'))
            raise CommandError('Error inesperado. Contacta al administrador.') from None

        finally:
            service.close_connection()

    def _cleanup_cache(self):
        """Clean up expired or oversized cached PDF files.

        This command removes:
        1. Files older than SFTP_CACHE_TTL seconds
        2. Oldest files if cache exceeds SFTP_CACHE_MAX_SIZE_MB

        Usage:
            python manage.py sftp cleanup_cache
        """
        cache_dir = Path(settings.SFTP_CACHE_DIR)
        ttl = getattr(settings, 'SFTP_CACHE_TTL', 3600)
        max_size_mb = getattr(settings, 'SFTP_CACHE_MAX_SIZE_MB', 500)
        max_size_bytes = max_size_mb * 1024 * 1024

        self.stdout.write('🧹 Limpiando caché SFTP...')
        self.stdout.write(f'  Directorio: {cache_dir}')
        self.stdout.write(f'  TTL: {ttl} segundos')
        self.stdout.write(f'  Tamaño máximo: {max_size_mb} MB')
        self.stdout.write('')

        # Check if cache directory exists
        if not cache_dir.exists():
            self.stdout.write(self.style.WARNING('⚠ El directorio de caché no existe.'))
            return

        # Get all files in cache directory
        all_files = []
        total_size = 0
        current_time = time.time()

        for file_path in cache_dir.iterdir():
            if file_path.is_file():
                file_size = file_path.stat().st_size
                file_mtime = file_path.stat().st_mtime
                file_age = current_time - file_mtime

                all_files.append(
                    {
                        'path': file_path,
                        'size': file_size,
                        'age': file_age,
                        'mtime': file_mtime,
                    }
                )
                total_size += file_size

        if not all_files:
            self.stdout.write('  No hay archivos en caché.')
            return

        # Sort by modification time (oldest first)
        all_files.sort(key=lambda x: x['mtime'])

        # Remove expired files
        expired_files = [f for f in all_files if f['age'] > ttl]
        removed_count = 0
        removed_size = 0

        for file_info in expired_files:
            try:
                file_info['path'].unlink()
                removed_count += 1
                removed_size += file_info['size']
                self.stdout.write(f'  ✗ Eliminado (expirado): {file_info["path"].name}')
            except OSError as e:
                logger.error('Error eliminando archivo %s: %s', file_info['path'], e)
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error eliminando {file_info["path"].name}: {e}')
                )

        # Recalculate total size after removing expired files
        total_size -= removed_size

        # If still over max size, remove oldest files
        if total_size > max_size_bytes:
            self.stdout.write('')
            self.stdout.write(
                f'⚠ Caché excede tamaño máximo ({total_size / (1024 * 1024):.2f} MB > {max_size_mb} MB)'
            )
            self.stdout.write('  Eliminando archivos más antiguos...')

            for file_info in all_files:
                if total_size <= max_size_bytes:
                    break

                try:
                    file_info['path'].unlink()
                    total_size -= file_info['size']
                    removed_count += 1
                    removed_size += file_info['size']
                    self.stdout.write(f'  ✗ Eliminado (espacio): {file_info["path"].name}')
                except OSError as e:
                    logger.error('Error eliminando archivo %s: %s', file_info['path'], e)
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error eliminando {file_info["path"].name}: {e}')
                    )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✓ Limpieza completada'))
        self.stdout.write(f'  Archivos eliminados: {removed_count}')
        self.stdout.write(f'  Espacio liberado: {removed_size / (1024 * 1024):.2f} MB')
        self.stdout.write(
            f'  Tamaño actual: {total_size / (1024 * 1024):.2f} MB / {max_size_mb} MB'
        )

    def _download(self, folio: str, filename: str, output_dir: str):
        """Download a PDF file from SFTP to local directory.

        This command validates both folio and filename, then downloads the file
        from SFTP to the specified output directory (defaults to cwd).

        Args:
            folio: Folio of the tramite.
            filename: Name of the PDF file to download.
            output_dir: Destination directory (default: current working directory).

        Raises:
            CommandError: If validation fails or download fails.
        """
        # Validate SFTP configuration
        self._validate_sftp_config()

        # Resolve and validate output directory
        output_path = Path(output_dir).resolve()
        if not output_path.exists():
            raise CommandError(f'El directorio de destino no existe: {output_path}')
        if not output_path.is_dir():
            raise CommandError(f'La ruta de destino no es un directorio: {output_path}')

        # Build local file path
        local_path = output_path / filename

        # Check if file already exists (no silent overwrite)
        if local_path.exists():
            raise CommandError(f'El archivo ya existe en el directorio de destino: {local_path}')

        self.stdout.write('📥 Descargando archivo desde SFTP...')
        self.stdout.write(f'  Folio: {folio}')
        self.stdout.write(f'  Archivo: {filename}')
        self.stdout.write(f'  Destino: {output_path}')
        self.stdout.write('')

        service = SFTPService()

        try:
            # Download file (includes all validations)
            service.download_file(
                folio=folio,
                filename=filename,
                local_path=local_path,
            )

            # Get file size for reporting
            file_size = local_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'✓ Archivo descargado exitosamente'))
            self.stdout.write(f'  Ruta: {local_path}')
            self.stdout.write(f'  Tamaño: {file_size_mb:.2f} MB')

        except SFTPConnectionError as e:
            self.stdout.write(self.style.ERROR(f'✗ {e}'))
            raise CommandError(str(e)) from None

        except Exception as e:
            logger.error(
                'Error inesperado descargando archivo %s para folio %s: %s',
                filename,
                folio,
                e,
            )
            self.stdout.write(self.style.ERROR('✗ Error inesperado. Revisa los logs del servidor.'))
            raise CommandError('Error inesperado. Contacta al administrador.') from None

        finally:
            service.close_connection()
