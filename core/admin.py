"""Django Admin global configuration.

Configures the admin interface for the backoffice with:
- Custom site headers and titles
- Custom User admin with role-based display
"""

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied

from core.admin_utils import render_badge
from core.forms import CustomUserAddForm, CustomUserChangeForm
from core.rbac.constants import BackOfficeRole
from core.admin_utils import render_quick_action, render_activo_badge

User = get_user_model()


# =============================================================================
# Admin Site Configuration
# =============================================================================

admin.site.site_header = 'Backoffice San Felipe'
admin.site.site_title = 'Backoffice San Felipe'
admin.site.index_title = 'Panel de Administración'


# =============================================================================
# Custom Filters
# =============================================================================


class EstadoFilter(SimpleListFilter):
    """Filter users by active status with Spanish labels."""

    title = 'Estado'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Activo'),
            ('0', 'Inactivo'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == '1':
            return queryset.filter(is_active=True)
        if value == '0':
            return queryset.filter(is_active=False)
        return queryset


class RolFilter(SimpleListFilter):
    """Filter users by role (group membership).

    Uses BackOfficeRole enum values for lookups, showing capitalised
    role names in the sidebar.  Includes a \"Sin rol\" option for users
    that do not belong to any role group.
    """

    title = 'Rol'
    parameter_name = 'rol'

    def lookups(self, request, model_admin):
        roles = [(role, role.capitalize()) for role in BackOfficeRole]
        return [*roles, ('sin_rol', 'Sin rol')]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'sin_rol':
            return queryset.exclude(groups__name__in=list(BackOfficeRole))
        if value in BackOfficeRole:
            return queryset.filter(groups__name=value)
        return queryset


# =============================================================================
# Custom User Admin
# =============================================================================


@admin.register(User)
class BackofficeUserAdmin(UserAdmin):
    """Custom User admin with role-based display.

    Replaces default User admin to show user role instead of is_staff.
    Uses badge styling for clear role identification.
    """

    # Custom list display with role instead of is_staff
    list_display = (
        'usuario',
        'rol',
        'usuario_estatus',
        'acciones',
    )

    list_filter = (
        EstadoFilter,
        RolFilter,
    )

    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_urls(self):
        """Register password change URL with custom name."""

        return [
            path(
                '<id>/password/',
                self.admin_site.admin_view(self.user_change_password),
                name='core_user_password_change',
            ),
            *super().get_urls(),
        ]

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'username',
                    ('first_name', 'last_name'),
                    'password',
                    'email',
                    'role',
                )
            },
        ),
    )

    # Fields to show in the add form
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    ('first_name', 'last_name'),  # Render on the same row
                    'email',
                    'password1',
                    'password2',
                    'role',
                ),
            },
        ),
    )

    # Add role as the first ordering field
    ordering = ('is_superuser', 'groups__name', 'username')

    # Admin actions
    actions = ('asignar_rol', 'marcar_como_activo', 'marcar_como_inactivo')

    # -- Superuser protection -------------------------------------------------

    def has_change_permission(self, request, obj=None):
        """Non-superusers cannot edit superusers."""
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Non-superusers cannot delete superusers."""
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly when a non-superuser views a superuser."""
        if obj and obj.is_superuser and not request.user.is_superuser:
            return ('username', 'first_name', 'last_name', 'email', 'password', 'role')
        return super().get_readonly_fields(request, obj)

    def changelist_view(self, request, extra_context=None):
        """Store request for use in list display methods."""
        self._request = request
        return super().changelist_view(request, extra_context)

    # -- Form configuration ---------------------------------------------------

    def get_form(self, request, obj=None, change=False, **kwargs):
        """Return CustomUserAddForm for new users, CustomUserChangeForm for edits."""
        if obj is None:
            return CustomUserAddForm
        return CustomUserChangeForm

    def save_model(self, request, obj, form, change):
        """Save user and manage role assignment.

        Sets is_staff and is_active BEFORE the actual save so they persist.
        Groups are managed AFTER save (M2M does not require obj.save()).
        """
        # Defense in depth: non-superusers cannot modify superusers
        if change and obj.is_superuser and not request.user.is_superuser:
            return

        role = form.cleaned_data.get('role') if hasattr(form, 'cleaned_data') else None

        # is_staff: any valid role grants admin access; no role revokes it
        if role and role in BackOfficeRole:
            obj.is_staff = True
        else:
            obj.is_staff = False

        # New users are always active
        if not change:
            obj.is_active = True

        super().save_model(request, obj, form, change)

        # Manage groups AFTER save (M2M, no save needed)
        obj.groups.remove(*obj.groups.filter(name__in=list(BackOfficeRole)))

        if role and role in BackOfficeRole:
            group = Group.objects.filter(name=role).first()
            if group:
                obj.groups.add(group)

    def asignar_rol(self, request, queryset):
        """Admin action to assign roles to selected users."""
        if not request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)
        selected_ids = list(queryset.values_list('id', flat=True))
        request.session['selected_user_ids'] = selected_ids
        request.session['user_ids_count'] = len(selected_ids)
        return HttpResponseRedirect(reverse('asignar-rol'))

    asignar_rol.short_description = 'Asignar rol'

    def marcar_como_activo(self, request, queryset):
        """Admin action to mark selected users as active."""
        if not request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)
        rows_updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{rows_updated} usuario(s) marcado(s) como activos.',
        )

    marcar_como_activo.short_description = 'Marcar como activos'

    def marcar_como_inactivo(self, request, queryset):
        """Admin action to mark selected users as inactive."""
        if not request.user.is_superuser:
            queryset = queryset.exclude(is_superuser=True)
        rows_updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{rows_updated} usuario(s) marcado(s) como inactivos.',
        )

    marcar_como_inactivo.short_description = 'Marcar como inactivos'

    def get_actions(self, request):
        """Remove default delete action — we use soft delete instead."""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def delete_model(self, request, obj):
        """Prevent hard delete — mark as inactive instead."""
        obj.is_active = False
        obj.save()

    def delete_queryset(self, request, queryset):
        """Prevent bulk hard delete — mark as inactive instead."""
        queryset.update(is_active=False)

    def usuario(self, obj) -> str:
        """Display user's full name or username."""
        full_name = f'{obj.get_full_name()}'.strip()
        return full_name if full_name else obj.username

    usuario.short_description = _('Usuario')

    def usuario_estatus(self, obj:User) -> str:
        return render_activo_badge(obj.is_active)

    def rol(self, obj) -> str:
        """Display user role as a badge.

        Uses the custom User properties (is_administrador, etc.) for
        clean role detection, falling back to cached ``obj.roles`` when
        the property's internal fallback is needed.
        """
        if obj.is_superuser:
            return render_badge(_('Superusuario'), 'badge-success')

        # Use custom properties for clean role detection
        if obj.is_administrador:
            return render_badge(_('Administrador'), 'badge-primary')
        if obj.is_coordinador:
            return render_badge(_('Coordinador'), 'badge-warning')
        if obj.is_analista:
            return render_badge(_('Analista'), 'badge-info')

        return render_badge(_('Sin rol'), 'badge-secondary')

    rol.short_description = _('Rol')
    rol.admin_order_field = 'groups__name'

    def user_change_password(self, request, id, form_url=''):
        """Override to prevent non-superusers from changing superuser passwords."""

        user = self.get_object(request, id)
        if user and user.is_superuser and not request.user.is_superuser:
            raise PermissionDenied
        return super().user_change_password(request, id, form_url)

    def acciones(self, obj:User) -> str:
        """Quick action links for the user list.

        Only shows password change link for superusers if current user
        is also a superuser.
        """
        # Don't show password change link for superusers unless current user is also superuser
        if obj.is_superuser and (not hasattr(self, '_request') or not self._request.user.is_superuser):
            return '—'
        url = reverse('admin:core_user_password_change', args=[obj.pk])
        return render_quick_action('🔑 Cambiar contraseña', target=url)
        # return format_html('<a href="{}">Cambiar password</a>', url)

    acciones.short_description = _('Acciones')
