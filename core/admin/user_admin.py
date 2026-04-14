"""Custom User admin configuration.

Provides a custom User admin with role-based display:
- Shows user role instead of is_staff
- Uses badge styling for clear role identification
- Includes bulk action to assign roles
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from core.admin_utils import render_badge
from core.rbac.constants import BackOfficeRole

UserModel = get_user_model()


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
        model = UserModel
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
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def save(self, commit=True):
        """Save user with role assignment."""
        user = super().save(commit=False)

        # Store role for later if commit=False
        role = self.cleaned_data.get('role')
        if role:
            group = Group.objects.filter(name=role).first()
            if group:
                self._role_group = group

        # Save the user (parent class handles password hashing)
        if commit:
            user.save()
            # Add to group if stored
            if hasattr(self, '_role_group') and self._role_group:
                user.groups.add(self._role_group)

        return user

    def save_m2m(self):
        """Handle many-to-many relationships including role assignment."""
        # Add user to the assigned role group
        if hasattr(self, '_role_group') and self._role_group and hasattr(self.instance, 'pk'):
            self.instance.groups.add(self._role_group)


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

        # Get current role from user's groups
        if self.instance and self.instance.pk:
            roles = getattr(self.instance, 'roles', None)
            if roles is None:
                # Fallback for instances not processed by middleware
                roles = set(self.instance.groups.values_list('name', flat=True))

            if self.instance.is_superuser:
                self.fields['role'].initial = 'superuser'
                self.fields['role'].choices = [('superusuario', 'Superusuario')] + self.fields[
                    'role'
                ].choices[1:]
            elif BackOfficeRole.ADMINISTRADOR in roles:
                self.fields['role'].initial = BackOfficeRole.ADMINISTRADOR
            elif BackOfficeRole.COORDINADOR in roles:
                self.fields['role'].initial = BackOfficeRole.COORDINADOR
            elif BackOfficeRole.ANALISTA in roles:
                self.fields['role'].initial = BackOfficeRole.ANALISTA
            else:
                self.fields['role'].initial = ''


class BackofficeUserAdmin(UserAdmin):
    """
    Custom User admin with role-based display.

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
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
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

    # Disable is_staff in the change form for editing users
    def get_form(self, request, obj=None, **kwargs):
        """
        Return CustomUserAddForm for new users, CustomUserChangeForm for edits.

        When adding a new user, return CustomUserAddForm with role selection.
        When editing an existing user, return CustomUserChangeForm with role management.
        """
        if obj is None:
            return CustomUserAddForm
        return CustomUserChangeForm

    def save_model(self, request, obj, form, change):
        """
        Save user and manage role assignment.

        When adding a new user, assign the role selected in the form.
        When editing an existing user, update the role based on form selection.
        Users created via this admin are not staff - they access the system
        through front-end views, not the Django admin.
        """
        super().save_model(request, obj, form, change)

        # Handle role assignment
        role = form.cleaned_data.get('role') if hasattr(form, 'cleaned_data') else None

        if change:  # Editing an existing user
            # Clear existing role groups
            obj.groups.remove(*obj.groups.filter(name__in=list(BackOfficeRole)))

            # Add new role group
            if role and role != '' and role != 'superuser':
                group = Group.objects.filter(name=role).first()
                if group:
                    obj.groups.add(group)
        else:  # Adding a new user
            # Assign role or fallback to default
            if role:
                group = Group.objects.filter(name=role).first()
            else:
                # Fallback to default role (Analista)
                group = Group.objects.filter(name=BackOfficeRole.ANALISTA).first()

            if group:
                obj.groups.add(group)

    # Add role as the first ordering field
    ordering = ('is_superuser', 'groups__name', 'username')

    # Admin actions
    actions = ('asignar_rol', 'marcar_como_activo', 'marcar_como_inactivo')

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

    # Disable delete action - use soft delete instead
    def get_actions(self, request):
        """
        Remove default delete action.

        We use soft delete (mark as inactive) instead of hard delete.
        """
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def delete_model(self, request, obj):
        """
        Prevent hard delete of users.

        Instead, mark the user as inactive (soft delete).
        """
        obj.is_active = False
        obj.save()

    def delete_queryset(self, request, queryset):
        """
        Prevent bulk hard delete of users.

        Instead, mark all selected users as inactive (soft delete).
        """
        queryset.update(is_active=False)

    def usuario(self, obj: UserModel) -> str:
        """
        Display user's full name or username.

        Args:
            obj: User instance

        Returns:
            str: Full name if available, otherwise username
        """
        full_name = f'{obj.get_full_name()}'.strip()
        return full_name if full_name else obj.username

    usuario.short_description = _('Usuario')

    def rol(self, obj: UserModel) -> str:
        """
        Display user role as a badge.

        Role priority:
        - Superuser (highest)
        - Administrador group
        - Coordinador group
        - Analista group
        - None (no role)

        Args:
            obj: User instance

        Returns:
            str: HTML badge with role text and styling
        """
        if obj.is_superuser:
            return render_badge(_('Superusuario'), 'badge-success')

        # Use cached roles when available (avoids per-row DB queries)
        roles = getattr(obj, 'roles', None)
        if roles is None:
            roles = set(obj.groups.values_list('name', flat=True))

        # Check groups in priority order
        if BackOfficeRole.ADMINISTRADOR in roles:
            return render_badge(_('Administrador'), 'badge-primary')

        if BackOfficeRole.COORDINADOR in roles:
            return render_badge(_('Coordinador'), 'badge-warning')

        if BackOfficeRole.ANALISTA in roles:
            return render_badge(_('Analista'), 'badge-info')

        return render_badge(_('Sin rol'), 'badge-secondary')

    rol.short_description = _('Rol')
    rol.admin_order_field = 'groups__name'
