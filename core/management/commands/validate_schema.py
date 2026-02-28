"""Django management command to validate schema against external PostgreSQL database."""

from django.core.management.base import BaseCommand

from core.schema_validator import SchemaValidator


class Command(BaseCommand):
    """Validate Django models against external PostgreSQL schema."""

    help = 'Validate Django models against external PostgreSQL schema'

    def handle(self, *args, **options):
        """Execute schema validation."""
        validator = SchemaValidator()
        success = validator.validate_all()
