"""Factory-boy factories for catalogos models."""

from datetime import date

import factory


class CatTramiteFactory(factory.django.DjangoModelFactory):
    """Factory for CatTramite model."""

    class Meta:
        model = 'catalogos.CatTramite'

    nombre = factory.Sequence(lambda n: f'Trámite {n}')
    descripcion = factory.Faker('text', max_nb_chars=200)
    area = factory.Faker('word')
    respuesta_dias = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    pago_inicial = False
    url = factory.Faker('url')
    activo = True


class CatEstatusFactory(factory.django.DjangoModelFactory):
    """Factory for CatEstatus model."""

    class Meta:
        model = 'catalogos.CatEstatus'

    id = factory.Sequence(lambda n: 100 + n)  # Start from 100 for status codes
    estatus = factory.Sequence(lambda n: f'Estatus {n}')
    responsable = factory.Faker('name')
    descripcion = factory.Faker('text', max_nb_chars=100)


class CatUsuarioFactory(factory.django.DjangoModelFactory):
    """Factory for CatUsuario model."""

    class Meta:
        model = 'catalogos.CatUsuario'

    nombre = factory.Faker('name')
    usuario = factory.Sequence(lambda n: f'usuario_{n}')
    password = factory.Faker('password')
    fecha_baja = date(2099, 12, 31)  # Far future date
    fecha_alta = date(2020, 1, 1)
    activo = True
    correo = factory.LazyAttribute(lambda obj: f'{obj.usuario}@example.com')
    nivel = factory.Faker('word')


class CatPeritoFactory(factory.django.DjangoModelFactory):
    """Factory for CatPerito model."""

    class Meta:
        model = 'catalogos.CatPerito'

    paterno = factory.Faker('last_name')
    materno = factory.Faker('last_name')
    nombre = factory.Faker('first_name')
    domicilio = factory.Faker('address')
    colonia = factory.Faker('word')
    telefono = factory.Faker('phone_number')
    celular = factory.Faker('phone_number')
    correo = factory.Faker('email')
    revalidacion = date(2025, 12, 31)
    fecha_registro = date(2020, 1, 1)
    rfc = factory.Faker('ssn')
    estatus = True
    cedula = factory.Faker('ssn')


class CatActividadFactory(factory.django.DjangoModelFactory):
    """Factory for CatActividad model."""

    class Meta:
        model = 'catalogos.CatActividad'

    actividad = factory.Sequence(lambda n: f'Actividad {n}')


class CatCategoriaFactory(factory.django.DjangoModelFactory):
    """Factory for CatCategoria model."""

    class Meta:
        model = 'catalogos.CatCategoria'

    categoria = factory.Sequence(lambda n: f'Categoría {n}')


class CatIncisoFactory(factory.django.DjangoModelFactory):
    """Factory for CatInciso model."""

    class Meta:
        model = 'catalogos.CatInciso'

    inciso = factory.Sequence(lambda n: n)
    descripcion = factory.Faker('text', max_nb_chars=200)


class CatRequisitoFactory(factory.django.DjangoModelFactory):
    """Factory for CatRequisito model."""

    class Meta:
        model = 'catalogos.CatRequisito'

    requisito = factory.Sequence(lambda n: f'Requisito {n}')


class CatTipoFactory(factory.django.DjangoModelFactory):
    """Factory for CatTipo model."""

    class Meta:
        model = 'catalogos.CatTipo'

    tipo = factory.Sequence(lambda n: f'Tipo {n}')


class RelTmtCateReqFactory(factory.django.DjangoModelFactory):
    """Factory for RelTmtCateReq model."""

    class Meta:
        model = 'catalogos.RelTmtCateReq'

    id_cat_tramite = factory.Sequence(lambda n: n)
    id_cat_requisito = factory.Sequence(lambda n: n)
    id_cat_categoria = factory.Sequence(lambda n: n)


class RelTmtCategoriaFactory(factory.django.DjangoModelFactory):
    """Factory for RelTmtCategoria model."""

    class Meta:
        model = 'catalogos.RelTmtCategoria'

    id_cat_tramite = factory.Sequence(lambda n: n)
    id_cat_categoria = factory.Sequence(lambda n: n)


class RelTmtIncisoFactory(factory.django.DjangoModelFactory):
    """Factory for RelTmtInciso model."""

    class Meta:
        model = 'catalogos.RelTmtInciso'

    id_cat_inciso = factory.Sequence(lambda n: n)
    id_cat_tramite = factory.Sequence(lambda n: n)


class RelTmtTipoReqFactory(factory.django.DjangoModelFactory):
    """Factory for RelTmtTipoReq model."""

    class Meta:
        model = 'catalogos.RelTmtTipoReq'

    id_cat_tipo = factory.Sequence(lambda n: n)
    id_cat_tramite = factory.Sequence(lambda n: n)
    id_cat_requisito = factory.Sequence(lambda n: n)


class ActividadesFactory(factory.django.DjangoModelFactory):
    """Factory for Actividades model."""

    class Meta:
        model = 'catalogos.Actividades'

    id_tramite = factory.Sequence(lambda n: n)
    id_cat_actividad = factory.Sequence(lambda n: n)
    id_cat_estatus = factory.Sequence(lambda n: n)
    fecha_inicio = date(2024, 1, 1)
    fecha_fin = date(2024, 1, 31)
    id_cat_usuario = factory.Sequence(lambda n: n)
    secuencia = factory.Sequence(lambda n: n)
    observacion = factory.Faker('text', max_nb_chars=200)


class CobroFactory(factory.django.DjangoModelFactory):
    """Factory for Cobro model."""

    class Meta:
        model = 'catalogos.Cobro'

    concepto = factory.Faker('sentence')
    importe = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    inciso = factory.Sequence(lambda n: n)
    id_tramite = factory.Sequence(lambda n: n)


class RelTmtActividadFactory(factory.django.DjangoModelFactory):
    """Factory for RelTmtActividad model."""

    class Meta:
        model = 'catalogos.RelTmtActividad'

    id_cat_tramite = factory.Sequence(lambda n: n)
    id_cat_actividad = factory.Sequence(lambda n: n)
