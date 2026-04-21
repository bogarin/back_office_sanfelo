"""Factories for catalog models (now in tramites app)."""

import factory
from datetime import date

from tramites.models import (
    Actividades,
    Perito,
    TramiteCatalogo,
    TramiteEstatus,
)


class TramiteCatalogoFactory(factory.django.DjangoModelFactory):
    """Factory for TramiteCatalogo model."""

    class Meta:
        model = 'tramites.TramiteCatalogo'

    nombre = factory.Faker('word')
    descripcion = factory.Faker('text', max_nb_chars=200)
    area = factory.Faker('word')
    respuesta_dias = factory.Faker('random_int', min=1, max=60)
    pago_inicial = True
    url = factory.Faker('url')
    activo = True


class TramiteEstatusFactory(factory.django.DjangoModelFactory):
    """Factory for TramiteEstatus model."""

    class Meta:
        model = 'tramites.TramiteEstatus'

    estatus = factory.Sequence(lambda n: f'Estatus {n}')
    responsable = factory.Faker('name')
    descripcion = factory.Faker('text', max_nb_chars=200)


class PeritoFactory(factory.django.DjangoModelFactory):
    """Factory for Perito model."""

    class Meta:
        model = 'tramites.Perito'

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


class ActividadFactory(factory.django.DjangoModelFactory):
    """Factory for Actividad (catálogo) model."""

    class Meta:
        model = 'tramites.Actividad'

    actividad = factory.Sequence(lambda n: f'Actividad {n}')
