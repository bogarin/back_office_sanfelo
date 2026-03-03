"""
Models for catalogos app.

Contains all catalog (cat_*) models from the external SQL schema.
Note: This is a mapping to the external SQL schema - do NOT use Django migrations.
"""

from django.db import models


class CatTramite(models.Model):
    """Catálogo de tipos de trámites."""

    class Meta:
        managed = True
        db_table = 'cat_tramite'
        verbose_name = 'Catálogo Trámite'
        verbose_name_plural = 'Catálogo Trámites'
        ordering = ['nombre']

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
        return f'{self.nombre}'


class CatEstatus(models.Model):
    """Catálogo de estatus de trámites.

    States are grouped by prefix:
    - 1xx: Inicio (Draft, Pending Payment, etc.)
    - 2xx: Proceso (Presented, In Review, etc.)
    - 3xx: Finalizado (Completed, Rejected, etc.)
    """

    class Meta:
        managed = True
        db_table = 'cat_estatus'
        verbose_name = 'Catálogo Estatus'
        verbose_name_plural = 'Catálogo Estatus'
        ordering = ['id']

    id = models.AutoField(primary_key=True)
    estatus = models.CharField(max_length=30, verbose_name='Estatus')
    responsable = models.CharField(max_length=64, blank=True, null=True, verbose_name='Responsable')
    descripcion = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Descripción'
    )

    def __str__(self) -> str:
        return f'{self.estatus}'


class CatUsuario(models.Model):
    """Catálogo de usuarios del sistema."""

    class Meta:
        managed = True
        db_table = 'cat_usuario'
        verbose_name = 'Catálogo Usuario'
        verbose_name_plural = 'Catálogo Usuarios'
        ordering = ['nombre']

    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=125, verbose_name='Nombre')
    usuario = models.CharField(max_length=20, verbose_name='Usuario')
    password = models.CharField(
        max_length=24,
        blank=True,
        null=True,
        verbose_name='Contraseña',
        db_column='pass',
    )
    fecha_baja = models.DateField(verbose_name='Fecha de Baja')
    fecha_alta = models.DateField(verbose_name='Fecha de Alta')
    activo = models.BooleanField(verbose_name='Activo')
    correo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Correo')
    nivel = models.CharField(max_length=60, verbose_name='Nivel')

    def __str__(self) -> str:
        return f'{self.nombre}'


class CatPerito(models.Model):
    """Catálogo de peritos autorizados."""

    class Meta:
        managed = True
        db_table = 'cat_perito'
        verbose_name = 'Catálogo Perito'
        verbose_name_plural = 'Catálogo Peritos'
        ordering = ['paterno', 'materno', 'nombre']

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


class CatActividad(models.Model):
    """Catálogo de actividades realizadas durante el trámite."""

    class Meta:
        managed = True
        db_table = 'cat_actividad'
        verbose_name = 'Catálogo Actividad'
        verbose_name_plural = 'Catálogo Actividades'
        ordering = ['actividad']

    id = models.AutoField(primary_key=True)
    actividad = models.CharField(max_length=250, verbose_name='Actividad')

    def __str__(self) -> str:
        return f'{self.actividad}'


class CatCategoria(models.Model):
    """Catálogo de categorías de trámites."""

    class Meta:
        managed = True
        db_table = 'cat_categoria'
        verbose_name = 'Catálogo Categoría'
        verbose_name_plural = 'Catálogo Categorías'
        ordering = ['categoria']

    id = models.AutoField(primary_key=True)
    categoria = models.CharField(max_length=120, blank=True, null=True, verbose_name='Categoría')

    def __str__(self) -> str:
        return f'{self.categoria}'


class CatInciso(models.Model):
    """Catálogo de incisos presupuestarios."""

    class Meta:
        managed = True
        db_table = 'cat_inciso'
        verbose_name = 'Catálogo Inciso'
        verbose_name_plural = 'Catálogo Incisos'
        ordering = ['inciso']

    id = models.AutoField(primary_key=True)
    inciso = models.IntegerField(verbose_name='Inciso')
    descripcion = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Descripción'
    )

    def __str__(self) -> str:
        return f'{self.inciso} - {self.descripcion}'


class CatRequisito(models.Model):
    """Catálogo de requisitos para trámites."""

    class Meta:
        managed = True
        db_table = 'cat_requisito'
        verbose_name = 'Catálogo Requisito'
        verbose_name_plural = 'Catálogo Requisitos'
        ordering = ['requisito']

    id = models.AutoField(primary_key=True)
    requisito = models.CharField(max_length=480, verbose_name='Requisito')

    def __str__(self) -> str:
        return f'{self.requisito}'


class CatTipo(models.Model):
    """Catálogo de tipos de trámites (para costos)."""

    class Meta:
        managed = True
        db_table = 'cat_tipo'
        verbose_name = 'Catálogo Tipo'
        verbose_name_plural = 'Catálogo Tipos'
        ordering = ['tipo']

    id = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=120, verbose_name='Tipo')

    def __str__(self) -> str:
        return f'{self.tipo}'


# ============================================================================
# RELATIONSHIP TABLES (rel_*)
# ============================================================================


