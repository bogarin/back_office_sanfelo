"""
Database router for multi-database configuration.

Routes business apps (tramites, catalogos, costos, bitacora) to PostgreSQL
while keeping Django's auth, admin, sessions on SQLite.
"""

from typing import Optional


class BusinessDatabaseRouter:
    """Router for business apps to PostgreSQL."""

    # Apps that store business data in PostgreSQL
    BUSINESS_APPS = {"tramites", "catalogos", "costos", "bitacora"}

    def db_for_read(self, model: type) -> Optional[str]:
        """Route read queries to business DB for business apps."""
        if model._meta.app_label in self.BUSINESS_APPS:
            return "business"
        return "default"

    def db_for_write(self, model: type) -> Optional[str]:
        """Route write queries to business DB for business apps."""
        if model._meta.app_label in self.BUSINESS_APPS:
            return "business"
        return "default"

    def allow_relation(self, obj1: type, obj2: type) -> Optional[bool]:
        """Allow relations only within the same database."""
        # Allow relations within business apps (same PostgreSQL)
        if (
            obj1._meta.app_label in self.BUSINESS_APPS
            and obj2._meta.app_label in self.BUSINESS_APPS
        ):
            return True
        # Allow relations within auth apps (same SQLite)
        if (
            obj1._meta.app_label not in self.BUSINESS_APPS
            and obj2._meta.app_label not in self.BUSINESS_APPS
        ):
            return True
        # Cross-database relations not allowed
        return False

    def allow_migrate(
        self, db: str, app_label: str, model_name: str | None = None, **hints
    ) -> bool:
        """Only run migrations on SQLite for Django auth/admin."""
        # Business apps use managed=False, no migrations needed
        if app_label in self.BUSINESS_APPS:
            return False
        # Only migrate default (SQLite) for auth/admin
        return db == "default"
