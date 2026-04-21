"""Factory-boy factories for tramites models."""

import factory

from tests.factories.catalogos import TramiteCatalogoFactory, TramiteEstatusFactory
from tramites.models import Actividades


class TramiteFactory(factory.django.DjangoModelFactory):
    """Factory for Tramite model.

    Creates a Tramite without Actividades (estatus is derived from
    Actividades). Use ``TramiteWithEstatusFactory`` or manually
    create ``Actividades`` when you need a specific estatus.

    Note: Tramite is a managed=False model that maps to v_tramites_unificado view.
    """

    class Meta:
        model = 'tramites.Tramite'

    folio = factory.Sequence(lambda n: f'TRAM-{n:06d}')
    tramite_catalogo = factory.SubFactory('tests.factories.TramiteCatalogoFactory')
    clave_catastral = factory.Faker('bothify', text='???####-??-####-#')
    es_propietario = True
    solicitante_nombre = factory.Faker('name')
    solicitante_telefono = factory.Faker('phone_number')
    solicitante_correo = factory.Faker('email')
    importe_total = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    urgente = factory.Faker('boolean')
    solicitante_comentario = factory.Faker('text', max_nb_chars=200)


class TramiteWithEstatusFactory(factory.django.DjangoModelFactory):
    """Factory for Tramite with an Actividades record (sets estatus).

    Creates a Tramite AND an Actividades record with specified
    estatus. This is needed because estatus is now derived from
    latest Actividades record.

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

    # Model fields
    folio = factory.Sequence(lambda n: f'TRAM-{n:06d}')
    tramite_catalogo = factory.SubFactory('tests.factories.TramiteCatalogoFactory')
    clave_catastral = factory.Faker('bothify', text='???####-??-####-#')
    es_propietario = True
    solicitante_nombre = factory.Faker('name')
    solicitante_telefono = factory.Faker('phone_number')
    solicitante_correo = factory.Faker('email')
    importe_total = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    urgente = factory.Faker('boolean')
    solicitante_comentario = factory.Faker('text', max_nb_chars=200)

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
        # Priority order: estatus_id kwarg -> estatus kwarg -> create default
        estatus_id = kwargs.get('estatus_id', None)

        if estatus_id is not None:
            # Use estatus_id kwarg
            estatus_obj = TramiteEstatus.objects.get(id=estatus_id)
        else:
            # Try to get estatus from multiple sources
            estatus_obj = None

            # 1. Check if estatus was passed as a kwarg
            estatus_passed = kwargs.get('estatus', None)
            if estatus_passed is not None:
                estatus_obj = estatus_passed

            # 2. Check if estatus was stored on instance
            if estatus_obj is None:
                try:
                    estatus_obj = getattr(tramite_instance, '_estatus')
                except AttributeError:
                    pass

            # 3. If still no estatus, create a default one
            if estatus_obj is None or estatus_obj.id >= 300:
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
