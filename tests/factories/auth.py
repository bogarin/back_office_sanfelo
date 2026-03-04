"""Factory-boy factories for Django auth models."""

import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_staff = False
    is_active = True
    is_superuser = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to use create_user instead of create."""
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class SuperUserFactory(UserFactory):
    """Factory for superuser."""

    is_staff = True
    is_superuser = True
    username = factory.Sequence(lambda n: f'superuser_{n}')


class AdminUserFactory(UserFactory):
    """Factory for administrador staff user."""

    is_staff = True
    is_superuser = False
    username = factory.Sequence(lambda n: f'admin_{n}')


class GroupFactory(factory.django.DjangoModelFactory):
    """Factory for Group model."""

    class Meta:
        model = 'auth.Group'
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'group_{n}')


class PermissionFactory(factory.django.DjangoModelFactory):
    """Factory for Permission model."""

    class Meta:
        model = 'auth.Permission'
        django_get_or_create = ('codename', 'content_type')

    codename = factory.Sequence(lambda n: f'permission_{n}')
    name = factory.LazyAttribute(lambda obj: f'Can {obj.codename}')
    content_type = factory.SubFactory('tests.factories.auth.ContentTypeFactory')


class ContentTypeFactory(factory.django.DjangoModelFactory):
    """Factory for ContentType model."""

    class Meta:
        model = 'contenttypes.ContentType'
        django_get_or_create = ('app_label', 'model')

    app_label = factory.Faker('word')
    model = factory.Faker('word')
