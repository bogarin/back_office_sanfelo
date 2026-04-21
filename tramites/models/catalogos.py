"""Catálogo models migrated from the legacy catalogos app.

These are read-heavy reference tables with infrequent changes.
All map to existing PostgreSQL tables via db_table (no schema changes).

All catalog models are routed to the 'backend' database with read-only access
using the ReadOnlyManager, which prevents all write operations (create, update,
delete) at the ORM level to ensure data integrity.
"""

from django.db import models

from core.managers import ReadOnlyManager
from core.model_config import AccessPattern, register_model


@register_model('backend', AccessPattern.READ_ONLY, False)
class TramiteCatalogo(models.Model):
    """Tipos de trámites disponibles en el sistema.

    Routed to backend database with read-only access. All write operations
    are prevented to maintain data integrity of this reference table.
    """

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'cat_tramite'
        verbose_name = 'Catálogo Trámite'
        verbose_name_plural = 'Catálogo Trámites'
        ordering = ('nombre',)

    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255, verbose_name='Nombre')
    descripcion = models.CharField(
        max_length=600, blank=True, null=True, verbose_name='Descripción'
    )
    area = models.CharField(max_length=80, blank=True, null=True, verbose_name='Área')
    respuesta_dias = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True, verbose_name='Respuesta en Días'
    )
    pago_inicial = models.BooleanField(null=True, blank=True, verbose_name='Pago Inicial')
    url = models.CharField(max_length=512, blank=True, null=True, verbose_name='URL')
    activo = models.BooleanField(null=True, verbose_name='Activo')

    def __str__(self) -> str:
        return self.nombre


@register_model('backend', AccessPattern.READ_ONLY, False)
class TramiteEstatus(models.Model):
    """Estatus de trámites agrupados por prefijo.

    States are grouped by prefix:
    - 1xx: Inicio (Draft, Pending Payment, etc.)
    - 2xx: Proceso (Presented, In Review, etc.)
    - 3xx: Finalizado (Completed, Rejected, etc.)

    Routed to backend database with read-only access. All write operations
    are prevented to maintain data integrity of this reference table.
    """

    class Estatus(models.IntegerChoices):
        BORRADOR = 101, 'BORRADOR'
        PENDIENTE_PAGO = 102, 'PENDIENTE PAGO'
        PAGO_EXPIRADO = 103, 'PAGO EXPIRADO'

        PRESENTADO = 201, 'PRESENTADO'
        EN_REVISION = 202, 'EN REVISIÓN'
        REQUERIMIENTO = 203, 'REQUERIMIENTO'
        SUBSANADO = 204, 'SUBSANADO'
        EN_DILIGENCIA = 205, 'EN DILIGENCIA'

        POR_RECOGER = 301, 'POR RECOGER'
        RECHAZADO = 302, 'RECHAZADO'
        FINALIZADO = 303, 'FINALIZADO'
        CANCELADO = 304, 'CANCELADO'


        @classmethod
        def es_activo(cls, estatus: int) -> bool:
            return estatus in (
                cls.PRESENTADO,
                cls.EN_REVISION,
                cls.REQUERIMIENTO,
                cls.SUBSANADO,
                cls.EN_DILIGENCIA,
            )

        @classmethod
        def finalizados(cls):
            return (
                cls.POR_RECOGER,
                cls.RECHAZADO,
                cls.FINALIZADO,
                cls.CANCELADO,
                cls.PAGO_EXPIRADO,
            )

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'cat_estatus'
        verbose_name = 'Estatus de Trámite'
        verbose_name_plural = 'Estatus de Trámites'
        ordering = ('id',)

    id = models.AutoField(primary_key=True)
    estatus = models.CharField(max_length=30, verbose_name='Estatus')
    responsable = models.CharField(max_length=64, blank=True, null=True, verbose_name='Responsable')
    descripcion = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Descripción'
    )

    def __str__(self) -> str:
        return self.estatus

    @classmethod
    def get_en_revision(cls):
        """Obtiene la instancia de estatus EN_REVISION (id=202).

        Este método es un helper para simplificar la lógica de asignación
        de trámites. Usa caché del manager para evitar queries repetidas.

        Returns:
            TramiteEstatus: La instancia de estatus con id=202
        """
        return cls.objects.get_cached(202)


