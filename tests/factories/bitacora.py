"""Factory-boy factories for bitacora models."""

from datetime import date

import factory


class BitacoraFactory(factory.django.DjangoModelFactory):
    """Factory for Bitacora model."""

    class Meta:
        model = 'bitacora.Bitacora'

    usuario_sis = factory.Faker('user_name')
    tipo_mov = factory.Iterator(['CREATE', 'UPDATE', 'DELETE', 'VIEW'])
    usuario_pc = factory.Faker('ipv4')
    fecha = date.today()
    maquina = factory.Faker('hostname')
    val_anterior = factory.Faker('text', max_nb_chars=100)
    val_nuevo = factory.Faker('text', max_nb_chars=100)
    observaciones = factory.Faker('text', max_nb_chars=200)
