"""
Schema Validator Utility

Validates that Django models are synchronized with the external SQL schema.
Run with: uv run python -m core.schema_validator
"""

import sys
from typing import Any

from django.conf import settings
from django.db import connection


class SchemaValidator:
    """Validates Django models against PostgreSQL schema."""

    # Mapping of Django field types to PostgreSQL types
    TYPE_MAPPING = {
        'AutoField': 'integer',
        'BigIntegerField': 'bigint',
        'BinaryField': 'bytea',
        'BooleanField': 'boolean',
        'CharField': 'character varying',
        'DateField': 'date',
        'DateTimeField': 'timestamp without time zone',
        'DecimalField': 'numeric',
        'DurationField': 'interval',
        'FileField': 'character varying',
        'FilePathField': 'character varying',
        'FloatField': 'double precision',
        'IntegerField': 'integer',
        'GenericIPAddressField': 'character varying',
        'NullBooleanField': 'boolean',
        'PositiveIntegerField': 'integer',
        'PositiveSmallIntegerField': 'smallint',
        'SlugField': 'character varying',
        'SmallIntegerField': 'smallint',
        'TextField': 'text',
        'TimeField': 'time without time zone',
        'URLField': 'character varying',
        'UUIDField': 'uuid',
        'ForeignKey': 'integer',
        'OneToOneField': 'integer',
        'ManyToManyField': 'integer',  # junction table
    }

    def __init__(self):
        """Initialize the validator."""
        from django.db import connections

        self.errors: list[str] = []
        self.warnings: list[str] = []
        # Use business connection (PostgreSQL) for schema validation
        self.connection = connections['business']

    def get_sql_columns(self, table_name: str) -> list[dict[str, Any]]:
        """Get column information from PostgreSQL.

        Args:
            table_name: Name of the table to inspect

        Returns:
            List of dictionaries with column information
        """
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """,
                [table_name],
            )
            columns = cursor.fetchall()

            return [
                {
                    'name': col[0],
                    'data_type': col[1],
                    'max_length': col[2],
                    'nullable': col[3] == 'YES',
                    'default': col[4],
                }
                for col in columns
            ]

    def get_django_fields(self, model_class: type) -> list[dict[str, Any]]:
        """Get field information from Django model.

        Args:
            model_class: Django model class

        Returns:
            List of dictionaries with field information
        """
        fields = []
        for field in model_class._meta.get_fields():
            # Skip reverse relations
            if field.auto_created:
                continue

            field_info = {
                'name': field.name,
                'type': field.__class__.__name__,
                'nullable': field.null,
                'blank': field.blank,
                'default': field.default if field.default != 'NOT PROVIDED' else None,
            }

            # Get max_length for CharField
            if hasattr(field, 'max_length') and field.max_length is not None:
                field_info['max_length'] = field.max_length

            # Get max_digits and decimal_places for DecimalField
            if field.__class__.__name__ == 'DecimalField':
                field_info['max_digits'] = field.max_digits
                field_info['decimal_places'] = field.decimal_places

            fields.append(field_info)

        return fields

    def compare_types(self, django_type: str, sql_type: str) -> bool:
        """Compare Django field type with PostgreSQL type.

        Args:
            django_type: Django field type name
            sql_type: PostgreSQL data type

        Returns:
            True if types are compatible, False otherwise
        """
        # Map Django type to SQL type
        mapped_type = self.TYPE_MAPPING.get(django_type, sql_type)

        # Direct match
        if mapped_type == sql_type:
            return True

        # Character varying can match any length
        if mapped_type == 'character varying' and sql_type.startswith('character varying'):
            return True

        # Integer can match serial
        if mapped_type == 'integer' and sql_type == 'integer':
            return True

        return False

    def validate_model(self, model_class: type, table_name: str) -> None:
        """Validate a single Django model against SQL schema.

        Args:
            model_class: Django model class to validate
            table_name: Name of the SQL table to compare against
        """
        print(f'\nValidating: {model_class.__name__} → {table_name}')

        # Get SQL columns
        sql_columns = self.get_sql_columns(table_name)
        if not sql_columns:
            self.errors.append(f"Table '{table_name}' not found in database")
            return

        # Get Django fields
        django_fields = self.get_django_fields(model_class)

        # Create maps for comparison
        sql_map = {col['name']: col for col in sql_columns}
        django_map = {field['name']: field for field in django_fields}

        # Check for fields in Django but not in SQL
        for field_name, field in django_map.items():
            if field_name not in sql_map:
                # Skip auto fields (id)
                if field_name == 'id':
                    continue
                self.errors.append(
                    f"Field '{field_name}' exists in {model_class.__name__} "
                    f"but not in table '{table_name}'"
                )
                continue

            # Compare column properties
            sql_col = sql_map[field_name]

            # Compare types
            if not self.compare_types(field['type'], sql_col['data_type']):
                self.errors.append(
                    f'Type mismatch for {model_class.__name__}.{field_name}: '
                    f'Django={field["type"]}, SQL={sql_col["data_type"]}'
                )

            # Compare nullability
            # Note: Django null=False means NOT NULL in SQL
            if not field['nullable'] and sql_col['nullable']:
                self.warnings.append(
                    f'Nullable mismatch for {model_class.__name__}.{field_name}: '
                    f'Django=NOT NULL, SQL=nullable'
                )

            # Compare max_length
            if 'max_length' in field and sql_col['max_length'] is not None:
                if field['max_length'] != sql_col['max_length']:
                    self.errors.append(
                        f'Max length mismatch for {model_class.__name__}.{field_name}: '
                        f'Django={field["max_length"]}, SQL={sql_col["max_length"]}'
                    )

        # Check for columns in SQL but not in Django
        for col_name, col in sql_map.items():
            if col_name not in django_map:
                # Skip id (auto field)
                if col_name == 'id':
                    continue
                self.warnings.append(
                    f"Column '{col_name}' exists in table '{table_name}' "
                    f'but not in {model_class.__name__}'
                )

    def validate_all(self) -> bool:
        """Validate all registered models.

        Returns:
            True if validation passed (no errors), False otherwise
        """
        from django.apps import apps

        print('=' * 60)
        print('SCHEMA VALIDATION REPORT')
        print('=' * 60)

        # Get all models
        for model in apps.get_models():
            # Skip models from third-party apps
            if model._meta.app_label in [
                'admin',
                'auth',
                'contenttypes',
                'sessions',
                'sites',
            ]:
                continue

            # Get table name
            table_name = model._meta.db_table

            # Validate model
            self.validate_model(model, table_name)

        # Print summary
        print('\n' + '=' * 60)
        print('SUMMARY')
        print('=' * 60)

        if self.warnings:
            print(f'\n⚠️  Warnings ({len(self.warnings)}):')
            for warning in self.warnings:
                print(f'  - {warning}')

        if self.errors:
            print(f'\n❌ Errors ({len(self.errors)}):')
            for error in self.errors:
                print(f'  - {error}')

        if not self.errors and not self.warnings:
            print('\n✅ All models are synchronized with the database schema!')

        return len(self.errors) == 0


def main():
    """Main entry point for schema validator."""
    # Check if business database is PostgreSQL
    if not settings.DATABASES.get('business', {}).get('ENGINE', '').startswith('postgresql'):
        print('❌ Schema validation only works with PostgreSQL business database')
        sys.exit(1)

    validator = SchemaValidator()
    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    import os

    import django

    # Configure Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sanfelipe.settings')
    django.setup()

    main()
