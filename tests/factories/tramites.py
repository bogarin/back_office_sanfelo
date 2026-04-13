"""Factory-boy factories for tramites models."""

import factory

from tests.factories.catalogos import TramiteEstatusFactory


class TramiteFactory(factory.django.DjangoModelFactory):
    """Factory for Tramite model.

    Creates a Tramite without Actividades (estatus is derived from
    Actividades). Use ``TramiteWithEstatusFactory`` or manually
    create ``Actividades`` when you need a specific estatus.
    """

    class Meta:
        model = 'tramites.Tramite'

    folio = factory.Sequence(lambda n: f'TRAM-{n:06d}')
    tramite_catalogo = factory.SubFactory('tests.factories.TramiteCatalogoFactory')
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


class TramiteWithEstatusFactory(factory.django.DjangoModelFactory):
    """Factory for Tramite with an Actividades record (sets estatus).

    Creates a Tramite AND an Actividades record with the specified
    estatus. This is needed because estatus is now derived from
    the latest Actividades record.

    Usage:
        # Default estatus (201 - PRESENTADO)
        tramite = TramiteWithEstatusFactory()

        # Specific estatus
        tramite = TramiteWithEstatusFactory(estatus=my_estatus)

        # Specific estatus_id
        tramite = TramiteWithEstatusFactory(estatus_id=201)
    """

    class Meta:
        model = 'tramites.Tramite'
        exclude = ['estatus', 'estatus_id']

    # Model fields
    folio = factory.Sequence(lambda n: f'TRAM-{n:06d}')
    tramite_catalogo = factory.SubFactory('tests.factories.TramiteCatalogoFactory')
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

    # Extra params for Actividades (excluded from model, used in post_generation)
    estatus = factory.SubFactory('tests.factories.TramiteEstatusFactory')
    estatus_id = None  # Override: use this instead of estatus object

    @factory.post_generation
    def create_actividades(self, create, extracted, **kwargs):
        """Create an Actividades record to set tramite's estatus."""
        if not create:
            return

        # The tramite instance is available via self
        tramite_instance = self

        from tramites.models import Actividades, TramiteEstatus

        # Determine estatus to use
        # Priority order: estatus_id kwarg -> estatus kwarg -> _estatus attribute -> create default
        estatus_id = kwargs.get('estatus_id', None)

        if estatus_id is not None:
            # Use the estatus_id kwarg
            estatus_obj = TramiteEstatus.objects.get(id=estatus_id)
        else:
            # Try to get estatus from multiple sources
            estatus_obj = None

            # 1. Check if estatus was passed as a kwarg
            estatus_passed = kwargs.get('estatus', None)
            if estatus_passed is not None:
                estatus_obj = estatus_passed

            # 2. Check if estatus was stored on the instance
            if estatus_obj is None:
                try:
                    estatus_obj = getattr(tramite_instance, 'estatus')
                except AttributeError:
                    pass

            # 3. Get the estatus that was created by the SubFactory (_estatus)
            if estatus_obj is None:
                try:
                    estatus_obj = getattr(tramite_instance, '_estatus')
                except AttributeError:
                    pass

            # 4. If still no estatus, create or find a default non-finalizado one
            if estatus_obj is None or (hasattr(estatus_obj, 'id') and estatus_obj.id >= 300):
                # Try to find an existing non-finalizado estatus
                estatus_obj = TramiteEstatus.objects.filter(id__lt=300).first()
                if not estatus_obj:
                    # Create a default one
                    estatus_obj = TramiteEstatusFactory(estatus='Presentado')

        # Create Actividades record with new schema (backoffice_user_id, timestamp)
        Actividades.objects.create(
            tramite=tramite_instance,
            estatus=estatus_obj,
            backoffice_user_id=None,
            observacion='Created via factory',
        )
