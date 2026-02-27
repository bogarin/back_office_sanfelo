"""Django Admin global configuration.

Configures the admin interface for the backoffice with:
- Custom site headers and titles
- Dashboard modifications
- Admin actions and permissions
"""

from django.contrib import admin

# Admin Site Configuration
admin.site.site_header = "Backoffice San Felipe"
admin.site.site_title = "Backoffice San Felipe"
admin.site.index_title = "Panel de Administración"


# Custom ModelAdmin Base Classes
class BaseModelAdmin(admin.ModelAdmin):
    """Base ModelAdmin with common configuration for all models."""

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # Enable save_on_top for better UX
        self.save_on_top = True

    class Media:
        css = {
            "all": ("admin/css/custom.css",),
        }


class ReadOnlyModelAdmin(BaseModelAdmin):
    """ModelAdmin for read-only models (like bitacora)."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Catalog base classes for catalog tables
class CatalogBaseAdmin(BaseModelAdmin):
    """Base ModelAdmin for catalog tables with common features."""

    list_per_page = 50
    search_fields = ("nombre", "descripcion")
    save_as = True


# Audit trail mixin for tracking changes
class AuditTrailMixin:
    """Mixin to add audit trail functionality to ModelAdmin.

    Automatically logs changes to the bitacora when model instances are modified.
    """

    def save_model(self, request, obj, form, change):
        """Save model and log changes to bitacora."""
        from datetime import date

        from bitacora.models import Bitacora

        super().save_model(request, obj, form, change)

        if change:
            # Log the change to bitacora
            Bitacora.objects.create(
                usuario_sis=request.user.username
                if hasattr(request, "user")
                else "admin",
                tipo_mov="UPDATE",
                usuario_pc=request.META.get("REMOTE_ADDR", "localhost"),
                fecha=date.today(),
                maquina=request.META.get("REMOTE_HOST", ""),
                observaciones=f"Actualizado {self.model._meta.verbose_name}: {obj}",
            )

    def delete_model(self, request, obj):
        """Delete model and log to bitacora."""
        from datetime import date

        from bitacora.models import Bitacora

        # Log the deletion to bitacora
        Bitacora.objects.create(
            usuario_sis=request.user.username if hasattr(request, "user") else "admin",
            tipo_mov="DELETE",
            usuario_pc=request.META.get("REMOTE_ADDR", "localhost"),
            fecha=date.today(),
            maquina=request.META.get("REMOTE_HOST", ""),
            observaciones=f"Eliminado {self.model._meta.verbose_name}: {obj}",
        )

        super().delete_model(request, obj)


# Custom Admin Actions
def mark_as_active(modeladmin, request, queryset):
    """Admin action to mark selected items as active."""
    rows_updated = queryset.update(activo=True)
    modeladmin.message_user(
        request,
        f"{rows_updated} {((rows_updated == 1) and 'registro') or 'registros'} marcados como activos.",
    )


mark_as_active.short_description = "Marcar como activos"


def mark_as_inactive(modeladmin, request, queryset):
    """Admin action to mark selected items as inactive."""
    rows_updated = queryset.update(activo=False)
    modeladmin.message_user(
        request,
        f"{rows_updated} {((rows_updated == 1) and 'registro') or 'registros'} marcados como inactivos.",
    )


mark_as_inactive.short_description = "Marcar como inactivos"


def mark_urgent(modeladmin, request, queryset):
    """Admin action to mark tramites as urgent."""
    rows_updated = queryset.update(urgente=True)
    modeladmin.message_user(
        request,
        f"{rows_updated} {((rows_updated == 1) and 'trámite') or 'trámites'} marcados como urgentes.",
    )


mark_urgent.short_description = "Marcar como urgentes"


def mark_not_urgent(modeladmin, request, queryset):
    """Admin action to mark tramites as not urgent."""
    rows_updated = queryset.update(urgente=False)
    modeladmin.message_user(
        request,
        f"{rows_updated} {((rows_updated == 1) and 'trámite') or 'trámites'} marcados como no urgentes.",
    )


mark_not_urgent.short_description = "Marcar como no urgentes"


def mark_as_paid(modeladmin, request, queryset):
    """Admin action to mark tramites as paid."""

    rows_updated = queryset.update(pagado=True)
    modeladmin.message_user(
        request,
        f"{rows_updated} {((rows_updated == 1) and 'trámite') or 'trámites'} marcados como pagados.",
    )


mark_as_paid.short_description = "Marcar como pagados"


def mark_as_unpaid(modeladmin, request, queryset):
    """Admin action to mark tramites as unpaid."""
    rows_updated = queryset.update(pagado=False)
    modeladmin.message_user(
        request,
        f"{rows_updated} {((rows_updated == 1) and 'trámite') or 'trámites'} marcados como no pagados.",
    )


mark_as_unpaid.short_description = "Marcar como no pagados"


# Custom Admin Site (optional for future customization)
class BackofficeAdminSite(admin.AdminSite):
    """Custom admin site for backoffice with specific configurations."""

    site_header = "Backoffice San Felipe"
    site_title = "Backoffice San Felipe"
    index_title = "Panel de Administración"

    def get_app_list(self, request, app_label=None):
        """Customize app list ordering."""
        app_list = super().get_app_list(request, app_label)

        # Reorder apps: tramites first, then catalogs, then others
        order = {"tramites": 0, "catalogos": 1, "costos": 2, "bitacora": 3}
        app_list.sort(key=lambda x: order.get(x["app_label"], 999))

        return app_list


# Uncomment to use custom admin site instead of default
# admin_site = BackofficeAdminSite(name="backoffice_admin")
