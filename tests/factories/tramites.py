"""Factory-boy factories for tramites models."""


import factory


class TramiteFactory(factory.django.DjangoModelFactory):
    """Factory for Tramite model."""

    class Meta:
        model = 'tramites.Tramite'

    folio = factory.Sequence(lambda n: f'TRAM-{n:06d}')
    id_cat_tramite = factory.Sequence(lambda n: n)
    id_cat_estatus = 101  # Default status
    id_cat_perito = factory.Sequence(lambda n: n)
    clave_catastral = factory.Faker('bothify', text='???####-??-####-#')
    es_propietario = True
    nom_sol = factory.Faker('name')
    tel_sol = factory.Faker('phone_number')
    correo_sol = factory.Faker('email')
    importe_total = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    pagado = False
    tipo = factory.Faker('word')
    observacion = factory.Faker('text')
    urgente = factory.Faker('boolean')
