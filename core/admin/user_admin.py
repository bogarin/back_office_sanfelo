"""Custom User admin configuration.

Provides a custom User admin with role-based display:
- Shows user role instead of is_staff
- Uses badge styling for clear role identification
- Includes bulk action to assign roles
"""

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from core.admin_utils import render_badge


class CustomUserAddForm(forms.Form):
    """Form for adding users with role assignment."""

    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        required=True,
    )
    email = forms.EmailField(
        label='Correo electrónico',
        required=True,
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        required=True,
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput,
        required=True,
    )
    role = forms.ChoiceField(
        choices=[
            ('', 'Seleccionar rol...'),
        ],
        label='Rol',
        widget=forms.RadioSelect,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set role choices dynamically based on available groups
        self.fields['role'].choices = [
            (settings.ADMINISTRADOR_GROUP_NAME, 'Administrador'),
            (settings.COORDINADOR_GROUP_NAME, 'Coordinador'),
            (settings.ANALISTA_GROUP_NAME, 'Analista'),
        ]
        self.fields['role'].initial = settings.ANALISTA_GROUP_NAME

    def clean_username(self):
        """Validate username is unique."""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Ya existe un usuario con este nombre de usuario.')
        return username

    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def clean_password2(self):
        """Validate passwords match."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return password2

    def clean_password1(self):
        """Validate password length."""
        password1 = self.cleaned_data.get('password1')
        if password1 and len(password1) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
        return password1


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

    # Disable is_staff in the change form for editing users
    def get_form(self, request, obj=None, **kwargs):
        """
        Disable is_staff for editing users.

        When editing an existing user, disable is_staff field as it's managed by roles.
        """
        form = super().get_form(request, obj, **kwargs)

        if obj is not None:  # Editing an existing user
            if 'is_staff' in form.base_fields:
                form.base_fields['is_staff'].disabled = True
                form.base_fields['is_staff'].help_text = _(
                    'Este campo se gestiona automáticamente al asignar un rol.'
                )

        return form

    def save_model(self, request, obj, form, change):
        """
        Save user and assign selected role.

        When adding a new user, assign the default role and set is_staff=True.
        When editing, preserve the super method behavior.
        """
        super().save_model(request, obj, form, change)

        if not change:  # Adding a new user
            # Assign default role (Analista) to new users
            group = Group.objects.filter(name=settings.ANALISTA_GROUP_NAME).first()
            if group:
                obj.groups.add(group)
                obj.is_staff = True
                obj.save()

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

    def usuario(self, obj: User) -> str:
        """
        Display user's full name or username.

        Args:
            obj: User instance

        Returns:
            str: Full name if available, otherwise username
        """
        full_name = f'{obj.first_name} {obj.last_name}'.strip()
        return full_name if full_name else obj.username

    usuario.short_description = _('Usuario')

    def rol(self, obj: User) -> str:
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

        # Check groups in priority order
        if obj.groups.filter(name=settings.ADMINISTRADOR_GROUP_NAME).exists():
            return render_badge(_('Administrador'), 'badge-primary')

        if obj.groups.filter(name=settings.COORDINADOR_GROUP_NAME).exists():
            return render_badge(_('Coordinador'), 'badge-warning')

        if obj.groups.filter(name=settings.ANALISTA_GROUP_NAME).exists():
            return render_badge(_('Analista'), 'badge-info')

        return render_badge(_('Sin rol'), 'badge-secondary')

    rol.short_description = _('Rol')
    rol.admin_order_field = 'groups__name'
