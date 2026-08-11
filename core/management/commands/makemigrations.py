"""
Custom makemigrations command that warns about migrations
for models configured as READ_ONLY or APPEND_ONLY.

This command extends Django's standard makemigrations to check
access pattern constraints defined in ModelConfig.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import apps
from django.core.management.commands.makemigrations import Command as BaseCommand

if TYPE_CHECKING:
    pass

from core.model_config import AccessPattern, get_model_config


class Command(BaseCommand):
    """
    Custom makemigrations command with migration guard for restricted models.

    This command extends Django's standard makemigrations command to warn
    about migration creation for models configured with READ_ONLY or
    APPEND_ONLY access patterns. Such models should remain unmanaged and
    should not have migrations generated.

    The guard warns about potential data integrity risks from schema changes
    to models that are designated as read-only or create-only views/tables.
    """

    help = 'Creates new migration(s) for apps, with guards for READ_ONLY and APPEND_ONLY models'

    def handle(self, *args: object, **options: object) -> None:
        """
        Execute the makemigrations command with access pattern validation.

        This method:
        1. Calls the parent's handle() to generate migration candidates
        2. Validates each model's access pattern configuration
        3. Warns if a READ_ONLY or APPEND_ONLY model would receive a migration

        Args:
            *args: Positional arguments passed to the command
            **options: Keyword options passed to the command

        Returns:
            None
        """
        # Call parent's handle to process migration candidates
        super().handle(*args, **options)

        # Warn about READ_ONLY and APPEND_ONLY models with existing migrations
        for model in apps.get_models():
            config = get_model_config(model)

            if config is None:
                continue

            if config.access_pattern in (
                AccessPattern.READ_ONLY,
                AccessPattern.APPEND_ONLY,
            ):
                model_name = f'{model._meta.app_label}.{model._meta.model_name}'
                self.stderr.write(
                    self.style.WARNING(  # type: ignore[attr-defined]
                        f'⚠ {model_name} is configured as '
                        f'{config.access_pattern.value}. '
                        f'Schema changes must be managed in the database '
                        f'repo, not via Django migrations.'
                    )
                )
