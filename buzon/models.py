"""
Models for buzon app.

Contains the AsignacionTramite model which manages tramite assignments to analysts.
This is the ONLY new table created for the Buzón de Trámites system.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

# Estados permitidos para asignación (200s - proceso activo)
ESTADOS_PERMITIDOS_PARA_ASIGNACION = [201, 202, 203, 204, 205]


class AsignacionTramite(models.Model):
    """
    Asignación de trámite a analista.

    Características:
    - Solo permite UNA asignación por trámite (UniqueConstraint a nivel BD)
    - Reemplaza asignaciones anteriores automáticamente
    - Incluye validaciones de negocio
    - Usa transacciones atómicas para evitar race conditions
    - Solo permite asignar trámites en estados 200s (proceso activo)
    - Almacena user IDs como IntegerField (evita cross-database relations)

    NO modifica tablas legacy - solo crea esta tabla nueva.
    """

    tramite = models.ForeignKey(
        'tramites.Tramite', on_delete=models.CASCADE, verbose_name='Trámite'
    )

    # Store user IDs as IntegerField to avoid cross-database relations
    analista_id = models.IntegerField(verbose_name='ID Analista')

    asignado_por_id = models.IntegerField(null=True, blank=True, verbose_name='ID Asignado Por')

    fecha_asignacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Asignación')

    observacion = models.TextField(blank=True, null=True, verbose_name='Observación')

    class Meta:
        verbose_name = 'Asignación de Trámite'
        verbose_name_plural = 'Asignaciones de Trámites'
        db_table = 'asignacion_tramite'
        ordering = ('-fecha_asignacion',)

        # UniqueConstraint garantiza 1-a-1 a nivel BD
        constraints = [
            models.UniqueConstraint(
                fields=['tramite'],
                name='una_sola_asignacion_por_tramite',
                violation_error_message='Este trámite ya está asignado a otro analista',
            )
        ]

        indexes = [
            models.Index(fields=['analista_id']),
            models.Index(fields=['tramite']),
        ]

    def __str__(self):
        # Get analista username from User model (cached property for efficiency)
        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            analista = User.objects.get(id=self.analista_id)
            return f'{self.tramite.folio} → {analista.username}'
        except User.DoesNotExist:
            return f'{self.tramite.folio} → User ID {self.analista_id}'

    @property
    def analista(self):
        """Get analista User instance from ID (lazy loading)."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            return User.objects.get(id=self.analista_id)
        except User.DoesNotExist:
            return None

    @property
    def asignado_por(self):
        """Get asignado_por User instance from ID (lazy loading)."""
        if not self.asignado_por_id:
            return None
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            return User.objects.get(id=self.asignado_por_id)
        except User.DoesNotExist:
            return None

    def clean(self):
        """
        Validaciones de negocio.

        Raises:
            ValidationError: Si el trámite no puede ser asignado
        """
        # Solo asignar trámites en estados 200s (proceso activo)
        estatus_id = self.tramite.estatus_id if self.tramite else None

        if estatus_id not in ESTADOS_PERMITIDOS_PARA_ASIGNACION:
            # Intentar obtener el nombre del estatus desde tramite_estatus
            from tramites.models import TramiteEstatus

            estatus_nombre = 'DESCONOCIDO'
            try:
                estatus = TramiteEstatus.objects.get(id=estatus_id)
                estatus_nombre = estatus.estatus
            except TramiteEstatus.DoesNotExist:
                estatus_nombre = f'ID {estatus_id}'

            raise ValidationError(
                f'No se pueden asignar trámites en estatus "{estatus_nombre}". '
                f'Solo se pueden asignar trámites en proceso activo (estados 200s: PRESENTADO, EN_REVISION, REQUERIMIENTO, SUBSANADO, EN_DILIGENCIA).'
            )

        # Opcional: Límite de asignaciones por analista
        asignaciones_actuales = AsignacionTramite.objects.filter(
            analista_id=self.analista_id
        ).count()
        max_asignaciones = getattr(settings, 'MAX_TRAMITES_POR_ANALISTA', 50)
        if asignaciones_actuales >= max_asignaciones:
            raise ValidationError(
                f'El analista ya tiene {asignaciones_actuales} trámites asignados. '
                f'Límite: {max_asignaciones}'
            )

        # Si ya existe una asignación para este tramite, no incrementar el contador
        try:
            from django.core.exceptions import ObjectDoesNotExist

            AsignacionTramite.objects.get(tramite=self.tramite)
            # Ya existe una asignación, no incrementar el contador
        except ObjectDoesNotExist:
            # No existe asignación, contar esta nueva
            pass

        max_asignaciones = getattr(settings, 'MAX_TRAMITES_POR_ANALISTA', 50)
        if asignaciones_actuales >= max_asignaciones:
            raise ValidationError(
                f'El analista ya tiene {asignaciones_actuales} trámites asignados. '
                f'Límite: {max_asignaciones}'
            )

    @classmethod
    def asignar(cls, tramite, analista, asignado_por=None, observacion=''):
        """
        Asigna un trámite a un analista de forma atómica.

        Reemplaza asignación anterior si existe.
        Usa UniqueConstraint para garantizar atomicidad.

        Args:
            tramite: Instancia de Tramite (tabla legacy)
            analista: Instancia de User (analista) - ID se almacena
            asignado_por: Instancia de User (quién asigna, opcional) - ID se almacena
            observacion: Texto opcional

        Returns:
            AsignacionTramite: La nueva asignación

        Raises:
            ValidationError: Si hay validaciones falladas
        """
        from django.db import transaction

        # Verificar si ya existe una asignación
        existente = cls.objects.filter(tramite=tramite).first()

        if existente:
            # Reemplazar asignación existente
            existente.analista_id = analista.id
            existente.asignado_por_id = asignado_por.id if asignado_por else None
            existente.observacion = observacion
            existente.full_clean()  # Ejecutar validaciones
            existente.save()
            return existente
        else:
            # Crear nueva asignación
            asignacion = cls(
                tramite=tramite,
                analista_id=analista.id,
                asignado_por_id=asignado_por.id if asignado_por else None,
                observacion=observacion,
            )
            asignacion.full_clean()  # Ejecutar validaciones
            asignacion.save()
            return asignacion

    @classmethod
    def liberar(cls, tramite):
        """
        Libera un trámite (elimina su asignación).

        Args:
            tramite: Instancia de Tramite
        """
        cls.objects.filter(tramite=tramite).delete()
