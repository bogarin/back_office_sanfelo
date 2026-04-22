"""
Django management command for SFTP operations.

Usage:
    python manage.py sftp ping
    python manage.py sftp list <folio>
"""

import importlib.metadata
import logging
from pathlib import Path

import django
import paramiko
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tramites.constants import FORBIDDEN_FOLIO_CHARS
from tramites.exceptions import SFTPConnectionError
from tramites.services import SFTPService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """SFTP management command with ping and list subcommands."""

    help = 'Test SFTP connection and list files for tramites'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['ping', 'list'],
            help='Action to perform: ping (test connection) or list (list files for tramite)',
        )
        parser.add_argument(
            'folio',
            type=str,
            nargs='?',
            help='Folio del trámite para listar sus archivos (solo para acción list)',
        )

    def handle(self, *args, **options):
        action = options['action']
        folio = options.get('folio')

        match action:
            case 'ping':
                self._ping()
            case 'list':
                if not folio:
                    raise CommandError(
                        'Error: Se requiere el parámetro <folio> para la acción list.'
                    )
                self._list_files(folio)

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
