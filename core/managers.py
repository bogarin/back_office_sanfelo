"""
Custom Django managers for enforcing access patterns at the ORM level.

This module provides manager classes that restrict database operations to ensure
data integrity and enforce business logic at the model level. These managers
follow Django's manager pattern and can be attached to any model.

Classes:
    ReadOnlyManager: Prevents all write operations on a model.
    CreateOnlyManager: Allows creation but prevents updates and deletes.
"""

from typing import TYPE_CHECKING, Any, Generic, Iterable, TypeVar

from django.core.cache import cache
from django.db import models

if TYPE_CHECKING:
    from django.db.models import Model


T = TypeVar('T', bound='Model')


class ReadOnlyQuerySet(models.QuerySet):
    """
    QuerySet that prevents all write operations.

    This QuerySet overrides all methods that could lead to write operations and
    raises a RuntimeError with a descriptive message. This is useful for models
    that should be immutable after creation, such as reference data or audit logs.

    Note:
        This manager prevents write operations at the QuerySet level. Model instances
        returned from this QuerySet should also have their save() method overridden
        to prevent direct modifications.

    Example:
        >>> class ImmutableModel(models.Model):
        ...     name = models.CharField(max_length=100)
        ...     objects = ReadOnlyManager.as_manager()
        ...
        >>> ImmutableModel.objects.create(name="test")  # Raises RuntimeError
        >>> ImmutableModel.objects.all()  # Works (read-only)
    """

    def create(self, **kwargs: Any) -> 'Model':
        """
        Create and save a new object with the given kwargs.

        Args:
            **kwargs: Field values for the new object.

        Returns:
            The created and saved model instance.

        Raises:
            RuntimeError: Always raised since this is a read-only manager.
        """
        raise RuntimeError(
            'Cannot perform write operation on read-only model. '
            'This model is configured as read-only and does not allow modifications.'
        )

    def bulk_create(
        self,
        objs: Iterable[T],
        batch_size: int | None = None,
        ignore_conflicts: bool = False,
        update_conflicts: bool = False,
        update_fields: list[str] | None = None,
        unique_fields: list[str] | None = None,
    ) -> list[T]:
        """
        Insert each of the instances into the database.

        Args:
            objs: Iterable of model instances to create.
            batch_size: Number of objects to create in each batch.
            ignore_conflicts: If True, ignore conflicts.
            update_conflicts: If True, update on conflicts.
            update_fields: Fields to update on conflict.
            unique_fields: Fields that trigger unique constraint conflicts.

        Returns:
            List of created model instances.

        Raises:
            RuntimeError: Always raised since this is a read-only manager.
        """
        raise RuntimeError(
            'Cannot perform write operation on read-only model. '
            'This model is configured as read-only and does not allow modifications.'
        )

    def update(self, **kwargs: Any) -> int:
        """
        Update all elements in the current QuerySet.

        Args:
            **kwargs: Field update values.

        Returns:
            Number of rows matched.

        Raises:
            RuntimeError: Always raised since this is a read-only manager.
        """
        raise RuntimeError(
            'Cannot perform write operation on read-only model. '
            'This model is configured as read-only and does not allow modifications.'
        )

    def delete(self) -> tuple[int, dict[str, int]]:
        """
        Delete all objects in the QuerySet.

        Returns:
            Tuple of (number of objects deleted, dictionary with counts per type).

        Raises:
            RuntimeError: Always raised since this is a read-only manager.
        """
        raise RuntimeError(
            'Cannot perform write operation on read-only model. '
            'This model is configured as read-only and does not allow modifications.'
        )

    def update_or_create(
        self,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple['Model', bool]:
        """
        Look up an object with the given kwargs, creating one if necessary.

        Args:
            defaults: Dictionary of field values to use when creating.
            **kwargs: Lookup parameters.

        Returns:
            Tuple of (object, created boolean).

        Raises:
            RuntimeError: Always raised since this is a read-only manager.
        """
        raise RuntimeError(
            'Cannot perform write operation on read-only model. '
            'This model is configured as read-only and does not allow modifications.'
        )

    def _clone(self) -> 'ReadOnlyQuerySet':
        """
        Return a copy of the current QuerySet.

        Returns:
            A cloned ReadOnlyQuerySet instance.
        """
        clone = super()._clone()
        return clone

    def all(self) -> 'ReadOnlyQuerySet':
        """
        Return a new QuerySet containing all objects.

        Returns:
            ReadOnlyQuerySet containing all model objects.

        Note:
            While this method returns a QuerySet, instances returned from it
            should have their save() method overridden to prevent modifications.
        """
        return super().all()  # type: ignore[return-value]

    def filter(self, *args: Any, **kwargs: Any) -> 'ReadOnlyQuerySet':
        """
        Return a new QuerySet with objects matching the given parameters.

        Args:
            *args: Q objects for filtering.
            **kwargs: Field lookup parameters.

        Returns:
            ReadOnlyQuerySet with filtered objects.

        Note:
            While this method returns a QuerySet, instances returned from it
            should have their save() method overridden to prevent modifications.
        """
        return super().filter(*args, **kwargs)  # type: ignore[return-value]

    def exclude(self, *args: Any, **kwargs: Any) -> 'ReadOnlyQuerySet':
        """
        Return a new QuerySet with objects not matching the given parameters.

        Args:
            *args: Q objects for exclusion.
            **kwargs: Field lookup parameters.

        Returns:
            ReadOnlyQuerySet with excluded objects.

        Note:
            While this method returns a QuerySet, instances returned from it
            should have their save() method overridden to prevent modifications.
        """
        return super().exclude(*args, **kwargs)  # type: ignore[return-value]

    def get(self, *args: Any, **kwargs: Any) -> 'Model':
        """
        Return the object matching the given lookup parameters.

        Args:
            *args: Q objects for lookup.
            **kwargs: Field lookup parameters.

        Returns:
            The matching model instance.

        Raises:
            Model.DoesNotExist: If no matching object is found.
            Model.MultipleObjectsReturned: If multiple objects are returned.

        Note:
            While this method returns a model instance, it should have its
            save() method overridden to prevent modifications.
        """
        return super().get(*args, **kwargs)


class ReadOnlyManager(models.Manager.from_queryset(ReadOnlyQuerySet)):  # type: ignore[misc]
    """
    Manager that prevents all write operations on a model.

    This manager extends ReadOnlyQuerySet and provides the same read-only
    functionality. Attach this manager to models that should be completely
    immutable, preventing any create, update, or delete operations.

    Additionally provides caching methods for catalog/reference data to avoid
    repeated database queries on read-only tables.

    Example:
        >>> class ReferenceData(models.Model):
        ...     code = models.CharField(max_length=10, primary_key=True)
        ...     description = models.CharField(max_length=100)
        ...     objects = ReadOnlyManager()
        ...
        >>> ReferenceData.objects.create(code="A", description="Test")
        RuntimeError: Cannot perform write operation on read-only model...
        >>> ReferenceData.objects.all_cached()  # Returns cached data
    """

    # Cache timeout for catalog data (5 minutes by default)
    CACHE_TIMEOUT = 300

    def _get_cache_key(self) -> str:
        """
        Generate cache key for this model.

        Returns:
            str: Cache key in format 'catalog:{model_name}:all'
        """
        model_name = self.model._meta.model_name
        return f'catalog:{model_name}:all'

    def all_cached(self) -> list['Model']:
        """
        Return all objects from cache or database.

        First attempts to retrieve all objects from cache. If cache miss,
        loads from database and caches the result for future requests.

        This is particularly useful for catalog/reference tables that are
        read-only and change infrequently.

        Returns:
            list[Model]: List of all model instances.

        Example:
            >>> estatus_list = TramiteEstatus.objects.all_cached()
            >>> all_estatus = {e.id: e.estatus for e in estatus_list}
        """
        cache_key = self._get_cache_key()
        cached_objects = cache.get(cache_key)

        if cached_objects is not None:
            return cached_objects

        # Cache miss - load from database
        objects_list = list(self.all())
        cache.set(cache_key, objects_list, self.CACHE_TIMEOUT)
        return objects_list

    def get_cached(self, pk: int | str) -> 'Model | None':
        """
        Retrieve single object by primary key from cache or database.

        First attempts to retrieve from cache. If cache miss or not found,
        loads from database using get() and caches individual objects.

        This is useful for looking up individual catalog items without
        repeated database queries.

        Args:
            pk: Primary key of the object to retrieve.

        Returns:
            Model | None: The model instance if found, None otherwise.

        Raises:
            Model.DoesNotExist: If object not found in database.

        Example:
            >>> estatus = TramiteEstatus.objects.get_cached(1)
            >>> print(estatus.estatus)
            'iniciado'
        """
        # Try to get from cached list first
        cached_objects = cache.get(self._get_cache_key())
        if cached_objects is not None:
            for obj in cached_objects:
                if obj.pk == pk:
                    return obj

        # Not in cache or cache miss - fetch from database
        try:
            obj = self.get(pk=pk)
            return obj
        except self.model.DoesNotExist:
            return None


class CreateOnlyQuerySet(models.QuerySet):
    """
    QuerySet that allows creation but prevents updates and deletes.

    This QuerySet permits creating new records through create() and bulk_create()
    but blocks update() and delete() operations. This is useful for audit logs,
    transaction records, or any data that should be append-only.

    Read operations (all(), filter(), exclude(), get()) return model instances
    with their save() method overridden to prevent modifications after retrieval.

    Example:
        >>> class AuditLog(models.Model):
        ...     action = models.CharField(max_length=100)
        ...     timestamp = models.DateTimeField(auto_now_add=True)
        ...     objects = CreateOnlyManager.as_manager()
        ...
        >>> AuditLog.objects.create(action="login")  # Works
        >>> log = AuditLog.objects.first()
        >>> log.action = "logout"  # Works in memory
        >>> log.save()  # Raises RuntimeError
    """

    def update(self, **kwargs: Any) -> int:
        """
        Update all elements in the current QuerySet.

        Args:
            **kwargs: Field update values.

        Returns:
            Number of rows matched.

        Raises:
            RuntimeError: Always raised since this is a create-only manager.
        """
        raise RuntimeError(
            'Cannot perform update operation on create-only model. '
            'This model is configured as create-only and does not allow modifications '
            'after initial creation.'
        )

    def delete(self) -> tuple[int, dict[str, int]]:
        """
        Delete all objects in the QuerySet.

        Returns:
            Tuple of (number of objects deleted, dictionary with counts per type).

        Raises:
            RuntimeError: Always raised since this is a create-only manager.
        """
        raise RuntimeError(
            'Cannot perform delete operation on create-only model. '
            'This model is configured as create-only and does not allow '
            'deletion of existing records.'
        )

    def update_or_create(
        self,
        defaults: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple['Model', bool]:
        """
        Look up an object with the given kwargs, creating one if necessary.

        Args:
            defaults: Dictionary of field values to use when creating.
            **kwargs: Lookup parameters.

        Returns:
            Tuple of (object, created boolean).

        Raises:
            RuntimeError: Always raised since update is not allowed.
        """
        raise RuntimeError(
            'Cannot perform update operation on create-only model. '
            'This model is configured as create-only and does not allow modifications '
            'after initial creation.'
        )

    def _clone(self) -> 'CreateOnlyQuerySet':
        """
        Return a copy of the current QuerySet.

        Returns:
            A cloned CreateOnlyQuerySet instance.
        """
        clone = super()._clone()
        return clone

    def _wrap_instance_for_read_only(self, instance: T) -> T:
        """
        Wrap a model instance to prevent save operations.

        This method dynamically overrides the save method on the returned
        instance to prevent modifications after retrieval.

        Args:
            instance: The model instance to wrap.

        Returns:
            The same instance with save method overridden.
        """
        original_save = instance.save

        def read_only_save(
            force_insert: bool = False,
            force_update: bool = False,
            using: str | None = None,
            update_fields: list[str] | None = None,
        ) -> None:
            """
            Override save to prevent modifications on create-only models.

            Args:
                force_insert: Force an INSERT operation.
                force_update: Force an UPDATE operation.
                using: Database alias to use.
                update_fields: Fields to update.

            Raises:
                RuntimeError: Always raised to prevent modifications.
            """
            raise RuntimeError(
                'Cannot perform save operation on create-only model instance. '
                'This model is configured as create-only and does not allow '
                'modifications after initial creation.'
            )

        # Override the save method on the instance
        instance.save = read_only_save  # type: ignore[method-assign]

        return instance

    def _fetch_all(self) -> None:
        """
        Fetch all objects from the database and wrap them for read-only.

        This internal method is called when the QuerySet is evaluated.
        We override it to wrap returned instances with our read-only protection.
        """
        super()._fetch_all()

        # Wrap all instances to prevent save operations
        for i, instance in enumerate(self._result_cache):
            self._result_cache[i] = self._wrap_instance_for_read_only(instance)

    def all(self) -> 'CreateOnlyQuerySet':
        """
        Return a new QuerySet containing all objects.

        Returns:
            CreateOnlyQuerySet containing all model objects.

        Note:
            Instances returned from this QuerySet will have their save()
            method overridden to prevent modifications.
        """
        return super().all()  # type: ignore[return-value]

    def filter(self, *args: Any, **kwargs: Any) -> 'CreateOnlyQuerySet':
        """
        Return a new QuerySet with objects matching the given parameters.

        Args:
            *args: Q objects for filtering.
            **kwargs: Field lookup parameters.

        Returns:
            CreateOnlyQuerySet with filtered objects.

        Note:
            Instances returned from this QuerySet will have their save()
            method overridden to prevent modifications.
        """
        return super().filter(*args, **kwargs)  # type: ignore[return-value]

    def exclude(self, *args: Any, **kwargs: Any) -> 'CreateOnlyQuerySet':
        """
        Return a new QuerySet with objects not matching the given parameters.

        Args:
            *args: Q objects for exclusion.
            **kwargs: Field lookup parameters.

        Returns:
            CreateOnlyQuerySet with excluded objects.

        Note:
            Instances returned from this QuerySet will have their save()
            method overridden to prevent modifications.
        """
        return super().exclude(*args, **kwargs)  # type: ignore[return-value]

    def get(self, *args: Any, **kwargs: Any) -> 'Model':
        """
        Return the object matching the given lookup parameters.

        Args:
            *args: Q objects for lookup.
            **kwargs: Field lookup parameters.

        Returns:
            The matching model instance with save method overridden.

        Raises:
            Model.DoesNotExist: If no matching object is found.
            Model.MultipleObjectsReturned: If multiple objects are returned.

        Note:
            The returned instance will have its save() method overridden
            to prevent modifications.
        """
        instance = super().get(*args, **kwargs)
        return self._wrap_instance_for_read_only(instance)


class CreateOnlyManager(models.Manager.from_queryset(CreateOnlyQuerySet)):  # type: ignore[misc]
    """
    Manager that allows creation but prevents updates and deletes.

    This manager extends CreateOnlyQuerySet and provides the same create-only
    functionality. Attach this manager to models that should be append-only,
    such as audit logs, transaction records, or any immutable history data.

    Example:
        >>> class TransactionLog(models.Model):
        ...     transaction_id = models.CharField(max_length=50)
        ...     amount = models.DecimalField(max_digits=10, decimal_places=2)
        ...     objects = CreateOnlyManager()
        ...
        >>> log = TransactionLog.objects.create(
        ...     transaction_id="TXN001", amount=100.00
        ... )  # Works
        >>> TransactionLog.objects.update(amount=200.00)
        RuntimeError: Cannot perform update operation...
    """

    pass
