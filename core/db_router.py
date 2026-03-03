from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import Model


class BaseRouter:
    def db_for_read(self, model: type[Model], **hints: object) -> str | None:
        raise NotImplementedError

    def db_for_write(self, model: type[Model], **hints: object) -> str | None:
        raise NotImplementedError

    def allow_relation(
        self,
        obj1: Model | type[Model],
        obj2: Model | type[Model],
        **hints: object,
    ) -> bool | None:
        raise NotImplementedError

    def allow_migrate(
        self,
        db: str,
        app_label: str,
        model_name: str | None = None,
        **hints: object,
    ) -> bool:
        raise NotImplementedError


class TestRouter(BaseRouter):
    def db_for_read(self, model: type[Model], **hints: object) -> str | None:
        return 'default'

    def db_for_write(self, model: type[Model], **hints: object) -> str | None:
        return 'default'

    def allow_relation(
        self,
        obj1: Model | type[Model],
        obj2: Model | type[Model],
        **hints: object,
    ) -> bool | None:
        return True

    def allow_migrate(
        self,
        db: str,
        app_label: str,
        model_name: str | None = None,
        **hints: object,
    ) -> bool:
        return db == 'default'


class MultiDatabaseRouter:
    """
    Custom database router for managing multi-database configuration.

    This router intelligently routes database operations between SQLite (for
    Django's built-in authentication and session management) and PostgreSQL
    (for business domain models).

    Attributes:
        AUTH_APPS: Set of Django built-in apps that use SQLite
        BUSINESS_APPS: Set of business domain apps that use PostgreSQL
        AUTH_DB: Database alias for auth data (SQLite)
        BUSINESS_DB: Database alias for business data (PostgreSQL)

    Example:
        >>> router = MultiDatabaseRouter()
        >>> router.db_for_read(User)
        'default'
        >>> router.db_for_read(Tramite)
        'business'
    """

    # Django built-in apps that use SQLite (auth data)
    AUTH_APPS: frozenset[str] = frozenset(
        {
            'auth',
            'contenttypes',
            'admin',
            'sessions',
            'messages',
            'staticfiles',
            'debug_toolbar',  # Debug tools in SQLite
        }
    )

    # Business domain apps that use PostgreSQL (business data)
    BUSINESS_APPS: frozenset[str] = frozenset(
        {
            'catalogos',
            'costos',
            'tramites',
            'core',
        }
    )

    # Database aliases
    AUTH_DB: str = 'default'
    BUSINESS_DB: str = 'business'

    def _is_auth_app(self, app_label: str) -> bool:
        """
        Check if an app belongs to the auth category.

        Args:
            app_label: The Django app label to check

        Returns:
            True if the app is an auth app, False otherwise
        """
        return app_label in self.AUTH_APPS

    def _is_business_app(self, app_label: str) -> bool:
        """
        Check if an app belongs to the business category.

        Args:
            app_label: The Django app label to check

        Returns:
            True if the app is a business app, False otherwise
        """
        return app_label in self.BUSINESS_APPS

    def _get_db_for_model(self, app_label: str) -> str | None:
        """
        Determine the appropriate database for a given app.

        Args:
            app_label: The Django app label

        Returns:
            The database alias ('default' or 'business'), or None if
            the app is not recognized
        """
        if self._is_auth_app(app_label):
            return self.AUTH_DB
        if self._is_business_app(app_label):
            return self.BUSINESS_DB
        # Unknown app - let Django decide (return None)
        return None

    def db_for_read(self, model: type[Model], **hints: object) -> str | None:
        """
        Suggest the database to read from for a model.

        This method is called by Django's ORM when performing read queries.
        It routes business models to PostgreSQL and auth models to SQLite.

        Args:
            model: The model class being queried
            **hints: Additional hints that may help determine routing

        Returns:
            The database alias to use for reading, or None to use default routing

        Example:
            >>> router.db_for_read(User)
            'default'
            >>> router.db_for_read(Tramite)
            'business'
        """
        # Check hints first for model class or instance
        if 'model' in hints:
            model = hints['model']  # type: ignore[assignment]

        app_label = getattr(model, '_meta', {}).app_label  # type: ignore[attr-defined]
        return self._get_db_for_model(app_label)

    def db_for_write(self, model: type[Model], **hints: object) -> str | None:
        """
        Suggest the database to write to for a model.

        This method is called by Django's ORM when performing write queries
        (INSERT, UPDATE, DELETE). It uses the same routing logic as reads.

        Args:
            model: The model class being modified
            **hints: Additional hints that may help determine routing

        Returns:
            The database alias to use for writing, or None to use default routing

        Example:
            >>> router.db_for_write(User)
            'default'
            >>> router.db_for_write(Tramite)
            'business'
        """
        # Check hints first for model class or instance
        if 'model' in hints:
            model = hints['model']  # type: ignore[assignment]

        app_label = getattr(model, '_meta', {}).app_label  # type: ignore[attr-defined]
        return self._get_db_for_model(app_label)

    def allow_relation(
        self,
        obj1: Model | type[Model],
        obj2: Model | type[Model],
        **hints: object,
    ) -> bool | None:
        """
        Determine if a relation between two models is allowed.

        Relations (Foreign Keys, Many-to-Many) are only allowed within the
        same database to prevent cross-database joins, which are not
        supported by Django.

        Args:
            obj1: First model in the relation
            obj2: Second model in the relation
            **hints: Additional hints that may help determine routing

        Returns:
            True if relation is allowed, False if not, None to let Django decide

        Note:
            Cross-database relations (e.g., User → Tramite) are not supported
            and will return False. Use database-level triggers or application
            logic instead.

        Example:
            >>> # Same database - allowed
            >>> router.allow_relation(User(), UserGroup())
            True
            >>> # Cross-database - not allowed
            >>> router.allow_relation(User(), Tramite())
            False
        """
        # Handle both model instances and model classes
        app_label1 = (
            obj1._meta.app_label  # type: ignore[attr-defined]
            if hasattr(obj1, '_meta')
            else getattr(obj1, 'app_label', '')
        )
        app_label2 = (
            obj2._meta.app_label  # type: ignore[attr-defined]
            if hasattr(obj2, '_meta')
            else getattr(obj2, 'app_label', '')
        )

        # Both in auth DB
        if self._is_auth_app(app_label1) and self._is_auth_app(app_label2):
            return True

        # Both in business DB
        if self._is_business_app(app_label1) and self._is_business_app(app_label2):
            return True

        # Cross-database relations not allowed
        # Prevents User → Tramite FK which would cause runtime errors
        return False

    def allow_migrate(
        self,
        db: str,
        app_label: str,
        model_name: str | None = None,
        **hints: object,
    ) -> bool:
        """
        Determine if migrations should run for a model on a database.

        This method controls which database receives migrations for which apps.
        Auth apps get migrations on SQLite; business apps don't get migrations
        on any database (they use managed=False).

        Args:
            db: The database alias being checked
            app_label: The Django app label
            model_name: The name of the model being migrated (optional)
            **hints: Additional hints that may help determine routing

        Returns:
            True if migrations should run, False otherwise

        Note:
            Business apps use managed=False and are maintained externally,
            so Django should not create or modify their tables.

        Example:
            >>> # Auth app on SQLite - allow migration
            >>> router.allow_migrate('default', 'auth', 'user')
            True
            >>> # Auth app on PostgreSQL - block migration
            >>> router.allow_migrate('business', 'auth', 'user')
            False
            >>> # Business app on any DB - block migration
            >>> router.allow_migrate('default', 'tramites', 'tramite')
            False
        """
        # Business apps: never migrate (managed=False, external DB)
        if self._is_business_app(app_label):
            return False

        # Auth apps: only migrate on SQLite (default)
        if self._is_auth_app(app_label):
            return db == self.AUTH_DB

        # Unknown app: follow default Django behavior
        # Return None to let the next router decide
        return True

    def allow_syncdb(self, db: str, model: type[Model]) -> bool:
        """
        Legacy method for Django < 1.7. Kept for backward compatibility.

        This method is deprecated in favor of allow_migrate but is included
        for compatibility with older Django versions or third-party apps that
        may still call it.

        Args:
            db: The database alias being checked
            model: The model class

        Returns:
            True if syncdb should run, False otherwise
        """
        return self.allow_migrate(db, model._meta.app_label)  # type: ignore[attr-defined]
