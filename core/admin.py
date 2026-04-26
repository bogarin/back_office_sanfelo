"""Django Admin global configuration.

Configures the admin interface for the backoffice with:
- Custom site headers and titles
- Custom User admin with role-based display
"""

from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from core.admin_utils import render_badge
from core.rbac.constants import BackOfficeRole

User = get_user_model()


# =============================================================================
# Admin Site Configuration
# =============================================================================

admin.site.site_header = 'Backoffice San Felipe'
admin.site.site_title = 'Backoffice San Felipe'
admin.site.index_title = 'Panel de Administración'


# =============================================================================
# Custom Forms
# =============================================================================


class CustomReadOnlyPasswordHashWidget(forms.Widget):
    """Custom widget for readonly password hash field."""

    template_name = 'core/widgets/read_only_password_hash.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        # Determine if password is usable
        usable_password = value and not value.startswith(UNUSABLE_PASSWORD_PREFIX)

        # Set button label
        context['button_label'] = _('Reset password') if usable_password else _('Set password')

        # Set password URL (will be overridden by admin if available)
        context['password_url'] = '../../password/'

        return context


class CustomUserAddForm(AdminUserCreationForm):
    """Form for adding users with role assignment in admin."""

    role = forms.ChoiceField(
        choices=[
            ('', 'Seleccionar rol...'),
        ],
        label='Rol',
        widget=forms.RadioSelect,
        required=True,
    )

    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ('username', 'last_name', 'first_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set role choices from BackOfficeRole enum
        self.fields['role'].choices = [
            ('', 'Seleccionar rol...'),
        ] + [(role, role.name.capitalize()) for role in BackOfficeRole]
        self.fields['role'].initial = BackOfficeRole.ANALISTA

    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def save(self, commit=True):
        """Save user with role assignment."""
        user = super().save(commit=False)
        return user


class CustomUserChangeForm(UserChangeForm):
    """Form for editing users with role assignment in admin."""

    role = forms.ChoiceField(
        choices=[
            ('', 'Sin rol'),
        ],
        label='Rol',
        widget=forms.Select,
        required=False,
    )

    class Meta(UserChangeForm.Meta):
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Use custom widget for password field
        if 'password' in self.fields:
            self.fields['password'].widget = CustomReadOnlyPasswordHashWidget()

        # Disable username field when editing existing user
        if self.instance and self.instance.pk and 'username' in self.fields:
            self.fields['username'].disabled = True
            self.fields['username'].help_text = _(
                'El nombre de usuario no se puede cambiar después de crearlo.'
            )

        # Disable is_staff field as it's managed by roles
        if 'is_staff' in self.fields:
            self.fields['is_staff'].disabled = True
            self.fields['is_staff'].help_text = _(
                'Este campo se gestiona automáticamente al asignar un rol.'
            )

        # Set role choices from BackOfficeRole enum
        self.fields['role'].choices = [
            ('', 'Sin rol'),
        ] + [(role, role.name.capitalize()) for role in BackOfficeRole]

        # Get current role from user's groups using the custom properties
        if self.instance and self.instance.pk:
            if self.instance.is_superuser:
                self.fields['role'].initial = 'superuser'
                self.fields['role'].choices = [('superusuario', 'Superusuario')] + self.fields[
                    'role'
                ].choices[1:]
            elif self.instance.is_administrador:
                self.fields['role'].initial = BackOfficeRole.ADMINISTRADOR
            elif self.instance.is_coordinador:
                self.fields['role'].initial = BackOfficeRole.COORDINADOR
            elif self.instance.is_analista:
                self.fields['role'].initial = BackOfficeRole.ANALISTA
            else:
                self.fields['role'].initial = ''


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
        'is_active',
    )

    list_filter = (
        'username',
        'is_active',
        'groups',
    )
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

    def get_form(self, request, obj=None, change=False, **kwargs):
        """Return CustomUserAddForm for new users, CustomUserChangeForm for edits."""
        if obj is None:
            return CustomUserAddForm
        return CustomUserChangeForm

    def save_model(self, request, obj, form, change):
        """Save user and manage role assignment."""
        super().save_model(request, obj, form, change)

        role = form.cleaned_data.get('role') if hasattr(form, 'cleaned_data') else None

        # Clear existing role groups
        obj.groups.remove(*obj.groups.filter(name__in=list(BackOfficeRole)))

        # Assign new role if provided
        if role and role in BackOfficeRole:
            group = Group.objects.filter(name=role).first()
            if group:
                obj.groups.add(group)
                # Only Administrador needs is_staff=True for admin access
                obj.is_staff = role == BackOfficeRole.ADMINISTRADOR

        # New users should be active by default
        if not change:
            obj.is_active = True

    def asignar_rol(self, request, queryset):
        """Admin action to assign roles to selected users."""
        selected_ids = list(queryset.values_list('id', flat=True))
        request.session['selected_user_ids'] = selected_ids
        request.session['user_ids_count'] = len(selected_ids)
        return HttpResponseRedirect('/admin/auth/user/asignar-rol/')

    asignar_rol.short_description = 'Asignar rol'

    def marcar_como_activo(self, request, queryset):
        """Admin action to mark selected users as active."""
        rows_updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{rows_updated} usuario(s) marcado(s) como activos.',
        )

    marcar_como_activo.short_description = 'Marcar como activos'

    def marcar_como_inactivo(self, request, queryset):
        """Admin action to mark selected users as inactive."""
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
