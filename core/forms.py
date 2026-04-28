"""Custom forms for the backoffice admin interface.

Provides forms for user management with role assignment, including:
- Custom add form with role selection via radio buttons
- Custom change form with role display and password hash widget
- Custom readonly password hash widget
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.utils.translation import gettext_lazy as _

from core.rbac.constants import BackOfficeRole

User = get_user_model()


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
        widget=forms.Select,
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
                self.fields['role'].initial = BackOfficeRole.ANALISTA
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