@register_model('backend', AccessPattern.READ_ONLY, False)
class Perito(models.Model):
    """Peritos autorizados para trámites.

    Routed to backend database with read-only access. All write operations
    are prevented to maintain data integrity of this reference table.
    """

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'cat_perito'
        verbose_name = 'Perito'
        verbose_name_plural = 'Peritos'
        ordering = ('paterno', 'materno', 'nombre')

    id = models.AutoField(primary_key=True)
    paterno = models.CharField(
        max_length=30, blank=True, null=True, verbose_name='Apellido Paterno'
    )
    materno = models.CharField(
        max_length=30, blank=True, null=True, verbose_name='Apellido Materno'
    )
    nombre = models.CharField(max_length=90, blank=True, null=True, verbose_name='Nombre')
    domicilio = models.CharField(max_length=250, blank=True, null=True, verbose_name='Domicilio')
    colonia = models.CharField(max_length=120, blank=True, null=True, verbose_name='Colonia')
    telefono = models.CharField(max_length=16, blank=True, null=True, verbose_name='Teléfono')
    celular = models.CharField(max_length=16, blank=True, null=True, verbose_name='Celular')
    correo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Correo')
    revalidacion = models.DateField(blank=True, null=True, verbose_name='Revalidación')
    fecha_registro = models.DateField(blank=True, null=True, verbose_name='Fecha de Registro')
    rfc = models.CharField(max_length=17, blank=True, null=True, verbose_name='RFC')
    estatus = models.BooleanField(verbose_name='Estatus')
    cedula = models.CharField(max_length=19, blank=True, null=True, verbose_name='Cédula')

    @property
    def nombre_completo(self) -> str:
        """Get full name of the perito."""
        parts = [
            str(self.paterno) if self.paterno else None,
            str(self.materno) if self.materno else None,
            str(self.nombre) if self.nombre else None,
        ]
        return ' '.join(p for p in parts if p)

    def __str__(self) -> str:
        return self.nombre_completo


@register_model('backend', AccessPattern.READ_ONLY, False)
class Actividad(models.Model):
    """Actividades que pueden realizarse durante un trámite.

    Routed to backend database with read-only access. All write operations
    are prevented to maintain data integrity of this reference table.
    """

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'cat_actividad'
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['actividad']

    id = models.AutoField(primary_key=True)
    actividad = models.CharField(max_length=250, verbose_name='Actividad')

    def __str__(self) -> str:
        return self.actividad


@register_model('backend', AccessPattern.READ_ONLY, False)
class Categoria(models.Model):
    """Categorías de trámites.

    Routed to backend database with read-only access. All write operations
    are prevented to maintain data integrity of this reference table.
    """

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'cat_categoria'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['categoria']

    id = models.AutoField(primary_key=True)
    categoria = models.CharField(max_length=120, blank=True, null=True, verbose_name='Categoría')

    def __str__(self) -> str:
        return self.categoria or ''


@register_model('backend', AccessPattern.READ_ONLY, False)
class Requisito(models.Model):
    """Requisitos para trámites.

    Routed to backend database with read-only access. All write operations
    are prevented to maintain data integrity of this reference table.
    """

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'cat_requisito'
        verbose_name = 'Requisito'
        verbose_name_plural = 'Requisitos'
        ordering = ['requisito']

    id = models.AutoField(primary_key=True)
    requisito = models.CharField(max_length=480, verbose_name='Requisito')

    def __str__(self) -> str:
        return self.requisito


@register_model('backend', AccessPattern.READ_ONLY, False)
class Tipo(models.Model):
    """Tipos de trámites (para costos).

    Routed to backend database with read-only access. All write operations
    are prevented to maintain data integrity of this reference table.
    """

    objects = ReadOnlyManager()

    class Meta:
        managed = False
        db_table = 'cat_tipo'
        verbose_name = 'Tipo'
        verbose_name_plural = 'Tipos'
        ordering = ['tipo']

    id = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=120, verbose_name='Tipo')

    def __str__(self) -> str:
        return self.tipo
