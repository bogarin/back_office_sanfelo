"""Tests for core.forms: CustomUserAddForm, CustomUserChangeForm, CustomReadOnlyPasswordHashWidget.

Tests cover field configuration, role choices, validation, and widget rendering.
"""

import pytest
from django.contrib.auth import get_user_model

from core.forms import (
    CustomReadOnlyPasswordHashWidget,
    CustomUserAddForm,
    CustomUserChangeForm,
)
from core.rbac.constants import BackOfficeRole

User = get_user_model()


# ---------------------------------------------------------------------------
# CustomReadOnlyPasswordHashWidget
# ---------------------------------------------------------------------------


class TestCustomReadOnlyPasswordHashWidget:
    """Tests for the custom password hash widget."""

    def test_usable_password_context(self):
        """Usable password shows 'Reset password' label."""
        widget = CustomReadOnlyPasswordHashWidget()
        context = widget.get_context('password', 'pbkdf2_sha256$hash', {})
        assert context['button_label'] == 'Restablecer contraseña'

    def test_unusable_password_context(self):
        """Unusable password shows 'Establecer contraseña' label."""
        widget = CustomReadOnlyPasswordHashWidget()
        context = widget.get_context('password', '!abc123', {})
        assert context['button_label'] == 'Establecer contraseña'

    def test_none_password_context(self):
        """None password shows 'Establecer contraseña' label."""
        widget = CustomReadOnlyPasswordHashWidget()
        context = widget.get_context('password', None, {})
        assert context['button_label'] == 'Establecer contraseña'

    def test_password_url_in_context(self):
        """Context includes the password change URL."""
        widget = CustomReadOnlyPasswordHashWidget()
        context = widget.get_context('password', 'pbkdf2_sha256$hash', {})
        assert 'password_url' in context
        assert context['password_url'] == '../../password/'


# ---------------------------------------------------------------------------
# CustomUserAddForm
# ---------------------------------------------------------------------------


class TestCustomUserAddForm:
    """Tests for CustomUserAddForm — user creation with role selection."""

    def test_role_field_has_backoffice_choices(self):
        """Role field includes all BackOfficeRole options."""
        form = CustomUserAddForm()
        role_values = [choice[0] for choice in form.fields['role'].choices]
        for role in BackOfficeRole:
            assert role in role_values

    def test_role_field_has_empty_choice(self):
        """Role field starts with an empty 'Seleccionar rol...' choice."""
        form = CustomUserAddForm()
        assert form.fields['role'].choices[0] == ('', 'Seleccionar rol...')

    def test_role_field_required(self):
        """Role field is required."""
        form = CustomUserAddForm()
        assert form.fields['role'].required is True

    @pytest.mark.django_db
    def test_valid_data(self, db):
        """Form is valid with all required fields + role."""
        form = CustomUserAddForm(
            data={
                'username': 'newuser',
                'password1': 'SecurePass123!',
                'password2': 'SecurePass123!',
                'role': BackOfficeRole.ANALISTA,
            }
        )
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_duplicate_email_rejected(self, db):
        """clean_email rejects emails already in use."""
        User.objects.create_user(
            username='existing',
            email='taken@example.com',
            password='pass123',
        )
        form = CustomUserAddForm(
            data={
                'username': 'newuser',
                'password1': 'SecurePass123!',
                'password2': 'SecurePass123!',
                'email': 'taken@example.com',
                'role': BackOfficeRole.ANALISTA,
            }
        )
        assert not form.is_valid()
        assert 'email' in form.errors

    @pytest.mark.django_db
    def test_unique_email_accepted(self, db):
        """clean_email accepts emails not yet in use."""
        form = CustomUserAddForm(
            data={
                'username': 'newuser',
                'password1': 'SecurePass123!',
                'password2': 'SecurePass123!',
                'email': 'unique@example.com',
                'role': BackOfficeRole.ANALISTA,
            }
        )
        assert form.is_valid(), form.errors

    @pytest.mark.django_db
    def test_save_returns_user_without_commit(self, db):
        """save(commit=False) returns user without persisting."""
        form = CustomUserAddForm(
            data={
                'username': 'newuser',
                'password1': 'SecurePass123!',
                'password2': 'SecurePass123!',
                'role': BackOfficeRole.ANALISTA,
            }
        )
        assert form.is_valid(), form.errors
        user = form.save(commit=False)
        assert isinstance(user, User)
        assert user.pk is None


