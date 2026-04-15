"""Model-based database router for Django.

This router provides fine-grained control over database routing at the model
level, allowing models within the same Django app to route to different
databases. It uses the ModelConfig system to determine routing behavior.

Example:
    >>> from core.model_config import get_model_config, register_model_config
    >>> from django.contrib.auth.models import User
    >>> register_model_config(User, 'default', allow_migrations=True)
    >>> router = ModelBasedRouter()
    >>> router.db_for_read(User)
    'default'
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.model_config import get_model_config, ModelConfig

if TYPE_CHECKING:
    from django.db.models import Model


class ModelBasedRouter:
    """Database router that uses model-level configuration.

    This router routes database operations based on individual model
    configuration rather than app labels. This enables mixed models within
    the same Django app to use different databases.

    Key features:
        - Model-level routing precision
        - Prevention of cross-database relationships
        - Fine-grained migration control
        - Self-documenting through explicit configuration

    Example:
        >>> router = ModelBasedRouter()
        >>> router.db_for_read(MyModel)
        'backend'
    """

    def db_for_read(self, model: type[Model], **hints: object) -> str | None:
        """Suggest the database to read from for a model.

        This method is called by Django's ORM when performing read queries.
        It uses the model's configuration to determine the appropriate
        database alias. Unregistered models default to 'default' database.

        Args:
            model: The model class being queried
            **hints: Additional hints that may help determine routing

        Returns:
            The configured database alias, or 'default' if no configuration found

        Example:
            >>> router.db_for_read(MyModel)
            'backend'
            >>> router.db_for_read(UnconfiguredModel)
            'default'
        """
        config = get_model_config(model)
        if config is not None:
            return config.db_alias
        return 'default'  # Unregistered models route to default database

    def db_for_write(self, model: type[Model], **hints: object) -> str | None:
        """Suggest the database to write to for a model.

        This method is called by Django's ORM when performing write queries
        (INSERT, UPDATE, DELETE). It uses the same routing logic as reads.
        Unregistered models default to 'default' database.

        Args:
            model: The model class being modified
            **hints: Additional hints that may help determine routing

        Returns:
            The configured database alias, or 'default' if no configuration found

        Example:
            >>> router.db_for_write(MyModel)
            'backend'
            >>> router.db_for_write(UnconfiguredModel)
            'default'
        """
        config = get_model_config(model)
        if config is not None:
            return config.db_alias
        return 'default'  # Unregistered models route to default database

    def allow_relation(
        self,
        obj1: Model | type[Model],
        obj2: Model | type[Model],
        **hints: object,
    ) -> bool:
        """Determine if a relation between two models is allowed.

        Relations (Foreign Keys, Many-to-Many) are only allowed if both
        models use the same database alias. This prevents cross-database
        joins, which are not supported by Django and would cause runtime errors.

        Args:
            obj1: First model in the relation
            obj2: Second model in the relation
            **hints: Additional hints that may help determine routing

        Returns:
            True if both models have the same db_alias, False otherwise

        Note:
            Cross-database relations are explicitly blocked to maintain data
            integrity and prevent runtime errors. Use database-level triggers
            or application logic for cross-database data synchronization.

        Example:
            >>> # Same database - allowed
            >>> router.allow_relation(ModelA(), ModelB())
            True
            >>> # Different databases - not allowed
            >>> router.allow_relation(SQLiteModel(), PostgresModel())
            False
        """
        # Get the actual model classes from instances or classes
        model1 = obj1 if isinstance(obj1, type) else type(obj1)
        model2 = obj2 if isinstance(obj2, type) else type(obj2)

        config1 = get_model_config(model1)
        config2 = get_model_config(model2)

        # Both models are unregistered - let Django decide (likely same DB for auth models)
        if config1 is None and config2 is None:
            return True

        # One model is registered but not the other - can't guarantee same DB
        if config1 is None or config2 is None:
            return False

        # Both models are registered - allow only if same database
        return config1.db_alias == config2.db_alias

    def allow_migrate(
        self,
        db: str,
        app_label: str,
        model_name: str | None = None,
        **hints: object,
    ) -> bool:
        """Determine if migrations should run for a model on a database.

        This method controls which database receives migrations for which models.
        It uses the model's configuration to determine if Django should manage
        the schema.

        Args:
            db: The database alias being checked
            app_label: The Django app label
            model_name: The name of the model being migrated (optional)
            **hints: Additional hints that may help determine routing

        Returns:
            The configured allow_migrations flag, or True if no configuration

        Note:
            Models with managed=False should have allow_migrations=False
            to prevent Django from attempting to create or modify tables
            that are managed externally.

        Example:
            >>> # Managed model - allow migrations
            >>> router.allow_migrate('backend', 'myapp', 'MyModel')
            True
            >>> # External model - block migrations
            >>> router.allow_migrate('backend', 'myapp', 'ExternalModel')
            False
        """
        # Try to get the model from hints
        if 'model' in hints:
            model = hints['model']
            if model is not None and isinstance(model, type):
                config = get_model_config(model)
                if config is not None:
                    return config.allow_migrations

        # If no model in hints or no configuration, allow default behavior
        return True
