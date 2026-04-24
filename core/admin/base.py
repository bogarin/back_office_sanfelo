"""Base ModelAdmin classes for the Django admin interface.

Provides common configuration and specialized admin classes:
- BaseModelAdmin: Base configuration for all model admins
- ReadOnlyModelAdmin: For read-only models
- ActionableReadOnlyMixin: Enables actions on read-only models
"""

from django.contrib import admin


# =============================================================================
# Custom ModelAdmin Base Classes
# =============================================================================


class BaseModelAdmin(admin.ModelAdmin):
    """Base ModelAdmin with common configuration for all models."""

    save_on_top = True
    # Pagination
    list_per_page = 25
    list_max_show_all = 100


class ReadOnlyModelAdmin(BaseModelAdmin):
    """ModelAdmin for read-only models."""

    list_editable = ()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ActionableReadOnlyMixin:
    """Enables Django admin actions on a ReadOnlyModelAdmin.

    ReadOnlyModelAdmin blocks all write operations by design.
    This mixin selectively re-enables the action infrastructure
    (action dropdown, checkbox selection) WITHOUT enabling
    the change form or inline editing.

    Django uses ``has_change_permission(request, obj=None)`` in two contexts:

    1. **obj=None** (changelist): decides whether to show the action dropdown.
    2. **obj=instance** (change form): decides whether to allow editing.

    This mixin allows context 1 (actions work) and blocks context 2 (readonly).

    Usage::

        class MyAdmin(ActionableReadOnlyMixin, ReadOnlyModelAdmin):
            actions = ('my_action',)

            @admin.action(description='Do something')
            def my_action(self, request, queryset):
                ...

    Important:
        MRO order matters. ``ActionableReadOnlyMixin`` must come BEFORE
        ``ReadOnlyModelAdmin`` so that its ``has_change_permission`` takes
        precedence.
    """

    def has_change_permission(self, request, obj=None):
        """Allow actions on changelist, block the change form.

        Returns True when obj is None (changelist context) so Django
        renders the action dropdown.  Returns False when obj is an
        instance to keep the change form truly read-only.
        """
        return obj is None