class RelTmtCateReq(models.Model):
    """Relación entre catálogo trámites, requisitos y categorías.

    Many-to-Many relationship: Tramite ↔ Requisito ↔ Categoría
    """

    class Meta:
        managed = True
        db_table = 'rel_tmt_cate_req'
        verbose_name = 'Relación Trámite-Requisito-Categoría'
        verbose_name_plural = 'Relaciones Trámite-Requisito-Categoría'

    id = models.AutoField(primary_key=True)
    id_cat_tramite = models.IntegerField(verbose_name='ID Catálogo Trámite')
    id_cat_requisito = models.IntegerField(verbose_name='ID Catálogo Requisito')
    id_cat_categoria = models.IntegerField(blank=True, null=True, verbose_name='ID Categoría')

    def __str__(self) -> str:
        return f'Trámite {self.id_cat_tramite} - Req {self.id_cat_requisito}'


class RelTmtCategoria(models.Model):
    """Relación entre catálogo trámites y categorías.

    Many-to-Many relationship: Tramite ↔ Categoría
    """

    class Meta:
        managed = True
        db_table = 'rel_tmt_categoria'
        verbose_name = 'Relación Trámite-Categoría'
        verbose_name_plural = 'Relaciones Trámite-Categoría'

    id = models.AutoField(primary_key=True)
    id_cat_tramite = models.IntegerField(verbose_name='ID Catálogo Trámite')
    id_cat_categoria = models.IntegerField(verbose_name='ID Categoría')

    def __str__(self) -> str:
        return f'Trámite {self.id_cat_tramite} - Cat {self.id_cat_categoria}'


class RelTmtInciso(models.Model):
    """Relación entre incisos y trámites.

    Many-to-Many relationship: Tramite ↔ Inciso
    """

    class Meta:
        managed = True
        db_table = 'rel_tmt_inciso'
        verbose_name = 'Relación Inciso-Trámite'
        verbose_name_plural = 'Relaciones Inciso-Trámite'

    id = models.AutoField(primary_key=True)
    id_cat_inciso = models.IntegerField(verbose_name='ID Inciso')
    id_cat_tramite = models.IntegerField(verbose_name='ID Catálogo Trámite')

    def __str__(self) -> str:
        return f'Inciso {self.id_cat_inciso} - Trámite {self.id_cat_tramite}'


class RelTmtTipoReq(models.Model):
    """Relación entre cat_tipo, trámites y requisitos.

    Many-to-Many relationship with three-way join: Tramite ↔ Requisito ↔ Tipo
    """

    class Meta:
        managed = True
        db_table = 'rel_tmt_tipo_req'
        verbose_name = 'Relación Tipo-Trámite-Requisito'
        verbose_name_plural = 'Relaciones Tipo-Trámite-Requisito'

    id = models.AutoField(primary_key=True)
    id_cat_tipo = models.IntegerField(verbose_name='ID Tipo')
    id_cat_tramite = models.IntegerField(verbose_name='ID Catálogo Trámite')
    id_cat_requisito = models.IntegerField(verbose_name='ID Catálogo Requisito')

    def __str__(self) -> str:
        return (
            f'Tipo {self.id_cat_tipo} - Trámite {self.id_cat_tramite} - Req {self.id_cat_requisito}'
        )


# ============================================================================
# ADDITIONAL TABLES
# ============================================================================


class Actividades(models.Model):
    """Registro de actividades realizadas durante el trámite.

    Tracks each activity performed on a tramite.
    """

    class Meta:
        managed = True
        db_table = 'actividades'
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['-secuencia']

    id = models.AutoField(primary_key=True)
    id_tramite = models.IntegerField(verbose_name='ID Trámite')
    id_cat_actividad = models.IntegerField(verbose_name='ID Catálogo Actividad')
    id_cat_estatus = models.IntegerField(verbose_name='ID Catálogo Estatus')
    fecha_inicio = models.DateField(verbose_name='Fecha Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha Fin')
    id_cat_usuario = models.IntegerField(verbose_name='ID Usuario')
    secuencia = models.IntegerField(verbose_name='Secuencia')
    observacion = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Observación'
    )

    def __str__(self) -> str:
        return f'Actividad {self.id} - Trámite {self.id_tramite}'


class Cobro(models.Model):
    """Registro de cobros realizados por trámite.

    Tracks payments made for tramite procedures.
    """

    class Meta:
        managed = True
        db_table = 'cobro'
        verbose_name = 'Cobro'
        verbose_name_plural = 'Cobros'
        ordering = ['-id']

    id = models.AutoField(primary_key=True)
    concepto = models.CharField(max_length=250, verbose_name='Concepto')
    importe = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Importe')
    inciso = models.IntegerField(blank=True, null=True, verbose_name='Inciso')
    id_tramite = models.IntegerField(verbose_name='ID Trámite')

    def __str__(self) -> str:
        return f'{self.concepto} - ${self.importe}'


class RelTmtActividad(models.Model):
    """Relación entre catálogo trámites y actividades.

    Many-to-Many relationship: Tramite ↔ Actividad
    """

    class Meta:
        managed = True
        db_table = 'rel_tmt_actividad'
        verbose_name = 'Relación Trámite-Actividad'
        verbose_name_plural = 'Relaciones Trámite-Actividad'

    id = models.AutoField(primary_key=True)
    id_cat_tramite = models.IntegerField(verbose_name='ID Catálogo Trámite')
    id_cat_actividad = models.IntegerField(verbose_name='ID Actividad')

    def __str__(self) -> str:
        return f'Trámite {self.id_cat_tramite} - Actividad {self.id_cat_actividad}'
