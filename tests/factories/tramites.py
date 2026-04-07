"""Factory-boy factories for tramites models."""

import factory


class TramiteFactory(factory.django.DjangoModelFactory):
    """Factory for Tramite model."""

    class Meta:
        model = 'tramites.Tramite'

    folio = factory.Sequence(lambda n: f'TRAM-{n:06d}')
    tramite_catalogo = factory.SubFactory('tests.factories.TramiteCatalogoFactory')
    estatus = factory.SubFactory('tests.factories.TramiteEstatusFactory')
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
