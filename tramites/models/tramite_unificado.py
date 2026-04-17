import logging
from typing import ForwardRef

from django.contrib.auth import get_user_model
from django.db import DatabaseError, models

from core.model_config import AccessPattern, register_model
from tramites.exceptions import TramiteNoAsignableError
from tramites.models import Actividades, Tramite, TramiteEstatus

User = get_user_model()
logger = logging.getLogger(__name__)


@register_model('default', AccessPattern.READ_ONLY, False)
class TramiteUnificado(models.Model):
    """
    Modelo de Django que mapea a la vista v_tramites_unificado en el esquema backoffice.
    Esta vista unifica información de trámites con sus actividades, usuarios asignados y categorías.
    """

    id = models.IntegerField(primary_key=True)
    folio = models.CharField(max_length=50, help_text='Folio del trámite')
    tramite_id = models.IntegerField()
    tramite_nombre = models.CharField(max_length=255, help_text='Tipo de trámite')
    tramite_categoria_id = models.IntegerField(null=True, blank=True)
    tramite_categoria_nombre = models.CharField(
        max_length=255, null=True, blank=True, help_text='Categoría'
    )
    tramite_tipo_cobro_id = models.IntegerField(null=True, blank=True)
    tramite_tipo_cobro_nombre = models.CharField(
        max_length=100, null=True, blank=True, help_text='Tipo de cobro'
    )
    clave_catastral = models.CharField(
        max_length=100, null=True, blank=True, help_text='Clave catastral'
    )
    es_propietario = models.BooleanField(
        help_text='Indica si el solicitante es el propietario del inmueble'
    )
    importe_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Importe total del trámite',
    )
    urgente = models.BooleanField(help_text='Indica si el trámite es urgente')
    solicitante_nombre = models.CharField(
        max_length=200, null=True, blank=True, help_text='Nombre del solicitante'
    )
    solicitante_telefono = models.CharField(
        max_length=20, null=True, blank=True, help_text='Teléfono del solicitante'
    )
    solicitante_correo = models.CharField(
        max_length=100, null=True, blank=True, help_text='Correo del solicitante'
    )
    solicitante_comentario = models.TextField(
        null=True, blank=True, help_text='Comentario del solicitante'
    )
    perito_id = models.IntegerField(null=True, blank=True)
    perito_nombre = models.CharField(
        max_length=200, null=True, blank=True, help_text='Nombre del perito'
    )
    ultima_actividad_estatus_id = models.IntegerField(null=True, blank=True)
    ultima_actividad_estatus = models.CharField(
        max_length=100, null=True, blank=True, help_text='Estado de la última actividad'
    )
    ultima_actividad_responsable = models.CharField(
        max_length=100, null=True, blank=True, help_text='Responsable de la última actividad'
    )
    ultima_actividad_descripcion = models.TextField(
        null=True, blank=True, help_text='Descripción de la última actividad'
    )
    ultima_actividad_observacion = models.TextField(
        null=True, blank=True, help_text='Observación de la última actividad'
    )
    asignado_user_id = models.IntegerField(null=True, blank=True)
    asignado_username = models.CharField(
        max_length=150, null=True, blank=True, help_text='Nombre de usuario del analista asignado'
    )
    asignado_nombre = models.CharField(
        max_length=150, null=True, blank=True, help_text='Nombre del analista asignado'
    )
    asignado_group_id = models.IntegerField(null=True, blank=True)
    asignado_rol = models.CharField(
        max_length=150, null=True, blank=True, help_text='Rol del analista asignado'
    )
    creado = models.DateTimeField(help_text='Fecha y hora de creación del trámite')
    actualizado = models.DateTimeField(
        null=True, blank=True, help_text='Fecha y hora de la última actualización del trámite'
    )

    class Meta:
        managed = False
        db_table = 'v_tramites_unificado'
        verbose_name = 'Lista de Trámites'
        verbose_name_plural = 'Trámites'
        ordering = ('-creado', 'urgente')

    def __str__(self):
        return f'{self.folio} - {self.tramite_nombre}'

    def asignar(
        self,
        analista: User,
        asignado_por: User | None = None,
        observacion: str = '',
    ) -> bool:
        """
        Asigna un trámite creando registro en Actividades.

        Source of truth: Actividades table (backend database).
        La vista v_tramites_unificado se actualiza automáticamente.

        Args:
            analista: Instancia de User que recibe la asignación
            asignado_por: Instancia de User que hace la asignación (opcional)
            observacion: Texto opcional para la actividad

        Returns:
            None: La asignación se realizó exitosamente

        Raises:
            TramiteNoAsignableError: Estatus no está en rango 200-299
            DatabaseError: Si falla el INSERT en Actividades
        """
        # Validar estatus actual
        if self.ultima_actividad_estatus_id is None:
            raise TramiteNoAsignableError('El trámite no tiene estatus definido')

        if not (200 <= self.ultima_actividad_estatus_id < 300):
            estatus = TramiteEstatus.objects.get_cached(self.ultima_actividad_estatus_id)
            estatus_nombre = (
                estatus.estatus if estatus else f'ID {self.ultima_actividad_estatus_id}'
            )

            raise TramiteNoAsignableError(
                f'Solo se pueden asignar trámites en proceso activo (estados 200s). '
                f'Estatus actual: "{estatus_nombre}"'
            )

        # Validar si ya está asignado al mismo analista (reasignación silenciosa)
        if self.asignado_user_id == analista.id:
            # Reasignación al mismo analista - loggear warning y continuar
            logging.warning(
                f'⚠️ REASIGNACIÓN OMITIDA: Trámite {self.tramite_id} '
                f'ya está asignado a {analista.username} ({analista.id})'
            )
            # NO levantar excepción - retornar False para indicar omisión
            return False

        # Determinar observación si no se provee
        if not observacion:
            if analista == asignado_por:
                observacion = 'Trámite autoasignado'
            else:
                asignado_por_name = asignado_por.get_full_name() if asignado_por else 'Sistema'
                observacion = f'Trámite asignado por {asignado_por_name}'

        # Obtener instancia de Tramite (para ForeignKey en Actividades)
        try:
            tramite_obj = Tramite.objects.using('backend').get(id=self.pk)
        except Tramite.DoesNotExist as e:
            raise TramiteNoAsignableError(f'El trámite con ID {self.pk} no existe') from e

        # Crear registro en Actividades
        try:
            Actividades.objects.create(
                tramite=tramite_obj,
                estatus_id=202,  # EN_REVISION
                backoffice_user_id=analista.id,
                observacion=observacion,
            )
            logging.info(
                f'✅ ASIGNACIÓN COMPLETADA: Trámite {self.tramite_id} → '
                f'Analista {analista.id} ({analista.username})'
            )
            return True
        except DatabaseError as e:
            logging.error(f'❌ Error al crear registro de actividad: {e}')
            raise DatabaseError(
                f'Error de base de datos al crear registro de actividad: {e}'
            ) from e


class Abiertos(TramiteUnificado):
    """Proxy model for 'Todos' view - shows all trámites."""

    class Meta:
        proxy = True
        verbose_name = 'Todos los Trámites'
        verbose_name_plural = 'Todos'
        ordering = ('-creado', '-urgente')


class TramiteAsignados(TramiteUnificado):
    """Proxy model for 'Asignados' view - shows assigned trámites."""

    class Meta:
        proxy = True
        verbose_name = 'Trámites Asignados'
        verbose_name_plural = 'Asignados'
        ordering = ('-creado', '-urgente')
