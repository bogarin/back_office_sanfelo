"""Factory-boy factories for costos models."""

from datetime import date

import factory


class CostoFactory(factory.django.DjangoModelFactory):
    """Factory for Costo model."""

    class Meta:
        model = 'costos.Costo'

    id_tramite = factory.Sequence(lambda n: n)
    axo = 2024
    descripcion = factory.Sequence(lambda n: f'Costo para trámite {n}')
    formula = factory.Faker('word')
    cant_umas = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    rango_ini = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    rango_fin = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    inciso = factory.Sequence(lambda n: n)
    fomento = True
    cruz_roja = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    bomberos = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    activo = True
    id_usuario = factory.Sequence(lambda n: n)
    fecha_actualiza = date.today()
    observacion = factory.Faker('text', max_nb_chars=200)
    id_tipo = factory.Sequence(lambda n: n)


class UmaFactory(factory.django.DjangoModelFactory):
    """Factory for Uma model."""

    class Meta:
        model = 'costos.Uma'

    id = 1
    valor = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
