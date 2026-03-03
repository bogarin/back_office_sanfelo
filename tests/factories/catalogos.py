"""Factories for catalogos models."""

import factory
from datetime import date

from catalogos.models import (
    CatEstatus,
    CatPerito,
    CatTramite,
    Actividades,
)


class CatTramiteFactory(factory.django.DjangoModelFactory):
    """Factory for CatTramite model."""

    class Meta:
        model = 'catalogos.CatTramite'

    nombre = factory.Faker('word')
    descripcion = factory.Faker('text', max_nb_chars=200)
    area = factory.Faker('word')
    respuesta_dias = factory.Faker('random_int', min=1, max=60)
    pago_inicial = factory.Faker('pyfloat')
    url = factory.Faker('url')
    activo = True


class CatEstatusFactory(factory.django.DjangoModelFactory):
    """Factory for CatEstatus model."""

    class Meta:
        model = 'catalogos.CatEstatus'

    estatus = factory.Sequence(lambda n: f'Estatus {n}')
    responsable = factory.Faker('boolean')
    descripcion = factory.Faker('text', max_nb_chars=200)


class CatPeritoFactory(factory.django.DjangoModelFactory):
    """Factory for CatPerito model."""

    class Meta:
        model = 'catalogos.CatPerito'

    paterno = factory.Faker('last_name')
    materno = factory.Faker('last_name')
    nombre = factory.Faker('first_name')
    rfc = factory.Faker('ssn')
    cedula = factory.Faker('ssn')
    telefono = factory.Faker('phone_number')
    celular = factory.Faker('phone_number')
    correo = factory.Faker('email')
    estatus = True
    fecha_registro = date(2020, 1, 1)
    revalidacion = date(2025, 12, 31)


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