# ---------------------------------------------------------------------------
# CustomUserChangeForm
# ---------------------------------------------------------------------------


class TestCustomUserChangeForm:
    """Tests for CustomUserChangeForm — user editing with role display."""

    @pytest.mark.django_db
    def test_role_choices_include_empty(self, db):
        """Role field has 'Sin rol' empty option."""
        user = User.objects.create_user(
            username='edituser',
            password='testpass123',
            is_staff=True,
        )
        form = CustomUserChangeForm(instance=user)
        assert form.fields['role'].choices[0] == ('', 'Sin rol')

    @pytest.mark.django_db
    def test_role_choices_include_all_roles(self, db):
        """Role field includes all BackOfficeRole options."""
        user = User.objects.create_user(
            username='edituser',
            password='testpass123',
            is_staff=True,
        )
        form = CustomUserChangeForm(instance=user)
        role_values = [choice[0] for choice in form.fields['role'].choices]
        for role in BackOfficeRole:
            assert role in role_values

    @pytest.mark.django_db
    def test_role_field_not_required(self, db):
        """Role field is optional on change form."""
        user = User.objects.create_user(
            username='edituser',
            password='testpass123',
            is_staff=True,
        )
        form = CustomUserChangeForm(instance=user)
        assert form.fields['role'].required is False

    @pytest.mark.django_db
    def test_username_disabled_on_existing_user(self, db):
        """Username field is disabled when editing existing user."""
        user = User.objects.create_user(
            username='edituser',
            password='testpass123',
            is_staff=True,
        )
        form = CustomUserChangeForm(instance=user)
        assert form.fields['username'].disabled is True

    @pytest.mark.django_db
    def test_password_uses_custom_widget(self, db):
        """Password field uses CustomReadOnlyPasswordHashWidget."""
        user = User.objects.create_user(
            username='edituser',
            password='testpass123',
            is_staff=True,
        )
        form = CustomUserChangeForm(instance=user)
        assert isinstance(
            form.fields['password'].widget,
            CustomReadOnlyPasswordHashWidget,
        )

    @pytest.mark.django_db
    def test_analista_initial_role(self, db):
        """Analista user gets ANALISTA as initial role value."""
        user = User.objects.create_user(
            username='edituser',
            password='testpass123',
            is_staff=True,
        )
        from django.contrib.auth.models import Group

        user.groups.add(Group.objects.get_or_create(name=BackOfficeRole.ANALISTA)[0])

        form = CustomUserChangeForm(instance=user)
        assert form.fields['role'].initial == BackOfficeRole.ANALISTA

    @pytest.mark.django_db
    def test_coordinador_initial_role(self, db):
        """Coordinador user gets COORDINADOR as initial role value."""
        user = User.objects.create_user(
            username='edituser',
            password='testpass123',
            is_staff=True,
        )
        from django.contrib.auth.models import Group

        user.groups.add(
            Group.objects.get_or_create(name=BackOfficeRole.COORDINADOR)[0],
        )

        form = CustomUserChangeForm(instance=user)
        assert form.fields['role'].initial == BackOfficeRole.COORDINADOR

    @pytest.mark.django_db
    def test_administrador_initial_role(self, db):
        """Administrador user gets ADMINISTRADOR as initial role value."""
        user = User.objects.create_user(
            username='edituser',
            password='testpass123',
            is_staff=True,
        )
        from django.contrib.auth.models import Group

        user.groups.add(
            Group.objects.get_or_create(name=BackOfficeRole.ADMINISTRADOR)[0],
        )

        form = CustomUserChangeForm(instance=user)
        assert form.fields['role'].initial == BackOfficeRole.ADMINISTRADOR

    @pytest.mark.django_db
    def test_superuser_shows_superusuario_choice(self, db):
        """Superuser gets 'superusuario' as first role choice."""
        user = User.objects.create_superuser(
            username='superuser',
            email='su@example.com',
            password='testpass123',
        )
        form = CustomUserChangeForm(instance=user)
        first_choice_value = form.fields['role'].choices[0][0]
        assert first_choice_value == 'superusuario'

    @pytest.mark.django_db
    def test_no_role_user_initial_empty(self, db):
        """User without role gets empty string as initial role."""
        user = User.objects.create_user(
            username='norole',
            password='testpass123',
            is_staff=True,
        )
        form = CustomUserChangeForm(instance=user)
        assert form.fields['role'].initial == ''
