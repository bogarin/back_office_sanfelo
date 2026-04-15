"""
Model configuration system for multi-database routing.

This module provides a decorator-based system to configure Django models
for multi-database access patterns, including read-only, full access,
and create-only patterns.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class AccessPattern(StrEnum):
    """Enum defining database access patterns for models.

    This enum controls what types of database operations are permitted
    for a given model when routed to a specific database.

    Attributes:
        FULL_ACCESS: Model can perform all CRUD operations (Create, Read, Update, Delete)
        READ_ONLY: Model can only perform read operations, no writes allowed
        APPEND_ONLY: Model can perform read and create operations, but updates and deletes are forbidden

    Example:
        >>> from core.model_config import AccessPattern
        >>> pattern = AccessPattern.FULL_ACCESS
        >>> pattern.value
        'full_access'
    """

    FULL_ACCESS = 'full_access'
    READ_ONLY = 'read_only'
    APPEND_ONLY = 'append_only'


@dataclass(frozen=True)
class ModelConfig:
    """Configuration dataclass for a Django model.

    This immutable dataclass stores the routing configuration for a specific
    model, including database alias, access pattern, and migration settings.

    Attributes:
        db_alias: The Django database alias to route this model to (e.g., 'default', 'backend')
        access_pattern: The AccessPattern defining permitted operations
        allow_migrations: Whether Django migrations should be generated and applied for this model

    Example:
        >>> from core.model_config import ModelConfig, AccessPattern
        >>> config = ModelConfig('default', AccessPattern.READ_ONLY, False)
        >>> config.db_alias
        'default'
        >>> config.access_pattern
        <AccessPattern.READ_ONLY: 'read_only'>
    """

    db_alias: str
    access_pattern: AccessPattern
    allow_migrations: bool


# Global registry mapping model classes to their configurations
# This dict is populated by the @register_model decorator
_model_registry: dict[Any, ModelConfig] = {}


def _is_model_class(model_class: Any) -> bool:
    """Check if a class is a Django Model.

    This is needed because we need to check model inheritance
    at runtime, but django.db.models may not be available in
    all contexts.

    Args:
        model_class: The class to check

    Returns:
        bool: True if it's a Django Model subclass, False otherwise
    """
    # Check if the class has a _meta attribute (Django Models have this)
    return hasattr(model_class, '_meta')


def register_model(
    db_alias: str,
    access_pattern: AccessPattern,
    allow_migrations: bool,
) -> Callable[[type[Any]], type[Any]]:
    """Decorator to register a Django model with its routing configuration.

    This decorator attaches a ModelConfig instance to a model class in the
    global registry, which can then be queried by the database router
    to determine the appropriate database and access pattern.

    The decorator does not modify the model class itself - it simply
    registers the configuration and returns the original class unchanged.

    Args:
        db_alias: The Django database alias for this model
        access_pattern: The AccessPattern defining permitted operations
        allow_migrations: Whether migrations are allowed for this model

    Returns:
        A decorator function that registers the model and returns it unchanged

    Raises:
        TypeError: If applied to a non-model class

    Example:
        >>> from django.db import models
        >>> from core.model_config import register_model, AccessPattern
        >>>
        >>> @register_model('default', AccessPattern.FULL_ACCESS, True)
        >>> class MyModel(models.Model):
        ...     name = models.CharField(max_length=100)

    Note:
        Multiple decorators can be stacked if needed, though only the
        @register_model decorator affects the configuration registry.
    """

    def decorator(model_class: type[Any]) -> type[Any]:
        # Validate that we're decorating a Django model
        if not _is_model_class(model_class):
            raise TypeError(
                f'@register_model can only be applied to Django Model classes, '
                f'got {model_class.__name__} of type {type(model_class)}'
            )

        # Create and store the configuration
        config = ModelConfig(
            db_alias=db_alias,
            access_pattern=access_pattern,
            allow_migrations=allow_migrations,
        )
        _model_registry[model_class] = config

        # Return the original class unchanged (decorator pattern)
        return model_class

    return decorator


def get_model_config(model: type[Any]) -> ModelConfig | None:
    """Retrieve the ModelConfig for a given Django model.

    This function looks up the model in the global registry and returns
    its associated ModelConfig if one exists. If the model has not been
    registered, returns None.

    Args:
        model: The Django model class to look up

    Returns:
        The ModelConfig instance if the model was registered, None otherwise

    Example:
        >>> from core.model_config import get_model_config, AccessPattern
        >>> from myapp.models import MyModel
        >>>
        >>> config = get_model_config(MyModel)
        >>> if config:
        ...     print(f"Routing to: {config.db_alias}")
        ...     print(f"Access: {config.access_pattern}")
        ... else:
        ...     print("Model not registered")

    Note:
        This function uses EAFP (Easier to Ask for Forgiveness than Permission)
        internally - it simply attempts a dictionary lookup rather than checking
        if the key exists first, which is more Pythonic.
    """
    return _model_registry.get(model)
