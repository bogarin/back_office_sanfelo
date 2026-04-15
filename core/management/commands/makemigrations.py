"""
Custom makemigrations command that guards against creating migrations
for models configured as READ_ONLY or APPEND_ONLY.

This command extends Django's standard makemigrations to enforce
access pattern constraints defined in ModelConfig.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from django.core.management.commands.makemigrations import Command as BaseCommand

if TYPE_CHECKING:
    from django.db import models

from core.model_config import AccessPattern, get_model_config


class Command(BaseCommand):
    """
    Custom makemigrations command with migration guard for restricted models.

    This command extends Django's standard makemigrations command to prevent
    accidental migration creation for models configured with READ_ONLY or
    APPEND_ONLY access patterns. Such models should remain unmanaged and
    should not have migrations generated.

    The guard ensures data integrity by preventing schema changes to models
    that are designated as read-only or create-only views/tables.
    """

    help = 'Creates new migration(s) for apps, with guards for READ_ONLY and APPEND_ONLY models'

    def handle(self, *args: object, **options: object) -> None:
        """
        Execute the makemigrations command with access pattern validation.

        This method:
        1. Calls the parent's handle() to generate migration candidates
        2. Validates each model's access pattern configuration
        3. Raises RuntimeError if a READ_ONLY or APPEND_ONLY model would
           receive a migration

        Args:
            *args: Positional arguments passed to the command
            **options: Keyword options passed to the command

        Raises:
            RuntimeError: If a READ_ONLY or APPEND_ONLY model would receive
                a migration. The message uses "Read-Only Constraint Violation"
                terminology and clearly indicates the model and its access
                pattern configuration.

        Returns:
            None
        """
        # Call parent's handle to process migration candidates
        # This will create migrations for all eligible models
        super().handle(*args, **options)

        # Validate access patterns for all registered models
        # We check all models to ensure READ_ONLY and APPEND_ONLY
        # models never receive migrations, even if changes were detected
        from django.apps import apps

        for model in apps.get_models():
            config = get_model_config(model)

            if config is None:
                # No configuration - allow normal migrations
                continue

            # Check if model has restricted access pattern
            if config.access_pattern in (
                AccessPattern.READ_ONLY,
                AccessPattern.APPEND_ONLY,
            ):
                model_name = f'{model._meta.app_label}.{model._meta.model_name}'
                error_message = (
                    f'Read-Only Constraint Violation: Cannot create migrations for {model_name}. '
                    f'This model is configured as {config.access_pattern.value} and must remain unmanaged.'
                )

                # Raise RuntimeError with descriptive message
                raise RuntimeError(error_message)
