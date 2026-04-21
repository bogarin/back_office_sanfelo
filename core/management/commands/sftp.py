"""
Django management command for SFTP operations.

Usage:
    python manage.py sftp ping
    python manage.py sftp list <folio>
"""

import importlib.metadata
from pathlib import Path

import django
import paramiko
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


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

        if action == 'ping':
            self._ping()
        elif action == 'list':
            if not folio:
                raise CommandError('Error: Se requiere el parámetro <folio> para la acción list.')
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

    def _get_sftp_client(self):
        """Crea y conecta cliente SFTP usando llave o contraseña."""

        host = settings.SFTP_HOST
        port = settings.SFTP_PORT
        username = settings.SFTP_USERNAME
        password = settings.SFTP_PASSWORD
        key_path = Path(settings.SFTP_PRIVATE_KEY_PATH).expanduser()
        key_path_str = str(key_path)
        key_passphrase = settings.SFTP_PRIVATE_KEY_PASSPHRASE

        # Prioridad: llave privada > contraseña
        if key_path:
            try:
                key = None
                auth_method = 'unknown'

                try:
                    key = paramiko.RSAKey.from_private_key_file(key_path_str)
                    auth_method = 'RSA key'
                except paramiko.SSHException:
                    pass

                if key is None:
                    try:
                        key = paramiko.Ed25519Key.from_private_key_file(key_path_str)
                        auth_method = 'Ed25519 key'
                    except paramiko.SSHException:
                        pass

                if key is None:
                    try:
                        key = paramiko.ECDSAKey.from_private_key_file(key_path_str)
                        auth_method = 'ECDSA key'
                    except paramiko.SSHException:
                        pass

                # DSA key está deprecado, no soportado en paramiko 4.0+

                # Intentar cargar con passphrase si está configurada
                if key is None and key_passphrase:
                    try:
                        key = paramiko.RSAKey.from_private_key_file(
                            key_path_str, password=key_passphrase
                        )
                        auth_method = 'RSA key with passphrase'
                    except paramiko.SSHException:
                        pass

                    if key is None:
                        try:
                            key = paramiko.Ed25519Key.from_private_key_file(
                                key_path_str, password=key_passphrase
                            )
                            auth_method = 'Ed25519 key with passphrase'
                        except paramiko.SSHException:
                            pass

                if key is None:
                    raise CommandError(
                        'No se pudo cargar la llave privada SSH. '
                        'Verifica el tipo (RSA, Ed25519, ECDSA, DSA) y passphrase.'
                    ) from None

            except paramiko.SSHException as e:
                raise CommandError(f'Error al cargar llave privada SSH: {e}') from None
            except FileNotFoundError:
                raise CommandError(
                    f'Archivo de llave privada no encontrado: {str(key_path)}'
                ) from None

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.stdout.write(f'  Método de autenticación: {auth_method}')

            client.connect(hostname=host, port=port, username=username, pkey=key)

        elif password:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.stdout.write('  Método de autenticación: password')

            client.connect(hostname=host, port=port, username=username, password=password)
        else:
            raise CommandError(
                'No hay método de autenticación disponible (password o llave privada)'
            )

        return client

    def _ping(self):
        """Prueba conexión SFTP con validación completa."""
        host = settings.SFTP_HOST
        port = settings.SFTP_PORT
        username = settings.SFTP_USERNAME
        base_dir = settings.SFTP_BASE_DIR

        self._print_versions()
        self._validate_sftp_config()

        self.stdout.write('Probando conexión SFTP...')
        self.stdout.write(f'  Host: {host}:{port}')
        self.stdout.write(f'  Usuario: {username}')
        self.stdout.write(f'  Directorio base: {base_dir}')

        try:
            client = self._get_sftp_client()
            sftp = client.open_sftp()
            sftp.listdir(base_dir)
            client.close()

        except paramiko.AuthenticationException as e:
            self.stdout.write(self.style.ERROR(f'✗ Error de autenticación: {e}'))
            raise CommandError(
                'Autenticación fallida. Verifica password o llave privada.'
            ) from None

        except paramiko.SSHException as e:
            self.stdout.write(self.style.ERROR(f'✗ Error SSH: {e}'))
            raise CommandError(str(e)) from None

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'✗ Directorio no encontrado: {base_dir}'))
            raise CommandError(f'El directorio base {base_dir} no existe en el servidor.') from None

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error al conectar al servidor SFTP: {e}'))
            raise CommandError(str(e)) from None

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ Conexión SFTP exitosa'))

    def _list_files(self, folio: str):
        """Lista archivos de un trámite específico."""
        base_dir = settings.SFTP_BASE_DIR
        folio_dir = f'{base_dir}/{folio}'

        self._validate_sftp_config()

        self.stdout.write(f'Listando archivos para trámite: {folio}')
        self.stdout.write(f'  Directorio: {folio_dir}')
        self.stdout.write('')

        try:
            client = self._get_sftp_client()
            sftp = client.open_sftp()

            # Verificar que el directorio del trámite existe
            try:
                sftp.stat(folio_dir)
            except FileNotFoundError:
                self.stdout.write(
                    self.style.WARNING(f'⚠ El directorio {folio_dir} no existe en el servidor')
                )
                client.close()
                return

            files = sftp.listdir(folio_dir)

            if not files:
                self.stdout.write('  No se encontraron archivos')
            else:
                self.stdout.write(f'  Archivos encontrados: {len(files)}')
                self.stdout.write('')

                for file_name in files:
                    try:
                        file_path = f'{folio_dir}/{file_name}'
                        attrs = sftp.stat(file_path)
                        st_size = getattr(attrs, 'st_size', 0) or 0
                        size_mb = st_size / (1024 * 1024)
                        self.stdout.write(f'    - {file_name} ({size_mb:.2f} MB)')
                    except Exception as e:
                        self.stdout.write(f'    - {file_name} (error: {e})')

            client.close()

        except paramiko.AuthenticationException as e:
            self.stdout.write(self.style.ERROR(f'✗ Error de autenticación: {e}'))
            raise CommandError(
                'Autenticación fallida. Verifica password o llave privada.'
            ) from None

        except paramiko.SSHException as e:
            self.stdout.write(self.style.ERROR(f'✗ Error SSH: {e}'))
            raise CommandError(str(e)) from None

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error al listar archivos: {e}'))
            raise CommandError(str(e)) from None

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ Listado completado'))
