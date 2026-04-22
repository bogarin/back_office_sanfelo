"""
Django management command to simulate a payment for a trámite.

.. warning::

    This command is intended **exclusively** for development and testing.
    **NEVER** use it in production. It bypasses the normal payment flow
    and directly registers a PRESENTADO activity on the trámite.

Usage::

    python manage.py simular_pago <folio>

The command will prompt for explicit confirmation before making any changes.
"""

from django.core.management.base import BaseCommand, CommandError

from tramites.models.catalogos import TramiteEstatus
from tramites.models.tramite import Tramite

OBSERVACION = 'Marcado como pagado desde la línea de comandos'

BANNER_ADVERTENCIA = (
    '\n'
    '⚠️  ADVERTENCIA\n'
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
    'Este comando es SOLO para pruebas de desarrollo.\n'
    'NO debe utilizarse en producción.\n'
    'Modifica directamente el estado de un trámite simulando\n'
    'un pago que nunca ocurrió.\n'
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
)


class Command(BaseCommand):
    """Simulate payment for a trámite by registering a PRESENTADO activity."""

    help = (
        'Simula el pago de un trámite registrando una actividad PRESENTADO. '
        'SOLO para desarrollo y pruebas.'
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            'folio',
            type=str,
            help='Folio del trámite a simular como pagado',
        )

    def handle(self, *args, **options) -> None:
        folio: str = options['folio']

        # ── Buscar trámite ──────────────────────────────────────────
        try:
            tramite = Tramite.objects.get(folio=folio)
        except Tramite.DoesNotExist:
            raise CommandError(f'No se encontró ningún trámite con folio "{folio}".')

        # ── Advertencia y confirmación ──────────────────────────────
        self.stdout.write(self.style.WARNING(BANNER_ADVERTENCIA))
        self.stdout.write(f'\n  Trámite encontrado: {tramite.folio} — {tramite.tramite_nombre}')
        self.stdout.write(f'  Estatus actual: {tramite.ultima_actividad_estatus}\n')

        confirmacion = (
            input('¿Comprende las consecuencias y desea continuar? [sí/no]: ').strip().lower()
        )

        if confirmacion not in ('sí', 'si', 's'):
            self.stdout.write(self.style.ERROR('Operación cancelada.'))
            return

        # ── Registrar actividad ─────────────────────────────────────
        tramite.registrar_actividad(
            estatus_id=TramiteEstatus.Estatus.PRESENTADO,
            analista_id=None,
            observacion=OBSERVACION,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Trámite {tramite.folio} marcado como pagado (estatus → PRESENTADO).'
            )
        )
